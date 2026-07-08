# -*- coding: utf-8 -*-
"""Challenge mode v2 (SO TREINO): assimetria positiva com stops LARGOS.

Licao da v1: com stop de 1 ATR (~0.3%), o custo taker de ~0.16%/trade vira
0.5R — EV -0.3R e nenhuma assimetria salva. Aqui: stop >= 5 ATR (~1.5-2.5%
de distancia) faz o custo cair para <0.1R; alvo 4-6R; posicoes de dias;
poucos trades decidem o challenge.

Uso: py research/quant_lab5.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import (SCRATCH, SYMS, run_engine, stats,
                       sig_donchian, sig_momentum)
from quant_lab4 import mc_approval

FAMILIES = {
    "donch24h s5 tp20 2sem":  (lambda d, f: sig_donchian(d, 96),      dict(stop_atr=5, tp_atr=20, max_bars=1344)),
    "donch24h s5 tp30 2sem":  (lambda d, f: sig_donchian(d, 96),      dict(stop_atr=5, tp_atr=30, max_bars=1344)),
    "donch24h s8 tp32 2sem":  (lambda d, f: sig_donchian(d, 96),      dict(stop_atr=8, tp_atr=32, max_bars=1344)),
    "donch48h s6 tp24 2sem":  (lambda d, f: sig_donchian(d, 192),     dict(stop_atr=6, tp_atr=24, max_bars=1344)),
    "mom24h 3% s5 tp20":      (lambda d, f: sig_momentum(d, 96, 3.0), dict(stop_atr=5, tp_atr=20, max_bars=1344)),
    "mom24h 5% s6 tp24":      (lambda d, f: sig_momentum(d, 96, 5.0), dict(stop_atr=6, tp_atr=24, max_bars=1344)),
    "mom48h 5% s6 tp30":      (lambda d, f: sig_momentum(d, 192, 5.0), dict(stop_atr=6, tp_atr=30, max_bars=1344)),
    "donch24h s5 trail8":     (lambda d, f: sig_donchian(d, 96),      dict(stop_atr=8, max_bars=1344, trail=True)),
}

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

    print(f"{len(data)} simbolos | TREINO | criterio = aprovacao MC")
    print(f"{'familia':22s} {'n':>5s} {'WR':>6s} {'exp':>8s} {'PF':>5s} | "
          f"{'ap@0.75%':>8s} {'ap@1%':>7s} {'ap@1.5%':>8s} {'med.d':>5s}")
    for name, (sigfn, cfg) in FAMILIES.items():
        frames = []
        for sym, (df, fund) in data.items():
            tr = run_engine(df, fund, sigfn(df, fund), cfg)
            if tr:
                frames.append(pd.DataFrame(
                    tr, columns=["net_pct", "ts_entry", "ts_exit", "side",
                                 "stop_dist_pct"]))
        if not frames:
            continue
        allt = pd.concat(frames).sort_values("ts_entry")
        s = stats(list(allt[["net_pct", "ts_entry", "ts_exit"]].itertuples(index=False)))
        aps = []
        med1 = None
        for r in (0.0075, 0.01, 0.015):
            ap, med = mc_approval(allt, r)
            aps.append(ap)
            if r == 0.01:
                med1 = med
        ap_s = " ".join(f"{a:7.1f}%" if a is not None else "     -- " for a in aps)
        print(f"{name:22s} {s['n']:5d} {s['wr']:5.1f}% {s['exp']:+8.4f} "
              f"{s['pf']:5.2f} | {ap_s} {med1 or '--':>5}")
