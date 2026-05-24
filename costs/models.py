"""Dataclasses do módulo de custos. Tipos monetários em Decimal."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Trade:
    side: str            # "long" | "short"
    qty: Decimal
    entry_price: Decimal
    exit_price: Decimal
    entry_time: int      # epoch ms
    exit_time: int       # epoch ms

    @property
    def direction(self) -> int:
        return 1 if self.side == "long" else -1


@dataclass
class FundingEvent:
    timestamp: int       # epoch ms
    rate: Decimal


@dataclass
class CostBreakdown:
    pnl_bruto: Decimal
    fee_entrada: Decimal
    fee_saida: Decimal
    funding_total: Decimal
    pnl_liquido: Decimal
    n_funding_events: int = 0


@dataclass
class CostResult:
    breakdowns: list = field(default_factory=list)   # list[CostBreakdown]
    pnl_bruto_total: Decimal = Decimal("0")
    pnl_liquido_total: Decimal = Decimal("0")
    fees_total: Decimal = Decimal("0")
    funding_total: Decimal = Decimal("0")
    metrics_gross: dict = field(default_factory=dict)
    metrics_net: dict = field(default_factory=dict)
