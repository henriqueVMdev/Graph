# -*- coding: utf-8 -*-
"""Rodada 5: qual definicao de candle de reversao reproduz EXATAMENTE os
242 gatilhos do TrapM? Testa combinacoes base x padrao e imprime a matriz
de confusao no nivel do gatilho. Depois lista os FN/FP restantes da melhor.

Uso: py research/analyze_trapm5.py
"""

import json
import os
from collections import Counter

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

# padroes candidatos (lado long; short espelhado)
def d_eng(g, d):        # engolfo classico de corpo
    o0, c0, o1, c1 = O[g], C[g], O[g-1], C[g-1]
    return (c0 > o0 and o0 <= c1 and c0 >= o1) if d == 1 else \
           (c0 < o0 and o0 >= c1 and c0 <= o1)

def d_eng_strict(g, d): # engolfo exigindo prev de cor oposta
    o1, c1 = O[g-1], C[g-1]
    return d_eng(g, d) and ((c1 < o1) if d == 1 else (c1 > o1))

def d_close_prev_ext(g, d):   # fecha alem do extremo anterior
    return (C[g] > O[g] and C[g] > H[g-1]) if d == 1 else \
           (C[g] < O[g] and C[g] < L[g-1])

def d_close_prev_close(g, d): # fecha alem do close anterior (LW)
    return (C[g] > O[g] and C[g] > C[g-1]) if d == 1 else \
           (C[g] < O[g] and C[g] < C[g-1])

def d_eng_or_ext(g, d):
    return d_eng(g, d) or d_close_prev_ext(g, d)

def d_eng_body_open(g, d):    # corpo engolfa: close alem do open anterior
    return (C[g] > O[g] and C[g] > O[g-1]) if d == 1 else \
           (C[g] < O[g] and C[g] < O[g-1])

def d_any_rev(g, d):          # qualquer candle na direcao
    return (C[g] > O[g]) if d == 1 else (C[g] < O[g])

def d_cross_ma(g, d):         # o candle CRUZA a rapida: abre aquem, fecha alem
    return (O[g] <= E8[g] and C[g] > E8[g]) if d == 1 else \
           (O[g] >= E8[g] and C[g] < E8[g])

def d_close_cross(g, d):      # close cruza: prev close aquem, close alem
    return (C[g-1] <= E8[g-1] and C[g] > E8[g]) if d == 1 else \
           (C[g-1] >= E8[g-1] and C[g] < E8[g])

def d_any_cross(g, d):        # qualquer cruzamento (open OU prev close aquem)
    return d_cross_ma(g, d) or d_close_cross(g, d)

PATTERNS = {
    "engolfo classico": d_eng,
    "engolfo estrito": d_eng_strict,
    "close>prev extremo": d_close_prev_ext,
    "close>prev close": d_close_prev_close,
    "engolfo|prev ext": d_eng_or_ext,
    "close>prev open": d_eng_body_open,
    "candle na direcao": d_any_rev,
    "candle cruza MA": d_cross_ma,
    "close cruza MA": d_close_cross,
    "qualquer cruzamento": d_any_cross,
}

def base_ok(g, d, prev_close_cond):
    bias = 1 if C[g] > S40[g] else (-1 if C[g] < S40[g] else 0)
    if bias != d:
        return False
    if not ((O[g] <= E8[g]) if d == 1 else (O[g] >= E8[g])):
        return False
    if prev_close_cond and not ((C[g-1] <= E8[g-1]) if d == 1 else (C[g-1] >= E8[g-1])):
        return False
    level = H[g] if d == 1 else L[g]
    lo = max(0, g - 3)
    stop = (L[lo:g+1].min() - TICK) if d == 1 else (H[lo:g+1].max() + TICK)
    return abs(level - stop) / level * 100 >= 0.5

print(f"TV gatilhos: {len(tv)}")
print(f"{'base':12s} {'padrao':20s} {'TPos':>5s} {'FNeg':>5s} {'FPos':>5s}")
best = None
for prev_close in (False, True):
    for name, fn in PATTERNS.items():
        mine = set()
        for g in range(41, len(df)):
            for d in (1, -1):
                if base_ok(g, d, prev_close) and fn(g, d):
                    mine.add((g, d))
        tp = len(mine & tv)
        fneg = len(tv - mine)
        fpos = len(mine - tv)
        print(f"{'prev_close' if prev_close else 'simples':12s} {name:20s} "
              f"{tp:5d} {fneg:5d} {fpos:5d}")
        score = fneg + fpos
        if best is None or score < best[0]:
            best = (score, prev_close, name, fn, mine)

score, prev_close, name, fn, mine = best
print(f"\nMELHOR: base={'prev_close' if prev_close else 'simples'} + {name} "
      f"(erros={score})")
print("\nFN restantes (TV sim, meu nao) — contexto completo:")
for g, d in sorted(tv - mine)[:12]:
    print(f"  {df.index[g]} {'L' if d==1 else 'S'} "
          f"| prev O={O[g-1]:.0f} H={H[g-1]:.0f} L={L[g-1]:.0f} C={C[g-1]:.0f} "
          f"| cur O={O[g]:.0f} H={H[g]:.0f} L={L[g]:.0f} C={C[g]:.0f} "
          f"| E8={E8[g]:.0f} S40={S40[g]:.0f}")
print("\nFP restantes (meu sim, TV nao) — primeiros 12:")
for g, d in sorted(mine - tv)[:12]:
    print(f"  {df.index[g]} {'L' if d==1 else 'S'} "
          f"| prev O={O[g-1]:.0f} H={H[g-1]:.0f} L={L[g-1]:.0f} C={C[g-1]:.0f} "
          f"| cur O={O[g]:.0f} H={H[g]:.0f} L={L[g]:.0f} C={C[g]:.0f} "
          f"| E8={E8[g]:.0f} S40={S40[g]:.0f}")
