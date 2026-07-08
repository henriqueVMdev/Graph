# -*- coding: utf-8 -*-
"""Challenge mode v3 (SO TREINO): refinamento do vencedor (donchian stop
largo) — alvos 4-8R x riscos 0.4-1.0%.

Uso: py research/quant_lab6.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import SCRATCH, SYMS, run_engine, sig_donchian
from quant_lab4 import mc_approval

CONFIGS = {
    "donch24h s8 tp32 (4R)": (96, dict(stop_atr=8, tp_atr=32, max_bars=1344)),
    "donch24h s8 tp48 (6R)": (96, dict(stop_atr=8, tp_atr=48, max_bars=1344)),
    "donch24h s8 tp64 (8R)": (96, dict(stop_atr=8, tp_atr=64, max_bars=2016)),
    "donch24h s6 tp36 (6R)": (96, dict(stop_atr=6, tp_atr=36, max_bars=1344)),
    "donch48h s8 tp48 (6R)": (192, dict(stop_atr=8, tp_atr=48, max_bars=1344)),
}
RISKS = (0.004, 0.005, 0.0075, 0.01)

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

    print(f"{len(data)} simbolos | TREINO")
    hdr = " ".join(f"ap@{r*100:.2f}%".rjust(9) for r in RISKS)
    print(f"{'config':24s} {'n':>5s} {'WR':>6s} | {hdr}")
    for name, (n_don, cfg) in CONFIGS.items():
        frames = []
        for sym, (df, fund) in data.items():
            tr = run_engine(df, fund, sig_donchian(df, n_don), cfg)
            if tr:
                frames.append(pd.DataFrame(
                    tr, columns=["net_pct", "ts_entry", "ts_exit", "side",
                                 "stop_dist_pct"]))
        allt = pd.concat(frames).sort_values("ts_entry")
        wr = (allt["net_pct"] > 0).mean() * 100
        cells = []
        for r in RISKS:
            ap, med = mc_approval(allt, r, n_sims=4000)
            cells.append(f"{ap:5.1f}%({med:.0f}d)" if ap is not None else "   --   ")
        print(f"{name:24s} {len(allt):5d} {wr:5.1f}% | " + " ".join(cells))
