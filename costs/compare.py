"""
Orquestração: roda N estratégias × N exchanges e devolve a comparação
bruto vs líquido lado a lado. O delta entre os dois é o insight inteiro.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .models import Trade
from .config import DEFAULT_FEES, SCENARIOS
from .calculator import CostCalculator
from .funding import get_funding_events


def trades_from_platform(raw_trades, default_qty=Decimal("0")) -> list:
    """Converte os trades produzidos pelo backtest da plataforma em costs.Trade.

    Aceita os dicts emitidos por strategies/*.run() (com qty, direction/side,
    entry_price, exit_price, entry_ts, exit_ts). Trades sem timestamp ou qty
    são ignorados (não dá pra custear sem notional nem janela de funding)."""
    out = []
    for t in raw_trades:
        side = t.get("side")
        if side is None:
            side = "long" if int(t.get("direction", 1)) == 1 else "short"
        qty = t.get("qty", default_qty)
        entry_ts = t.get("entry_ts") or 0
        exit_ts = t.get("exit_ts") or 0
        entry_price = t.get("entry_price")
        exit_price = t.get("exit_price")
        if not qty or not entry_ts or not exit_ts or entry_price is None or exit_price is None:
            continue
        out.append(Trade(
            side=side,
            qty=Decimal(str(qty)),
            entry_price=Decimal(str(entry_price)),
            exit_price=Decimal(str(exit_price)),
            entry_time=int(entry_ts),
            exit_time=int(exit_ts),
        ))
    return out


def _calculator(exchange: str, scenario: str) -> CostCalculator:
    fees = DEFAULT_FEES[exchange]
    sc = SCENARIOS[scenario]
    return CostCalculator(
        exchange=exchange,
        fees=fees,
        use_maker_entry=False,   # default taker nas duas pontas
        use_maker_exit=False,
        funding_multiplier=sc["funding_multiplier"],
        slippage_pct=sc["slippage_pct"],
    )


def _survives(metrics_net, pnl_liquido_total) -> bool:
    sharpe = metrics_net.get("sharpe") or 0.0
    return float(pnl_liquido_total) > 0 and sharpe > 0


def compare_exchanges(strategies, symbol: str,
                      exchanges=("binance", "bybit", "okx"),
                      scenario: str = "realista",
                      initial_capital: float = 1000.0,
                      funding_provider=None,
                      candles=None) -> pd.DataFrame:
    """
    Para cada (estratégia, exchange): baixa funding, aplica custos e devolve
    um DataFrame com PnL bruto, líquido, fees, funding e métricas net.

    strategies      : dict[str, list[costs.Trade]]
    funding_provider: callable(exchange, symbol, since_ms, until_ms) -> list[FundingEvent].
                      Default = get_funding_events (CCXT + cache). Injetável p/ testes.
    candles         : opcional, p/ notional rigoroso no instante do funding.
    """
    provider = funding_provider or get_funding_events
    rows = []

    for strat_name, trades in strategies.items():
        if not trades:
            continue
        since_ms = min(t.entry_time for t in trades)
        until_ms = max(t.exit_time for t in trades)

        for exchange in exchanges:
            funding_events = provider(exchange, symbol, since_ms, until_ms)
            calc = _calculator(exchange, scenario)
            res = calc.apply(trades, funding_events, candles=candles,
                             initial_capital=initial_capital)

            mg, mn = res.metrics_gross, res.metrics_net
            sharpe_g = mg.get("sharpe") or 0.0
            sharpe_n = mn.get("sharpe") or 0.0
            rows.append({
                "Estratégia": strat_name,
                "Exchange": exchange,
                "Cenário": scenario,
                "PnL Bruto": float(res.pnl_bruto_total),
                "PnL Líquido": float(res.pnl_liquido_total),
                "Fees": float(res.fees_total),
                "Funding": float(res.funding_total),
                "Sharpe Bruto": sharpe_g,
                "Sharpe Líquido": sharpe_n,
                "Δ Sharpe": sharpe_n - sharpe_g,
                "Sortino Líquido": mn.get("sortino"),
                "Calmar Líquido": mn.get("calmar"),
                "Max DD Líquido": mn.get("max_dd"),
                "Sobrevive?": _survives(mn, res.pnl_liquido_total),
            })

    return pd.DataFrame(rows)
