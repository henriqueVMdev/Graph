# -*- coding: utf-8 -*-
"""Rodada 3: plato de robustez do carry+momentum (SO TREINO).
Grid pequeno; o criterio e a VIZINHANCA positiva, nao o pico.

Uso: py research/quant_lab3.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import SCRATCH, SYMS, run_engine, stats
from quant_lab2 import sig_carry_mom

if __name__ == "__main__":
    data = {}
    for sym in SYMS:
        try:
            df = pd.read_csv(os.path.join(SCRATCH, f"{sym}_15m_bybit.csv"),
                             index_col=0, parse_dates=True)
            fund = pd.read_csv(os.path.join(SCRATCH, f"funding_{sym}.csv"))
        except FileNotFoundError:
            continue
        cut = int(len(df) * 0.7)
        data[sym] = (df.iloc[:cut], fund)

    print(f"{len(data)} simbolos | apenas TREINO")
    print(f"{'mom_n':>5s} {'pct':>4s} {'stop':>4s} {'tmax':>4s} | "
          f"{'n':>5s} {'WR':>6s} {'exp':>8s} {'PF':>5s} {'pos':>5s}")
    rows = []
    for n in (48, 96, 192):
        for pct in (70, 80, 85):
            for stop in (2.0, 3.0):
                for tmax in (96, 192):
                    allt = []
                    pos = 0
                    for sym, (df, fund) in data.items():
                        tr = run_engine(df, fund, sig_carry_mom(df, fund, n, pct),
                                        dict(stop_atr=stop, max_bars=tmax))
                        if tr:
                            p = np.array([t[0] for t in tr])
                            if p.mean() > 0:
                                pos += 1
                            allt += tr
                    s = stats(allt)
                    if not s:
                        continue
                    rows.append((n, pct, stop, tmax, s, pos))
                    print(f"{n:5d} {pct:4d} {stop:4.1f} {tmax:4d} | {s['n']:5d} "
                          f"{s['wr']:5.1f}% {s['exp']:+8.4f} {s['pf']:5.2f} {pos:3d}/12")
