# -*- coding: utf-8 -*-
"""Rodada 2 da engenharia reversa do TrapM:
  A) os 38 fills que nao batem com o extremo do candle anterior — ordem
     armada em candle mais antigo? gap?
  B) TP2 em R via TP2/TP1 (posicoes com ambos os fills)
  C) papel da EMA8 no candle de gatilho (pullback toca a media?)
  D) padrao do candle de gatilho (engolfo/PFR/qualquer)

Uso: py research/analyze_trapm2.py
"""

import json
import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TICK = 0.1

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
O, H, L, C = (df[c].values for c in ["Open", "High", "Low", "Close"])
ts2i = {int(t): k for k, t in enumerate(TS)}
E8 = pd.Series(C).ewm(span=8, adjust=False).mean().values
S40 = pd.Series(C).rolling(40).mean().values

pos = defaultdict(list)
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    pos[(int(e_tm), int(side))].append(dict(e_p=e_p, q=q, x_tm=int(x_tm),
                                            x_p=x_p, code=code))

# A) trigger: procura o candle g <= s cujo extremo == preco da ordem
trig_lag = Counter()
gatilho = []          # (indice do candle de gatilho, i, side, e_p)
for (e_tm, side), lg in sorted(pos.items()):
    i = ts2i.get(e_tm)
    if i is None or i < 60:
        continue
    e_p = lg[0]["e_p"]
    found = None
    for lag in range(1, 13):
        g = i - lag
        ext = H[g] if side == 1 else L[g]
        if abs(e_p - ext) < TICK * 1.5:
            found = lag
            break
    trig_lag[found if found else ("gap" if (O[i] > e_p if side == 1 else O[i] < e_p) else "?")] += 1
    if found:
        gatilho.append((i - found, i, side, e_p))

print("A) lag do candle de gatilho (fill - gatilho):", dict(trig_lag))

# B) TP2/TP1 nas posicoes com os dois fills no lucro
ratios = []
for (e_tm, side), lg in pos.items():
    e_p = lg[0]["e_p"]
    d1 = d2 = None
    for leg in lg:
        win = (leg["x_p"] > e_p) if side == 1 else (leg["x_p"] < e_p)
        if leg["code"] == 1 and win:
            d1 = abs(leg["x_p"] - e_p)
        if leg["code"] == 2 and win:
            d2 = abs(leg["x_p"] - e_p)
    if d1 and d2:
        ratios.append(d2 / d1)
a = np.array(ratios)
print(f"\nB) TP2/TP1: mediana {np.median(a):.3f} | p10 {np.percentile(a,10):.3f} "
      f"| p90 {np.percentile(a,90):.3f} | n={len(a)}")

# C/D) candle de gatilho: relacao com EMA8 e padrao
c_touch = Counter()
c_pat = Counter()
for g, i, side, e_p in gatilho:
    if side == 1:
        c_touch["low<=EMA8" if L[g] <= E8[g] else "nao toca"] += 1
    else:
        c_touch["high>=EMA8" if H[g] >= E8[g] else "nao toca"] += 1
    o1, c1, h1, l1 = O[g - 1], C[g - 1], H[g - 1], L[g - 1]
    o0, c0, h0, l0 = O[g], C[g], H[g], L[g]
    if side == 1:
        eng = c0 > o0 and o0 <= c1 and c0 >= o1
        pfr = l0 < l1 and c0 > c1
    else:
        eng = c0 < o0 and o0 >= c1 and c0 <= o1
        pfr = h0 > h1 and c0 < c1
    c_pat["engolfo" if eng else ("pfr" if pfr else "nenhum")] += 1

print("\nC) gatilho toca a EMA8:", dict(c_touch))
print("D) padrao do candle de gatilho:", dict(c_pat))

# E) extremo do gatilho vs candles seguintes ate o fill (ordem armada
#    persiste ou renova?): quantos candles entre gatilho e fill
lags = [i - g for g, i, _, _ in gatilho]
print("\nE) distancia gatilho->fill em candles:", dict(Counter(lags)))
