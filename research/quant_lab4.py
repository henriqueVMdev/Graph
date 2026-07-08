# -*- coding: utf-8 -*-
"""Challenge mode (SO TREINO): estrategias de ASSIMETRIA POSITIVA — stop
apertado, alvo grande — otimizando P(aprovacao) no Monte Carlo do prop
challenge (+5% alvo, -10% total, -5% diaria), nao EV.

Racional: com risco ~1%/trade, cabem ~10 perdas antes de reprovar; um
unico vencedor de 5R+ fecha o alvo. P(pass) = 1-(1-p)^10 — p=15% ja da
~80%. Execucao honesta identica (quant_lab.run_engine).

Uso: py research/quant_lab4.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import (SCRATCH, SYMS, run_engine, stats,
                       sig_donchian, sig_momentum, sig_session_break)

LEV_CAP = 5.0


def mc_approval(trades_df, risk, n_sims=3000, seed=11,
                target=0.05, max_loss=-0.10, daily=-0.05, max_days=120):
    trades_df = trades_df.copy()
    trades_df["day"] = pd.to_datetime(trades_df["ts_entry"], unit="ms").dt.date
    pool = [g[["net_pct", "stop_dist_pct"]].values
            for _, g in trades_df.groupby("day", sort=True)]
    if len(pool) < 40:
        return None, None
    rng = np.random.default_rng(seed)
    wins, dtp = 0, []
    for _ in range(n_sims):
        bal = 1.0
        res = 0
        for d in range(1, max_days + 1):
            day = pool[int(rng.integers(len(pool)))]
            start = bal
            for net, sd in day:
                expo = min(risk * 100 / sd, LEV_CAP) if sd > 0 else 0.0
                bal += bal * (net / 100) * expo
                if (bal - 1.0) <= max_loss or (bal / start - 1.0) <= daily:
                    res, dd = 0, d
                    break
                if (bal - 1.0) >= target:
                    res, dd = 1, d
                    break
            else:
                continue
            break
        else:
            res, dd = 0, max_days
        wins += res
        if res:
            dtp.append(dd)
    return wins / n_sims * 100, (float(np.median(dtp)) if dtp else None)


FAMILIES = {
    "donch24h s1 tp6":     (lambda d, f: sig_donchian(d, 96),        dict(stop_atr=1.0, tp_atr=6, max_bars=96)),
    "donch24h s1 tp8":     (lambda d, f: sig_donchian(d, 96),        dict(stop_atr=1.0, tp_atr=8, max_bars=192)),
    "donch24h s0.75 tp6":  (lambda d, f: sig_donchian(d, 96),        dict(stop_atr=0.75, tp_atr=6, max_bars=96)),
    "donch24h s1.5 tp8":   (lambda d, f: sig_donchian(d, 96),        dict(stop_atr=1.5, tp_atr=8, max_bars=192)),
    "mom24h2% s1 tp6":     (lambda d, f: sig_momentum(d, 96, 2.0),   dict(stop_atr=1.0, tp_atr=6, max_bars=96)),
    "mom24h2% s1 tp8":     (lambda d, f: sig_momentum(d, 96, 2.0),   dict(stop_atr=1.0, tp_atr=8, max_bars=192)),
    "mom24h3% s1.5 tp8":   (lambda d, f: sig_momentum(d, 96, 3.0),   dict(stop_atr=1.5, tp_atr=8, max_bars=192)),
    "sessao s1 tp6":       (lambda d, f: sig_session_break(d),       dict(stop_atr=1.0, tp_atr=6, max_bars=96)),
    "sessao s0.75 tp5":    (lambda d, f: sig_session_break(d),       dict(stop_atr=0.75, tp_atr=5, max_bars=96)),
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
    print(f"{'familia':20s} {'n':>5s} {'WR':>6s} {'exp':>8s} {'PF':>5s} | "
          f"{'ap@0.75%':>8s} {'ap@1%':>7s} {'ap@1.5%':>8s} {'med.d':>5s}")
    for name, (sigfn, cfg) in FAMILIES.items():
        frames = []
        for sym, (df, fund) in data.items():
            tr = run_engine(df, fund, sigfn(df, fund), cfg)
            if tr:
                w = pd.DataFrame(tr, columns=["net_pct", "ts_entry", "ts_exit",
                                              "side", "stop_dist_pct"])
                frames.append(w)
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
        ap_s = " ".join(f"{a:7.1f}%" if a else "     -- " for a in aps)
        print(f"{name:20s} {s['n']:5d} {s['wr']:5.1f}% {s['exp']:+8.4f} "
              f"{s['pf']:5.2f} | {ap_s} {med1 or '--':>5}")
