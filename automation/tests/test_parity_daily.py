# -*- coding: utf-8 -*-
"""
Paridade da estratégia POSICIONAL (market/open + exit_on_flip): o caminho
real do runner alimentado candle a candle deve reproduzir os segmentos do
sinal vetorizado do research (daily_opt: ensemble + regime + gate) —
mesmos candles, entradas/saídas exatamente nas aberturas, mesmos lados.

Requer research/data/btc_1d_binance.csv (research/download_daily.py).
"""

import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DATA_CSV = os.path.join(ROOT, "research", "data", "btc_1d_binance.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(DATA_CSV),
    reason="research/data ausente — rode research/download_daily.py")

START_K = 400          # warm-up do runner (len(df_hist) >= 400)


@pytest.fixture()
def df_daily():
    return pd.read_csv(DATA_CSV, index_col=0, parse_dates=True)


@pytest.fixture()
def tmp_store(monkeypatch):
    from automation import store
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(store, "DB_PATH", path)
    store.init_db()
    yield store
    for suf in ("", "-wal", "-shm"):
        try:
            os.remove(path + suf)
        except OSError:
            pass


def _expected_segments(df):
    """Referência vetorizada (mesma matemática de research/daily_opt.py):
    lista de (entry_ts, entry_open, exit_ts, exit_open, side); posição
    final ainda aberta é ignorada."""
    C = df["Close"].values
    vs = []
    for n in (7, 14, 21, 28):
        r = pd.Series(C).pct_change(n).values
        s = np.where(r > 0, 1.0, -1.0)
        s[np.isnan(r)] = 0.0
        vs.append(s)
    m = np.mean(vs, axis=0)
    raw = np.where(m >= 0.5, 1, np.where(m <= -0.5, -1, 0))
    sma = pd.Series(C).rolling(200).mean().values
    with np.errstate(invalid="ignore"):
        bull = C > sma
    s = np.where(bull & (raw > 0), 1, np.where(~bull & (raw < 0), -1, 0))

    ts = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype("int64")
    O = df["Open"].values
    segs, pos, e = [], 0, None
    for i in range(START_K, len(df) - 1):
        si = int(s[i])
        if si != pos:
            if pos != 0:
                segs.append((int(ts[e]), float(O[e]),
                             int(ts[i + 1]), float(O[i + 1]), pos))
            pos = si
            e = i + 1 if si != 0 else None
    return segs


def test_parity_daily_positional(df_daily, tmp_store, monkeypatch):
    from automation import runner as rn
    from automation.signals import load_strategy

    mod = load_strategy("daily_ensemble")
    mod._regime_cache = None
    monkeypatch.setattr(mod, "_fetch_regime", lambda ma: df_daily)

    dep_id = tmp_store.create_deployment(
        "parity-daily", "daily_ensemble", {}, "BTC", "1d", "binance",
        "paper", 1000)
    ts_all = ((df_daily.index - pd.Timestamp(0)).total_seconds().values
              * 1000).astype("int64")
    tmp_store.update_deployment(dep_id, status="running",
                                last_candle_ts=int(ts_all[START_K - 1]))
    dep = tmp_store.get_deployment(dep_id)
    rn.Runner()._process_deployment(dep, df_daily, "1d")

    live = tmp_store.list_closed_positions(dep_id, limit=100000)
    live.sort(key=lambda p: p["entry_candle_ts"])
    segs = _expected_segments(df_daily)

    assert len(segs) == len(live), \
        f"n trades: referencia={len(segs)} live={len(live)}"
    for k, (seg, p) in enumerate(zip(segs, live)):
        e_ts, e_px, x_ts, x_px, side = seg
        assert int(p["entry_candle_ts"]) == e_ts, f"trade {k}: entry_ts"
        assert abs(p["entry_price"] - e_px) < 1e-9, f"trade {k}: entry_price"
        assert int(p["exit_candle_ts"]) == x_ts, f"trade {k}: exit_ts"
        assert abs(p["exit_price"] - x_px) < 1e-9, f"trade {k}: exit_price"
        assert int(p["side"]) == side, f"trade {k}: side"
        assert p["exit_reason"] == "Sinal contrário", f"trade {k}: reason"
        assert 0 < p["exposure"] <= 1.5, f"trade {k}: exposure"
    assert len(live) > 20, "amostra pequena demais para o teste significar algo"


def test_signal_contract_daily(df_daily, monkeypatch):
    """signal() respeita o contrato market/open e é None sem warm-up."""
    from automation.signals import get_signal, load_strategy
    mod = load_strategy("daily_ensemble")
    mod._regime_cache = None
    monkeypatch.setattr(mod, "_fetch_regime", lambda ma: df_daily)

    assert get_signal("daily_ensemble", df_daily.iloc[:100], {}) is None
    sig = None
    for k in range(len(df_daily) - 1, START_K, -1):
        sig = get_signal("daily_ensemble", df_daily.iloc[:k], {})
        if sig:
            break
    assert sig is not None
    assert sig["side"] in (1, -1)
    assert sig["price"] is None and sig["fill_rule"] == "open"
    assert sig["exit_on_flip"] is True
    assert 0 < sig["exposure"] <= 1.5
