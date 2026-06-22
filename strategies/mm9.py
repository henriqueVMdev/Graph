"""
Estratégia MM9 — Cruzamento de Médias + Gatilho por Candle de Reversão
======================================================================
Viés de tendência por duas médias (rápida x lenta):
  - Rápida ACIMA da lenta  -> só compras (LONG)
  - Rápida ABAIXO da lenta -> só vendas (SHORT)

Gatilho (caso LONG; SHORT é o espelho):
  1. Pullback: preço negociando ABAIXO da média rápida (abertura <= rápida), com a
     MÁXIMA do candle alcançando a rápida ou mais (High >= rápida). O fechamento é
     livre — pode fechar abaixo ou já romper acima da média.
  2. Candle de reversão = engolfo clássico OU PFR de fundo (toggles independentes).
  3. Entrada por ROMPIMENTO da máxima do candle de gatilho na barra seguinte.
     Opcional: se a próxima barra não romper e for um INSIDE BAR, o nível de
     rompimento passa a ser a máxima do inside bar (encadeia enquanto formar).
  4. STOP estrutural = (menor mínima das últimas N barras até o gatilho) - tick.
  5. ALVO = entrada + target_r * risco.  Risco = entrada - stop.
  6. Parcial (opcional) = entrada + parcial_r * risco, realizando parcial_pct%.

Motor próprio (barra a barra). Reaproveita `calc_ma` e o dataclass `Trade` de
backtesting.py e espelha o contrato de retorno de strategies/depaula.py (metrics,
equity_curve, trades, drawdown, chart), incluindo os modos _fast e _charts.
"""

import sys
import os
import math
import numpy as np
import pandas as pd

# Garante que o diretório raiz do projeto está no sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backtesting import calc_ma, Trade

NAME = "MM9 — Cruzamento + Reversão"
DESCRIPTION = (
    "Cruzamento de médias para viés; entrada por rompimento de candle de reversão "
    "(engolfo/PFR) na média rápida. Stop estrutural por mínimas e alvo/parcial em R."
)

CONFIG_SCHEMA = [
    {
        "title": "Médias",
        "fields": [
            {
                "key": "ma_fast_type",
                "label": "Tipo Rápida",
                "type": "select",
                "default": "EMA",
                "options": ["SMA", "EMA", "HMA", "RMA", "WMA"],
            },
            {
                "key": "ma_fast_len",
                "label": "Período Rápida",
                "type": "number",
                "default": 9,
                "min": 2,
                "max": 200,
                "step": 1,
            },
            {
                "key": "ma_slow_type",
                "label": "Tipo Lenta",
                "type": "select",
                "default": "EMA",
                "options": ["SMA", "EMA", "HMA", "RMA", "WMA"],
            },
            {
                "key": "ma_slow_len",
                "label": "Período Lenta",
                "type": "number",
                "default": 21,
                "min": 3,
                "max": 500,
                "step": 1,
            },
        ],
    },
    {
        "title": "Gatilho",
        "fields": [
            {
                "key": "use_engulfing",
                "label": "Usar Engolfo",
                "type": "checkbox",
                "default": True,
            },
            {
                "key": "use_pfr",
                "label": "Usar PFR",
                "type": "checkbox",
                "default": True,
            },
            {
                "key": "use_inside_bar",
                "label": "Usar Inside Bar",
                "type": "checkbox",
                "default": False,
            },
        ],
    },
    {
        "title": "Stop",
        "fields": [
            {
                "key": "stop_lookback",
                "label": "Mínimas p/ Stop (N)",
                "type": "number",
                "default": 2,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "key": "tick_size",
                "label": "Tick (folga do stop)",
                "type": "number",
                "default": 0.01,
                "min": 0.0,
                "step": 0.01,
            },
        ],
    },
    {
        "title": "Alvo",
        "fields": [
            {
                "key": "target_r",
                "label": "Alvo (x risco)",
                "type": "number",
                "default": 2.0,
                "min": 0.1,
                "step": 0.1,
            },
        ],
    },
    {
        "title": "Saida Parcial",
        "fields": [
            {
                "key": "use_parcial",
                "label": "Usar Parcial",
                "type": "checkbox",
                "default": False,
            },
            {
                "key": "parcial_r",
                "label": "Parcial (x risco)",
                "type": "number",
                "default": 1.0,
                "min": 0.1,
                "step": 0.1,
                "show_if": "use_parcial",
            },
            {
                "key": "parcial_pct",
                "label": "Realizar (%)",
                "type": "number",
                "default": 50.0,
                "min": 1,
                "max": 99,
                "step": 5,
                "show_if": "use_parcial",
            },
        ],
    },
    {
        "title": "Alavancagem / Sizing",
        "fields": [
            {
                "key": "sizing_mode",
                "label": "Modo de Sizing",
                "type": "select",
                "default": "Alavancagem fixa",
                "options": ["Alavancagem fixa", "Quantidade fixa", "Risco por trade"],
            },
            {
                "key": "leverage",
                "label": "Alavancagem (x)",
                "type": "number",
                "default": 1.0,
                "min": 1.0,
                "max": 125.0,
                "step": 1.0,
            },
            {
                "key": "margin_pct",
                "label": "Margem por Trade (% do capital)",
                "type": "number",
                "default": 100.0,
                "min": 1.0,
                "max": 100.0,
                "step": 5.0,
            },
            {
                "key": "fixed_qty",
                "label": "Quantidade Fixa (unidades)",
                "type": "number",
                "default": 0.1,
                "min": 0.0,
                "step": 0.01,
            },
            {
                "key": "risk_per_trade",
                "label": "Risco por Trade (%)",
                "type": "number",
                "default": 1.0,
                "min": 0.1,
                "max": 100,
                "step": 0.1,
            },
        ],
    },
]


# Grids de otimizacao (parametros e valores a testar)
OPTIMIZER_GRIDS = {
    "rapido": {
        "ma_fast_type":   ["EMA"],
        "ma_fast_len":    [7, 9, 12],
        "ma_slow_type":   ["EMA"],
        "ma_slow_len":    [21, 34, 50],
        "use_engulfing":  [True, False],
        "use_pfr":        [True, False],
        "use_inside_bar": [False, True],
        "stop_lookback":  [1, 2, 3],
        "target_r":       [1.5, 2.0, 3.0],
        "use_parcial":    [False],
    },
    "completo": {
        "ma_fast_type":   ["SMA", "EMA"],
        "ma_fast_len":    [5, 7, 9, 12, 20],
        "ma_slow_type":   ["EMA", "SMA"],
        "ma_slow_len":    [21, 34, 50, 100, 200],
        "use_engulfing":  [True, False],
        "use_pfr":        [True, False],
        "use_inside_bar": [False, True],
        "stop_lookback":  [1, 2, 3, 5],
        "target_r":       [1.0, 1.5, 2.0, 3.0, 4.0],
        "use_parcial":    [False, True],
        "parcial_r":      [0.5, 1.0, 1.5],
        "parcial_pct":    [25, 50, 75],
    },
}


def is_valid_config(params):
    """Remove combinacoes que nao fazem sentido para esta estrategia."""
    # Rápida precisa ser mais curta que a lenta
    if int(params.get("ma_fast_len", 9)) >= int(params.get("ma_slow_len", 21)):
        return False
    # Pelo menos um gatilho ligado
    if not params.get("use_engulfing", True) and not params.get("use_pfr", True):
        return False
    # Parcial desligada -> params parciais no default
    if not params.get("use_parcial", False):
        if float(params.get("parcial_r", 1.0)) != 1.0:
            return False
        if float(params.get("parcial_pct", 50.0)) != 50.0:
            return False
    return True


def prepare_optimizer_params(params):
    """Sem simetrias derivadas nesta estrategia."""
    return params


def _safe(val):
    """Converte NaN/Inf para None (JSON-safe)."""
    if val is None:
        return None
    try:
        if math.isnan(val) or math.isinf(val):
            return None
    except (TypeError, ValueError):
        pass
    return val


# ==============================
# Detecção de padrões (LONG = direction 1; SHORT = -1)
# ==============================

def _is_engulfing(d, o, c, o1, c1):
    """Engolfo clássico: corpo do candle atual engolfa o corpo anterior + direção."""
    if d == 1:
        return c > o and o <= c1 and c >= o1   # candle de alta engolfando
    return c < o and o >= c1 and c <= o1       # candle de baixa engolfando


def _is_pfr(d, h, l, h1, l1, c, c1):
    """PFR (Ponto de Falso Rompimento): rompe a extremidade anterior e fecha de volta.
    Fundo (long) = mínima menor que a anterior + fecha acima do fechamento anterior.
    Topo (short) = máxima maior que a anterior + fecha abaixo do fechamento anterior."""
    if d == 1:
        return l < l1 and c > c1
    return h > h1 and c < c1


def _is_inside_bar(h, l, h1, l1):
    """Inside bar clássico: contido na barra anterior."""
    return h < h1 and l > l1


# ==============================
# Sizing (espelha _open_position de backtesting.py com stop estrutural)
# ==============================

def _compute_sizing(equity, entry, stop, params):
    """Retorna (qty, leverage, exposure) conforme o modo de sizing."""
    equity = equity if equity > 0 else 1.0
    lev = max(float(params.get("leverage", 1.0)), 1.0)
    mode = params.get("sizing_mode", "Alavancagem fixa")

    if mode == "Quantidade fixa":
        qty = max(float(params.get("fixed_qty", 0.0)), 0.0)
        exposure = (qty * entry) / equity
        return qty, lev, exposure

    if mode == "Risco por trade":
        stop_dist_pct = abs(entry - stop) / entry * 100 if entry > 0 else 0.0
        if stop_dist_pct > 0:
            exposure = float(params.get("risk_per_trade", 1.0)) / stop_dist_pct
        else:
            exposure = 1.0
        if exposure > lev:
            exposure = lev
        qty = (exposure * equity) / entry if entry > 0 else 0.0
        return qty, lev, exposure

    # "Alavancagem fixa"
    margin_frac = max(min(float(params.get("margin_pct", 100.0)) / 100.0, 1.0), 0.0)
    exposure = margin_frac * lev
    qty = (exposure * equity) / entry if entry > 0 else 0.0
    return qty, lev, exposure


# ==============================
# Motor barra a barra
# ==============================

def _run_backtest_mm9(df: pd.DataFrame, params: dict):
    """Executa o backtest MM9. Retorna (bt_df, trades, final_equity)."""
    df = df.copy()

    ma_fast_len = int(params.get("ma_fast_len", 9))
    ma_slow_len = int(params.get("ma_slow_len", 21))
    df["Fast"] = calc_ma(df["Close"], ma_fast_len, params.get("ma_fast_type", "EMA"))
    df["Slow"] = calc_ma(df["Close"], ma_slow_len, params.get("ma_slow_type", "EMA"))

    # Filtro de data opcional
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]

    use_engulfing = bool(params.get("use_engulfing", True))
    use_pfr = bool(params.get("use_pfr", True))
    use_inside_bar = bool(params.get("use_inside_bar", False))
    stop_lookback = max(int(params.get("stop_lookback", 2)), 1)
    tick = float(params.get("tick_size", 0.01))
    target_r = float(params.get("target_r", 2.0))
    use_parcial = bool(params.get("use_parcial", False))
    parcial_r = float(params.get("parcial_r", 1.0))
    parcial_frac = float(params.get("parcial_pct", 50.0)) / 100.0
    initial_capital = float(params.get("initial_capital", 1000.0))

    o = df["Open"].values
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values
    fast = df["Fast"].values
    slow = df["Slow"].values
    idx = df.index
    n = len(df)

    # Estado
    st = {
        "position": 0,          # 0 flat, 1 long, -1 short
        "entry": 0.0,
        "stop": 0.0,
        "target": 0.0,
        "partial": 0.0,
        "partial_taken": False,
        "position_size": 1.0,   # reduz após parcial
        "exposure": 1.0,        # notional / equity
        "leverage": 1.0,
        "qty": 0.0,
        "entry_bar": -1,
        "trade": None,
        "equity": initial_capital,
        # setup armado (pré-entrada)
        "armed": False,
        "armed_dir": 0,
        "armed_level": 0.0,
        "armed_stop": 0.0,
    }
    trades = []
    equity_curve = []

    def _ts(i):
        try:
            return int(idx[i].value // 1_000_000)
        except AttributeError:
            return 0

    def open_position(i, direction, entry_price, stop_price):
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return False
        if direction == 1:
            target_price = entry_price + target_r * risk
            partial_price = entry_price + parcial_r * risk
        else:
            target_price = entry_price - target_r * risk
            partial_price = entry_price - parcial_r * risk

        qty, lev, exposure = _compute_sizing(st["equity"], entry_price, stop_price, params)

        st["position"] = direction
        st["entry"] = entry_price
        st["stop"] = stop_price
        st["target"] = target_price
        st["partial"] = partial_price
        st["partial_taken"] = False
        st["position_size"] = 1.0
        st["exposure"] = exposure
        st["leverage"] = lev
        st["qty"] = qty
        st["entry_bar"] = i
        st["trade"] = Trade(
            entry_date=str(idx[i]),
            entry_price=entry_price,
            direction=direction,
            comment="L" if direction == 1 else "S",
            stop_price=stop_price,
            target_price=target_price,
            qty=qty,
            leverage=lev,
            notional=qty * entry_price,
            exposure=exposure,
            entry_ts=_ts(i),
        )
        return True

    def take_partial(i, price):
        frac = parcial_frac
        d = st["position"]
        partial_pnl = d * (price - st["entry"]) / st["entry"] * 100
        st["equity"] *= (1 + partial_pnl / 100 * frac * st["exposure"])
        st["position_size"] -= frac
        st["partial_taken"] = True
        tr = st["trade"]
        tr.partial_exit_price = price
        tr.partial_exit_date = str(idx[i])
        tr.partial_pct_closed = frac

    def close_position(i, price, comment):
        tr = st["trade"]
        if tr is None:
            st["position"] = 0
            return
        d = tr.direction
        tr.exit_date = str(idx[i])
        tr.exit_price = price
        tr.exit_comment = comment
        tr.exit_ts = _ts(i)

        frac = st["exposure"]
        remaining_pnl = d * (price - st["entry"]) / st["entry"] * 100
        st["equity"] *= (1 + remaining_pnl / 100 * st["position_size"] * frac)

        if st["partial_taken"] and tr.partial_pct_closed > 0:
            partial_pnl = d * (tr.partial_exit_price - st["entry"]) / st["entry"] * 100
            tr.pnl_pct = (tr.partial_pct_closed * partial_pnl
                          + st["position_size"] * remaining_pnl) * frac
        else:
            tr.pnl_pct = remaining_pnl * frac

        trades.append(tr)
        # reset
        st["position"] = 0
        st["entry"] = 0.0
        st["trade"] = None
        st["partial_taken"] = False
        st["position_size"] = 1.0
        st["exposure"] = 1.0
        st["leverage"] = 1.0
        st["qty"] = 0.0
        st["entry_bar"] = -1

    for i in range(n):
        # Sem médias ainda: marca equity e segue
        if np.isnan(fast[i]) or np.isnan(slow[i]):
            equity_curve.append(st["equity"])
            continue

        # ── 1. ENTRADA a partir de setup armado (flat) ──────────────────────
        if st["position"] == 0 and st["armed"]:
            d = st["armed_dir"]
            bias = 1 if fast[i] > slow[i] else (-1 if fast[i] < slow[i] else 0)
            if (d == 1 and bias < 0) or (d == -1 and bias > 0):
                st["armed"] = False  # viés inverteu -> cancela
            elif d == 1 and h[i] > st["armed_level"]:
                entry_price = max(o[i], st["armed_level"])
                open_position(i, 1, entry_price, st["armed_stop"])
                st["armed"] = False
            elif d == -1 and l[i] < st["armed_level"]:
                entry_price = min(o[i], st["armed_level"])
                open_position(i, -1, entry_price, st["armed_stop"])
                st["armed"] = False
            elif use_inside_bar and i >= 1 and _is_inside_bar(h[i], l[i], h[i - 1], l[i - 1]):
                # não rompeu, mas é inside bar -> move o gatilho E o stop p/ o inside bar
                lo = max(0, i - stop_lookback + 1)
                if d == 1:
                    st["armed_level"] = h[i]
                    st["armed_stop"] = float(np.min(l[lo:i + 1])) - tick
                else:
                    st["armed_level"] = l[i]
                    st["armed_stop"] = float(np.max(h[lo:i + 1])) + tick
            else:
                st["armed"] = False  # expira

        # ── 2. GESTÃO DA POSIÇÃO ABERTA (exits a partir da barra seguinte) ──
        if st["position"] != 0 and i > st["entry_bar"]:
            d = st["position"]
            stop_price = st["stop"]

            # Liquidação (perda adversa >= 1/alavancagem). Conservador p/ o trader.
            liq_price = None
            if st["leverage"] and st["leverage"] > 1.0:
                liq_price = (st["entry"] * (1 - 1.0 / st["leverage"]) if d == 1
                             else st["entry"] * (1 + 1.0 / st["leverage"]))
            sl_is_liq = False
            if liq_price is not None:
                if (d == 1 and liq_price > stop_price) or (d == -1 and liq_price < stop_price):
                    stop_price = liq_price
                    sl_is_liq = True

            hit_sl = (l[i] <= stop_price) if d == 1 else (h[i] >= stop_price)

            if hit_sl:
                close_position(i, stop_price, "Liquidação" if sl_is_liq else "Stop Loss")
            else:
                # Parcial (uma vez)
                if use_parcial and not st["partial_taken"]:
                    hit_p = (h[i] >= st["partial"]) if d == 1 else (l[i] <= st["partial"])
                    if hit_p:
                        take_partial(i, st["partial"])
                # Alvo
                if st["position"] != 0:
                    hit_tp = (h[i] >= st["target"]) if d == 1 else (l[i] <= st["target"])
                    if hit_tp:
                        close_position(i, st["target"], "Alvo Atingido")

        # ── 3. NOVO SETUP (flat, sem armado, precisa de barra anterior) ─────
        if st["position"] == 0 and not st["armed"] and i >= 1:
            bias = 1 if fast[i] > slow[i] else (-1 if fast[i] < slow[i] else 0)
            if bias == 1:
                # Long: preço negociando ABAIXO da rápida (abertura <= rápida) e a
                # MÁXIMA alcançando a média ou mais (high >= rápida). O fechamento não
                # importa. A entrada sai no rompimento dessa máxima (na média ou acima).
                touches_ma = o[i] <= fast[i] and h[i] >= fast[i]
                pattern = ((use_engulfing and _is_engulfing(1, o[i], c[i], o[i - 1], c[i - 1]))
                           or (use_pfr and _is_pfr(1, h[i], l[i], h[i - 1], l[i - 1], c[i], c[i - 1])))
                if touches_ma and pattern:
                    lo = max(0, i - stop_lookback + 1)
                    st["armed"] = True
                    st["armed_dir"] = 1
                    st["armed_level"] = h[i]
                    st["armed_stop"] = float(np.min(l[lo:i + 1])) - tick
            elif bias == -1:
                # Short (espelho): preço negociando ACIMA da rápida (abertura >= rápida)
                # e a MÍNIMA alcançando a média ou menos (low <= rápida). O fechamento
                # não importa. A entrada sai no rompimento dessa mínima (na média ou abaixo).
                touches_ma = o[i] >= fast[i] and l[i] <= fast[i]
                pattern = ((use_engulfing and _is_engulfing(-1, o[i], c[i], o[i - 1], c[i - 1]))
                           or (use_pfr and _is_pfr(-1, h[i], l[i], h[i - 1], l[i - 1], c[i], c[i - 1])))
                if touches_ma and pattern:
                    lo = max(0, i - stop_lookback + 1)
                    st["armed"] = True
                    st["armed_dir"] = -1
                    st["armed_level"] = l[i]
                    st["armed_stop"] = float(np.max(h[lo:i + 1])) + tick

        # ── 4. Equity mark-to-market ────────────────────────────────────────
        if st["position"] != 0 and st["trade"] is not None:
            unrealized = st["position"] * (c[i] - st["entry"]) / st["entry"]
            equity_curve.append(st["equity"] * (1 + unrealized * st["position_size"] * st["exposure"]))
        else:
            equity_curve.append(st["equity"])

    # Fecha posição aberta no fim do período
    if st["position"] != 0 and n > 0:
        close_position(n - 1, c[-1], "Fim do Período")
        # corrige a última marcação de equity para o valor realizado
        if equity_curve:
            equity_curve[-1] = st["equity"]

    df["Equity"] = equity_curve[:n]
    return df, trades, st["equity"]


def run(df, params: dict) -> dict:
    """Executa o backtest MM9 e retorna metrics/equity_curve/trades/drawdown/chart."""
    initial_capital = float(params.get("initial_capital", 1000.0))
    bt_df, trades, final_equity = _run_backtest_mm9(df, params)

    # ── Métricas (mesmo bloco/contrato de strategies/depaula.py) ───────────
    total_return = (final_equity / initial_capital - 1) * 100
    wins = [t for t in trades if t.pnl_pct > 0]
    losses_t = [t for t in trades if t.pnl_pct <= 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win = float(np.mean([t.pnl_pct for t in wins])) if wins else 0
    avg_loss = float(np.mean([t.pnl_pct for t in losses_t])) if losses_t else 0
    pf_num = sum(t.pnl_pct for t in wins)
    pf_den = abs(sum(t.pnl_pct for t in losses_t))
    profit_factor = pf_num / pf_den if pf_den > 0 else None

    eq = bt_df["Equity"].values
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak * 100
    max_dd = float(dd.min())

    total_days = max((bt_df.index[-1] - bt_df.index[0]).days, 1) if len(bt_df) > 1 else 1
    cagr = ((final_equity / initial_capital) ** (365.25 / total_days) - 1) * 100
    calmar = float(cagr / abs(max_dd)) if abs(max_dd) > 0 else 0

    bars_per_year = len(bt_df) / (total_days / 365.25) if total_days > 0 else 252

    sharpe = 0.0
    pnls = [t.pnl_pct for t in trades]
    if len(eq) > 2:
        eq_rets = np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)
        eq_rets = eq_rets[np.isfinite(eq_rets)]
        eq_std = float(eq_rets.std(ddof=1)) if len(eq_rets) > 1 else 0.0
        if len(eq_rets) > 1 and eq_std > 0:
            sharpe = float(eq_rets.mean() / eq_std * np.sqrt(bars_per_year))

    downside_sq = [min(p, 0) ** 2 for p in pnls]
    downside_dev = float(np.sqrt(np.mean(downside_sq))) if downside_sq else 0
    trades_per_year = len(pnls) / (total_days / 365.25) if total_days > 0 else len(pnls)
    sortino = float(np.mean(pnls) / downside_dev * np.sqrt(trades_per_year)) if downside_dev > 0 else 0

    gains_sum = sum(p for p in pnls if p > 0)
    losses_sum = abs(sum(p for p in pnls if p < 0))
    omega = float(gains_sum / losses_sum) if losses_sum > 0 else None

    ep_troughs = []
    _in_dd = False
    _ep_start = None
    for _k, _val in enumerate(dd):
        if _val < 0 and not _in_dd:
            _in_dd = True
            _ep_start = _k
        elif _val >= 0 and _in_dd:
            _in_dd = False
            ep_troughs.append(float(dd[_ep_start:_k].min()))
    if _in_dd and _ep_start is not None:
        ep_troughs.append(float(dd[_ep_start:].min()))

    if ep_troughs:
        n_worst = min(5, len(ep_troughs))
        worst_troughs = sorted(ep_troughs)[:n_worst]
        avg_worst_dd = abs(float(np.mean(worst_troughs)))
        sterling = float(cagr / avg_worst_dd) if avg_worst_dd > 0 else 0
        burke_denom = float(np.sqrt(np.sum(np.array(worst_troughs) ** 2)))
        burke = float(cagr / burke_denom) if burke_denom > 0 else 0
    else:
        sterling = 0
        burke = 0

    _fast = bool(params.get("_fast", False))
    dates = [str(idx)[:10] for idx in bt_df.index]

    if _fast:
        recovery_factor = None
        ulcer_index = None
        avg_dd = None
        avg_dd_len = None
        n_dd_episodes = 0
        dd_dates = []
        dd_values = []
        dd_episodes = []
        equity_values = [_safe(float(v)) for v in bt_df["Equity"].tolist()]
        trades_list = [
            {
                "pnl_pct": _safe(float(t.pnl_pct)),
                "qty": _safe(float(t.qty)),
                "leverage": _safe(float(t.leverage)),
                "notional": _safe(float(t.notional)),
                "direction": t.direction,
                "entry_price": _safe(float(t.entry_price)),
                "exit_price": _safe(float(t.exit_price)),
                "entry_ts": t.entry_ts,
                "exit_ts": t.exit_ts,
            }
            for t in trades
        ]
    else:
        net_profit = final_equity - initial_capital
        recovery_factor = _safe(float(net_profit / abs(max_dd * initial_capital / 100))) if max_dd < 0 else None
        ulcer_index = _safe(float(np.sqrt(np.mean(dd ** 2)))) if len(dd) > 0 else None

        dd_episodes = []
        in_dd = False
        ep_start = None
        ep_peak_idx = None
        for k, val in enumerate(dd):
            if val < 0 and not in_dd:
                in_dd = True
                ep_start = k
                ep_peak_idx = k
            elif val < 0 and in_dd:
                if val < dd[ep_peak_idx]:
                    ep_peak_idx = k
            elif val >= 0 and in_dd:
                in_dd = False
                ep_trough = float(dd[ep_start:k].min())
                ep_len = k - ep_start
                dd_episodes.append({
                    "start": dates[ep_start] if ep_start < len(bt_df) else None,
                    "end": dates[k - 1] if (k - 1) < len(bt_df) else None,
                    "trough": _safe(ep_trough),
                    "length_bars": ep_len,
                })
        if in_dd and ep_start is not None:
            ep_trough = float(dd[ep_start:].min())
            dd_episodes.append({
                "start": dates[ep_start],
                "end": dates[-1],
                "trough": _safe(ep_trough),
                "length_bars": len(dd) - ep_start,
            })

        avg_dd = _safe(float(np.mean([e["trough"] for e in dd_episodes]))) if dd_episodes else None
        avg_dd_len = _safe(float(np.mean([e["length_bars"] for e in dd_episodes]))) if dd_episodes else None
        n_dd_episodes = len(dd_episodes)
        dd_dates = dates
        dd_values = [_safe(float(v)) for v in dd.tolist()]
        equity_values = [_safe(float(v)) for v in bt_df["Equity"].tolist()]

        trades_list = [
            {
                "entry_date": t.entry_date[:10] if t.entry_date else "",
                "exit_date": t.exit_date[:10] if t.exit_date else "",
                "direction": t.direction,
                "comment": t.comment,
                "entry_price": _safe(float(t.entry_price)),
                "exit_price": _safe(float(t.exit_price)),
                "exit_comment": t.exit_comment,
                "stop_price": _safe(float(t.stop_price)) if t.stop_price else None,
                "target_price": _safe(float(t.target_price)) if t.target_price else None,
                "pnl_pct": _safe(float(t.pnl_pct)),
                "partial_exit_price": _safe(float(t.partial_exit_price)) if t.partial_exit_price else None,
                "partial_exit_date": t.partial_exit_date[:10] if t.partial_exit_date else None,
                "partial_pct_closed": t.partial_pct_closed if t.partial_pct_closed else None,
                "qty": _safe(float(t.qty)),
                "leverage": _safe(float(t.leverage)),
                "notional": _safe(float(t.notional)),
                "entry_ts": t.entry_ts,
                "exit_ts": t.exit_ts,
            }
            for t in trades
        ]

    # ── Séries para os gráficos (candles + médias) ─────────────────────────
    chart = None
    if params.get("_charts"):
        def _col(name):
            return [_safe(float(v)) for v in bt_df[name].tolist()] if name in bt_df.columns else None
        chart = {
            "dates": [str(idx) for idx in bt_df.index],
            "ohlc": {
                "open": _col("Open"),
                "high": _col("High"),
                "low": _col("Low"),
                "close": _col("Close"),
                "volume": _col("Volume"),
            },
            "indicators": {
                "ma": _col("Fast"),
                "ma_slow": _col("Slow"),
            },
        }

    return {
        "chart": chart,
        "metrics": {
            "final_equity": _safe(float(final_equity)),
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
            "n_dd_episodes": n_dd_episodes,
            "initial_capital": float(initial_capital),
        },
        "drawdown": {
            "dates": dd_dates,
            "values": dd_values,
            "episodes": dd_episodes if not _fast else [],
        },
        "equity_curve": {
            "dates": dates,
            "values": equity_values,
        },
        "trades": trades_list,
    }
