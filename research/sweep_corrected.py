# -*- coding: utf-8 -*-
"""Varre tp/sl da MM9 Pullback Maker com a semantica CORRIGIDA (TP do candle
do fill segue a forma da barra), custos stress e janela 19-00h BRT.

Selecao APENAS no treino (70%); o forward so avalia a config vencedora.
Metrica de treino: expectancia media ponderada por n, agregada nos 12 ativos.

Uso: py research/sweep_corrected.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from research.research6_multi import SCRATCH, SYMS, prep, run, stats, fmt

TPS = [0.4, 0.5, 0.75, 1.0, 1.5, 2.0]
SLS = [0.9, 1.2, 1.5, 2.0, 3.0]

data = {}
for sym in SYMS:
    try:
        df = pd.read_csv(SCRATCH + fr"\{sym}_15m_bybit.csv", index_col=0, parse_dates=True)
        fund = pd.read_csv(SCRATCH + fr"\funding_{sym}.csv")
    except FileNotFoundError:
        continue
    d = prep(df)
    N = d["N"]
    data[sym] = (d, fund["timestamp"].values, fund["rate"].values,
                 np.arange(N) < int(N * 0.7))

print(f"{len(data)} simbolos carregados")
print(f"{'tp':>5s} {'sl':>5s} | {'n_tr':>5s} {'exp_tr':>8s} {'pf_tr':>6s} | pos/total ativos")

rows = []
for tp in TPS:
    for sl in SLS:
        pnls = []
        pos = 0
        for sym, (d, fts, fr, tr_mask) in data.items():
            t = run(d, fts, fr, tp_pct=tp, sl_pct=sl, mask=tr_mask)
            p = [x[0] for x in t]
            pnls += p
            if p and np.mean(p) > 0:
                pos += 1
        p = np.array(pnls)
        if len(p) == 0:
            continue
        loss = abs(p[p <= 0].sum())
        pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
        rows.append(dict(tp=tp, sl=sl, n=len(p), exp=p.mean(), pf=pf, pos=pos))
        print(f"{tp:5.2f} {sl:5.2f} | {len(p):5d} {p.mean():+8.4f} {pf:6.2f} | {pos}/{len(data)}")

best = max(rows, key=lambda r: r["exp"])
print(f"\nMelhor no TREINO: tp={best['tp']} sl={best['sl']} "
      f"(exp {best['exp']:+.4f}, pf {best['pf']:.2f}, {best['pos']}/{len(data)} ativos positivos)")

print("\n=== FORWARD da config vencedora (nunca visto na selecao) ===")
print(f"{'sym':5s} | {'FORWARD n/wr/exp/pf/tot/freq':42s}")
fwd_frames = []
for sym, (d, fts, fr, tr_mask) in data.items():
    t = run(d, fts, fr, tp_pct=best["tp"], sl_pct=best["sl"], mask=~tr_mask)
    s = stats(t)
    print(f"{sym.upper():5s} | {fmt(s):42s}")
    if t:
        w = pd.DataFrame(t, columns=["net_pct", "ts_entry", "ts_exit", "side"])
        w["symbol"] = sym
        fwd_frames.append(w)

allf = pd.concat(fwd_frames)
p = allf["net_pct"].values
loss = abs(p[p <= 0].sum())
pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
print(f"\nAGREGADO forward: n={len(p)} WR={(p > 0).mean()*100:.1f}% "
      f"exp={p.mean():+.4f} PF={pf:.2f}")
allf.sort_values("ts_entry").to_csv(SCRATCH + r"\trades_sweep_best_fwd.csv", index=False)
