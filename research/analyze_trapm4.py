# -*- coding: utf-8 -*-
"""Rodada 4: que condicao separa os gatilhos REAIS do TrapM dos falsos
positivos do meu motor? Compara propriedades do candle de gatilho:
  - candle anterior de cor oposta (engolfo estrito)
  - close vs media rapida / abertura vs media rapida
  - vies tambem por EMA8 vs SMA40
  - risco % (min gain no nivel do gatilho)
  - corpo minimo do candle de gatilho

Uso: py research/analyze_trapm4.py
"""

import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategies.mm9 as mm9

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

# gatilhos reais do TV: acha o candle g cujo extremo == preco de entrada
tv_trigs = set()
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
            tv_trigs.add((g, side))
            break

# gatilhos do meu motor (mesmas condicoes do mm9.py novo)
mine = set()
for g in range(41, len(df)):
    bias = 1 if C[g] > S40[g] else (-1 if C[g] < S40[g] else 0)
    if bias == 0:
        continue
    d = bias
    touches = (O[g] <= E8[g]) if d == 1 else (O[g] >= E8[g])
    if not touches:
        continue
    if not mm9._is_engulfing(d, O[g], C[g], O[g - 1], C[g - 1]):
        continue
    level = H[g] if d == 1 else L[g]
    lo = max(0, g - 3)
    stop = (L[lo:g + 1].min() - TICK) if d == 1 else (H[lo:g + 1].max() + TICK)
    if abs(level - stop) / level * 100 < 0.5:
        continue
    mine.add((g, d))

true_pos = mine & tv_trigs
false_pos = mine - tv_trigs
missed = tv_trigs - mine
print(f"TV gatilhos: {len(tv_trigs)} | meus: {len(mine)} | "
      f"comuns: {len(true_pos)} | so meus: {len(false_pos)} | perdidos: {len(missed)}")


def props(bars):
    c = Counter()
    n = max(len(bars), 1)
    for g, d in bars:
        prev_opposite = (C[g-1] < O[g-1]) if d == 1 else (C[g-1] > O[g-1])
        c["prev cor oposta"] += prev_opposite
        c["close alem da rapida"] += (C[g] > E8[g]) if d == 1 else (C[g] < E8[g])
        c["open aquem da rapida"] += (O[g] <= E8[g]) if d == 1 else (O[g] >= E8[g])
        c["EMA8 vs SMA40 a favor"] += (E8[g] > S40[g]) if d == 1 else (E8[g] < S40[g])
        c["corpo > 50% range"] += abs(C[g]-O[g]) > 0.5*(H[g]-L[g]) if H[g] > L[g] else 0
        c["extremo alem do prev"] += (H[g] > H[g-1]) if d == 1 else (L[g] < L[g-1])
        c["close alem prev extremo"] += (C[g] > H[g-1]) if d == 1 else (C[g] < L[g-1])
        c["prev tambem aquem (open)"] += (O[g-1] <= E8[g-1]) if d == 1 else (O[g-1] >= E8[g-1])
        c["prev close aquem"] += (C[g-1] <= E8[g-1]) if d == 1 else (C[g-1] >= E8[g-1])
        c["prev toca rapida"] += (L[g-1] <= E8[g-1]) if d == 1 else (H[g-1] >= E8[g-1])
        c["extremo nao rompeu SMA40"] += (L[g] > S40[g]) if d == 1 else (H[g] < S40[g])
        c["corpo engolfa range prev"] += (C[g] >= H[g-1] and O[g] <= L[g-1]) if d == 1 else (C[g] <= L[g-1] and O[g] >= H[g-1])
        rng = H[g] - L[g]
        rng1 = H[g-1] - L[g-1]
        c["range > range prev"] += rng > rng1
    return {k: f"{v/n*100:.0f}%" for k, v in c.items()}


print("\nPropriedades dos gatilhos REAIS (comuns):")
for k, v in props(true_pos).items():
    print(f"  {k:26s} {v}")
print("\nPropriedades dos FALSOS POSITIVOS (so meus):")
for k, v in props(false_pos).items():
    print(f"  {k:26s} {v}")
print("\nPerdidos (gatilho TV que meu motor nao gera) — primeiros 8:")
for g, d in sorted(missed)[:8]:
    print(f"  {df.index[g]} {'L' if d==1 else 'S'} | eng={mm9._is_engulfing(d, O[g], C[g], O[g-1], C[g-1])} "
          f"toca={(L[g]<=E8[g]) if d==1 else (H[g]>=E8[g])} "
          f"bias={'ok' if ((C[g]>S40[g]) if d==1 else (C[g]<S40[g])) else 'x'}")
