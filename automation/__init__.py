"""Módulo de automação: executa estratégias validadas em paper trading
(simulação local com candles reais) ou na conta demo da Bybit.

Uso pelo server.py:
    from automation import get_runner
    from automation.api import automation_bp
"""

from .runner import get_runner  # noqa: F401
