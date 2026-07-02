# -*- coding: utf-8 -*-
"""
Teste de paridade: o caminho REAL do runner (signal() + engine_paper +
store, via runner._process_deployment) alimentado candle a candle com o
histórico deve reproduzir EXATAMENTE os trades do backtest run() —
mesmos preços de entrada/saída, mesmos candles, mesmos motivos.

Também é o teste de replay: processar 8.000 candles de uma vez é o mesmo
código que roda quando o PC fica desligado e religa.

Requer research/data/btc_15m_bybit.csv (gerado por research/download_data.py).
"""

import json
import os
import sys
import tempfile

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DATA_CSV = os.path.join(ROOT, "research", "data", "btc_15m_bybit.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(DATA_CSV),
    reason="research/data ausente — rode research/download_data.py")


@pytest.fixture()
def df8k():
    df = pd.read_csv(DATA_CSV, index_col=0, parse_dates=True)
    return df.tail(8000)


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


def _run_backtest_trades(df, params):
    from automation.signals import load_strategy
    m = load_strategy("mm9_pullback")
    r = m.run(df.copy(), params)
    trades = r["trades"]
    # o backtest fecha posição pendente no último candle ("Fim dos Dados");
    # o runner a deixa aberta — ignorar na comparação
    return [t for t in trades if t["exit_comment"] != "Fim dos Dados"]


def _run_live_replay(df, params, tmp_store):
    """Roda o caminho de produção: um deployment paper reprocessando todo o
    histórico como se fosse um gap gigante de replay."""
    from automation import runner as rn

    dep_id = tmp_store.create_deployment(
        "parity", "mm9_pullback", params, "BTC", "15m", "bybit",
        "paper", params.get("initial_capital", 50000))
    ts_all = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype("int64")
    # começa após o warm-up mínimo do signal() (400 barras)
    tmp_store.update_deployment(dep_id, status="running",
                                last_candle_ts=int(ts_all[399]))
    dep = tmp_store.get_deployment(dep_id)
    r = rn.Runner()
    r._process_deployment(dep, df, "15m")
    return dep_id


def _compare(bt_trades, live_positions, first_live_ts):
    # o backtest pode ter trades antes do ponto onde o replay começou
    bt = [t for t in bt_trades if t["entry_ts"] >= first_live_ts]
    assert len(bt) == len(live_positions), \
        f"n trades: backtest={len(bt)} live={len(live_positions)}"
    for k, (t, p) in enumerate(zip(bt, live_positions)):
        assert int(t["entry_ts"]) == int(p["entry_candle_ts"]), f"trade {k}: entry_ts"
        assert int(t["exit_ts"]) == int(p["exit_candle_ts"]), f"trade {k}: exit_ts"
        assert abs(t["entry_price"] - p["entry_price"]) < 1e-9, f"trade {k}: entry"
        assert abs(t["exit_price"] - p["exit_price"]) < 1e-9, f"trade {k}: exit"
        assert int(t["direction"]) == int(p["side"]), f"trade {k}: side"
        assert t["exit_comment"] == p["exit_reason"], f"trade {k}: reason"


@pytest.mark.parametrize("params", [
    {"initial_capital": 50000},                            # janela 19-00h (default)
    {"initial_capital": 50000, "use_hour_filter": False},  # 24h (mais fills)
])
def test_parity_runner_vs_backtest(df8k, tmp_store, params):
    bt_trades = _run_backtest_trades(df8k, params)
    dep_id = _run_live_replay(df8k, params, tmp_store)

    live = tmp_store.list_closed_positions(dep_id, limit=100000)
    live.sort(key=lambda p: p["entry_candle_ts"])
    ts_all = ((df8k.index - pd.Timestamp(0)).total_seconds().values * 1000).astype("int64")
    _compare(bt_trades, live, first_live_ts=int(ts_all[400]))
    assert len(live) > 10, "amostra pequena demais para o teste significar algo"


def test_signal_contract(df8k):
    """signal() respeita o contrato e é None sem warm-up."""
    from automation.signals import get_signal
    assert get_signal("mm9_pullback", df8k.iloc[:100], {}) is None
    sig_found = None
    # procura um candle com sinal no fim do dataset (24h p/ facilitar)
    for k in range(len(df8k) - 1, 400, -1):
        sig_found = get_signal("mm9_pullback", df8k.iloc[:k],
                               {"use_hour_filter": False})
        if sig_found:
            break
    assert sig_found is not None
    assert sig_found["side"] in (1, -1)
    assert sig_found["price"] > 0
    assert sig_found["fill_rule"] == "cross"
