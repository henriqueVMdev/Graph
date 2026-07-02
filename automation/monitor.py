"""
Monitor de invalidação — compara o desempenho realizado do deployment com a
referência do backtest (backtest_ref gravado na criação).

Regra combinada com o dono: o edge maker morre se a WR realizada ficar
significativamente abaixo da esperada. Teste binomial:
  warn        -> WR realizada < percentil 10 de Binomial(N, p_esperada)
  invalidated -> WR realizada < percentil 1 E N >= 20
  antes de 20 trades: 'insufficient' (amostra insuficiente).
"""

from __future__ import annotations


def compare(deployment: dict, closed_positions: list) -> dict:
    ref = deployment.get("backtest_ref") or {}
    n = len(closed_positions)
    wins = sum(1 for p in closed_positions if (p.get("pnl_pct") or 0) > 0)
    realized_wr = (wins / n * 100) if n else None

    expected_wr = ref.get("win_rate")
    out = {
        "n_trades": n,
        "realized_wr": round(realized_wr, 2) if realized_wr is not None else None,
        "expected_wr": expected_wr,
        "expected_pf": ref.get("profit_factor"),
        "avg_pnl_pct": (round(sum(p["pnl_pct"] for p in closed_positions) / n, 4)
                        if n else None),
        "verdict": "insufficient",
        "detail": None,
    }
    if expected_wr is None:
        out["detail"] = "sem referência de backtest — comparação indisponível"
        return out
    if n < 20:
        out["detail"] = f"amostra insuficiente ({n}/20 trades)"
        return out

    try:
        from scipy import stats
        p = float(expected_wr) / 100.0
        # limiares em nº de wins para os percentis 10 e 1 da Binomial(n, p)
        p10 = stats.binom.ppf(0.10, n, p)
        p01 = stats.binom.ppf(0.01, n, p)
        if wins < p01:
            out["verdict"] = "invalidated"
            out["detail"] = (f"WR {out['realized_wr']}% < percentil 1 da esperada "
                             f"({expected_wr}%) com N={n} — edge provavelmente morto")
        elif wins < p10:
            out["verdict"] = "warn"
            out["detail"] = (f"WR {out['realized_wr']}% abaixo do percentil 10 "
                             f"da esperada ({expected_wr}%) — acompanhar de perto")
        else:
            out["verdict"] = "ok"
            out["detail"] = f"WR compatível com o backtest ({expected_wr}%)"
    except Exception as e:                      # scipy indisponível
        out["detail"] = f"comparação estatística indisponível: {e}"
    return out
