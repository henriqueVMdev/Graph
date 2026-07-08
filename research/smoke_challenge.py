# -*- coding: utf-8 -*-
"""Smoke test do strategies/challenge_donchian.py (BTC 1 ano)."""
import sys
sys.path.insert(0, '.')
import pandas as pd
import strategies.challenge_donchian as s

df = pd.read_csv('research/data/btc_15m_bybit.csv', index_col=0, parse_dates=True)
r = s.run(df, {'initial_capital': 50000})
m = r['metrics']
print(f"BTC 1 ano (bruto): trades {m['total_trades']} | WR {m['win_rate']:.1f}% | "
      f"PF {m['profit_factor']:.2f} | ret {m['total_return']:+.2f}% | "
      f"maxDD {m['max_dd']:.2f}%")
print("signal() ultimo candle:", s.signal(df, {}))
print("ultimos 3 trades:")
for t in r["trades"][-3:]:
    print(f"  {t['entry_date']} {'L' if t['direction']==1 else 'S'} "
          f"in {t['entry_price']:.0f} -> {t['exit_price']:.0f} "
          f"({t['exit_comment']}) {t['pnl_pct']:+.3f}%")
