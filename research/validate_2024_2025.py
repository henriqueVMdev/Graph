# -*- coding: utf-8 -*-
"""Validacao multi-regime do Challenge Donchian (48h, s8, tp6R) em
2024 e 2025 — dados que NUNCA participaram da selecao (que usou o
treino de jul/2025-abr/2026). Execucao honesta + funding stress.

Reporta por ano: metricas agregadas + aprovacao MC (+5/-10/-5 diaria)
nos riscos 0.4/0.5/0.75%.

Uso: py research/validate_2024_2025.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import SCRATCH, SYMS, run_engine, sig_donchian
from quant_lab4 import mc_approval

CFG = dict(stop_atr=8, tp_atr=48, max_bars=1344)
DON_N = 192

frames = []
for sym in SYMS:
    try:
        df = pd.read_csv(os.path.join(SCRATCH, f"{sym}_15m_bybit_2425.csv"),
                         index_col=0, parse_dates=True)
        fund = pd.read_csv(os.path.join(SCRATCH, f"funding_{sym}_2425.csv"))
    except FileNotFoundError:
        print(f"{sym}: dados 2024-2025 ausentes")
        continue
    tr = run_engine(df, fund, sig_donchian(df, DON_N), CFG)
    if tr:
        w = pd.DataFrame(tr, columns=["net_pct", "ts_entry", "ts_exit",
                                      "side", "stop_dist_pct"])
        w["symbol"] = sym
        frames.append(w)

allt = pd.concat(frames).sort_values("ts_entry")
allt["ano"] = pd.to_datetime(allt["ts_entry"], unit="ms").dt.year
allt.to_csv(os.path.join(SCRATCH, "trades_challenge_2425.csv"), index=False)

for ano in (2024, 2025):
    sub = allt[allt["ano"] == ano]
    p = sub["net_pct"].values
    if not len(p):
        continue
    loss = abs(p[p <= 0].sum())
    pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
    print(f"\n=== {ano}: n={len(p)} WR={(p>0).mean()*100:.1f}% "
          f"exp={p.mean():+.4f} PF={pf:.2f} ===")
    for r in (0.004, 0.005, 0.0075):
        ap, med = mc_approval(sub, r, n_sims=10000)
        if ap is None:
            print(f"  risco {r*100:.2f}%: pool de dias insuficiente")
            continue
        print(f"  risco {r*100:.2f}%: aprovacao {ap:5.1f}% | mediana {med:.0f} dias")

# consolidado 2024+2025+2026(parcial ja medido a parte)
p = allt["net_pct"].values
loss = abs(p[p <= 0].sum())
pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
print(f"\n=== 2024+2025: n={len(p)} WR={(p>0).mean()*100:.1f}% "
      f"exp={p.mean():+.4f} PF={pf:.2f} ===")
for r in (0.004, 0.005):
    ap, med = mc_approval(allt, r, n_sims=10000)
    print(f"  risco {r*100:.2f}%: aprovacao {ap:5.1f}% | mediana {med:.0f} dias")
