# -*- coding: utf-8 -*-
"""Otimizacoes ANTI-overfit do TSMOM diario. Protocolo:
- Desenvolvimento 100% no TREINO (<2024). Holdout 2026 esta QUEIMADO.
- Otimizacoes estruturais (regra uniforme, nada tunado por simbolo):
    * ensemble de lookbacks (media dos votos 7/14/21/28) — remove a
      escolha arbitraria de um n unico;
    * filtro de regime: BTC > SMA200 -> so longs; abaixo -> so shorts;
    * vol targeting por trade: peso = TARGET_ATRPCT / ATR%% na entrada
      (cap 1.5x) — regra classica, nao tunada.
- Teste de plato: vizinhos do parametro tambem precisam funcionar.
- Validacao 2024-25 SO com `--val` num pacote pre-comprometido (1 vez).

Uso: py research/daily_opt.py [--val]
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_lab import SCRATCH, SYMS, run_daily, sig_tsmom, TRAIN_END

TARGET_ATRPCT = 3.0   # ATR% "tipico" no diario; peso = target/atr%, cap 1.5
W_CAP = 1.5
VAL_END = "2026-01-01"

data = {}
for sym in SYMS:
    try:
        data[sym] = pd.read_csv(os.path.join(SCRATCH, f"{sym}_1d_binance.csv"),
                                index_col=0, parse_dates=True)
    except FileNotFoundError:
        continue


def sig_ensemble(df, ns=(7, 14, 21, 28), thr=0.5):
    votes = np.array([sig_tsmom(df, n) for n in ns])
    m = votes.mean(axis=0)
    return np.where(m >= thr, 1, np.where(m <= -thr, -1, 0)).astype(float)


def btc_regime(ma_n=200):
    c = data["btc"]["Close"]
    return (c > c.rolling(ma_n).mean())


def gate(sig, df, regime):
    r = regime.reindex(df.index).ffill().fillna(False).values
    return np.where(r & (sig > 0), 1, np.where(~r & (sig < 0), -1, 0)).astype(float)


def collect(sigfn, t0=None, t1=None):
    frames = []
    for sym, df in data.items():
        tr = run_daily(df, sigfn(df), dict())
        if len(tr):
            tr["symbol"] = sym
            frames.append(tr)
    allt = pd.concat(frames)
    if t0:
        allt = allt[allt["ts_entry"] >= pd.Timestamp(t0).value // 10**6]
    if t1:
        allt = allt[allt["ts_entry"] < pd.Timestamp(t1).value // 10**6]
    return allt


def stats(tr, label, weighted=True):
    p = tr["net_pct"].values
    if weighted:
        w = np.minimum(TARGET_ATRPCT / tr["stop_dist_pct"].values, W_CAP)
        p = p * w
    if len(p) < 30:
        print(f"{label:34s} amostra insuficiente ({len(p)})")
        return
    loss = abs(p[p <= 0].sum())
    pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
    days = (tr["ts_exit"].max() - tr["ts_entry"].min()) / 86400000
    tpy = len(p) / max(days / 365.25, 0.1)
    sh = p.mean() / p.std() * np.sqrt(tpy) if p.std() > 0 else 0
    anos = pd.to_datetime(tr["ts_entry"], unit="ms").dt.year
    por_ano = " ".join(f"{a}:{p[anos.values == a].sum():+.0f}"
                       for a in sorted(anos.unique()))
    print(f"{label:34s} n={len(p):5d} WR={(p>0).mean()*100:4.1f}% "
          f"exp={p.mean():+6.3f}% PF={pf:5.2f} sh~{sh:5.2f} | {por_ano}")


if __name__ == "__main__":
    val = "--val" in sys.argv
    t0, t1 = (TRAIN_END, VAL_END) if val else (None, TRAIN_END)
    print(f"{'VALIDACAO ' + TRAIN_END + '->' + VAL_END if val else 'TREINO <' + TRAIN_END}"
          f" | {len(data)} simbolos | vol-target {TARGET_ATRPCT}%/cap {W_CAP}")

    if not val:
        reg = btc_regime(200)
        print("\n-- baselines (peso igual) --")
        stats(collect(lambda d: sig_tsmom(d, 21, True), t0, t1), "tsmom21 LO", False)
        stats(collect(lambda d: sig_ensemble(d), t0, t1), "ensemble L/S", False)
        print("\n-- estruturais (vol-weighted) --")
        stats(collect(lambda d: sig_tsmom(d, 21, True), t0, t1), "tsmom21 LO +volw")
        stats(collect(lambda d: sig_ensemble(d), t0, t1), "ensemble L/S +volw")
        stats(collect(lambda d: gate(sig_ensemble(d), d, reg), t0, t1),
              "ensemble +regime200 +volw")
        stats(collect(lambda d: gate(sig_tsmom(d, 21), d, reg), t0, t1),
              "tsmom21 +regime200 +volw")
        print("\n-- platos (ensemble+regime, vol-weighted) --")
        for ma_n in (150, 200, 250):
            r = btc_regime(ma_n)
            stats(collect(lambda d, r=r: gate(sig_ensemble(d), d, r), t0, t1),
                  f"  regime MA{ma_n}")
        for ns in ((7, 14, 21), (14, 21, 28), (7, 14, 21, 28), (7, 21, 28)):
            stats(collect(lambda d, ns=ns: gate(sig_ensemble(d, ns), d, reg), t0, t1),
                  f"  ns={ns}")
        for thr in (0.25, 0.5, 0.75):
            stats(collect(lambda d, t=thr: gate(sig_ensemble(d, thr=t), d, reg), t0, t1),
                  f"  thr={t}" if False else f"  thr={thr}")
    else:
        # PACOTE PRE-COMPROMETIDO (editar UMA vez apos o treino, antes de rodar)
        # escolhido no treino 2026-07-08: ensemble(7,14,21,28) thr=0.5 +
        # regime BTC/MA200 + vol-weight — unico positivo em todos os anos
        # do treino (incl. 2022) e em plato (MA150-250, thr 0.25-0.5 ~iguais)
        PACKAGE = lambda d: gate(sig_ensemble(d), d, btc_regime(200))
        if PACKAGE is None:
            print("edite PACKAGE com o pacote escolhido no treino")
            sys.exit(1)
        stats(collect(PACKAGE, t0, t1), "PACOTE FINAL (val 24-25)")
