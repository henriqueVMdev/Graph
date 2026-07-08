# -*- coding: utf-8 -*-
"""Paridade das SAIDAS: nos pares TV x local casados por entrada, compara
timestamp e preco da ultima saida e da parcial. Divergencia de saida
cascateia para as proximas entradas — e o primeiro lugar para consertar.

Uso: py research/compare_trapm_exits.py
"""

import json
import os
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategies.mm9 as mm9

HERE = os.path.dirname(os.path.abspath(__file__))

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
tv_pos = defaultdict(list)
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    tv_pos[(int(e_tm), int(side))].append((int(x_tm), x_p, code))

df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
df = df[df.index >= "2026-02-28"]

res = mm9.run(df, {"initial_capital": 1_000_000.0})
loc = res["trades"]

TOL = 15 * 60 * 1000
used = set()
exit_ok = exit_bad = 0
bad_kinds = Counter()
examples = []
for (tm, side), exits in sorted(tv_pos.items()):
    hit = None
    for k, t in enumerate(loc):
        if k in used or t["direction"] != side:
            continue
        if abs(t["entry_ts"] - tm) <= TOL:
            hit = k
            break
    if hit is None:
        continue
    used.add(hit)
    t = loc[hit]
    tv_last_tm = max(x[0] for x in exits)
    tv_last_p = [x[1] for x in exits if x[0] == tv_last_tm][0]
    dt = abs(t["exit_ts"] - tv_last_tm)
    dp = abs(t["exit_price"] - tv_last_p)
    if dt <= TOL and dp < max(tv_last_p * 0.0005, 1.0):
        exit_ok += 1
    else:
        exit_bad += 1
        kind = ("timestamp" if dt > TOL else "preco")
        codes = sorted(set(x[2] for x in exits))
        bad_kinds[f"{kind} | tv_codes={codes} | local={t['exit_comment']}"] += 1
        if len(examples) < 10:
            examples.append((tm, side, exits, t))

print(f"saidas iguais: {exit_ok} | divergentes: {exit_bad}")
print("\ntipos de divergencia:")
for k, v in bad_kinds.most_common(12):
    print(f"  {v:3d}x {k}")


def fmt(ms):
    return str(pd.Timestamp(ms, unit="ms"))[:16]


print("\nexemplos:")
for tm, side, exits, t in examples:
    tv_str = "; ".join(f"{fmt(x[0])} @{x[1]:.1f} c{x[2]}" for x in sorted(exits))
    print(f"  {fmt(tm)} {'L' if side==1 else 'S'}")
    print(f"    TV:    {tv_str}")
    print(f"    local: parcial {t['partial_exit_price']} | "
          f"saida {fmt(t['exit_ts'])} @{t['exit_price']:.1f} ({t['exit_comment']})")
