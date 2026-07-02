"""
MM9 Pullback Maker — pullback à EMA9 no 15m com entrada por ordem LIMITE.

Regras (validadas em 1 ano de dados Bybit, sem lookahead):
- Entrada: limite no valor da EMA9 do candle ANTERIOR, válida por 1 candle
  (a cada candle de setup a limite é reposicionada). Fill exige o preço
  ATRAVESSAR a limite (Low < limite para long).
- Filtros (todos avaliados no candle anterior):
  tendência 15m (EMA50>EMA200 e Close>EMA200), slope da EMA9 do 1h usando
  APENAS horas fechadas (bucket 1h disponível somente 1h após abrir — o
  resample+ffill ingênuo vaza até 45min de futuro), Close>EMA9, e rank de
  volatilidade (ATR14% vs janela de 4 dias) acima do mínimo.
- Saídas: TP limite (+tp_pct), SL a mercado (-sl_pct), time-stop em
  max_bars. TP e SL no MESMO candle = LOSS (conservador).
- Janela de horário opcional (padrão 19h-00h Brasília): restringe só as
  ENTRADAS; as saídas são ordens que descansam na exchange (24/7).

O PnL emitido é BRUTO (preço), como as demais estratégias — fees e funding
ficam com o módulo de custos. Para refletir a execução real desta
estratégia, ligue os custos com use_maker_entry=True (entrada limite).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NAME = "MM9 Pullback Maker"
DESCRIPTION = (
    "Pullback à EMA9 no 15m com entrada limite (maker), filtros de tendência "
    "15m+1h e volatilidade, TP/SL assimétrico e janela de horário opcional. "
    "Use custos com maker na entrada."
)

CONFIG_SCHEMA = [
    {
        "title": "Entrada / Saída",
        "fields": [
            {"key": "tp_pct", "label": "Alvo (%)", "type": "number",
             "default": 0.5, "min": 0.1, "max": 5.0, "step": 0.1},
            {"key": "sl_pct", "label": "Stop (%)", "type": "number",
             "default": 1.5, "min": 0.3, "max": 10.0, "step": 0.1},
            {"key": "max_bars", "label": "Time-stop (barras)", "type": "number",
             "default": 48, "min": 4, "max": 384, "step": 4},
        ],
    },
    {
        "title": "Filtros",
        "fields": [
            {"key": "ma_fast", "label": "EMA pullback", "type": "number",
             "default": 9, "min": 3, "max": 50, "step": 1},
            {"key": "trend_fast", "label": "EMA tendência rápida", "type": "number",
             "default": 50, "min": 10, "max": 200, "step": 5},
            {"key": "trend_slow", "label": "EMA tendência lenta", "type": "number",
             "default": 200, "min": 50, "max": 500, "step": 10},
            {"key": "use_trend_1h", "label": "Filtro slope 1h", "type": "checkbox",
             "default": True},
            {"key": "vol_rank_min", "label": "Rank vol mínimo (0-1)", "type": "number",
             "default": 0.5, "min": 0.0, "max": 0.9, "step": 0.1},
            {"key": "allow_shorts", "label": "Operar short", "type": "checkbox",
             "default": True},
        ],
    },
    {
        "title": "Janela de Horário",
        "fields": [
            {"key": "use_hour_filter", "label": "Restringir horário de entrada",
             "type": "checkbox", "default": True},
            {"key": "hour_start", "label": "Início (hora local)", "type": "number",
             "default": 19, "min": 0, "max": 23, "step": 1, "show_if": "use_hour_filter"},
            {"key": "hour_end", "label": "Fim (hora local, exclusivo)", "type": "number",
             "default": 0, "min": 0, "max": 23, "step": 1, "show_if": "use_hour_filter"},
            {"key": "utc_offset", "label": "Fuso (Brasília = -3)", "type": "number",
             "default": -3, "min": -12, "max": 14, "step": 1, "show_if": "use_hour_filter"},
        ],
    },
    {
        "title": "Sizing",
        "fields": [
            {"key": "risk_per_trade", "label": "Risco por trade (%)", "type": "number",
             "default": 1.0, "min": 0.1, "max": 10.0, "step": 0.25},
            {"key": "leverage", "label": "Alavancagem máx (x)", "type": "number",
             "default": 2.0, "min": 1.0, "max": 25.0, "step": 0.5},
        ],
    },
]

# Grid usado pela otimização IS da WFA (e otimizador rápido)
OPTIMIZER_GRIDS = {
    "rapido": {
        "tp_pct":       [0.3, 0.4, 0.5, 0.6, 0.8],
        "sl_pct":       [0.9, 1.2, 1.5, 1.8],
        "max_bars":     [24, 48, 96],
        "vol_rank_min": [0.0, 0.3, 0.5, 0.7],
    },
}


def _safe(v):
    try:
        if v is None or np.isnan(v) or np.isinf(v):
            return None
    except (TypeError, ValueError):
        return v
    return float(v)


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _allowed_utc_hours(start: int, end: int, utc_offset: int) -> set:
    """Converte janela [start, end) em horas LOCAIS para o conjunto de horas
    UTC permitidas. end == start significa janela de 24h."""
    hours = set()
    h = start % 24
    while True:
        hours.add((h - utc_offset) % 24)
        h = (h + 1) % 24
        if h == end % 24 or len(hours) >= 24:
            break
    return hours


def run(df: pd.DataFrame, params: dict) -> dict:
    """Executa o backtest. df: OHLCV com DatetimeIndex UTC tz-naive.

    Retorna dict com keys: chart, metrics, drawdown, equity_curve, trades
    (mesmo contrato das demais estratégias da plataforma).
    """
    tp_pct       = float(params.get("tp_pct", 0.5))
    sl_pct       = float(params.get("sl_pct", 1.5))
    max_bars     = int(params.get("max_bars", 48))
    ma_fast      = int(params.get("ma_fast", 9))
    trend_fast   = int(params.get("trend_fast", 50))
    trend_slow   = int(params.get("trend_slow", 200))
    use_trend_1h = bool(params.get("use_trend_1h", True))
    vol_rank_min = float(params.get("vol_rank_min", 0.5))
    allow_shorts = bool(params.get("allow_shorts", True))
    use_hours    = bool(params.get("use_hour_filter", True))
    hour_start   = int(params.get("hour_start", 19))
    hour_end     = int(params.get("hour_end", 0))
    utc_offset   = int(params.get("utc_offset", -3))
    risk_pct     = float(params.get("risk_per_trade", 1.0))
    lev_cap      = max(float(params.get("leverage", 2.0)), 1.0)
    initial_capital = float(params.get("initial_capital", 1000.0))
    _fast        = bool(params.get("_fast", False))

    O = df["Open"].values
    H = df["High"].values
    L = df["Low"].values
    C = df["Close"].values
    N = len(df)
    # epoch ms independente da resolução interna do índice (ns ou us)
    TS = ((df.index - pd.Timestamp(0)).total_seconds().values * 1000).astype(np.int64)
    HOUR = df.index.hour.values

    close_s = pd.Series(C, index=df.index)
    e9   = _ema(close_s, ma_fast)
    e50  = _ema(close_s, trend_fast)
    e200 = _ema(close_s, trend_slow)

    h_s, l_s = pd.Series(H, index=df.index), pd.Series(L, index=df.index)
    tr = pd.concat([h_s - l_s,
                    (h_s - close_s.shift()).abs(),
                    (l_s - close_s.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=14, adjust=False).mean()
    vol_rank = (atr / close_s * 100).rolling(384).rank(pct=True)

    # Slope da EMA9 do 1h SEM lookahead: o bucket 1h só é conhecido depois
    # de fechar, então seu valor fica disponível em bucket_start + 1h.
    if use_trend_1h:
        c1h = close_s.resample("1h").last()
        e1h = c1h.ewm(span=9, adjust=False).mean()
        slope_raw = e1h.diff() > 0
        slope_raw.index = slope_raw.index + pd.Timedelta(hours=1)
        slope_up = slope_raw.reindex(df.index, method="ffill").fillna(False).values
    else:
        slope_up = np.ones(N, dtype=bool)

    # Condições avaliadas no candle ANTERIOR ao candle de fill
    def prev(a):
        out = np.roll(np.asarray(a, dtype=bool), 1)
        out[0] = False
        return out

    up_ok = (prev((e50.values > e200.values) & (C > e200.values))
             & prev(slope_up) & prev(C > e9.values))
    dn_ok = (prev((e50.values < e200.values) & (C < e200.values))
             & prev(~np.asarray(slope_up, dtype=bool)) & prev(C < e9.values))
    vol_ok = prev(vol_rank.values >= vol_rank_min) if vol_rank_min > 0 else np.ones(N, bool)

    setup = (up_ok | (dn_ok if allow_shorts else False)) & vol_ok
    sides = np.where(up_ok, 1, -1)

    hours_utc = _allowed_utc_hours(hour_start, hour_end, utc_offset) if use_hours else None

    exposure = min(risk_pct / sl_pct, lev_cap)   # notional / equity

    # ── Loop do backtest ──────────────────────────────────────────────────
    equity = initial_capital
    eq_curve = np.empty(N)
    trades = []
    e9v = e9.values
    i = 1
    pos_from = 0            # próximo bar a partir do qual estamos flat
    eq_curve[0] = equity

    while i < N:
        filled = False
        if setup[i] and (hours_utc is None or HOUR[i] in hours_utc):
            side = int(sides[i])
            limit = e9v[i - 1]
            filled = (L[i] < limit) if side == 1 else (H[i] > limit)
        if not filled:
            eq_curve[i] = equity
            i += 1
            continue

        entry = float(limit)
        tp = entry * (1 + tp_pct / 100 * side)
        sl = entry * (1 - sl_pct / 100 * side)
        qty = exposure * equity / entry if entry > 0 else 0.0

        exit_price = None
        exit_comment = ""
        j = i
        while j < N:
            hit_sl = (L[j] <= sl) if side == 1 else (H[j] >= sl)
            hit_tp = (H[j] > tp) if side == 1 else (L[j] < tp)
            if hit_sl:                      # SL primeiro: mesmo candle = LOSS
                exit_price, exit_comment = sl, "Stop Loss"
                break
            if hit_tp:
                exit_price, exit_comment = tp, "Alvo (maker)"
                break
            if j - i + 1 >= max_bars:
                exit_price, exit_comment = C[j], "Time Stop"
                break
            # mark-to-market do bar em posição
            eq_curve[j] = equity * (1 + side * (C[j] / entry - 1) * exposure)
            j += 1
        if exit_price is None:              # dataset acabou com posição aberta
            j = N - 1
            exit_price, exit_comment = C[j], "Fim dos Dados"

        pnl_pct = side * (exit_price / entry - 1) * 100 * exposure
        equity *= (1 + pnl_pct / 100)
        eq_curve[j] = equity

        trades.append({
            "entry_date": str(df.index[i])[:10],
            "exit_date": str(df.index[j])[:10],
            "direction": side,
            "comment": "Pullback EMA9 (limite)",
            "entry_price": _safe(entry),
            "exit_price": _safe(float(exit_price)),
            "exit_comment": exit_comment,
            "pnl_pct": _safe(float(pnl_pct)),
            "partial_exit_price": None,
            "partial_exit_date": None,
            "partial_pct_closed": None,
            "qty": _safe(float(qty)),
            "leverage": _safe(float(exposure)),
            "notional": _safe(float(qty * entry)),
            "entry_ts": int(TS[i]),
            "exit_ts": int(TS[j]),
        })
        i = j + 1

    # ── Métricas (mesmo contrato das demais estratégias) ─────────────────
    eq = eq_curve
    pnls = [t["pnl_pct"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_return = (equity / initial_capital - 1) * 100
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0.0
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    pf_den = abs(sum(losses))
    profit_factor = (sum(wins) / pf_den) if pf_den > 0 else None

    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / np.where(peak != 0, peak, 1.0) * 100
    max_dd = float(dd.min()) if len(dd) else 0.0

    total_days = max((df.index[-1] - df.index[0]).days, 1) if N > 1 else 1
    cagr = ((equity / initial_capital) ** (365.25 / total_days) - 1) * 100
    calmar = float(cagr / abs(max_dd)) if abs(max_dd) > 0 else 0.0
    bars_per_year = N / (total_days / 365.25) if total_days > 0 else 252

    sharpe = 0.0
    if N > 2:
        rets = np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)
        rets = rets[np.isfinite(rets)]
        std = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
        if std > 0:
            sharpe = float(rets.mean() / std * np.sqrt(bars_per_year))

    downside_sq = [min(p, 0) ** 2 for p in pnls]
    downside_dev = float(np.sqrt(np.mean(downside_sq))) if downside_sq else 0.0
    trades_per_year = len(pnls) / (total_days / 365.25) if total_days > 0 else len(pnls)
    sortino = (float(np.mean(pnls) / downside_dev * np.sqrt(trades_per_year))
               if downside_dev > 0 else 0.0)

    gains_sum = sum(p for p in pnls if p > 0)
    losses_sum = abs(sum(p for p in pnls if p < 0))
    omega = float(gains_sum / losses_sum) if losses_sum > 0 else None

    # Episódios de drawdown (p/ Sterling, Burke e painel de DD)
    dates = [str(idx)[:10] for idx in df.index]
    ep_troughs = []
    dd_episodes = []
    in_dd, ep_start = False, None
    for k, val in enumerate(dd):
        if val < 0 and not in_dd:
            in_dd, ep_start = True, k
        elif val >= 0 and in_dd:
            in_dd = False
            ep_troughs.append(float(dd[ep_start:k].min()))
            dd_episodes.append({
                "start": dates[ep_start], "end": dates[k - 1],
                "trough": _safe(ep_troughs[-1]), "length_bars": k - ep_start,
            })
    if in_dd and ep_start is not None:
        ep_troughs.append(float(dd[ep_start:].min()))
        dd_episodes.append({
            "start": dates[ep_start], "end": dates[-1],
            "trough": _safe(ep_troughs[-1]), "length_bars": len(dd) - ep_start,
        })

    if ep_troughs:
        n_worst = min(5, len(ep_troughs))
        worst = sorted(ep_troughs)[:n_worst]
        avg_worst = abs(float(np.mean(worst)))
        sterling = float(cagr / avg_worst) if avg_worst > 0 else 0.0
        burke_den = float(np.sqrt(np.sum(np.array(worst) ** 2)))
        burke = float(cagr / burke_den) if burke_den > 0 else 0.0
    else:
        sterling = burke = 0.0

    net_profit = equity - initial_capital
    recovery_factor = (_safe(float(net_profit / abs(max_dd * initial_capital / 100)))
                       if max_dd < 0 else None)
    ulcer_index = _safe(float(np.sqrt(np.mean(dd ** 2)))) if len(dd) else None
    avg_dd = _safe(float(np.mean([e["trough"] for e in dd_episodes]))) if dd_episodes else None
    avg_dd_len = _safe(float(np.mean([e["length_bars"] for e in dd_episodes]))) if dd_episodes else None

    equity_values = [_safe(float(v)) for v in eq.tolist()]

    chart = None
    if params.get("_charts"):
        chart = {
            "dates": [str(idx) for idx in df.index],
            "ohlc": {
                "open":   [_safe(float(v)) for v in O.tolist()],
                "high":   [_safe(float(v)) for v in H.tolist()],
                "low":    [_safe(float(v)) for v in L.tolist()],
                "close":  [_safe(float(v)) for v in C.tolist()],
                "volume": [_safe(float(v)) for v in df["Volume"].tolist()],
            },
            "indicators": {
                "ma":    [_safe(float(v)) for v in e9v.tolist()],
                "upper": [_safe(float(v)) for v in e50.values.tolist()],
                "lower": [_safe(float(v)) for v in e200.values.tolist()],
            },
        }

    return {
        "chart": chart,
        "metrics": {
            "final_equity": _safe(float(equity)),
            "total_return": _safe(float(total_return)),
            "max_dd": _safe(max_dd),
            "total_trades": len(trades),
            "win_rate": _safe(float(win_rate)),
            "profit_factor": _safe(profit_factor),
            "avg_win": _safe(avg_win),
            "avg_loss": _safe(avg_loss),
            "sharpe": _safe(sharpe),
            "sortino": _safe(sortino),
            "calmar": _safe(calmar),
            "omega": _safe(omega),
            "sterling": _safe(sterling),
            "burke": _safe(burke),
            "recovery_factor": recovery_factor,
            "ulcer_index": ulcer_index,
            "avg_dd": avg_dd,
            "avg_dd_length": avg_dd_len,
            "n_dd_episodes": len(dd_episodes),
            "initial_capital": float(initial_capital),
        },
        "drawdown": {
            "dates": dates,
            "values": [_safe(float(v)) for v in dd.tolist()],
            "episodes": dd_episodes if not _fast else [],
        },
        "equity_curve": {
            "dates": dates,
            "values": equity_values,
        },
        "trades": trades,
    }
