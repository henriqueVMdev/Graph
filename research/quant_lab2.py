# -*- coding: utf-8 -*-
"""Rodada 2 do laboratorio (ainda SO TREINO): horizontes maiores para
amortizar o custo taker, e funding como sinal de carry combinado com
momentum. Mesma execucao honesta de quant_lab.py.

Uso: py research/quant_lab2.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant_lab import (SCRATCH, SYMS, ema, run_engine, stats,
                       sig_momentum, sig_donchian, sig_session_break)


def sig_funding_mom(df, fund, n=96, thr=0.5, f_thr=0.0):
    base = sig_momentum(df, n, thr)
    TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
    fts, fr = fund["timestamp"].values, fund["rate"].values
    idx = np.clip(np.searchsorted(fts, TS, side="right") - 1, 0, len(fr) - 1)
    f_now = fr[idx]
    sig = base.copy()
    sig[(base == 1) & (f_now > f_thr)] = 0
    sig[(base == -1) & (f_now < -f_thr)] = 0
    return sig


def sig_carry_mom(df, fund, n=192, f_pct=80):
    """Carry + momentum: entra no lado que RECEBE funding quando o funding
    esta extremo (percentil movel) E o momentum concorda."""
    C = df["Close"].values
    ret = pd.Series(C).pct_change(n).values * 100
    TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
    fts, fr = fund["timestamp"].values, fund["rate"].values
    idx = np.clip(np.searchsorted(fts, TS, side="right") - 1, 0, len(fr) - 1)
    f_now = fr[idx]
    fabs = pd.Series(np.abs(fr)).rolling(90).quantile(f_pct / 100).values
    f_hi = fabs[np.clip(idx, 0, len(fabs) - 1)]
    sig = np.zeros(len(df))
    # funding positivo extremo = longs pagam -> short recebe; exige mom < 0
    sig[(f_now > f_hi) & (ret < 0)] = -1
    # funding negativo extremo = shorts pagam -> long recebe; exige mom > 0
    sig[(f_now < -f_hi) & (ret > 0)] = 1
    return sig


def sig_donchian_fund(df, fund, n=192, trend=400, f_thr=0.0):
    base = sig_donchian(df, n, trend)
    TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
    fts, fr = fund["timestamp"].values, fund["rate"].values
    idx = np.clip(np.searchsorted(fts, TS, side="right") - 1, 0, len(fr) - 1)
    f_now = fr[idx]
    sig = base.copy()
    sig[(base == 1) & (f_now > f_thr)] = 0
    sig[(base == -1) & (f_now < -f_thr)] = 0
    return sig


def sig_session_fund(df, fund):
    base = sig_session_break(df)
    TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
    fts, fr = fund["timestamp"].values, fund["rate"].values
    idx = np.clip(np.searchsorted(fts, TS, side="right") - 1, 0, len(fr) - 1)
    f_now = fr[idx]
    sig = base.copy()
    sig[(base == 1) & (f_now > 0)] = 0
    sig[(base == -1) & (f_now < 0)] = 0
    return sig


FAMILIES = {
    "fundmom 48h2% s3 t48h":  (lambda d, f: sig_funding_mom(d, f, 192, 2.0), dict(stop_atr=3, max_bars=192)),
    "fundmom 48h3% s3 t96h":  (lambda d, f: sig_funding_mom(d, f, 192, 3.0), dict(stop_atr=3, max_bars=384)),
    "fundmom 96h4% s4 t96h":  (lambda d, f: sig_funding_mom(d, f, 384, 4.0), dict(stop_atr=4, max_bars=384)),
    "fundmom 48h2% trail4":   (lambda d, f: sig_funding_mom(d, f, 192, 2.0), dict(stop_atr=4, max_bars=384, trail=True)),
    "carry+mom 48h p80 t48h": (lambda d, f: sig_carry_mom(d, f, 192, 80),  dict(stop_atr=3, max_bars=192)),
    "carry+mom 48h p90 t96h": (lambda d, f: sig_carry_mom(d, f, 192, 90),  dict(stop_atr=3, max_bars=384)),
    "carry+mom 24h p80 t48h": (lambda d, f: sig_carry_mom(d, f, 96, 80),   dict(stop_atr=3, max_bars=192)),
    "donch48h fund s3 trail": (lambda d, f: sig_donchian_fund(d, f, 192),  dict(stop_atr=3, max_bars=384, trail=True)),
    "donch96h fund s4 t96h":  (lambda d, f: sig_donchian_fund(d, f, 384, 400), dict(stop_atr=4, max_bars=384)),
    "sessao fund s2 t11h":    (lambda d, f: sig_session_fund(d, f),        dict(stop_atr=2, max_bars=44)),
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

    print(f"{len(data)} simbolos | apenas TREINO (70%)")
    print(f"{'familia':24s} {'n':>6s} {'WR':>6s} {'exp/trade':>10s} {'PF':>6s} {'pos':>5s} {'tr/d':>5s}")
    for name, (sigfn, cfg) in FAMILIES.items():
        allt = []
        pos = 0
        for sym, (df, fund) in data.items():
            tr = run_engine(df, fund, sigfn(df, fund), cfg)
            if tr:
                p = np.array([t[0] for t in tr])
                if p.mean() > 0:
                    pos += 1
                allt += tr
        s = stats(allt)
        if not s:
            print(f"{name:24s}   sem trades")
            continue
        days = 255 * len(data)
        print(f"{name:24s} {s['n']:6d} {s['wr']:5.1f}% {s['exp']:+10.4f} "
              f"{s['pf']:6.2f} {pos:3d}/12 {s['n']/days:5.2f}")
