# -*- coding: utf-8 -*-
"""Monte Carlo do prop challenge (+5% alvo, -10% total, -5% diaria) sobre os
trades FORWARD da config vencedora do sweep corrigido (tp 1.5 / sl 2.0).

Sem selecao de cesta (todos os 12 ativos) para nao contaminar com escolha
olhando o forward; solos apenas informativos.

Uso: py research/mc_sweep_best.py
"""

import os

import numpy as np
import pandas as pd

SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SL_PCT = 2.0                      # o sizing escala o net_pct pelo SL da config
RISKS = [0.01, 0.02, 0.03, 0.04, 0.05]
N_SIMS = 10000

df = pd.read_csv(SCRATCH + r"\trades_sweep_best_fwd.csv")
df["day"] = pd.to_datetime(df["ts_entry"], unit="ms").dt.date


def day_groups(d):
    return [g["net_pct"].values for _, g in d.groupby("day", sort=True)]


def simulate(days_pool, risk, rng, target=0.05, max_loss=-0.10, daily=-0.05,
             max_days=120):
    bal = 1.0
    for d in range(1, max_days + 1):
        day = days_pool[int(rng.integers(len(days_pool)))]
        start = bal
        for t in day:
            bal += bal * risk * (t / SL_PCT)
            if (bal - 1.0) <= max_loss:
                return 0, d
            if (bal / start - 1.0) <= daily:
                return 0, d
            if (bal - 1.0) >= target:
                return 1, d
    return 0, max_days


def mc(days_pool, risk, n=N_SIMS, seed=23):
    rng = np.random.default_rng(seed)
    wins, dtp = 0, []
    for _ in range(n):
        ok, d = simulate(days_pool, risk, rng)
        wins += ok
        if ok:
            dtp.append(d)
    return wins / n * 100, (float(np.median(dtp)) if dtp else None)


pools = {"cesta 12 (sem selecao)": df}
for s in sorted(df["symbol"].unique()):
    pools[f"solo {s.upper()}"] = df[df["symbol"] == s]

print(f"{'pool':26s} | " + " | ".join(f"r{int(r*100)}%" for r in RISKS))
for name, d in pools.items():
    if d["day"].nunique() < 30:
        continue
    dp = day_groups(d)
    cells = []
    for r in RISKS:
        ap, med = mc(dp, r)
        cells.append(f"{ap:5.1f}% ({med or '-':>4} d)" if med else f"{ap:5.1f}%")
    print(f"{name:26s} | " + " | ".join(cells))
