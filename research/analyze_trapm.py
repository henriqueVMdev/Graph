# -*- coding: utf-8 -*-
"""Engenharia reversa do TrapM/MM9-LW a partir dos legs do Strategy Tester
(research/data/trapm_legs.json) cruzados com os candles BTC 15m Bybit.

Hipoteses testadas:
  H1 trigger de entrada  = High do candle de sinal (+tick) / Low (short)
  H2 stop (perna 70%)    = min Low de k candles ate o sinal (-tick)
  H3 TP1/TP2             = multiplos R do risco (entrada-stop)
  H4 saida "Slow MA"     = close cruza MA lenta (testa EMA/SMA 20/40/50)
  H5 vies                = MA rapida vs MA lenta no candle de sinal
  H6 filtro min gain     = piso na distancia % do risco/alvo (update novo)

Uso: py research/analyze_trapm.py
"""

import json
import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TICK = 0.1

legs = json.load(open(os.path.join(HERE, "data", "trapm_legs.json")))
df = pd.read_csv(os.path.join(HERE, "data", "btc_15m_bybit.csv"),
                 index_col=0, parse_dates=True)
TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
O, H, L, C = (df[c].values for c in ["Open", "High", "Low", "Close"])
ts2i = {int(t): k for k, t in enumerate(TS)}

# medias candidatas
mas = {}
for n in (8, 9, 20, 21, 40, 50):
    mas[f"EMA{n}"] = pd.Series(C).ewm(span=n, adjust=False).mean().values
    mas[f"SMA{n}"] = pd.Series(C).rolling(n).mean().values

# agrupa legs por posicao (mesmo entry tm)
pos = defaultdict(list)
for e_tm, e_p, q, side, x_tm, x_p, code in legs:
    pos[(int(e_tm), int(side))].append(dict(e_p=e_p, q=q, x_tm=int(x_tm),
                                            x_p=x_p, code=code))
print(f"{len(legs)} legs -> {len(pos)} posicoes")

h1 = Counter()
h2 = {k: Counter() for k in (1, 2, 3, 4, 5)}
r_tp1, r_tp2, risk_pct, gain_pct = [], [], [], []
h4 = {name: Counter() for name in mas}
h5 = {name: Counter() for name in mas}

for (e_tm, side), lg in pos.items():
    i = ts2i.get(e_tm)
    if i is None or i < 60:
        continue
    s = i - 1                       # candle de sinal
    e_p = lg[0]["e_p"]

    # H1: trigger = extremo do candle de sinal (fill sem gap = trigger)
    trig = H[s] if side == 1 else L[s]
    gap = (O[i] > trig + TICK) if side == 1 else (O[i] < trig - TICK)
    if gap:
        h1["gap (fill na abertura)"] += 1
    elif abs(e_p - trig) < TICK * 1.5:
        h1["== extremo do sinal"] += 1
    elif abs(e_p - trig - TICK * side) < TICK * 1.5:
        h1["== extremo + tick"] += 1
    else:
        h1["outro"] += 1

    # stop real: preco da perna 2 quando saiu por STOP (perda)
    sl_price = None
    for leg in lg:
        if leg["code"] == 2:
            lose = (leg["x_p"] < e_p) if side == 1 else (leg["x_p"] > e_p)
            if lose:
                sl_price = leg["x_p"]
    # H2: stop estrutural = min low (max high) de k candles ate o sinal
    if sl_price is not None:
        for k in h2:
            lo = max(0, s - k + 1)
            ref = L[lo:s + 1].min() if side == 1 else H[lo:s + 1].max()
            ref = ref - TICK * side
            if abs(sl_price - ref) < TICK * 2:
                h2[k]["bate"] += 1
            else:
                h2[k]["nao"] += 1
        risk = abs(e_p - sl_price)
        risk_pct.append(risk / e_p * 100)

    # H3: TP1/TP2 em R (só quando temos o stop da mesma posicao)
    for leg in lg:
        if sl_price is None:
            break
        risk = abs(e_p - sl_price)
        if risk <= 0:
            break
        if leg["code"] == 1:
            r_tp1.append(abs(leg["x_p"] - e_p) / risk)
            gain_pct.append(abs(leg["x_p"] - e_p) / e_p * 100)
        if leg["code"] == 2:
            win = (leg["x_p"] > e_p) if side == 1 else (leg["x_p"] < e_p)
            if win:
                r_tp2.append(abs(leg["x_p"] - e_p) / risk)

    # H4: saida MA lenta — close do candle da saida cruzou a media?
    for leg in lg:
        if leg["code"] != 3:
            continue
        j = ts2i.get(leg["x_tm"])
        if j is None:
            continue
        for name, m in mas.items():
            crossed = (C[j] < m[j]) if side == 1 else (C[j] > m[j])
            h4[name]["bate" if crossed else "nao"] += 1

    # H5: vies no candle de sinal (rapida vs lenta candidatas em pares)
    for name, m in mas.items():
        ok = (C[s] > m[s]) if side == 1 else (C[s] < m[s])
        h5[name]["bate" if ok else "nao"] += 1

print("\nH1 trigger de entrada:", dict(h1))
print("\nH2 stop = extremo de k candles ate o sinal (-tick):")
for k, c in h2.items():
    tot = sum(c.values())
    if tot:
        print(f"  k={k}: {c['bate']}/{tot} ({c['bate']/tot*100:.0f}%)")

for arr, lbl in ((r_tp1, "TP1"), (r_tp2, "TP2")):
    if arr:
        a = np.array(arr)
        print(f"\nH3 {lbl} em R: mediana {np.median(a):.3f} | p10 {np.percentile(a,10):.3f} "
              f"| p90 {np.percentile(a,90):.3f} | n={len(a)}")

print("\nH4 saida 'Slow MA Stop' = close cruza a media (no candle da saida):")
for name, c in sorted(h4.items(), key=lambda x: -x[1]["bate"]):
    tot = sum(c.values())
    if tot:
        print(f"  {name:6s}: {c['bate']}/{tot} ({c['bate']/tot*100:.0f}%)")

print("\nH5 vies no sinal (close vs media):")
for name, c in sorted(h5.items(), key=lambda x: -x[1]["bate"]):
    tot = sum(c.values())
    print(f"  {name:6s}: {c['bate']}/{tot} ({c['bate']/tot*100:.0f}%)")

if risk_pct:
    a = np.array(risk_pct)
    print(f"\nH6 risco%% (entrada->stop): min {a.min():.3f} | p5 {np.percentile(a,5):.3f} "
          f"| mediana {np.median(a):.3f} | max {a.max():.3f} | n={len(a)}")
if gain_pct:
    a = np.array(gain_pct)
    print(f"H6 ganho%% ate TP1:        min {a.min():.3f} | p5 {np.percentile(a,5):.3f} "
          f"| mediana {np.median(a):.3f} | max {a.max():.3f} | n={len(a)}")
