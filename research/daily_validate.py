# -*- coding: utf-8 -*-
"""Validacao 2024-2025 (uma vez) das familias diarias selecionadas no
TREINO (<2024) por research/daily_lab.py. Edite SELECTED com as escolhidas
ANTES de olhar qualquer numero pos-2024.

Uso: py research/daily_validate.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_lab import (SCRATCH, SYMS, FAMILIES, run_daily,
                       portfolio_stats, TRAIN_END)

# preencher apos a selecao no treino (nomes de FAMILIES)
SELECTED = []

VAL_END = "2026-01-01"

if __name__ == "__main__":
    if not SELECTED:
        print("edite SELECTED com as familias escolhidas no treino")
        sys.exit(1)
    data = {}
    for sym in SYMS:
        try:
            data[sym] = pd.read_csv(
                os.path.join(SCRATCH, f"{sym}_1d_binance.csv"),
                index_col=0, parse_dates=True)
        except FileNotFoundError:
            continue

    t0 = pd.Timestamp(TRAIN_END).value // 10**6
    t1 = pd.Timestamp(VAL_END).value // 10**6
    print(f"VALIDACAO {TRAIN_END} -> {VAL_END} | {len(data)} simbolos")
    for name in SELECTED:
        sigfn, cfg = FAMILIES[name]
        frames = []
        for sym, df in data.items():
            tr = run_daily(df, sigfn(df), cfg)
            if len(tr):
                tr = tr[(tr["ts_entry"] >= t0) & (tr["ts_entry"] < t1)]
                tr["symbol"] = sym
                frames.append(tr)
        if frames:
            portfolio_stats(pd.concat(frames), name)
