"""
Estratégia DePaula — Ângulo de Média Móvel
==========================================
Baseada no ângulo (derivada normalizada) de uma média móvel para detectar tendência.
Suporta entradas por pullback, zonas de entrada, stop loss configurável e múltiplos
modos de saída.

Usa o motor em backtesting.py (run_backtest + Config).
"""

import sys
import os
import math
import numpy as np

# Garante que o diretório raiz do projeto está no sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backtesting import run_backtest, Config

NAME = "DePaula — Ângulo de MA"
DESCRIPTION = "Detecta tendências pelo ângulo da média móvel. Suporta pullback, stop e múltiplos modos de saída."

CONFIG_SCHEMA = [
    {
        "title": "Média Móvel",
        "fields": [
            {
                "key": "ma_type",
                "label": "Tipo",
                "type": "select",
                "default": "HMA",
                "options": ["SMA", "EMA", "HMA", "RMA", "WMA"],
            },
            {
                "key": "ma_length",
                "label": "Período",
                "type": "number",
                "default": 50,
                "min": 2,
                "max": 500,
                "step": 1,
            },
            {
                "key": "lookback",
                "label": "Lookback",
                "type": "number",
                "default": 5,
                "min": 2,
                "max": 100,
                "step": 1,
            },
            {
                "key": "th_up",
                "label": "Ângulo Alta",
                "type": "number",
                "default": 0.5,
                "step": 0.1,
            },
            {
                "key": "th_dn",
                "label": "Ângulo Baixa",
                "type": "number",
                "default": -0.5,
                "step": 0.1,
                "optimizer_hidden": True,
            },
            {
                "key": "hysteresis",
                "label": "Histerese",
                "type": "number",
                "default": 0.2,
                "step": 0.1,
            },
        ],
    },
    {
        "title": "Saída",
        "fields": [
            {
                "key": "exit_mode",
                "label": "Modo de Saída",
                "type": "select",
                "default": "Banda + Tendência",
                "options": [
                    "Banda + Tendência",
                    "Somente Tendência",
                    "Alvo Fixo + Tendência",
                ],
            },
            {
                "key": "pct_up",
                "label": "Banda Sup (%)",
                "type": "number",
                "default": 3.0,
                "step": 0.5,
            },
            {
                "key": "pct_dn",
                "label": "Banda Inf (%)",
                "type": "number",
                "default": 3.0,
                "step": 0.5,
                "optimizer_hidden": True,
            },
            {
                "key": "alvo_fixo",
                "label": "Alvo Fixo (%)",
                "type": "number",
                "default": 5.0,
                "step": 0.5,
            },
            {
                "key": "exit_on_flat",
                "label": "Sair no Flat (cinza)",
                "type": "checkbox",
                "default": True,
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
                "key": "parcial_pct",
                "label": "Realizar (%)",
                "type": "number",
                "default": 50.0,
                "min": 1,
                "max": 99,
                "step": 5,
                "show_if": "use_parcial",
            },
            {
                "key": "parcial_mode",
                "label": "Alvo Parcial",
                "type": "select",
                "default": "Banda",
                "options": ["Banda", "Alvo Fixo"],
                "show_if": "use_parcial",
            },
            {
                "key": "parcial_banda_pct",
                "label": "Banda Parcial (%)",
                "type": "number",
                "default": 1.5,
                "step": 0.5,
                "show_if": "use_parcial",
            },
            {
                "key": "parcial_alvo_fixo",
                "label": "Alvo Fixo Parcial (%)",
                "type": "number",
                "default": 2.0,
                "step": 0.5,
                "show_if": "use_parcial",
            },
        ],
    },
    {
        "title": "Stop Loss",
        "fields": [
            {
                "key": "use_stop",
                "label": "Usar Stop",
                "type": "checkbox",
                "default": False,
            },
            {
                "key": "stop_type",
                "label": "Tipo de Stop",
                "type": "select",
                "default": "ATR",
                "options": ["ATR", "Fixo (%)", "Banda Stop"],
                "show_if": "use_stop",
            },
            {
                "key": "stop_atr_mult",
                "label": "ATR Mult",
                "type": "number",
                "default": 2.0,
                "step": 0.1,
                "show_if": "use_stop",
            },
            {
                "key": "stop_fixo_pct",
                "label": "Fixo (%)",
                "type": "number",
                "default": 2.0,
                "step": 0.5,
                "show_if": "use_stop",
            },
            {
                "key": "stop_band_pct",
                "label": "Banda (%)",
                "type": "number",
                "default": 1.5,
                "step": 0.5,
                "show_if": "use_stop",
            },
        ],
    },
    {
        "title": "Entrada",
        "fields": [
            {
                "key": "use_pullback",
                "label": "Pullback",
                "type": "checkbox",
                "default": True,
            },
            {
                "key": "use_entry_zone",
                "label": "Entry Zone",
                "type": "checkbox",
                "default": False,
            },
        ],
    },
    {
        "title": "Capital",
        "fields": [
            {
                "key": "initial_capital",
                "label": "Capital Inicial",
                "type": "number",
                "default": 1000.0,
                "min": 100,
                "step": 100,
            },
        ],
    },
]


# Grids de otimizacao (parametros e valores a testar)
OPTIMIZER_GRIDS = {
    "rapido": {
        "ma_type":       ["HMA", "EMA"],
        "ma_length":     [21, 50, 100],
        "lookback":      [3, 5, 8],
        "th_up":         [0.3, 0.5, 1.0],
        "exit_mode":     ["Banda + Tendência", "Somente Tendência"],
        "pct_up":        [2.0, 3.0, 5.0],
        "exit_on_flat":  [True, False],
        "use_stop":      [False, True],
        "stop_type":     ["ATR"],
        "stop_atr_mult": [1.5, 2.0, 3.0],
        "use_pullback":  [True, False],
        "use_norm":      [True, False],
        "atr_length":    [14],
        "hysteresis":    [0.1, 0.2, 0.5],
        "use_parcial":   [False],
        "cycle_filter":  [False],
    },
    "completo": {
        "ma_type":       ["SMA", "EMA", "HMA", "WMA"],
        "ma_length":     [14, 21, 34, 50, 100, 200],
        "lookback":      [3, 5, 8, 13],
        "th_up":         [0.2, 0.3, 0.5, 0.8, 1.0, 1.5],
        "exit_mode":     ["Banda + Tendência", "Somente Tendência", "Alvo Fixo + Tendência"],
        "pct_up":        [1.5, 2.0, 3.0, 5.0, 8.0],
        "alvo_fixo":     [3.0, 5.0, 8.0, 10.0],
        "exit_on_flat":  [True, False],
        "use_stop":      [False, True],
        "stop_type":     ["ATR", "Fixo (%)", "Banda Stop"],
        "stop_atr_mult": [1.0, 1.5, 2.0, 3.0],
        "stop_fixo_pct": [1.0, 2.0, 3.0],
        "stop_band_pct": [1.0, 1.5, 2.0],
        "use_pullback":  [True, False],
        "use_entry_zone": [False, True],
        "use_norm":      [True, False],
        "atr_length":    [10, 14, 21],
        "hysteresis":    [0.0, 0.1, 0.2, 0.5],
        "use_parcial":       [False, True],
        "parcial_pct":       [25, 50, 75],
        "parcial_mode":      ["Banda", "Alvo Fixo"],
        "parcial_banda_pct": [1.0, 1.5, 2.0, 3.0],
        "parcial_alvo_fixo": [1.0, 2.0, 3.0, 5.0],
        "cycle_filter":      [False, True],
    },
    "custom": {
        "ma_type":       ["EMA", "SMA", "HMA"],
        "ma_length":     list(range(40, 150, 5)),
        "lookback":      [0, 5],
        "th_up":         [0.1, 0.5, 1.5, 2.0, 2.5],
        "exit_mode":     ["Banda + Tendência", "Somente Tendência"],
        "pct_up":        list(range(5, 40, 2)),
        "exit_on_flat":  [False, True],
        "use_stop":      [True],
        "stop_type":     ["Banda Stop"],
        "stop_band_pct": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "use_pullback":  [True, False],
        "use_entry_zone": [True],
        "use_norm":      [False],
        "atr_length":    [14],
        "hysteresis":    [0.2],
        "use_parcial":       [False, True],
        "parcial_pct":       [50],
        "parcial_mode":      ["Banda"],
        "parcial_banda_pct": [1.0, 1.5, 2.0],
        "parcial_alvo_fixo": [2.0],
        "cycle_filter":      [False, True],
    },
}


def is_valid_config(params):
    """Remove combinacoes que nao fazem sentido para esta estrategia."""
    if not params.get("use_stop", False):
        if params.get("stop_type", "ATR") != "ATR":
            return False
        if params.get("stop_atr_mult", 2.0) != 2.0:
            return False
        if params.get("stop_fixo_pct", 2.0) != 2.0:
            return False
        if params.get("stop_band_pct", 1.5) != 1.5:
            return False

    stop_type = params.get("stop_type", "ATR")
    if params.get("use_stop", False):
        if stop_type != "ATR" and params.get("stop_atr_mult", 2.0) != 2.0:
            return False
        if stop_type != "Fixo (%)" and params.get("stop_fixo_pct", 2.0) != 2.0:
            return False
        if stop_type != "Banda Stop" and params.get("stop_band_pct", 1.5) != 1.5:
            return False

    exit_mode = params.get("exit_mode", "Banda + Tendência")
    if exit_mode == "Somente Tendência":
        if params.get("pct_up", 3.0) != 3.0:
            return False
        if params.get("alvo_fixo", 5.0) != 5.0:
            return False
    if exit_mode == "Banda + Tendência":
        if params.get("alvo_fixo", 5.0) != 5.0:
            return False
    if exit_mode == "Alvo Fixo + Tendência":
        if params.get("pct_up", 3.0) != 3.0:
            return False

    # Saida parcial: se desativada, params parciais devem estar no default
    if not params.get("use_parcial", False):
        if params.get("parcial_pct", 50.0) != 50.0:
            return False
        if params.get("parcial_mode", "Banda") != "Banda":
            return False
        if params.get("parcial_banda_pct", 1.5) != 1.5:
            return False
        if params.get("parcial_alvo_fixo", 2.0) != 2.0:
            return False
    else:
        parcial_mode = params.get("parcial_mode", "Banda")
        if parcial_mode == "Banda" and params.get("parcial_alvo_fixo", 2.0) != 2.0:
            return False
        if parcial_mode == "Alvo Fixo" and params.get("parcial_banda_pct", 1.5) != 1.5:
            return False

    return True


def prepare_optimizer_params(params):
    """Aplica regras de simetria antes de rodar."""
    if "th_up" in params:
        params["th_dn"] = -params["th_up"]
    if "pct_up" in params:
        params["pct_dn"] = params["pct_up"]
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


def run(df, params: dict) -> dict:
    """
    Executa o backtest DePaula.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV com colunas Open, High, Low, Close, Volume e índice datetime.
    params : dict
        Parâmetros do usuário (chaves = keys do CONFIG_SCHEMA).

    Returns
    -------
    dict com keys: metrics, equity_curve, trades
    """
    cfg = Config(
        ma_type=params.get("ma_type", "HMA"),
        ma_length=int(params.get("ma_length", 50)),
        lookback=int(params.get("lookback", 5)),
        th_up=float(params.get("th_up", 0.5)),
        th_dn=float(params.get("th_dn", -0.5)),
        hysteresis=float(params.get("hysteresis", 0.2)),
        exit_mode=params.get("exit_mode", "Banda + Tendência"),
        pct_up=float(params.get("pct_up", 3.0)),
        pct_dn=float(params.get("pct_dn", 3.0)),
        alvo_fixo=float(params.get("alvo_fixo", 5.0)),
        exit_on_flat=bool(params.get("exit_on_flat", True)),
        use_stop=bool(params.get("use_stop", False)),
        stop_type=params.get("stop_type", "ATR"),
        stop_atr_mult=float(params.get("stop_atr_mult", 2.0)),
        stop_fixo_pct=float(params.get("stop_fixo_pct", 2.0)),
        stop_band_pct=float(params.get("stop_band_pct", 1.5)),
        use_pullback=bool(params.get("use_pullback", True)),
        use_entry_zone=bool(params.get("use_entry_zone", False)),
        use_parcial=bool(params.get("use_parcial", False)),
        parcial_pct=float(params.get("parcial_pct", 50.0)),
        parcial_mode=params.get("parcial_mode", "Banda"),
        parcial_banda_pct=float(params.get("parcial_banda_pct", 1.5)),
        parcial_alvo_fixo=float(params.get("parcial_alvo_fixo", 2.0)),
        initial_capital=float(params.get("initial_capital", 1000.0)),
        cycle_filter=bool(params.get("cycle_filter", False)),
        cycle_long_months=params.get("cycle_long_months", []),
        cycle_short_months=params.get("cycle_short_months", []),
    )

    result = run_backtest(df, cfg)
    bt_df = result._df
    trades = result.trades

    # ── Métricas ──────────────────────────────────────────────────────────
    total_return = (result.equity / cfg.initial_capital - 1) * 100
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

    # ── Equity curve ──────────────────────────────────────────────────────
    dates = [str(idx)[:10] for idx in bt_df.index]
    equity_values = [_safe(float(v)) for v in bt_df["Equity"].tolist()]

    # ── Trades ────────────────────────────────────────────────────────────
    trades_list = [
        {
            "entry_date": t.entry_date[:10] if t.entry_date else "",
            "exit_date": t.exit_date[:10] if t.exit_date else "",
            "direction": t.direction,
            "comment": t.comment,
            "entry_price": _safe(float(t.entry_price)),
            "exit_price": _safe(float(t.exit_price)),
            "exit_comment": t.exit_comment,
            "pnl_pct": _safe(float(t.pnl_pct)),
            "partial_exit_price": _safe(float(t.partial_exit_price)) if t.partial_exit_price else None,
            "partial_exit_date": t.partial_exit_date[:10] if t.partial_exit_date else None,
            "partial_pct_closed": t.partial_pct_closed if t.partial_pct_closed else None,
        }
        for t in trades
    ]

    return {
        "metrics": {
            "final_equity": _safe(float(result.equity)),
            "total_return": _safe(float(total_return)),
            "max_dd": _safe(max_dd),
            "total_trades": len(trades),
            "win_rate": _safe(float(win_rate)),
            "profit_factor": _safe(profit_factor),
            "avg_win": _safe(avg_win),
            "avg_loss": _safe(avg_loss),
            "initial_capital": float(cfg.initial_capital),
        },
        "equity_curve": {
            "dates": dates,
            "values": equity_values,
        },
        "trades": trades_list,
    }
