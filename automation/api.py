"""
Blueprint Flask do módulo de automação — prefixo /api/automation.

server.py só registra: app.register_blueprint(automation_bp).
Estilo dos endpoints segue o restante do server: jsonify + {"error": str}.
"""

from __future__ import annotations

import time

import pandas as pd
from flask import Blueprint, jsonify, request

from . import monitor, signals, store
from .runner import ensure_started, get_runner, tf_ms

automation_bp = Blueprint("automation", __name__, url_prefix="/api/automation")

store.init_db()          # idempotente — garante o schema em qualquer entrada

_VALID_MODES = ("paper", "demo", "real")

# Perfis de conta p/ mode=real -> prefixo das chaves no .env
_ACCOUNT_PROFILES = {"prop": "BYBIT_PROP", "personal": "BYBIT_REAL"}


def _account_configured(profile: str) -> bool:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    prefix = _ACCOUNT_PROFILES[profile]
    return bool(os.getenv(f"{prefix}_API_KEY", "").strip()
                and os.getenv(f"{prefix}_API_SECRET", "").strip())


@automation_bp.get("/deployments")
def list_deployments():
    deps = store.list_deployments()
    out = []
    for d in deps:
        pos = store.get_open_position(d["id"])
        out.append({
            "id": d["id"], "name": d["name"], "strategy_file": d["strategy_file"],
            "symbol": d["symbol"], "interval": d["interval"],
            "exchange": d["exchange"], "mode": d["mode"],
            "account": d.get("account"), "status": d["status"],
            "initial_capital": d["initial_capital"], "equity": d["equity"],
            "return_pct": round((d["equity"] / d["initial_capital"] - 1) * 100, 2)
                          if d["initial_capital"] else None,
            "open_position": bool(pos),
            "last_candle_ts": d["last_candle_ts"],
            "last_tick_at": d["last_tick_at"], "error": d["error"],
            "created_at": d["created_at"],
        })
    return jsonify({"deployments": out})


@automation_bp.post("/deployments")
def create_deployment():
    try:
        body = request.get_json(force=True) or {}
        strategy_file = body.get("strategy_file", "")
        mode = body.get("mode", "paper")
        symbol = body.get("symbol", "")
        interval = body.get("interval", "15m")
        if not symbol:
            return jsonify({"error": "symbol obrigatório"}), 400
        if mode not in _VALID_MODES:
            return jsonify({"error": f"mode deve ser um de {_VALID_MODES}"}), 400
        tf_ms(interval)                       # valida timeframe suportado
        if not signals.is_automatable(strategy_file):
            return jsonify({"error": f"Estratégia '{strategy_file}' não expõe "
                                     "signal() — não automatizável"}), 400
        initial_capital = float(body.get("initial_capital", 10000))
        if initial_capital <= 0:
            return jsonify({"error": "initial_capital deve ser positivo"}), 400

        # Guardrails opcionais (default: nenhum) — números devem ser positivos
        guardrails = body.get("guardrails") or None
        if guardrails:
            for k in ("daily_loss_pct", "max_loss_pct", "max_notional"):
                v = guardrails.get(k)
                if v is not None and float(v) <= 0:
                    return jsonify({"error": f"guardrail {k} deve ser positivo"}), 400

        account = body.get("account")
        if mode == "real":
            if account not in _ACCOUNT_PROFILES:
                return jsonify({"error": "mode=real exige account 'prop' ou "
                                         "'personal'"}), 400
            if not _account_configured(account):
                return jsonify({"error": f"chaves da conta '{account}' ausentes "
                                         "no .env"}), 400
            # one-way mode: a reconciliação adota posições/cancela órfãs por
            # símbolo — 2 deployments reais no mesmo símbolo+conta conflitam
            for d in store.list_deployments():
                if (d["mode"] == "real" and d["status"] != "stopped"
                        and d["symbol"] == symbol and d.get("account") == account):
                    return jsonify({"error": f"já existe deployment REAL ativo em "
                                             f"{symbol} na conta '{account}'"}), 409
        else:
            account = None

        dep_id = store.create_deployment(
            name=body.get("name") or f"{strategy_file} {symbol} {interval}",
            strategy_file=strategy_file,
            params=body.get("params", {}),
            symbol=symbol, interval=interval,
            exchange=(body.get("exchange") or "bybit").lower(),
            mode=mode, initial_capital=initial_capital,
            backtest_ref=body.get("backtest_ref"),
            account=account, guardrails=guardrails)
        store.add_event(dep_id, "created",
                        f"Deployment criado ({mode}"
                        + (f", conta {account}" if account else "") + ")")
        return jsonify({"id": dep_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@automation_bp.post("/deployments/<dep_id>/start")
def start_deployment(dep_id):
    dep = store.get_deployment(dep_id)
    if not dep:
        return jsonify({"error": "deployment não encontrado"}), 404
    if dep["mode"] == "real":
        from . import executor_bybit
        try:
            executor_bybit._get_client(dep.get("account")).fetch_time()
        except Exception as e:
            return jsonify({"error": f"exchange inacessível para conta "
                                     f"'{dep.get('account')}': {str(e)[:200]}"}), 400
    store.update_deployment(dep_id, status="running", error=None,
                            started_at=int(time.time() * 1000))
    store.add_event(dep_id, "started", "Deployment iniciado")
    ensure_started()
    return jsonify({"ok": True, "status": "running"})


@automation_bp.post("/deployments/<dep_id>/stop")
def stop_deployment(dep_id):
    dep = store.get_deployment(dep_id)
    if not dep:
        return jsonify({"error": "deployment não encontrado"}), 404
    body = request.get_json(silent=True) or {}
    close_pos = bool(body.get("close_position", False))

    if close_pos:
        pos = store.get_open_position(dep_id)
        if pos:
            try:
                if dep["mode"] == "paper":
                    from . import engine_paper
                    engine_paper.close_position_now(dep, pos)
                else:
                    # demo/real: cancela ordem, fecha a mercado NA EXCHANGE e
                    # reconcilia o PnL real (antes o stop demo só fechava no DB)
                    from . import executor_bybit
                    executor_bybit.stop_close(dep, pos)
            except Exception as e:
                return jsonify({"error": f"falha ao fechar posição: {e}"}), 500

    # cancela ordem pendente
    order = store.get_working_order(dep_id)
    if order:
        store.update_order(order["id"], status="cancelled")

    store.update_deployment(dep_id, status="stopped",
                            stopped_at=int(time.time() * 1000))
    store.add_event(dep_id, "stopped",
                    "Parado" + (" (posição fechada a mercado)" if close_pos else
                                " (posição mantida)" if store.get_open_position(dep_id)
                                else ""))
    return jsonify({"ok": True, "status": "stopped"})


@automation_bp.get("/accounts")
def list_accounts():
    """Perfis de conta real disponíveis e se as chaves estão no .env."""
    return jsonify({"accounts": [
        {"id": p, "configured": _account_configured(p)}
        for p in _ACCOUNT_PROFILES
    ]})


@automation_bp.delete("/deployments/<dep_id>")
def delete_deployment(dep_id):
    dep = store.get_deployment(dep_id)
    if not dep:
        return jsonify({"error": "deployment não encontrado"}), 404
    if dep["status"] == "running":
        return jsonify({"error": "pare o deployment antes de excluir"}), 400
    store.delete_deployment(dep_id)
    return jsonify({"ok": True})


@automation_bp.get("/deployments/<dep_id>/status")
def deployment_status(dep_id):
    dep = store.get_deployment(dep_id)
    if not dep:
        return jsonify({"error": "deployment não encontrado"}), 404
    pos = store.get_open_position(dep_id)
    order = store.get_working_order(dep_id)
    trades = store.list_closed_positions(dep_id)
    curve = store.get_equity_curve(dep_id)
    events = store.list_events(dep_id, limit=80)
    return jsonify({
        "deployment": dep,
        "position": pos,
        "working_order": order,
        "trades": trades,
        "equity_curve": {
            "dates": [pd.Timestamp(ts, unit="ms").isoformat() for ts, _ in curve],
            "values": [v for _, v in curve],
        },
        "events": events,
        "comparison": monitor.compare(dep, trades),
    })


@automation_bp.get("/runner/status")
def runner_status():
    r = get_runner()
    running = store.list_deployments(status="running")
    st = r.status()
    st["active_count"] = len(running)
    # se há deployments ativos mas o runner morreu, religa
    if running and not st["alive"]:
        ensure_started()
        st = get_runner().status()
        st["active_count"] = len(running)
    return jsonify(st)
