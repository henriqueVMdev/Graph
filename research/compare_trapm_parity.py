# -*- coding: utf-8 -*-
"""Paridade: mm9.py reescrito x TrapM no Strategy Tester (BTC 15m Bybit,
janela do TV). Compara entradas (ts, preco, lado) e saidas.

Uso: py research/compare_trapm_parity.py
"""

import json
import os
import sys
from collections import defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import strategies.mm9 as mm9

HERE = os.path.dirname(os.path.abspath(__file__))

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
tv_pos = defaultdict(list)
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    tv_pos[(int(e_tm), int(side), round(e_p, 1))].append((int(x_tm), x_p, code))
tv_list = sorted(tv_pos.keys())

df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
first_tv = pd.Timestamp(tv_list[0][0], unit="ms")
# TV carregou dados a partir de ~Feb 28; espelha a janela
df = df[df.index >= "2026-02-28"]
print(f"janela local: {df.index[0]} -> {df.index[-1]} | 1o trade TV: {first_tv}")

res = mm9.run(df, {"initial_capital": 1_000_000.0})
loc = res["trades"]
print(f"TV: {len(tv_list)} posicoes | local: {len(loc)} trades")

TOL_MS = 15 * 60 * 1000
used = set()
matched = both = 0
tv_only, loc_only, price_diff = [], [], []
for tm, side, ep in tv_list:
    hit = None
    for k, t in enumerate(loc):
        if k in used or t["direction"] != side:
            continue
        if abs(t["entry_ts"] - tm) <= TOL_MS:
            hit = k
            break
    if hit is None:
        tv_only.append((tm, side, ep))
    else:
        used.add(hit)
        matched += 1
        if abs(loc[hit]["entry_price"] - ep) > 0.5:
            price_diff.append((tm, ep, loc[hit]["entry_price"]))

loc_only = [t for k, t in enumerate(loc) if k not in used]

print(f"\npareadas: {matched}/{len(tv_list)} "
      f"({matched/len(tv_list)*100:.0f}%) | preco divergente: {len(price_diff)}")
print(f"so no TV: {len(tv_only)} | so no local: {len(loc_only)}")


def fmt(ms):
    return str(pd.Timestamp(ms, unit="ms"))[:16]


print("\nso no TV (primeiras 10):")
for tm, side, ep in tv_only[:10]:
    print(f"  {fmt(tm)} {'L' if side==1 else 'S'} @ {ep}")
print("\nso no local (primeiras 10):")
for t in loc_only[:10]:
    print(f"  {fmt(t['entry_ts'])} {'L' if t['direction']==1 else 'S'} "
          f"@ {t['entry_price']:.1f} -> {t['exit_comment']}")
print("\nprecos divergentes (primeiros 5):")
for tm, ep, lp in price_diff[:5]:
    print(f"  {fmt(tm)}: TV {ep} vs local {lp:.1f}")
