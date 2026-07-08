# -*- coding: utf-8 -*-
"""Rodada 3: preco de saida do Slow MA Stop = close do candle do cruzamento
ou abertura do candle seguinte? E o candle do fill conta para o MA stop?"""

import json
import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
O, C = df["Open"].values, df["Close"].values
ts2i = {int(t): k for k, t in enumerate(TS)}

hits = Counter()
diffs_close, diffs_open = [], []
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    if code != 3:
        continue
    j = ts2i.get(int(x_tm))
    if j is None:
        continue
    dc = abs(x_p - C[j])
    do = abs(x_p - O[j]) if j > 0 else 1e9
    dn = abs(x_p - O[j + 1]) if j + 1 < len(O) else 1e9
    best = min(dc, do, dn)
    hits["close[j]" if best == dc else ("open[j]" if best == do else "open[j+1]")] += 1
    diffs_close.append(dc / x_p * 100)

print("Slow MA Stop, preco de saida mais proximo de:", dict(hits))
print(f"dif vs close[j]: mediana {np.median(diffs_close):.4f}% "
      f"| p90 {np.percentile(diffs_close, 90):.4f}%")

# entrada e saida no MESMO candle (fill bar conta p/ MA stop?)
same = sum(1 for e_tm, _, _, _, x_tm, _, c in legs if c == 3 and e_tm == x_tm)
print(f"saidas MA no MESMO candle do fill: {same}")
