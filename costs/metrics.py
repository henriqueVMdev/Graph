"""
Ponte para as métricas da plataforma, aplicadas à série de PnL (bruto e líquido).

Reaproveita as mesmas fórmulas usadas no resto da plataforma (Sharpe pela curva
de equity anualizado, Sortino anualizado por trades/ano, Calmar = CAGR/|maxDD|),
mas operando sobre PnL em dólares — antes e depois dos custos.

Float é aceitável aqui (agregação final); os custos trade-a-trade são Decimal.
"""

from __future__ import annotations

import numpy as np

_MS_PER_YEAR = 365.25 * 24 * 3600 * 1000


def _safe(v):
    try:
        if v is None or np.isnan(v) or np.isinf(v):
            return None
    except (TypeError, ValueError):
        return v
    return float(v)


def compute_metrics(pnls, exit_times_ms, initial_capital, entry_times_ms=None):
    """
    Calcula métricas a partir de uma série de PnL em dólares por trade.

    pnls          : lista de PnL ($) por trade, na ordem de execução.
    exit_times_ms : epoch ms do fechamento de cada trade (para anualizar).
    initial_capital: capital inicial ($) para construir a curva de equity.
    entry_times_ms: epoch ms de abertura (usa o 1º p/ span temporal); opcional.
    """
    pnls = [float(p) for p in pnls]
    n = len(pnls)
    if n == 0:
        return {
            "sharpe": None, "sortino": None, "calmar": None, "max_dd": None,
            "total_return": None, "final_equity": _safe(initial_capital),
            "total_pnl": 0.0, "n_trades": 0,
        }

    ic = float(initial_capital) if initial_capital else 1.0
    equity = [ic]
    for p in pnls:
        equity.append(equity[-1] + p)
    eq = np.array(equity, dtype=float)

    # Span de calendário (ms) -> trades por ano e fator de anualização
    t_start = entry_times_ms[0] if entry_times_ms else exit_times_ms[0]
    t_end = exit_times_ms[-1]
    span_ms = max(t_end - t_start, 1)
    years = span_ms / _MS_PER_YEAR
    trades_per_year = n / years if years > 0 else n

    # Retornos da curva de equity (mesma lógica da plataforma, ddof=1)
    rets = np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)
    rets = rets[np.isfinite(rets)]
    std = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sharpe = float(rets.mean() / std * np.sqrt(trades_per_year)) if std > 0 else 0.0

    # Sortino — desvio downside dos retornos, anualizado por trades/ano
    downside_sq = [min(r, 0.0) ** 2 for r in rets]
    dd_dev = float(np.sqrt(np.mean(downside_sq))) if downside_sq else 0.0
    sortino = (float(rets.mean() / dd_dev * np.sqrt(trades_per_year))
               if dd_dev > 0 else 0.0)

    # Max drawdown da curva de equity (%)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak * 100
    max_dd = float(dd.min())

    # Calmar = CAGR / |maxDD|
    final_equity = float(eq[-1])
    cagr = ((final_equity / ic) ** (1.0 / years) - 1) * 100 if (years > 0 and ic > 0 and final_equity > 0) else 0.0
    calmar = float(cagr / abs(max_dd)) if abs(max_dd) > 0 else 0.0

    total_return = (final_equity / ic - 1) * 100 if ic > 0 else 0.0

    return {
        "sharpe": _safe(sharpe),
        "sortino": _safe(sortino),
        "calmar": _safe(calmar),
        "max_dd": _safe(max_dd),
        "total_return": _safe(total_return),
        "final_equity": _safe(final_equity),
        "total_pnl": _safe(sum(pnls)),
        "n_trades": n,
    }
