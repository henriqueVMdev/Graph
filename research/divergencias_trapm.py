# -*- coding: utf-8 -*-
"""Lista completa, com data/hora exata (UTC), dos trades que divergem entre
o mm9.py (spec TrapM) e o Strategy Tester. Salva tambem em CSV:
research/data/divergencias_trapm.csv

Uso: py research/divergencias_trapm.py
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategies.mm9 as mm9

HERE = os.path.dirname(os.path.abspath(__file__))

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
tv = sorted({(int(e[0]), int(e[3]), round(e[1], 1)) for e in legs})

df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
df = df[df.index >= "2026-02-28"]
res = mm9.run(df, {"initial_capital": 1_000_000.0})
loc = res["trades"]

TOL = 15 * 60 * 1000
used = set()
rows = []
for tm, side, ep in tv:
    hit = None
    for k, t in enumerate(loc):
        if k in used or t["direction"] != side:
            continue
        if abs(t["entry_ts"] - tm) <= TOL:
            hit = k
            break
    if hit is None:
        rows.append(dict(tipo="SO_NO_TV", quando=str(pd.Timestamp(tm, unit="ms")),
                         lado="L" if side == 1 else "S", preco_tv=ep,
                         preco_local=None))
    else:
        used.add(hit)
        lp = loc[hit]["entry_price"]
        if abs(lp - ep) > 0.5:
            rows.append(dict(tipo="PRECO_DIFERENTE",
                             quando=str(pd.Timestamp(tm, unit="ms")),
                             lado="L" if side == 1 else "S", preco_tv=ep,
                             preco_local=round(lp, 1)))
for k, t in enumerate(loc):
    if k not in used:
        rows.append(dict(tipo="SO_NO_LOCAL",
                         quando=str(pd.Timestamp(t["entry_ts"], unit="ms")),
                         lado="L" if t["direction"] == 1 else "S",
                         preco_tv=None, preco_local=round(t["entry_price"], 1)))

out = pd.DataFrame(rows).sort_values("quando")
out.to_csv(os.path.join(HERE, "data", "divergencias_trapm.csv"), index=False)
print(f"{len(out)} divergencias (horarios em UTC; grafico TV em UTC-3 = -3h)")
for _, r in out.iterrows():
    ptv = f"tv@{r.preco_tv}" if r.preco_tv else ""
    plo = f"local@{r.preco_local}" if r.preco_local else ""
    print(f"{r.quando}  {r.lado}  {r.tipo:16s} {ptv} {plo}")
