"""Fees por exchange/tier e definição dos cenários (realista / pessimista)."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ExchangeFees:
    maker: Decimal
    taker: Decimal


# Tier base (VIP 0), confirmado para 2026. Override por tier do usuário.
# Default de uso = taker nas duas pontas (ver regra crítica #2 do CLAUDE.md).
DEFAULT_FEES = {
    "binance": ExchangeFees(maker=Decimal("0.0002"), taker=Decimal("0.0005")),
    "bybit":   ExchangeFees(maker=Decimal("0.0002"), taker=Decimal("0.00055")),
    "okx":     ExchangeFees(maker=Decimal("0.0002"), taker=Decimal("0.0005")),
}


# Cenários obrigatórios. O pessimista existe pra checar margem de segurança:
# funding amplificado + slippage somado às fees nas duas pontas.
SCENARIOS = {
    "realista": {
        "funding_multiplier": Decimal("1.0"),
        "slippage_pct": Decimal("0"),       # fração do notional, por ponta
    },
    "pessimista": {
        "funding_multiplier": Decimal("1.5"),
        "slippage_pct": Decimal("0.0005"),  # 0,05% de slippage por ponta
    },
}
