"""
CostCalculator — aplica fees (maker/taker) + funding rate aos trades.

Regras críticas (CLAUDE.md):
  - Fees/funding incidem sobre o NOTIONAL ALAVANCADO (qty × preço), não a margem.
  - Default TAKER nas duas pontas.
  - Sinal do funding: funding_payment = -direção × notional × rate.
  - Funding só incide com posição aberta no instante do settlement
    (entry_time <= funding_time <= exit_time).
  - Intervalo de funding lido dos próprios timestamps (nunca assumir 8h).
  - Decimal nos cálculos de custo; float só na agregação de métricas.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Trade, FundingEvent, CostBreakdown, CostResult
from .config import ExchangeFees
from . import metrics as _metrics


def _D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


class CostCalculator:
    def __init__(self, exchange: str, fees: ExchangeFees,
                 use_maker_entry: bool = False, use_maker_exit: bool = False,
                 funding_multiplier=Decimal("1.0"),
                 slippage_pct=Decimal("0")):
        self.exchange = exchange
        self.fees = fees
        self.use_maker_entry = use_maker_entry
        self.use_maker_exit = use_maker_exit
        self.funding_multiplier = _D(funding_multiplier)
        self.slippage_pct = _D(slippage_pct)

    def _fee_rate(self, maker: bool) -> Decimal:
        return self.fees.maker if maker else self.fees.taker

    def _notional_at(self, trade: Trade, ts: int, candles) -> Decimal:
        """Notional no instante do funding. Rigoroso se candles disponíveis;
        senão usa o notional de entrada (aproximação aceitável p/ v1)."""
        if candles is not None:
            price = _price_at(candles, ts)
            if price is not None:
                return trade.qty * _D(price)
        return trade.qty * trade.entry_price

    def apply_trade(self, trade: Trade, funding_events, candles=None) -> CostBreakdown:
        notional_entrada = trade.qty * trade.entry_price
        notional_saida = trade.qty * trade.exit_price
        direction = _D(trade.direction)

        fee_entrada = (notional_entrada * self._fee_rate(self.use_maker_entry)
                       + notional_entrada * self.slippage_pct)
        fee_saida = (notional_saida * self._fee_rate(self.use_maker_exit)
                     + notional_saida * self.slippage_pct)

        pnl_bruto = (trade.exit_price - trade.entry_price) * trade.qty * direction

        funding_total = Decimal("0")
        n_fund = 0
        for ev in funding_events:
            if trade.entry_time <= ev.timestamp <= trade.exit_time:
                notional_t = self._notional_at(trade, ev.timestamp, candles)
                rate = _D(ev.rate) * self.funding_multiplier
                funding_total += -direction * notional_t * rate
                n_fund += 1

        pnl_liquido = pnl_bruto - fee_entrada - fee_saida + funding_total

        return CostBreakdown(
            pnl_bruto=pnl_bruto,
            fee_entrada=fee_entrada,
            fee_saida=fee_saida,
            funding_total=funding_total,
            pnl_liquido=pnl_liquido,
            n_funding_events=n_fund,
        )

    def apply(self, trades, funding_events, candles=None,
              initial_capital=1000.0) -> CostResult:
        """Aplica fees + funding a todos os trades e recalcula as métricas
        (bruto vs líquido). funding_events: lista de FundingEvent ordenada."""
        breakdowns = [self.apply_trade(t, funding_events, candles) for t in trades]

        pnl_bruto_total = sum((b.pnl_bruto for b in breakdowns), Decimal("0"))
        pnl_liquido_total = sum((b.pnl_liquido for b in breakdowns), Decimal("0"))
        fees_total = sum((b.fee_entrada + b.fee_saida for b in breakdowns), Decimal("0"))
        funding_total = sum((b.funding_total for b in breakdowns), Decimal("0"))

        # Ordena por tempo de saída para construir as curvas de equity
        order = sorted(range(len(trades)), key=lambda i: trades[i].exit_time)
        exit_times = [trades[i].exit_time for i in order]
        entry_times = [trades[i].entry_time for i in order]
        pnls_gross = [float(breakdowns[i].pnl_bruto) for i in order]
        pnls_net = [float(breakdowns[i].pnl_liquido) for i in order]

        metrics_gross = _metrics.compute_metrics(pnls_gross, exit_times, initial_capital, entry_times)
        metrics_net = _metrics.compute_metrics(pnls_net, exit_times, initial_capital, entry_times)

        return CostResult(
            breakdowns=breakdowns,
            pnl_bruto_total=pnl_bruto_total,
            pnl_liquido_total=pnl_liquido_total,
            fees_total=fees_total,
            funding_total=funding_total,
            metrics_gross=metrics_gross,
            metrics_net=metrics_net,
        )


def _price_at(candles, ts: int):
    """Close do candle mais próximo (<=) do timestamp do funding.
    Aceita pandas DataFrame (índice datetime, coluna 'Close') ou dict {ts_ms: price}."""
    if isinstance(candles, dict):
        keys = [k for k in candles.keys() if k <= ts]
        if not keys:
            return None
        return candles[max(keys)]
    # pandas DataFrame
    try:
        import pandas as pd  # noqa
        idx_ms = candles.index.view("int64") // 1_000_000
        mask = idx_ms <= ts
        if not mask.any():
            return None
        pos = int(mask.nonzero()[0][-1])
        return float(candles["Close"].iloc[pos])
    except Exception:
        return None
