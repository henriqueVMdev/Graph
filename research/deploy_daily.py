# -*- coding: utf-8 -*-
"""Cria os deployments PAPER da daily_ensemble (portfólio validado em
research/daily_opt.py — 13 símbolos, 1d, Binance). Idempotente: pula
nomes que já existem. O runner (server) processa ao subir.

Uso: py research/deploy_daily.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from automation import store

SYMS = ["BTC", "ETH", "BNB", "LTC", "XRP", "ADA", "LINK", "DOGE",
        "SOL", "AVAX", "DOT", "NEAR", "SUI"]

store.init_db()
existing = {d["name"] for d in store.list_deployments()}
for sym in SYMS:
    name = f"DailyEns {sym}"
    if name in existing:
        print(name, "já existe — pulado")
        continue
    dep_id = store.create_deployment(
        name, "daily_ensemble", {}, sym, "1d", "binance", "paper", 1000.0,
        backtest_ref={"fonte": "research/daily_opt.py",
                      "treino_pf": 2.75, "val_24_25_pf": 1.64,
                      "premissas": "paper sem slippage e sem funding"})
    store.update_deployment(dep_id, status="running")
    print(name, dep_id, "running")
print("FIM")
