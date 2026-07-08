# -*- coding: utf-8 -*-
"""Metricas agregadas do mm9.py reescrito vs TrapM no tester (mesma janela)."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategies.mm9 as mm9

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
df = df[df.index >= "2026-02-28"]

res = mm9.run(df, {"initial_capital": 1_000_000.0})
m = res["metrics"]
print("LOCAL (mm9.py TrapM spec, bruto):")
print(f"  trades {m['total_trades']} | WR {m['win_rate']:.1f}% | "
      f"PF {m['profit_factor']:.2f} | retorno {m['total_return']:+.2f}% | "
      f"maxDD {m['max_dd']:.1f}%")
print("TV tester (TrapM - LW, mesma janela, comissao 0):")
print("  trades 373 (legs) / 242 posicoes | WR 44.2% (por leg) | "
      "PF 1.03 | retorno +3.66% | maxDD 26.2%")
