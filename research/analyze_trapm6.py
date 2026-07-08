# -*- coding: utf-8 -*-
"""Rodada 6: condicoes de contexto que separam gatilhos reais dos falsos.
Trabalha sobre base simples + engolfo classico (228 TP / 608 FP) e mede
cada condicao candidata em % nos dois grupos.

Uso: py research/analyze_trapm6.py
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TICK = 0.1

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
df = df[df.index >= "2026-02-28"]
TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
O, H, L, C = (df[c].values for c in ["Open", "High", "Low", "Close"])
ts2i = {int(t): k for k, t in enumerate(TS)}
E8 = pd.Series(C).ewm(span=8, adjust=False).mean().values
S40 = pd.Series(C).rolling(40).mean().values

tv = set()
seen = set()
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    key = (int(e_tm), int(side))
    if key in seen:
        continue
    seen.add(key)
    i = ts2i.get(int(e_tm))
    if i is None:
        continue
    for lag in range(1, 13):
        g = i - lag
        ext = H[g] if side == 1 else L[g]
        if abs(e_p - ext) < TICK * 1.5:
            tv.add((g, side))
            break


def eng(g, d):
    o0, c0, o1, c1 = O[g], C[g], O[g-1], C[g-1]
    return (c0 > o0 and o0 <= c1 and c0 >= o1) if d == 1 else \
           (c0 < o0 and o0 >= c1 and c0 <= o1)


mine = set()
for g in range(60, len(df)):
    bias = 1 if C[g] > S40[g] else (-1 if C[g] < S40[g] else 0)
    if bias == 0:
        continue
    d = bias
    if not ((O[g] <= E8[g]) if d == 1 else (O[g] >= E8[g])):
        continue
    if not eng(g, d):
        continue
    level = H[g] if d == 1 else L[g]
    lo = max(0, g - 3)
    stop = (L[lo:g+1].min() - TICK) if d == 1 else (H[lo:g+1].max() + TICK)
    if abs(level - stop) / level * 100 < 0.5:
        continue
    mine.add((g, d))

tp = mine & tv
fp = mine - tv
print(f"base: TP {len(tp)} | FP {len(fp)}")

CONDS = {
    "S40 subindo (g>g-1)":        lambda g, d: (S40[g] > S40[g-1]) if d == 1 else (S40[g] < S40[g-1]),
    "S40 subindo (g>g-4)":        lambda g, d: (S40[g] > S40[g-4]) if d == 1 else (S40[g] < S40[g-4]),
    "ult 4 closes alem S40":      lambda g, d: all((C[g-k] > S40[g-k]) if d == 1 else (C[g-k] < S40[g-k]) for k in range(4)),
    "ult 6 closes alem S40":      lambda g, d: all((C[g-k] > S40[g-k]) if d == 1 else (C[g-k] < S40[g-k]) for k in range(6)),
    "ult 8 closes alem S40":      lambda g, d: all((C[g-k] > S40[g-k]) if d == 1 else (C[g-k] < S40[g-k]) for k in range(8)),
    "E8 alem S40 ha 6 candles":   lambda g, d: all((E8[g-k] > S40[g-k]) if d == 1 else (E8[g-k] < S40[g-k]) for k in range(6)),
    "close alem E8 em g-2..g-6":  lambda g, d: any((C[g-k] > E8[g-k]) if d == 1 else (C[g-k] < E8[g-k]) for k in range(2, 7)),
    "dist close-S40 >= 0.3%":     lambda g, d: abs(C[g] - S40[g]) / C[g] * 100 >= 0.3,
    "dist close-S40 >= 0.5%":     lambda g, d: abs(C[g] - S40[g]) / C[g] * 100 >= 0.5,
    "extremo do gatilho alem E8": lambda g, d: (H[g] > E8[g]) if d == 1 else (L[g] < E8[g]),
    "stop alem da S40":           lambda g, d: (L[max(0,g-3):g+1].min() > S40[g]) if d == 1 else (H[max(0,g-3):g+1].max() < S40[g]),
    "level alem da S40":          lambda g, d: (H[g] > S40[g]) if d == 1 else (L[g] < S40[g]),
    "TP2 (2R) alem do gatilho":   lambda g, d: True,
}

print(f"\n{'condicao':30s} {'REAL':>6s} {'FALSO':>6s}")
for name, fn in CONDS.items():
    r = sum(1 for g, d in tp if fn(g, d)) / max(len(tp), 1) * 100
    f = sum(1 for g, d in fp if fn(g, d)) / max(len(fp), 1) * 100
    print(f"{name:30s} {r:5.0f}% {f:5.0f}%")
