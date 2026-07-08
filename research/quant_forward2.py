# -*- coding: utf-8 -*-
"""FORWARD (unico) do challenge mode selecionado no treino:
Donchian 48h, stop 8 ATR, alvo 6R (48 ATR), max 2 semanas, 12 perps.
Reporta metricas por ativo + MC de aprovacao no pool forward.

Uso: py research/quant_forward2.py
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
print("FORWARD — donch48h s8 tp48, execucao honesta")
print(f"{'sym':5s} {'n':>4s} {'WR':>6s} {'exp':>8s}")
for sym in SYMS:
    try:
        df = pd.read_csv(os.path.join(SCRATCH, f"{sym}_15m_bybit.csv"),
                         index_col=0, parse_dates=True)
        fund = pd.read_csv(os.path.join(SCRATCH, f"funding_{sym}.csv"))
    except FileNotFoundError:
        continue
    split_ms = (df.index[int(len(df) * 0.7)] - pd.Timestamp(0)).total_seconds() * 1000
    tr = run_engine(df, fund, sig_donchian(df, DON_N), CFG)
    tr = [t for t in tr if t[1] >= split_ms]
    if not tr:
        print(f"{sym.upper():5s}   sem trades")
        continue
    p = np.array([t[0] for t in tr])
    print(f"{sym.upper():5s} {len(p):4d} {(p>0).mean()*100:5.1f}% {p.mean():+8.4f}")
    frames.append(pd.DataFrame(tr, columns=["net_pct", "ts_entry", "ts_exit",
                                            "side", "stop_dist_pct"]))

allt = pd.concat(frames).sort_values("ts_entry")
p = allt["net_pct"].values
loss = abs(p[p <= 0].sum())
pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
print(f"\nAGREGADO: n={len(p)} WR={(p>0).mean()*100:.1f}% exp={p.mean():+.4f} PF={pf:.2f}")
allt.to_csv(os.path.join(SCRATCH, "trades_challenge_fwd.csv"), index=False)

print(f"\n{'risco':>6s} {'aprovacao':>10s} {'mediana':>8s}")
for r in (0.004, 0.005, 0.0075, 0.01):
    ap, med = mc_approval(allt, r, n_sims=10000)
    print(f"{r*100:5.2f}% {ap:9.1f}% {med or float('nan'):7.0f}d")

# sequencia real (sem bootstrap) @ 0.4%
bal, peak, mdd, worst = 1.0, 1.0, 0.0, 0.0
allt["day"] = pd.to_datetime(allt["ts_entry"], unit="ms").dt.date
for _, g in allt.groupby("day", sort=True):
    s0 = bal
    for net, sd in g[["net_pct", "stop_dist_pct"]].values:
        expo = min(0.4 / sd, 5.0) if sd > 0 else 0.0
        bal += bal * (net / 100) * expo
        peak = max(peak, bal)
        mdd = min(mdd, bal / peak - 1)
    worst = min(worst, bal / s0 - 1)
print(f"\nsequencia real fwd @0.4%: retorno {(bal-1)*100:+.2f}% | "
      f"maxDD {mdd*100:.2f}% | pior dia {worst*100:.2f}%")
