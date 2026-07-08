# -*- coding: utf-8 -*-
"""Esteira honesta da spec TrapM (strategies/mm9.py) nos 12 perps Bybit:
janela de 1 ano 15m, split 70/30 treino/forward por simbolo, custos reais
Bybit + funding historico, cenario stress (funding 1.5x + slippage 0.05%
nas saidas a mercado).

Custos por trade (sobre o notional, escalados pela exposicao):
  entrada: STOP dispara a mercado -> taker
  TP1/TP2: limite -> maker
  Slow MA Stop / Fim do Periodo / stop estrutural: mercado -> taker+slip

Uso: py research/trapm_pipeline.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategies.mm9 as mm9

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "data")
MAKER, TAKER, SLIP = 0.0002, 0.00055, 0.0005
FUND_MULT = 1.5
SYMS = ["btc", "eth", "sol", "xrp", "doge", "bnb", "ada", "link",
        "avax", "sui", "ltc", "near"]


def net_trades(df, fund, params):
    res = mm9.run(df, params)
    fts = fund["timestamp"].values
    fr = fund["rate"].values
    out = []
    for t in res["trades"]:
        exp = t["exposure"] or 1.0
        # frações e taxa de saída por perna
        frac_p = t["partial_pct_closed"] or 0.0
        p_is_tp = frac_p > 0           # parcial só existe em alvo ou stop da perna 2
        p_rate = MAKER if (t["partial_exit_price"] and
                           ((t["partial_exit_price"] - t["entry_price"]) * t["direction"] > 0)) \
            else (TAKER + SLIP)
        x_tp = t["exit_comment"] in ("Alvo 1", "Alvo 2")
        x_rate = MAKER if x_tp else (TAKER + SLIP)
        fee_pct = (TAKER + frac_p * p_rate + (1 - frac_p) * x_rate) * 100
        i0 = np.searchsorted(fts, t["entry_ts"], side="right")
        i1 = np.searchsorted(fts, t["exit_ts"], side="right")
        f = fr[i0:i1].sum() * FUND_MULT if i1 > i0 else 0.0
        f_pct = (f if t["direction"] == 1 else -f) * 100
        net = t["pnl_pct"] - (fee_pct + f_pct) * exp
        out.append((net, t["entry_ts"], t["exit_ts"], t["direction"]))
    return out


def stats(tr):
    if not tr:
        return None
    p = np.array([x[0] for x in tr])
    loss = abs(p[p <= 0].sum())
    pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
    days = (tr[-1][2] - tr[0][1]) / 86400000
    return dict(n=len(p), wr=(p > 0).mean() * 100, exp=p.mean(), pf=pf,
                tot=p.sum(), tpd=len(p) / max(days, 1))


fmt = lambda s: (f"{s['n']:4d} {s['wr']:5.1f}% {s['exp']:+8.4f} {s['pf']:5.2f} "
                 f"{s['tot']:+7.1f} {s['tpd']:4.2f}/d") if s else "sem trades"

PARAMS = {"initial_capital": 1_000_000.0}

frames = []
print(f"{'sym':5s} | {'TREINO n/wr/exp/pf/tot/freq':40s} | {'FORWARD n/wr/exp/pf/tot/freq':40s}")
print("-" * 95)
for sym in SYMS:
    try:
        df = pd.read_csv(os.path.join(SCRATCH, f"{sym}_15m_bybit.csv"),
                         index_col=0, parse_dates=True)
        fund = pd.read_csv(os.path.join(SCRATCH, f"funding_{sym}.csv"))
    except FileNotFoundError:
        print(f"{sym.upper():5s} | dados ausentes")
        continue
    split_ms = (df.index[int(len(df) * 0.7)] - pd.Timestamp(0)).total_seconds() * 1000
    tr = net_trades(df, fund, PARAMS)
    tr_train = [t for t in tr if t[1] < split_ms]
    tr_fwd = [t for t in tr if t[1] >= split_ms]
    print(f"{sym.upper():5s} | {fmt(stats(tr_train)):40s} | {fmt(stats(tr_fwd)):40s}")
    w = pd.DataFrame(tr, columns=["net_pct", "ts_entry", "ts_exit", "side"])
    w["symbol"] = sym
    w["is_forward"] = w["ts_entry"] >= split_ms
    frames.append(w)

allt = pd.concat(frames)
for label, sel in (("TREINO", ~allt["is_forward"]), ("FORWARD", allt["is_forward"])):
    p = allt[sel]["net_pct"].values
    loss = abs(p[p <= 0].sum())
    pf = p[p > 0].sum() / loss if loss > 0 else float("inf")
    print(f"\nAGREGADO {label}: n={len(p)} WR={(p>0).mean()*100:.1f}% "
          f"exp={p.mean():+.4f} PF={pf:.2f}")
allt.sort_values("ts_entry").to_csv(os.path.join(SCRATCH, "trades_trapm_stress.csv"),
                                    index=False)
