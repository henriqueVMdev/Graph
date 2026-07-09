"""
Carregamento de estratégias para automação e validação do contrato signal().

Uma estratégia é automatizável quando o módulo expõe:
    signal(df_candles_fechados, params) -> None | dict
com o dict contendo: side (1|-1), type ('limit'|'market'), price, valid_bars,
tp_pct, sl_pct, max_bars, fill_rule ('cross'|'open'), exposure.

- type='limit'/fill_rule='cross': limite que precisa ser atravessada.
- type='market'/fill_rule='open': fill na ABERTURA do próximo candle
  (fee taker); price deve ser None. tp_pct/sl_pct/max_bars podem ser
  None (sem TP/SL/time-stop).
- exit_on_flip (opcional, bool): estratégia POSICIONAL — enquanto a
  posição está aberta o runner reavalia signal() a cada candle fechado e
  fecha (na abertura seguinte, taker) quando o lado desejado muda.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

STRATEGIES_DIR = Path(__file__).resolve().parent.parent / "strategies"

_REQUIRED_KEYS = {"side", "type", "price", "valid_bars",
                  "tp_pct", "sl_pct", "max_bars", "fill_rule", "exposure"}

_module_cache: dict = {}


def load_strategy(strategy_file: str):
    """Carrega strategies/<nome>.py (mesmas guardas do server._load_strategy)."""
    if (not strategy_file or strategy_file.startswith("_")
            or "/" in strategy_file or "\\" in strategy_file
            or "." in strategy_file):
        raise ValueError(f"Nome de estratégia inválido: '{strategy_file}'")
    if strategy_file in _module_cache:
        return _module_cache[strategy_file]
    path = STRATEGIES_DIR / f"{strategy_file}.py"
    if not path.exists():
        raise FileNotFoundError(f"Estratégia '{strategy_file}' não encontrada")
    spec = importlib.util.spec_from_file_location(f"strategies.{strategy_file}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _module_cache[strategy_file] = module
    return module


def is_automatable(strategy_file: str) -> bool:
    try:
        return callable(getattr(load_strategy(strategy_file), "signal", None))
    except Exception:
        return False


def get_signal(strategy_file: str, df, params) -> dict | None:
    """Chama signal() e valida o contrato. Levanta ValueError se malformado."""
    module = load_strategy(strategy_file)
    fn = getattr(module, "signal", None)
    if not callable(fn):
        raise ValueError(f"Estratégia '{strategy_file}' não expõe signal()")
    sig = fn(df, params)
    if sig is None:
        return None
    missing = _REQUIRED_KEYS - set(sig)
    if missing:
        raise ValueError(f"signal() de '{strategy_file}' sem chaves: {missing}")
    if sig["type"] == "limit":
        if sig["fill_rule"] != "cross" or sig["price"] is None:
            raise ValueError(f"signal() de '{strategy_file}': limit exige "
                             "fill_rule='cross' e price")
    elif sig["type"] == "market":
        if sig["fill_rule"] != "open" or sig["price"] is not None:
            raise ValueError(f"signal() de '{strategy_file}': market exige "
                             "fill_rule='open' e price=None")
    else:
        raise ValueError(f"signal() de '{strategy_file}': type '{sig['type']}' "
                         "não suportado")
    return sig
