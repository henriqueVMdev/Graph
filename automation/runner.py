"""
Runner da automação — thread daemon que, a cada tick (~20s), processa os
candles FECHADOS novos de cada deployment ativo, em ordem.

Princípios:
- Nada é decidido por relógio local: candle fechado sse
  open_ts + tf <= now da EXCHANGE (fetch_time), com descarte defensivo da
  última linha. Skew do relógio exposto em status().
- PC desligado => ao religar, os candles perdidos são reprocessados em
  sequência (replay determinístico; ordens/posições avançam no candle certo).
- try/except por deployment: um deployment em erro não derruba os demais.
- Guard do reloader do Flask: iniciar via ensure_started() (idempotente);
  o server só chama no processo real (WERKZEUG_RUN_MAIN).
"""

from __future__ import annotations

import threading
import time
import traceback

import pandas as pd

from . import engine_paper as engine
from . import signals, store

_TICK_SECONDS = 20
_WARMUP_BARS = 450          # signal() exige >=400 candles fechados

_TF_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
          "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "1d": 86_400_000}


def tf_ms(interval: str) -> int:
    if interval not in _TF_MS:
        raise ValueError(f"timeframe não suportado: {interval}")
    return _TF_MS[interval]


class Runner(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="automation-runner")
        self._stop = threading.Event()
        self.last_tick_at: int | None = None
        self.last_error: str | None = None
        self.clock_skew_ms: int | None = None

    # ── ciclo ────────────────────────────────────────────────────────────
    def run(self):
        store.init_db()
        while not self._stop.is_set():
            try:
                self._tick()
                self.last_error = None
            except Exception as e:                      # nunca morrer
                self.last_error = f"{e}\n{traceback.format_exc()[-1000:]}"
            self.last_tick_at = int(time.time() * 1000)
            self._stop.wait(_TICK_SECONDS)

    def stop(self):
        self._stop.set()

    # ── tick ─────────────────────────────────────────────────────────────
    def _tick(self):
        deps = store.list_deployments(status="running")
        if not deps:
            return
        # agrupa por fonte de candles para buscar uma vez só
        by_feed: dict = {}
        for dep in deps:
            by_feed.setdefault((dep["exchange"], dep["symbol"], dep["interval"]),
                               []).append(dep)

        for (exchange, symbol, interval), group in by_feed.items():
            now_ex = self._exchange_now_ms(exchange)
            gap_bars = max(
                (now_ex - (d["last_candle_ts"] or now_ex)) // tf_ms(interval)
                for d in group)
            df = self._fetch_closed(exchange, symbol, interval,
                                    int(gap_bars) + _WARMUP_BARS, now_ex)
            if df is None or len(df) < 3:
                continue
            for dep in group:
                try:
                    self._process_deployment(dep, df, interval)
                except Exception as e:
                    store.update_deployment(dep["id"], status="error",
                                            error=str(e)[:500])
                    store.add_event(dep["id"], "runner_error", str(e)[:500],
                                    level="error")

    def _exchange_now_ms(self, exchange: str) -> int:
        try:
            from market_data import get_exchange
            now = int(get_exchange(exchange).fetch_time())
            self.clock_skew_ms = now - int(time.time() * 1000)
            return now
        except Exception:
            # fallback: relógio local (skew desconhecido)
            self.clock_skew_ms = None
            return int(time.time() * 1000)

    def _fetch_closed(self, exchange, symbol, interval, n_bars, now_ex):
        """Candles FECHADOS: descarta toda linha com open_ts + tf > now_ex."""
        from market_data import fetch_ohlcv
        df = fetch_ohlcv(symbol, interval, exchange=exchange,
                         total=max(int(n_bars), _WARMUP_BARS))
        ts = (df.index - pd.Timestamp(0)).total_seconds().values * 1000
        closed = ts + tf_ms(interval) <= now_ex
        return df[closed]

    # ── por deployment ───────────────────────────────────────────────────
    def _process_deployment(self, dep, df_closed, interval):
        if dep["mode"] != "paper":
            # modo demo entra na Fase 3 (executor_bybit)
            from . import executor_bybit
            executor_bybit.process(dep, df_closed, interval)
            store.update_deployment(dep["id"], last_tick_at=int(time.time() * 1000))
            return

        dep_id = dep["id"]
        tfm = tf_ms(interval)
        ts_all = ((df_closed.index - pd.Timestamp(0)).total_seconds().values
                  * 1000).astype("int64")

        last = dep["last_candle_ts"]
        if last is None:
            # primeiro tick: não replays histórico — só arma o sinal do
            # último candle fechado.
            last = int(ts_all[-2]) if len(ts_all) >= 2 else int(ts_all[-1]) - tfm

        new_idx = [k for k, t in enumerate(ts_all) if t > last]
        equity = float(dep["equity"])

        for k in new_idx:
            candle = {
                "ts": int(ts_all[k]),
                "open": float(df_closed["Open"].iloc[k]),
                "high": float(df_closed["High"].iloc[k]),
                "low": float(df_closed["Low"].iloc[k]),
                "close": float(df_closed["Close"].iloc[k]),
            }
            pos = store.get_open_position(dep_id)

            # 1) posição aberta: saída (SL -> TP -> time-stop) ou envelhece
            if pos:
                exit_ = engine.check_exit(pos, candle)
                if exit_:
                    res = engine.close_pnl(pos, exit_["exit_price"],
                                           exit_["exit_fee_rate"], equity)
                    store.update_position(
                        pos["id"], status="closed",
                        exit_price=exit_["exit_price"],
                        exit_candle_ts=candle["ts"],
                        exit_reason=exit_["reason"],
                        pnl_pct=res["pnl_pct"], pnl_quote=res["pnl_quote"],
                        fees_quote=res["fees_quote"])
                    equity = res["new_equity"]
                    store.update_deployment(dep_id, equity=equity)
                    store.add_event(dep_id, "position_closed",
                                    f"{exit_['reason']} @ {exit_['exit_price']:.2f} "
                                    f"({res['pnl_pct']:+.2f}%)",
                                    data={"pnl_pct": res["pnl_pct"]})
                    pos = None
                else:
                    store.update_position(pos["id"], bars_held=pos["bars_held"] + 1)
                    pos["bars_held"] += 1

            # 2) flat no início do candle: ordem working faz fill (cross) ou expira
            else:
                order = store.get_working_order(dep_id)
                if order:
                    if candle["ts"] == order["valid_candle_ts"] \
                            and engine.check_entry_fill(order, candle):
                        p = engine.open_position_from_order(order, equity, candle["ts"])
                        pos_id = store.open_position(
                            dep_id, p["side"], p["qty"], p["exposure"],
                            p["entry_price"], p["entry_candle_ts"],
                            p["tp_price"], p["sl_price"], p["max_bars"])
                        store.update_order(order["id"], status="filled")
                        store.add_event(dep_id, "order_filled",
                                        f"Entrada {'long' if p['side'] == 1 else 'short'} "
                                        f"@ {p['entry_price']:.2f}")
                        pos = {**p, "id": pos_id, "status": "open"}
                        # mesmo candle pode estopar (igual ao backtest)
                        exit_ = engine.check_exit(pos, candle)
                        if exit_:
                            res = engine.close_pnl(pos, exit_["exit_price"],
                                                   exit_["exit_fee_rate"], equity)
                            store.update_position(
                                pos_id, status="closed",
                                exit_price=exit_["exit_price"],
                                exit_candle_ts=candle["ts"],
                                exit_reason=exit_["reason"],
                                pnl_pct=res["pnl_pct"],
                                pnl_quote=res["pnl_quote"],
                                fees_quote=res["fees_quote"])
                            equity = res["new_equity"]
                            store.update_deployment(dep_id, equity=equity)
                            store.add_event(dep_id, "position_closed",
                                            f"{exit_['reason']} (mesmo candle) "
                                            f"({res['pnl_pct']:+.2f}%)")
                            pos = None
                        else:
                            # candle de entrada conta como 1 barra (j-i+1 do backtest)
                            store.update_position(pos_id, bars_held=1)
                            pos["bars_held"] = 1
                    elif candle["ts"] >= order["valid_candle_ts"]:
                        store.update_order(order["id"], status="expired")

            # 3) snapshot de equity (mark-to-market do candle)
            store.add_equity_snapshot(
                dep_id, candle["ts"],
                engine.mark_to_market(pos, equity, candle["close"]))

            # 4) flat ao fim do candle: pedir novo sinal p/ o PRÓXIMO candle
            if pos is None:
                stale = store.get_working_order(dep_id)
                if stale:                       # ordem antiga nunca avaliada
                    store.update_order(stale["id"], status="cancelled")
                df_hist = df_closed.iloc[:k + 1]
                if len(df_hist) >= 400:
                    sig = signals.get_signal(dep["strategy_file"], df_hist,
                                             dep["params"])
                    if sig:
                        store.create_order(
                            dep_id, "entry", sig["side"], sig["type"],
                            float(sig["price"]), None,
                            candle["ts"] + tfm,
                            tp_pct=sig["tp_pct"], sl_pct=sig["sl_pct"],
                            max_bars=sig["max_bars"], exposure=sig["exposure"])
                        store.add_event(
                            dep_id, "order_placed",
                            f"Limite {'long' if sig['side'] == 1 else 'short'} "
                            f"@ {sig['price']:.2f} (válida 1 candle)")

            store.update_deployment(dep_id, last_candle_ts=candle["ts"],
                                    last_tick_at=int(time.time() * 1000))

    # ── status ───────────────────────────────────────────────────────────
    def status(self) -> dict:
        return {
            "alive": self.is_alive(),
            "last_tick_at": self.last_tick_at,
            "last_error": self.last_error,
            "clock_skew_ms": self.clock_skew_ms,
            "tick_seconds": _TICK_SECONDS,
        }


_runner: Runner | None = None
_runner_lock = threading.Lock()


def get_runner() -> Runner:
    global _runner
    with _runner_lock:
        if _runner is None:
            _runner = Runner()
        return _runner


def ensure_started() -> Runner:
    """Inicia o runner uma única vez (idempotente, thread-safe)."""
    r = get_runner()
    with _runner_lock:
        if not r.is_alive():
            try:
                r.start()
            except RuntimeError:        # já foi start()ado e morreu — recria
                globals()["_runner"] = Runner()
                globals()["_runner"].start()
                return globals()["_runner"]
    return r
