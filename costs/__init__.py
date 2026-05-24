"""
Módulo de Custos de Futuros (fees + funding rate).

Agnóstico de exchange (Binance / Bybit / OKX via CCXT). Consome os trades
produzidos pelo backtest da plataforma e calcula o PnL líquido real,
descontando taxas de corretagem (maker/taker) e funding rate.

Não reescreve o backtest nem as métricas existentes — consome e reaproveita.
"""

from .models import Trade, FundingEvent, CostBreakdown, CostResult
from .config import ExchangeFees, DEFAULT_FEES, SCENARIOS
from .calculator import CostCalculator
from .compare import compare_exchanges, trades_from_platform
from .funding import get_funding_events, funding_events_from_raw

__all__ = [
    "Trade",
    "FundingEvent",
    "CostBreakdown",
    "CostResult",
    "ExchangeFees",
    "DEFAULT_FEES",
    "SCENARIOS",
    "CostCalculator",
    "compare_exchanges",
    "trades_from_platform",
    "get_funding_events",
    "funding_events_from_raw",
]
