# -*- coding: utf-8 -*-
"""Holdout final (2026 jan-jul, intocado) + consistencia por ano e por
simbolo do TSMOM 21d long-only (e vizinho 28d) — apos custos e funding.

Uso: py research/daily_final.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_lab import SCRATCH, SYMS, run_daily, sig_tsmom

data = {}
for sym in SYMS:
    try:
        data[sym] = pd.read_csv(os.path.join(SCRATCH, f"{sym}_1d_binance.csv"),
                                index_col=0, parse_dates=True)
    except FileNotFoundError:
        continue


def collect(n, long_only):
    frames = []
    for sym, df in data.items():
        tr = run_daily(df, sig_tsmom(df, n, long_only), dict())
        if len(tr):
            tr["symbol"] = sym
            frames.append(tr)
    allt = pd.concat(frames)
    allt["ano"] = pd.to_datetime(allt["ts_entry"], unit="ms").dt.year
    return allt


def line(p, label):
    if len(p) < 5:
        print(f"  {label:12s} n={len(p):4d}  (amostra pequena)")
        return
    loss = abs(p[p <= 0].sum())
    pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
    print(f"  {label:12s} n={len(p):4d} WR={(p>0).mean()*100:5.1f}% "
          f"exp={p.mean():+7.3f}% PF={pf:5.2f} soma={p.sum():+8.1f}%")


for n, lo, nome in ((21, True, "TSMOM 21d LONG-ONLY"), (28, False, "TSMOM 28d L/S")):
    allt = collect(n, lo)
    print(f"\n===== {nome} =====")
    print("por ano:")
    for ano in sorted(allt["ano"].unique()):
        line(allt[allt["ano"] == ano]["net_pct"].values, str(ano))
    print("2026 (holdout):")
    line(allt[allt["ano"] == 2026]["net_pct"].values, "2026")
    print("por simbolo (2024+):")
    rec = allt[allt["ano"] >= 2024]
    for sym in sorted(rec["symbol"].unique()):
        line(rec[rec["symbol"] == sym]["net_pct"].values, sym.upper())
