# -*- coding: utf-8 -*-
"""Rastreia o ciclo de vida do short de 2026-03-01 19:00 no motor mm9."""
import sys
sys.path.insert(0, '.')
import pandas as pd
import strategies.mm9 as mm9

df = pd.read_csv('research/data/btc_15m_bybit.csv', index_col=0, parse_dates=True)
df = df[df.index >= '2026-02-28']

orig_leg = mm9._run_backtest_mm9

# monkeypatch: injeta prints no engine via trace de linha seria pesado;
# em vez disso reproduz o run e imprime o trade bruto com todos os campos
res = mm9.run(df, {'initial_capital': 1_000_000.0})
for t in res['trades']:
    if t['entry_date'] == '2026-03-01' and t['direction'] == -1 \
            and abs(t['entry_price'] - 66211.8) < 1:
        for k, v in t.items():
            print(f"  {k}: {v}")
        break

# candles ao redor
w = df.loc['2026-03-01 18:30':'2026-03-01 20:30']
print(w[['Open', 'High', 'Low', 'Close']])
