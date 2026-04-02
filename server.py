"""
Iniciar: python server.py
"""

import io
import json
import math
import threading
import importlib.util
import numpy as np
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from scipy import stats as scipy_stats

from loader import load_csv
from config import DATA_DIR, TOP_N
from charts.scatter import (
    plot_return_vs_drawdown,
    plot_return_vs_sharpe,
    plot_return_vs_trades,
)
import itertools

# Diretório com os módulos de estratégia
STRATEGIES_DIR = Path(__file__).parent / "strategies"


def _load_strategy(strategy_file: str):
    """Carrega dinamicamente um módulo de estratégia de strategies/<name>.py."""
    # Segurança: impede path traversal e arquivos privados
    if not strategy_file or strategy_file.startswith("_") \
            or "/" in strategy_file or "\\" in strategy_file \
            or "." in strategy_file:
        raise ValueError(f"Nome de estratégia inválido: '{strategy_file}'")
    path = STRATEGIES_DIR / f"{strategy_file}.py"
    if not path.exists():
        raise FileNotFoundError(f"Estratégia '{strategy_file}' não encontrada em strategies/")
    spec = importlib.util.spec_from_file_location(f"strategies.{strategy_file}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Nao foi possivel carregar estrategia '{strategy_file}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])


def _download_data_safe(symbol: str, interval: str) -> pd.DataFrame:
    """Versão segura de download_data — nunca chama sys.exit."""
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError("yfinance não instalado. Execute: pip install yfinance")

    # Mapeia símbolos USDT → yfinance
    yf_symbol = symbol
    if "USDT" in symbol.upper():
        yf_symbol = symbol.upper().replace("USDT", "-USD")

    # yfinance nao suporta 2h e 4h diretamente — baixa 1h e resampla
    # Intervalos intraday tem limite de periodo no yfinance
    resample_rule = None
    yf_interval = interval
    yf_period = "max"

    if interval in ("2h", "4h"):
        yf_interval = "1h"
        yf_period = "2y"
        resample_rule = "2h" if interval == "2h" else "4h"
    elif interval == "15m":
        yf_period = "60d"
    elif interval == "30m":
        yf_period = "60d"
    elif interval == "1h":
        yf_period = "2y"

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=yf_period, interval=yf_interval)

    if df.empty:
        raise ValueError(f"Nenhum dado retornado para '{yf_symbol}' (intervalo={yf_interval})")

    # Garante colunas padrão
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Remove timezone do índice
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)  # type: ignore[union-attr]

    # Resampla para 2h ou 4h a partir de 1h
    if resample_rule:
        df = df.resample(resample_rule).agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }).dropna()

    return df.sort_index()

# Cache simples para correlações (evita re-download do yfinance)
_corr_cache: dict = {}

# Lista de ativos predefinidos (copiada de pages/backtest_live.py)
ASSETS = {
    "Indices US": {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
        "VIX": "^VIX",
    },
    "Acoes US - Tech": {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "NVIDIA (NVDA)": "NVDA",
        "Broadcom (AVGO)": "AVGO",
        "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "Meta (META)": "META",
        "Tesla (TSLA)": "TSLA",
        "AMD (AMD)": "AMD",
        "Intel (INTC)": "INTC",
        "Netflix (NFLX)": "NFLX",
        "Salesforce (CRM)": "CRM",
    },
    "Acoes US - Financeiro": {
        "JPMorgan (JPM)": "JPM",
        "Goldman Sachs (GS)": "GS",
        "Bank of America (BAC)": "BAC",
        "Visa (V)": "V",
        "Mastercard (MA)": "MA",
        "Berkshire Hathaway (BRK.B)": "BRK-B",
    },
    "Acoes US - Saude": {
        "UnitedHealth (UNH)": "UNH",
        "Johnson & Johnson (JNJ)": "JNJ",
        "Eli Lilly (LLY)": "LLY",
        "Pfizer (PFE)": "PFE",
        "AbbVie (ABBV)": "ABBV",
    },
    "Acoes US - Energia & Industria": {
        "ExxonMobil (XOM)": "XOM",
        "Chevron (CVX)": "CVX",
        "Boeing (BA)": "BA",
        "Caterpillar (CAT)": "CAT",
        "Lockheed Martin (LMT)": "LMT",
    },
    "Acoes US - Consumo": {
        "Walmart (WMT)": "WMT",
        "Coca-Cola (KO)": "KO",
        "McDonald's (MCD)": "MCD",
        "Nike (NKE)": "NKE",
        "Disney (DIS)": "DIS",
    },
    "Crypto": {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD",
        "BNB": "BNB-USD",
        "XRP": "XRP-USD",
        "Cardano (ADA)": "ADA-USD",
        "Avalanche (AVAX)": "AVAX-USD",
        "Polkadot (DOT)": "DOT-USD",
        "Chainlink (LINK)": "LINK-USD",
        "Dogecoin (DOGE)": "DOGE-USD",
        "Litecoin (LTC)": "LTC-USD",
    },
    "Commodities - Metais": {
        "Ouro (Gold)": "GC=F",
        "Prata (Silver)": "SI=F",
        "Cobre (Copper)": "HG=F",
        "Platina (Platinum)": "PL=F",
        "Paladio (Palladium)": "PA=F",
    },
    "Commodities - Energia": {
        "Petroleo WTI": "CL=F",
        "Petroleo Brent": "BZ=F",
        "Gas Natural": "NG=F",
    },
    "Commodities - Agricola": {
        "Milho (Corn)": "ZC=F",
        "Soja (Soybean)": "ZS=F",
        "Trigo (Wheat)": "ZW=F",
        "Cafe (Coffee)": "KC=F",
        "Acucar (Sugar)": "SB=F",
    },
}

# Flat map label → ticker para busca rápida
ALL_TICKERS = {
    label: ticker
    for cat in ASSETS.values()
    for label, ticker in cat.items()
}

CATEGORICAL_PARAMS = {
    "ma": "Tipo de Media",
    "saida": "Tipo de Saida",
    "stop": "Tipo de Stop",
    "flat": "Flat",
    "pullback": "Pullback",
    "entry_zone": "Entry Zone",
}

NUMERIC_PARAMS = {
    "periodo": "Periodo da Media",
    "lookback": "Lookback",
    "angulo": "Angulo",
    "banda_pct": "Banda (%)",
    "alvo_fixo_pct": "Alvo Fixo (%)",
    "stop_param": "Stop Param",
}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _safe(val):
    """Converte NaN/inf para None para serialização JSON segura."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def _df_to_records(df: pd.DataFrame) -> list:
    """Converte DataFrame para lista de dicts, tratando NaN → None."""
    df = df.where(pd.notnull(df), other=None)  # type: ignore[arg-type]
    return df.to_dict(orient="records")


def _apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Aplica filtros de trades, sharpe e retorno."""
    result = df.copy()
    min_trades = filters.get("min_trades", 0)
    min_sharpe = filters.get("min_sharpe", None)
    return_min = filters.get("return_min", None)
    return_max = filters.get("return_max", None)

    if "trades" in result.columns and min_trades is not None:
        result = result[result["trades"] >= min_trades]
    if "sharpe" in result.columns and min_sharpe is not None:
        result = result[result["sharpe"] >= min_sharpe]
    if "return_pct" in result.columns:
        if return_min is not None:
            result = result[result["return_pct"] >= return_min]
        if return_max is not None:
            result = result[result["return_pct"] <= return_max]
    return result


def _build_summary(df: pd.DataFrame) -> dict:
    """Calcula métricas resumo do DataFrame filtrado."""
    summary = {"total_params": len(df)}
    if "return_pct" in df.columns and len(df) > 0:
        summary["avg_return"] = _safe(float(df["return_pct"].mean()))  # type: ignore[arg-type]
    else:
        summary["avg_return"] = None
    if "sharpe" in df.columns and len(df) > 0:
        summary["avg_sharpe"] = _safe(float(df["sharpe"].mean()))  # type: ignore[arg-type]
    else:
        summary["avg_sharpe"] = None
    if "score" in df.columns and len(df) > 0:
        summary["best_score"] = _safe(float(df["score"].max()))  # type: ignore[arg-type]
    else:
        summary["best_score"] = None
    return summary


def _build_charts(df: pd.DataFrame) -> dict:
    """Gera os 3 gráficos scatter como JSON Plotly."""
    charts = {}
    if all(c in df.columns for c in ["max_dd_pct", "return_pct", "score"]):
        fig = plot_return_vs_drawdown(df)
        charts["return_vs_drawdown"] = json.loads(fig.to_json())  # type: ignore[arg-type]
    if all(c in df.columns for c in ["sharpe", "return_pct", "win_rate_pct"]):
        fig = plot_return_vs_sharpe(df)
        charts["return_vs_sharpe"] = json.loads(fig.to_json())  # type: ignore[arg-type]
    if all(c in df.columns for c in ["trades", "return_pct", "profit_factor"]):
        fig = plot_return_vs_trades(df)
        charts["return_vs_trades"] = json.loads(fig.to_json())  # type: ignore[arg-type]
    return charts


def _build_table(df: pd.DataFrame, filters: dict) -> list:
    """Retorna top-N linhas ordenadas para a tabela."""
    top_n = filters.get("top_n", TOP_N)
    sort_by = filters.get("sort_by", "score")
    sort_asc = filters.get("sort_asc", False)

    sort_map = {
        "score": "score",
        "return": "return_pct",
        "profit_factor": "profit_factor",
        "sharpe": "sharpe",
        "win_rate": "win_rate_pct",
        "trades": "trades",
        "drawdown_asc": "max_dd_pct",
        "drawdown_desc": "max_dd_pct",
    }
    col = sort_map.get(sort_by, "score")

    if col not in df.columns:
        col = "score" if "score" in df.columns else df.columns[0]

    top = df.sort_values(col, ascending=sort_asc).head(top_n)
    display_cols = [
        "ativo", "rank", "return_pct", "max_dd_pct", "trades", "win_rate_pct",
        "profit_factor", "sharpe", "score", "ma", "periodo", "lookback",
    ]
    available = [c for c in display_cols if c in top.columns]
    return _df_to_records(top[available])


def _build_best_params(df: pd.DataFrame, top_n: int = 20) -> dict:
    """Extrai análise de melhores parâmetros (lógica de best_params.py)."""
    if "score" not in df.columns:
        return {}

    top = df.nlargest(top_n, "score")
    result = {"categorical": {}, "numeric": {}, "summary_table": []}

    # Categóricos
    for param, label in CATEGORICAL_PARAMS.items():
        if param not in top.columns:
            continue
        counts = top[param].value_counts()
        if counts.empty:
            continue
        result["categorical"][param] = {
            "label": label,
            "counts": {str(k): int(v) for k, v in counts.items()},
            "top": str(counts.index[0]),
            "pct": round(float(counts.iloc[0]) / len(top) * 100, 1),
        }
        result["summary_table"].append({
            "Parametro": label,
            "Melhor Valor": str(counts.index[0]),
            "Frequencia no Top": f"{result['categorical'][param]['pct']:.0f}%",
            "Faixa Sugerida": ", ".join(counts.head(3).index.astype(str)),
        })

    # Numéricos
    for param, label in NUMERIC_PARAMS.items():
        if param not in top.columns:
            continue
        # Garante tipo numérico
        series = pd.to_numeric(top[param], errors="coerce").dropna()
        if series.empty:
            continue
        q25 = float(series.quantile(0.25))
        q75 = float(series.quantile(0.75))
        median = float(series.median())
        result["numeric"][param] = {
            "label": label,
            "median": _safe(median),
            "q25": _safe(q25),
            "q75": _safe(q75),
            "values": [_safe(v) for v in series.tolist()],
        }
        result["summary_table"].append({
            "Parametro": label,
            "Melhor Valor": f"{median:.2f} (mediana)",
            "Frequencia no Top": f"{len(series)}/{len(top)}",
            "Faixa Sugerida": f"{q25:.2f} a {q75:.2f}",
        })

    return result


def _map_backtest_params(row: dict) -> dict:
    """
    Mapeia campos do CSV para parâmetros do Config (lógica de strategy_detail.py).
    """
    params = {}

    if row.get("ma") is not None:
        params["ma_type"] = str(row["ma"]).upper()

    if row.get("periodo") is not None:
        try:
            params["ma_length"] = int(float(row["periodo"]))
        except (ValueError, TypeError):
            pass

    if row.get("lookback") is not None:
        try:
            params["lookback"] = int(float(row["lookback"]))
        except (ValueError, TypeError):
            pass

    if row.get("angulo") is not None:
        try:
            val = float(row["angulo"])
            params["th_up"] = abs(val)
            params["th_dn"] = -abs(val)
        except (ValueError, TypeError):
            pass

    if row.get("saida") is not None:
        saida = str(row["saida"])
        mode_map = {
            "Banda": "Banda + Tendência",
            "Banda + Tendência": "Banda + Tendência",
            "Tendência": "Somente Tendência",
            "Somente Tendência": "Somente Tendência",
            "Alvo Fixo": "Alvo Fixo + Tendência",
            "Alvo Fixo + Tendência": "Alvo Fixo + Tendência",
        }
        params["exit_mode"] = mode_map.get(saida, saida)

    if row.get("banda_pct") is not None:
        try:
            val = float(row["banda_pct"])
            params["pct_up"] = val
            params["pct_dn"] = val
        except (ValueError, TypeError):
            pass

    if row.get("alvo_fixo_pct") is not None:
        try:
            params["alvo_fixo"] = float(row["alvo_fixo_pct"])
        except (ValueError, TypeError):
            pass

    if row.get("flat") is not None:
        val = row["flat"]
        params["exit_on_flat"] = val in [True, 1, "True", "true", "Sim", "sim", "S", "s", "1"]

    if row.get("stop") is not None:
        stop_val = str(row["stop"])
        if stop_val.lower() in ["off", "false", "0", "nao", "não", ""]:
            params["use_stop"] = False
        else:
            params["use_stop"] = True
            params["stop_type"] = stop_val

    if row.get("stop_param") is not None:
        try:
            v = float(row["stop_param"])
            params["stop_atr_mult"] = v
            params["stop_fixo_pct"] = v
            params["stop_band_pct"] = v
        except (ValueError, TypeError):
            pass

    if row.get("pullback") is not None:
        val = row["pullback"]
        params["use_pullback"] = val in [True, 1, "True", "true", "Sim", "sim", "S", "s", "1"]

    if row.get("entry_zone") is not None:
        val = row["entry_zone"]
        params["use_entry_zone"] = val in [True, 1, "True", "true", "Sim", "sim", "S", "s", "1"]

    return params


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.route("/api/files", methods=["GET"])
def api_files():
    """Lista arquivos CSV na pasta data/."""
    try:
        if not DATA_DIR.exists():
            return jsonify({"files": []})
        files = sorted([f.name for f in DATA_DIR.glob("*.csv")])
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/load", methods=["POST"])
def api_load():
    """
    Carrega CSV (upload ou filename) e retorna dados brutos + filtros padrão + charts.
    Aceita multipart/form-data (file) ou application/json (filename + filters).
    """
    try:
        filters = {}
        df = None
        filename = ""

        if "file" in request.files:
            file_obj = request.files["file"]
            filename = file_obj.filename or "upload.csv"
            df = load_csv(file_obj)
            # Filtros do form
            filters_raw = request.form.get("filters", "{}")
            filters = json.loads(filters_raw)
        else:
            body = request.get_json(force=True) or {}
            filename = body.get("filename", "")
            filters = body.get("filters", {})
            if not filename:
                return jsonify({"error": "filename ou file obrigatório"}), 400
            path = DATA_DIR / filename
            if not path.exists():
                return jsonify({"error": f"Arquivo não encontrado: {filename}"}), 404
            df = load_csv(path)

        # Ranges reais do CSV completo
        filter_ranges = {}
        if "sharpe" in df.columns:
            filter_ranges["sharpe_min"] = _safe(float(df["sharpe"].min()))
            filter_ranges["sharpe_max"] = _safe(float(df["sharpe"].max()))
        if "return_pct" in df.columns:
            filter_ranges["return_min"] = _safe(float(df["return_pct"].min()))
            filter_ranges["return_max"] = _safe(float(df["return_pct"].max()))
        if "trades" in df.columns:
            filter_ranges["trades_min"] = int(df["trades"].min())
            filter_ranges["trades_max"] = int(df["trades"].max())

        # Aplica filtros
        if not filters:
            filters = {
                "min_trades": 0,
                "min_sharpe": filter_ranges.get("sharpe_min"),
                "return_min": filter_ranges.get("return_min"),
                "return_max": filter_ranges.get("return_max"),
                "top_n": TOP_N,
                "sort_by": "score",
                "sort_asc": False,
            }
        filtered = _apply_filters(df, filters)

        asset = str(df["ativo"].iloc[0]) if "ativo" in df.columns else filename

        return jsonify({
            "asset": asset,
            "filename": filename,
            "total_rows": len(df),
            "filtered_rows": len(filtered),
            "filter_ranges": filter_ranges,
            "raw_rows": _df_to_records(df),
            "summary": _build_summary(filtered),
            "charts": _build_charts(filtered),
            "table": _build_table(filtered, filters),
            "best_params": _build_best_params(filtered, filters.get("top_n", TOP_N)),
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/filter", methods=["POST"])
def api_filter():
    """
    Reaplicar filtros sobre os dados brutos (enviados pelo frontend).
    Backend stateless: frontend envia rawRows a cada filtragem.
    """
    try:
        body = request.get_json(force=True) or {}
        rows = body.get("rows", [])
        filters = body.get("filters", {})

        if not rows:
            return jsonify({"error": "rows obrigatório"}), 400

        df = pd.DataFrame(rows)

        # Garante tipos numéricos
        from config import NUMERIC_COLUMNS
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # periodo pode ser numérico para best_params
        if "periodo" in df.columns:
            df["periodo"] = pd.to_numeric(df["periodo"], errors="coerce")

        filtered = _apply_filters(df, filters)

        return jsonify({
            "filtered_rows": len(filtered),
            "summary": _build_summary(filtered),
            "charts": _build_charts(filtered),
            "table": _build_table(filtered, filters),
            "best_params": _build_best_params(filtered, filters.get("top_n", TOP_N)),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/filter-chart", methods=["POST"])
def api_filter_chart():
    """
    Filtra os dados brutos e regenera um unico grafico scatter.
    Recebe: rows, chart_type, chart_filters
    """
    try:
        body = request.get_json(force=True) or {}
        rows = body.get("rows", [])
        chart_type = body.get("chart_type", "")
        chart_filters = body.get("chart_filters", {})

        if not rows:
            return jsonify({"error": "rows obrigatorio"}), 400

        df = pd.DataFrame(rows)
        from config import NUMERIC_COLUMNS
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Aplica filtros visuais do grafico
        if "return_min" in chart_filters and chart_filters["return_min"] is not None:
            df = df[df["return_pct"] >= chart_filters["return_min"]]
        if "dd_max" in chart_filters and chart_filters["dd_max"] is not None:
            df = df[df["max_dd_pct"] >= chart_filters["dd_max"]]
        if "sharpe_min" in chart_filters and chart_filters["sharpe_min"] is not None:
            df = df[df["sharpe"] >= chart_filters["sharpe_min"]]
        if "trades_min" in chart_filters and chart_filters["trades_min"] is not None:
            df = df[df["trades"] >= chart_filters["trades_min"]]

        chart_json = None
        if chart_type == "return_vs_drawdown" and all(c in df.columns for c in ["max_dd_pct", "return_pct", "score"]):
            chart_json = json.loads(plot_return_vs_drawdown(df).to_json())  # type: ignore[arg-type]
        elif chart_type == "return_vs_sharpe" and all(c in df.columns for c in ["sharpe", "return_pct", "win_rate_pct"]):
            chart_json = json.loads(plot_return_vs_sharpe(df).to_json())  # type: ignore[arg-type]
        elif chart_type == "return_vs_trades" and all(c in df.columns for c in ["trades", "return_pct", "profit_factor"]):
            chart_json = json.loads(plot_return_vs_trades(df).to_json())  # type: ignore[arg-type]

        return jsonify({
            "chart": chart_json,
            "count": len(df),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/strategy", methods=["POST"])
def api_strategy():
    """
    Retorna detalhes de uma estratégia por rank + parâmetros mapeados para backtest.
    """
    try:
        body = request.get_json(force=True) or {}
        rank = body.get("rank")
        rows = body.get("rows", [])

        if not rows:
            return jsonify({"error": "rows obrigatório"}), 400

        df = pd.DataFrame(rows)
        from config import NUMERIC_COLUMNS
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if rank is not None and "rank" in df.columns:
            match = df[df["rank"] == rank]
            if match.empty:
                # Tenta por índice como fallback
                try:
                    row_dict = df.iloc[int(rank)].to_dict()
                except Exception:
                    return jsonify({"error": f"rank {rank} não encontrado"}), 404
            else:
                row_dict = match.iloc[0].to_dict()
        else:
            return jsonify({"error": "rank obrigatório"}), 400

        # Limpa NaN
        detail = {k: (_safe(v) if isinstance(v, float) else v) for k, v in row_dict.items()}
        backtest_params = _map_backtest_params(row_dict)

        return jsonify({"detail": detail, "backtest_params": backtest_params})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/backtest/assets", methods=["GET"])
def api_backtest_assets():
    """Retorna dicionário de ativos predefinidos."""
    return jsonify({"assets": ASSETS})


@app.route("/api/backtest/strategies", methods=["GET"])
def api_backtest_strategies():
    """Lista todos os módulos de estratégia disponíveis em strategies/."""
    strategies = []
    if STRATEGIES_DIR.exists():
        for path in sorted(STRATEGIES_DIR.glob("*.py")):
            if path.name.startswith("_"):
                continue  # ignora __init__.py e _utils.py
            try:
                module = _load_strategy(path.stem)
                strategies.append({
                    "file": path.stem,
                    "name": getattr(module, "NAME", path.stem),
                    "description": getattr(module, "DESCRIPTION", ""),
                    "schema": getattr(module, "CONFIG_SCHEMA", []),
                })
            except Exception as e:
                import traceback
                strategies.append({
                    "file": path.stem,
                    "name": path.stem,
                    "description": "",
                    "schema": [],
                    "error": str(e),
                })
    return jsonify({"strategies": strategies})


@app.route("/api/backtest/run", methods=["POST"])
def api_backtest_run():
    """
    Executa o backtest delegando ao módulo de estratégia escolhido.
    Aceita:
    - JSON: { "strategy_file": "depaula", "data_source": "asset",
              "symbol": "BTC-USD", "interval": "1d", "config": {...} }
    - multipart/form-data: file CSV + config (JSON) + strategy_file (form field)
    """
    try:
        df_data = None
        cfg_dict = {}
        symbol_label = ""
        interval_label = ""
        strategy_file = "depaula"  # padrão para backward compat

        if "file" in request.files:
            file_obj = request.files["file"]
            symbol_label = file_obj.filename or "CSV"
            interval_label = "-"
            cfg_raw = request.form.get("config", "{}")
            cfg_dict = json.loads(cfg_raw)
            strategy_file = request.form.get("strategy_file", "depaula") or "depaula"
            # Lê CSV de preços (colunas: Date,Open,High,Low,Close)
            raw = file_obj.read()
            for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
                try:
                    text = raw.decode(enc)
                    df_data = pd.read_csv(
                        io.StringIO(text),
                        parse_dates=["Date"],
                        index_col="Date"
                    ).sort_index()
                    break
                except Exception:
                    continue
            if df_data is None:
                return jsonify({"error": "Não foi possível ler o CSV de preços"}), 400
        else:
            body = request.get_json(force=True) or {}
            cfg_dict = body.get("config", {})
            strategy_file = body.get("strategy_file", "depaula") or "depaula"
            symbol_label = body.get("symbol_label", "")
            interval_label = body.get("interval", "1d")
            symbol = body.get("symbol", "")

            if not symbol:
                return jsonify({"error": "symbol obrigatório"}), 400

            df_data = _download_data_safe(symbol, interval_label)
            if symbol_label == "":
                symbol_label = symbol

        # Carrega o módulo de estratégia e executa
        module = _load_strategy(strategy_file)
        result_dict = module.run(df_data.copy(), cfg_dict)

        return jsonify({
            "symbol": symbol_label,
            "interval": interval_label,
            "strategy": strategy_file,
            **result_dict,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


def _extract_param_specs(module):
    """Extrai params para otimizacao IS a partir de OPTIMIZER_GRIDS['rapido'].
    Retorna (specs_dict, numeric_keys_list).
    """
    grids = getattr(module, 'OPTIMIZER_GRIDS', {})
    grid  = grids.get('rapido', grids.get('default', {}))
    if not grid:
        return {}, []
    specs = {}
    numeric_keys = []
    for key, values in grid.items():
        if not values or len(values) < 2:
            continue
        specs[key] = list(values)
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            numeric_keys.append(key)
    return specs, numeric_keys


def _random_config_from_grid(base_config, param_specs, rng):
    """Gera uma config aleatoria a partir das listas de valores do grid."""
    cfg = dict(base_config)
    for key, values in param_specs.items():
        cfg[key] = values[int(rng.integers(0, len(values)))]
    # Mantém simetria de params derivados
    if 'th_up' in cfg:
        cfg['th_dn'] = -abs(float(cfg['th_up']))
    if 'pct_up' in cfg:
        cfg['pct_dn'] = cfg['pct_up']
    return cfg


# Barras por ano por timeframe — usado para anualizar Sharpe corretamente
_BARS_PER_YEAR = {
    '1m': 98280, '5m': 19656, '15m': 6552, '30m': 3276,
    '1h': 1638,  '2h': 819,   '4h': 410,
    '1d': 252,   '1wk': 52,   '1mo': 12,
}


def _compute_window_metrics(df_slice, module, cfg_dict, interval='1d'):
    """Roda a estrategia em um slice do DataFrame e retorna metricas WFA.
    Retorna None se o slice for pequeno demais ou nao gerar trades suficientes.
    """
    if len(df_slice) < 20:
        return None
    try:
        result = module.run(df_slice.copy(), {**cfg_dict, "_fast": True})
    except Exception:
        return None

    metrics = result.get("metrics", {})
    n_trades = int(metrics.get("total_trades", 0))
    if n_trades < 2:
        return None

    eq_values = result.get("equity_curve", {}).get("values", [])
    eq_dates  = result.get("equity_curve", {}).get("dates", [])

    # Sharpe anualizado com fator correto para o timeframe (ddof=1 = variancia amostral)
    sharpe = 0.0
    if len(eq_values) > 2:
        ann_factor = _BARS_PER_YEAR.get(interval, 252)
        arr = np.array(eq_values, dtype=float)
        rets = np.diff(arr) / np.where(arr[:-1] != 0, arr[:-1], 1.0)
        rets = rets[np.isfinite(rets)]
        std = rets.std(ddof=1)
        if len(rets) > 1 and std > 0:
            sharpe = float(rets.mean() / std * np.sqrt(ann_factor))

    return {
        "return_pct":    _safe(float(metrics.get("total_return", 0.0))),
        "sharpe":        _safe(sharpe),
        "n_trades":      n_trades,
        "max_dd":        _safe(float(metrics.get("max_dd", 0.0))),
        "equity_values": [_safe(float(v)) for v in eq_values],
        "equity_dates":  eq_dates,
    }


@app.route("/api/backtest/wfa", methods=["POST"])
def api_backtest_wfa():
    """
    Walk-Forward Analysis.
    Input JSON: { symbol, interval, strategy_file, config, n_windows, is_pct }
    """
    try:
        body = request.get_json(force=True) or {}
        symbol        = body.get("symbol", "")
        interval      = body.get("interval", "1d")
        strategy_file = body.get("strategy_file", "depaula") or "depaula"
        cfg_dict      = body.get("config", {})
        n_windows            = int(max(3, min(30, body.get("n_windows", 10))))
        is_pct               = float(max(0.5, min(0.85, body.get("is_pct", 0.70))))
        optimize_is_samples  = int(max(0, min(200, body.get("optimize_is_samples", 0))))

        if not symbol:
            return jsonify({"error": "symbol obrigatorio para WFA"}), 400

        df = _download_data_safe(symbol, interval)
        total_bars = len(df)

        if total_bars < n_windows * 20:
            return jsonify({
                "error": f"Dados insuficientes ({total_bars} barras) para {n_windows} janelas. "
                         f"Reduza o numero de janelas ou use um timeframe maior."
            }), 400

        module = _load_strategy(strategy_file)
        param_specs, numeric_keys = (
            _extract_param_specs(module) if optimize_is_samples > 0 else ({}, [])
        )

        step_size = total_bars // n_windows
        is_bars   = int(step_size * is_pct)
        oos_bars  = step_size - is_bars

        windows = []
        for i in range(n_windows):
            is_start  = i * step_size
            is_end    = is_start + is_bars
            oos_start = is_end
            oos_end   = min(oos_start + oos_bars, total_bars)

            if oos_end <= oos_start:
                continue

            df_is  = df.iloc[is_start:is_end]
            df_oos = df.iloc[oos_start:oos_end]

            # IS optimization: random-sample the grid, keep best Sharpe config
            if optimize_is_samples > 0 and param_specs:
                best_sharpe = float('-inf')
                window_cfg  = dict(cfg_dict)
                win_rng     = np.random.default_rng(42 + i)
                for _ in range(optimize_is_samples):
                    trial_cfg = _random_config_from_grid(cfg_dict, param_specs, win_rng)
                    trial_m   = _compute_window_metrics(df_is, module, trial_cfg, interval)
                    if trial_m is None:
                        continue
                    trial_sharpe = trial_m['sharpe'] if trial_m['sharpe'] is not None else 0.0
                    if trial_sharpe > best_sharpe:
                        best_sharpe = trial_sharpe
                        window_cfg  = trial_cfg
            else:
                window_cfg = dict(cfg_dict)

            is_m  = _compute_window_metrics(df_is,  module, window_cfg, interval)
            oos_m = _compute_window_metrics(df_oos, module, window_cfg, interval)

            if is_m is None or oos_m is None:
                continue

            # Annualized return: (1 + r)^(365/days) - 1
            is_days  = max((df_is.index[-1]  - df_is.index[0]).days,  1)
            oos_days = max((df_oos.index[-1] - df_oos.index[0]).days, 1)
            is_ann  = _safe(((1 + (is_m["return_pct"]  or 0) / 100) ** (365 / is_days)  - 1) * 100)
            oos_ann = _safe(((1 + (oos_m["return_pct"] or 0) / 100) ** (365 / oos_days) - 1) * 100)

            windows.append({
                "window_idx":       i,
                "is_start":         str(df_is.index[0])[:10],
                "is_end":           str(df_is.index[-1])[:10],
                "oos_start":        str(df_oos.index[0])[:10],
                "oos_end":          str(df_oos.index[-1])[:10],
                "is_return":        is_m["return_pct"],
                "oos_return":       oos_m["return_pct"],
                "is_annualized":    is_ann,
                "oos_annualized":   oos_ann,
                "is_sharpe":        is_m["sharpe"],
                "oos_sharpe":       oos_m["sharpe"],
                "is_trades":        is_m["n_trades"],
                "oos_trades":       oos_m["n_trades"],
                "is_equity":        is_m["equity_values"],
                "oos_equity":       oos_m["equity_values"],
                "is_dates":         is_m["equity_dates"],
                "oos_dates":        oos_m["equity_dates"],
                "optimal_params":   {k: window_cfg.get(k) for k in numeric_keys} if numeric_keys else None,
            })

        if not windows:
            return jsonify({"error": "Nenhuma janela gerou trades suficientes. Tente reduzir o numero de janelas."}), 400

        # Concatena a curva OOS reescalando cada segmento para continuidade
        oos_dates_all  = []
        oos_values_all = []
        running_base   = None

        for w in windows:
            raw_vals  = w["oos_equity"]
            raw_dates = w["oos_dates"]
            if not raw_vals:
                continue
            initial = raw_vals[0] if raw_vals[0] else 1.0
            if running_base is None:
                oos_dates_all.extend(raw_dates)
                oos_values_all.extend(raw_vals)
                running_base = next((v for v in reversed(raw_vals) if v is not None), 1.0)
            else:
                scale = (running_base / initial) if initial != 0 else 1.0
                scaled = [v * scale if v is not None else None for v in raw_vals]
                oos_dates_all.extend(raw_dates)
                oos_values_all.extend(scaled)
                # Usa o ultimo valor nao-nulo para evitar que running_base fique None
                running_base = next((v for v in reversed(scaled) if v is not None), running_base)

        # WFE = media(oos_annualized / is_annualized) para janelas com is_annualized > 0
        # Razoes clampadas em [-2, 5] para evitar que outliers distorcam a media
        # WFE > 0.5 e geralmente aceitavel
        wfe_ratios = []
        for w in windows:
            ia = w["is_annualized"]
            oa = w["oos_annualized"]
            if ia is not None and ia > 0 and oa is not None:
                wfe_ratios.append(min(max(oa / ia, -2.0), 5.0))

        wfe = float(np.mean(wfe_ratios)) if wfe_ratios else 0.0

        ann_oos = [w["oos_annualized"] for w in windows if w["oos_annualized"] is not None]
        ann_is  = [w["is_annualized"]  for w in windows if w["is_annualized"]  is not None]
        avg_oos_annualized = float(np.mean(ann_oos)) if ann_oos else 0.0
        avg_is_annualized  = float(np.mean(ann_is))  if ann_is  else 0.0
        avg_oos_return = float(np.mean([w["oos_return"] for w in windows if w["oos_return"] is not None]))
        avg_is_return  = float(np.mean([w["is_return"]  for w in windows if w["is_return"]  is not None]))

        return jsonify({
            "windows":              windows,
            "oos_equity_curve":     {"dates": oos_dates_all, "values": oos_values_all},
            "wfe":                  _safe(wfe),
            "avg_oos_annualized":   _safe(avg_oos_annualized),
            "avg_is_annualized":    _safe(avg_is_annualized),
            "avg_oos_return":       _safe(avg_oos_return),
            "avg_is_return":        _safe(avg_is_return),
            "n_valid_windows":      len(windows),
            "param_keys":           numeric_keys,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/backtest/correlation", methods=["POST"])
def api_backtest_correlation():
    """
    Baixa retornos de 2 anos e retorna matriz de correlação + distribuições.
    Usa cache em memória para evitar re-download.
    """
    try:
        import yfinance as yf

        body = request.get_json(force=True) or {}
        tickers = body.get("tickers", {})  # { "Bitcoin (BTC)": "BTC-USD", ... }

        if len(tickers) < 2:
            return jsonify({"error": "Selecione pelo menos 2 ativos"}), 400

        cache_key = frozenset(tickers.items())
        if cache_key in _corr_cache:
            return jsonify(_corr_cache[cache_key])

        # Download dados (lógica de backtest_live.py linhas 348-370)
        closes = {}
        for label, ticker in tickers.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="2y", interval="1d")
                if not hist.empty:
                    series = hist["Close"].copy()
                    series.index = series.index.tz_localize(None).normalize()  # type: ignore[union-attr]
                    series = series[~series.index.duplicated(keep="first")]
                    closes[label] = series
            except Exception:
                continue

        if len(closes) < 2:
            return jsonify({"error": "Não foi possível carregar dados para correlação"}), 400

        df_closes = pd.DataFrame(closes).ffill().dropna()
        returns_df = df_closes.pct_change().dropna()

        # Matriz de correlação
        corr = returns_df.corr()
        labels = corr.columns.tolist()
        matrix = [[_safe(float(v)) for v in row] for row in corr.values]

        # Distribuições
        distributions = {}
        colors = [
            "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
            "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
        ]
        for i, col in enumerate(returns_df.columns):
            ret = returns_df[col].dropna()
            skew_val = float(ret.skew())  # type: ignore[arg-type]
            kurt_val = float(ret.kurtosis())  # type: ignore[arg-type]
            sharpe_val = float(ret.mean() / ret.std() * np.sqrt(252)) if ret.std() > 0 else 0

            # Histograma
            ret_pct = (ret * 100).tolist()

            # PDF teórico
            mu = float(ret.mean() * 100)
            sigma = float(ret.std() * 100)
            x_range = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 200).tolist()
            pdf = scipy_stats.norm.pdf(x_range, mu, sigma).tolist()

            distributions[col] = {
                "color": colors[i % len(colors)],
                "returns": [_safe(float(v)) for v in ret_pct],
                "pdf_x": [_safe(float(v)) for v in x_range],
                "pdf_y": [_safe(float(v)) for v in pdf],
                "stats": {
                    "mean": _safe(float(ret.mean() * 100)),
                    "std": _safe(float(ret.std() * 100)),
                    "skew": _safe(skew_val),
                    "kurtosis": _safe(kurt_val),
                    "sharpe_annual": _safe(sharpe_val),
                },
                "skew_desc": _skew_desc(skew_val),
                "kurt_desc": _kurt_desc(kurt_val),
            }

        # Retornos alinhados para scatter plot par a par (+ datas para hover)
        dates = [d.strftime("%d/%m/%Y") for d in returns_df.index]
        returns_aligned = {}
        for col in returns_df.columns:
            returns_aligned[col] = [_safe(float(v)) for v in (returns_df[col] * 100).tolist()]

        response = {
            "correlation": {"labels": labels, "matrix": matrix},
            "distributions": distributions,
            "returns_aligned": returns_aligned,
            "dates": dates,
        }
        _corr_cache[cache_key] = response
        return jsonify(response)

    except ImportError:
        return jsonify({"error": "yfinance não instalado: pip install yfinance"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/backtest/montecarlo", methods=["POST"])
def api_backtest_montecarlo():
    """
    Simulação Monte Carlo (GBM) sobre a equity curve do backtest.
    Recebe: { equity_curve: {dates, values}, num_sims, horizon, seed }
    Retorna: hist_dates, hist_values, proj_dates, p10, p50, p90, reg_line,
             sample_paths, stats
    """
    try:
        body = request.get_json(force=True) or {}
        equity   = body.get("equity_curve", {})
        num_sims = max(1, int(body.get("num_sims", 300)))
        horizon  = int(body.get("horizon", 0))   # 0 = auto
        seed     = int(body.get("seed", 42))

        dates  = equity.get("dates", [])
        values = equity.get("values", [])

        if not values or len(values) < 5:
            return jsonify({"error": "Dados insuficientes para simulação"}), 400

        arr = np.array(values, dtype=float)

        # ── Parâmetros estatísticos ──────────────────────────────────────────
        log_rets = np.diff(np.log(arr))
        log_rets = log_rets[np.isfinite(log_rets)]
        if len(log_rets) < 5:
            return jsonify({"error": "Retornos insuficientes"}), 400

        mu       = float(np.mean(log_rets))
        variance = float(np.var(log_rets))
        sigma    = float(np.std(log_rets))
        S0       = float(arr[-1])

        steps = max(int(len(arr) * 0.75), 30) if horizon == 0 else horizon

        # ── GBM vetorizado com numpy ─────────────────────────────────────────
        rng        = np.random.default_rng(seed)
        Z          = rng.standard_normal((num_sims, steps))
        increments = np.exp((mu - 0.5 * variance) + sigma * Z)
        paths      = np.cumprod(increments, axis=1) * S0          # (N, steps)
        paths      = np.hstack([np.full((num_sims, 1), S0), paths])  # prepend S0 → (N, steps+1)

        # ── Percentis ────────────────────────────────────────────────────────
        p10 = np.percentile(paths, 10, axis=0).tolist()
        p50 = np.percentile(paths, 50, axis=0).tolist()
        p90 = np.percentile(paths, 90, axis=0).tolist()

        # ── Regressão linear sobre a mediana (numpy.polyfit) ─────────────────
        x_idx    = np.arange(steps + 1, dtype=float)
        coeffs   = np.polyfit(x_idx, p50, 1)
        reg_line = (coeffs[0] * x_idx + coeffs[1]).tolist()

        # ── Amostra de caminhos para visualização (30 paths) ─────────────────
        sample_n    = min(30, num_sims)
        sample_idx  = np.linspace(0, num_sims - 1, sample_n, dtype=int)
        sample_paths = [
            [_safe(float(v)) for v in paths[i]]
            for i in sample_idx
        ]

        # ── Datas futuras via pandas (dias úteis) ────────────────────────────
        last_str = dates[-1] if dates else ""
        try:
            last_ts = pd.Timestamp(last_str)
        except Exception:
            day, mo, yr = last_str.split("/")
            last_ts = pd.Timestamp(f"{yr}-{mo}-{day}")

        future_bdays = pd.bdate_range(start=last_ts, periods=steps + 1)[1:]
        proj_dates   = [last_ts.strftime("%Y-%m-%d")] + [
            d.strftime("%Y-%m-%d") for d in future_bdays
        ]

        # ── Janela histórica visível (≤ metade do horizonte) ─────────────────
        hist_window = min(len(arr), math.ceil(steps / 2))
        hist_dates  = dates[-hist_window:]
        hist_values = [_safe(float(v)) for v in arr[-hist_window:]]

        # ── Estatísticas finais ───────────────────────────────────────────────
        finals = paths[:, -1]
        stats  = {
            "median_final": _safe(float(np.percentile(finals, 50))),
            "p10_final":    _safe(float(np.percentile(finals, 10))),
            "p90_final":    _safe(float(np.percentile(finals, 90))),
            "prob_profit":  _safe(float(np.mean(finals > S0) * 100)),
            "mu_daily":     _safe(mu),
            "sigma_daily":  _safe(sigma),
        }

        return jsonify({
            "hist_dates":   hist_dates,
            "hist_values":  hist_values,
            "proj_dates":   proj_dates,
            "p10":          [_safe(v) for v in p10],
            "p50":          [_safe(v) for v in p50],
            "p90":          [_safe(v) for v in p90],
            "reg_line":     [_safe(v) for v in reg_line],
            "sample_paths": sample_paths,
            "stats":        stats,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/backtest/validate", methods=["POST"])
def api_backtest_validate():
    """
    Validação estatística da estratégia via Monte Carlo + Permutation Test.

    Recebe:
      trades         — lista de trades com pnl_pct
      equity_curve   — {dates, values}
      metrics        — métricas do backtest (initial_capital, final_equity, etc.)
      n_sims         — nº de simulações MC (default 500)
      n_perms        — nº de permutações (default 300)
      seed           — semente aleatória

    Retorna:
      original, reshuffle, resample, randomized, return_alteration,
      permutation_test, report
    """
    import sys as _sys
    import os as _os
    _ROOT = _os.path.dirname(_os.path.abspath(__file__))
    if _ROOT not in _sys.path:
        _sys.path.insert(0, _ROOT)

    try:
        from monte_carlo.monte_carlo      import MonteCarlo
        from monte_carlo.permutation_test import PermutationTestEquity
        from monte_carlo.report           import generate as gen_report
    except ImportError as e:
        return jsonify({"error": f"Módulo monte_carlo_project não encontrado: {e}"}), 500

    try:
        body         = request.get_json(force=True) or {}
        trades       = body.get("trades", [])
        equity       = body.get("equity_curve", {})
        metrics_in   = body.get("metrics", {})
        n_sims       = max(50, int(body.get("n_sims", 500)))
        n_perms      = max(50, int(body.get("n_perms", 300)))
        seed         = int(body.get("seed", 42))

        eq_values    = equity.get("values", [])
        eq_dates     = equity.get("dates", [])

        if len(trades) < 5:
            return jsonify({"error": "São necessários pelo menos 5 trades para a validação"}), 400
        if len(eq_values) < 10:
            return jsonify({"error": "Equity curve insuficiente"}), 400

        ic           = float(metrics_in.get("initial_capital", eq_values[0]))
        interval_mc  = body.get("interval", "1d")
        ann_factor   = _BARS_PER_YEAR.get(interval_mc, 252)

        # ── Monte Carlo ──────────────────────────────────────────────────────
        mc = MonteCarlo(initial_capital=ic, seed=seed, ann_factor=ann_factor)

        reshuffle_r         = mc.reshuffle(trades,        n_sims=n_sims)
        resample_r          = mc.resample(trades,         n_sims=n_sims)
        randomized_r        = mc.randomized(trades,       n_sims=n_sims)
        return_alteration_r = mc.return_alteration(eq_values, eq_dates, n_sims=n_sims)

        # ── Permutation Test (equity-curve based) ────────────────────────────
        pt          = PermutationTestEquity(seed=seed, ann_factor=ann_factor)
        perm_result = pt.run(eq_values, trades, n_perms=n_perms)

        # ── Métricas originais enriquecidas ──────────────────────────────────
        arr_eq  = np.array(eq_values, dtype=float)
        rets_eq = np.diff(arr_eq) / np.where(arr_eq[:-1] != 0, arr_eq[:-1], 1.0)
        rets_eq = rets_eq[np.isfinite(rets_eq)]
        _std_eq = float(rets_eq.std(ddof=1)) if len(rets_eq) > 1 else 0.0
        sharpe  = float(rets_eq.mean() / _std_eq * np.sqrt(ann_factor)) if _std_eq > 0 else 0.0

        pnls      = [t.get("pnl_pct", 0) for t in trades]
        wins      = [p for p in pnls if p > 0]
        losses    = [p for p in pnls if p <= 0]
        win_rate  = float(metrics_in.get("win_rate", len(wins) / len(pnls) * 100 if pnls else 0))
        avg_win   = float(np.mean(wins))   if wins   else 0.0
        avg_loss  = float(np.mean(losses)) if losses else 0.0
        expectancy = win_rate / 100 * avg_win + (1 - win_rate / 100) * avg_loss

        # Sortino — annualized by trades_per_year
        _ds_sq  = [min(p, 0) ** 2 for p in pnls]
        _ds_dev = float(np.sqrt(np.mean(_ds_sq))) if _ds_sq else 0.0
        from datetime import datetime as _dt2
        _sort_days = 1
        if len(eq_dates) > 1:
            try:
                _sort_days = max((_dt2.fromisoformat(str(eq_dates[-1])[:10]) - _dt2.fromisoformat(str(eq_dates[0])[:10])).days, 1)
            except Exception:
                _sort_days = max(len(arr_eq) - 1, 1)
        _trades_per_year = len(pnls) / (_sort_days / 365.25) if _sort_days > 0 else len(pnls)
        sortino = float(np.mean(pnls) / _ds_dev * np.sqrt(_trades_per_year)) if _ds_dev > 0 else 0.0

        # Calmar — CAGR uses calendar days derived from equity curve dates
        ic_val = float(metrics_in.get("initial_capital", arr_eq[0] if len(arr_eq) else 1.0))
        if len(eq_dates) > 1:
            try:
                _t0 = _dt2.fromisoformat(str(eq_dates[0])[:10])
                _t1 = _dt2.fromisoformat(str(eq_dates[-1])[:10])
                _cal_days = max((_t1 - _t0).days, 1)
            except Exception:
                _cal_days = max(len(arr_eq) - 1, 1)
        else:
            _cal_days = max(len(arr_eq) - 1, 1)
        cagr = ((arr_eq[-1] / ic_val) ** (365.25 / _cal_days) - 1) * 100 if ic_val > 0 else 0.0
        max_dd_val = float(metrics_in.get("max_dd", 0)) or 0
        calmar = float(cagr / abs(max_dd_val)) if abs(max_dd_val) > 0 else 0.0

        # Omega
        gains_sum  = sum(p for p in pnls if p > 0)
        losses_sum = abs(sum(p for p in pnls if p < 0))
        omega = float(gains_sum / losses_sum) if losses_sum > 0 else 0.0

        # Extract dd episode troughs for Sterling and Burke
        peak_eq = np.maximum.accumulate(arr_eq)
        dd_eq   = (arr_eq - peak_eq) / peak_eq * 100
        _ep_tr  = []
        _in_dd  = False
        _ep_s   = None
        for _ki, _vi in enumerate(dd_eq):
            if _vi < 0 and not _in_dd:
                _in_dd = True
                _ep_s  = _ki
            elif _vi >= 0 and _in_dd:
                _in_dd = False
                _ep_tr.append(float(dd_eq[_ep_s:_ki].min()))
        if _in_dd and _ep_s is not None:
            _ep_tr.append(float(dd_eq[_ep_s:].min()))

        # Sterling (CAGR / mean of N worst episode troughs)
        if _ep_tr:
            _nw = min(5, len(_ep_tr))
            _wt = sorted(_ep_tr)[:_nw]
            _aw = abs(float(np.mean(_wt)))
            sterling = float(cagr / _aw) if _aw > 0 else 0.0
        else:
            sterling = 0.0

        # Burke (CAGR / sqrt(sum of N worst episode trough^2))
        if _ep_tr:
            _nw = min(5, len(_ep_tr))
            _wt = sorted(_ep_tr)[:_nw]
            _bd = float(np.sqrt(np.sum(np.array(_wt) ** 2)))
            burke = float(cagr / _bd) if _bd > 0 else 0.0
        else:
            burke = 0.0

        original = {
            **{k: _safe(v) for k, v in metrics_in.items()},
            "sharpe":     _safe(sharpe),
            "sortino":    _safe(sortino),
            "calmar":     _safe(calmar),
            "omega":      _safe(omega),
            "sterling":   _safe(sterling),
            "burke":      _safe(burke),
            "avg_win":    _safe(avg_win),
            "avg_loss":   _safe(avg_loss),
            "expectancy": _safe(expectancy),
        }

        # ── Relatório textual ────────────────────────────────────────────────
        report_text = gen_report(
            original=original,
            mc_results={
                "reshuffle":        reshuffle_r,
                "resample":         resample_r,
                "randomized":       randomized_r,
                "return_alteration": return_alteration_r,
            },
            perm_result=perm_result,
            strategy_label=body.get("strategy_label", "Estratégia"),
            asset_label=body.get("asset_label", "-"),
            period_label=f"{eq_dates[0] if eq_dates else '-'} → {eq_dates[-1] if eq_dates else '-'}",
            n_sims=n_sims,
        )

        return jsonify({
            "original":          original,
            "reshuffle":         reshuffle_r,
            "resample":          resample_r,
            "randomized":        randomized_r,
            "return_alteration": return_alteration_r,
            "permutation_test":  perm_result,
            "report":            report_text,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# ─── Optimizer ────────────────────────────────────────────────────────────────

# Estado global do otimizador (cancel + progresso)
_optimizer_cancel = threading.Event()
_optimizer_progress = {"current": 0, "total": 0, "valid": 0, "status": "idle"}
_optimizer_lock = threading.Lock()
_optimizer_result_store = {"data": None, "error": None}


def _parse_grid_generic(grid_raw, schema):
    """Converte valores do grid usando o CONFIG_SCHEMA da estrategia para tipos corretos."""
    type_map = {}
    for section in (schema or []):
        for field in section.get("fields", []):
            type_map[field["key"]] = field.get("type", "number")

    typed = {}
    for key, values in grid_raw.items():
        if not isinstance(values, list) or len(values) == 0:
            continue
        ft = type_map.get(key)
        if ft is None:
            # Infere tipo a partir dos valores
            ft = _infer_grid_type(values)
        if ft == "checkbox":
            typed[key] = [v if isinstance(v, bool) else str(v).lower() in ("true", "1") for v in values]
        elif ft == "number":
            typed[key] = [float(v) for v in values]
        elif ft == "select":
            typed[key] = [str(v) for v in values]
        else:
            typed[key] = values
    return typed


def _infer_grid_type(values):
    """Infere o tipo de um campo a partir dos valores no grid."""
    if all(isinstance(v, bool) or str(v).lower() in ("true", "false") for v in values):
        return "checkbox"
    try:
        [float(v) for v in values]
        return "number"
    except (ValueError, TypeError):
        return "select"


def _generate_combos(grid, validator=None):
    """Gera todas as combinacoes de parametros a partir de um grid dict."""
    keys = sorted(grid.keys())
    values = [grid[k] for k in keys]
    combos = []
    for combo in itertools.product(*values):
        params = dict(zip(keys, combo))
        if validator and not validator(params):
            continue
        combos.append(params)
    return combos


def _calc_optimizer_row(result, params, param_labels):
    """Extrai metricas padrao do resultado de module.run() e monta linha para ranking."""
    m = result.get("metrics", {})
    trades = result.get("trades", [])

    total_return = m.get("total_return", 0) or 0
    max_dd = m.get("max_dd", 0) or 0
    win_rate = m.get("win_rate", 0) or 0
    pf = m.get("profit_factor", 0) or 0
    avg_win = m.get("avg_win", 0) or 0
    avg_loss = m.get("avg_loss", 0) or 0

    # Reuse pre-computed formula-accurate values from the strategy module
    sharpe  = m.get("sharpe")  or 0.0
    sortino = m.get("sortino") or 0.0
    calmar  = m.get("calmar")  or 0.0
    omega   = m.get("omega")   or 0.0
    sterling = m.get("sterling") or 0.0
    burke   = m.get("burke")   or 0.0

    # Score composto
    score = total_return * (win_rate / 100) / max(abs(max_dd), 1)

    row = {
        "Retorno (%)": round(total_return, 2),
        "Max DD (%)": round(max_dd, 2),
        "Trades": m.get("total_trades", 0),
        "Win Rate (%)": round(win_rate, 1),
        "Avg Win (%)": round(avg_win, 2),
        "Avg Loss (%)": round(avg_loss, 2),
        "Profit Factor": round(pf, 2),
        "Sharpe": round(sharpe, 2),
        "Sortino": round(sortino, 2),
        "Calmar": round(calmar, 2),
        "Omega": round(omega, 2),
        "Sterling": round(sterling, 2),
        "Burke": round(burke, 2),
        "Score": round(score, 2),
    }
    # Adiciona parametros com labels amigaveis
    for k, v in params.items():
        label = param_labels.get(k, k)
        row[label] = v
    return row


def _build_param_labels(schema):
    """Monta mapa key -> label a partir do CONFIG_SCHEMA."""
    labels = {}
    for section in (schema or []):
        for field in section.get("fields", []):
            labels[field["key"]] = field.get("label", field["key"])
    return labels


@app.route("/api/optimizer/grids", methods=["GET"])
def api_optimizer_grids():
    """Retorna os grids disponiveis para uma estrategia."""
    strategy_file = request.args.get("strategy", "depaula")
    try:
        module = _load_strategy(strategy_file)
        raw_grids = getattr(module, "OPTIMIZER_GRIDS", {})
        grids_info = {}
        for name, grid in raw_grids.items():
            grids_info[name] = {k: [str(v) for v in vals] for k, vals in grid.items()}
        schema = getattr(module, "CONFIG_SCHEMA", [])
        return jsonify({"grids": grids_info, "schema": schema})
    except Exception as e:
        return jsonify({"grids": {}, "schema": [], "error": str(e)})


@app.route("/api/optimizer/count", methods=["POST"])
def api_optimizer_count():
    """Conta quantas combinacoes o grid vai gerar (sem rodar)."""
    try:
        body = request.get_json(force=True) or {}
        grid_raw = body.get("grid", {})
        strategy_file = body.get("strategy_file", "depaula")

        module = _load_strategy(strategy_file)
        schema = getattr(module, "CONFIG_SCHEMA", [])
        validator = getattr(module, "is_valid_config", None)

        typed_grid = _parse_grid_generic(grid_raw, schema)
        combos = _generate_combos(typed_grid, validator)
        return jsonify({"count": len(combos)})
    except Exception as e:
        return jsonify({"error": str(e), "count": 0}), 400


@app.route("/api/optimizer/stop", methods=["POST"])
def api_optimizer_stop():
    """Para a otimizacao em andamento e retorna resultados parciais."""
    _optimizer_cancel.set()
    return jsonify({"ok": True})


@app.route("/api/optimizer/progress", methods=["GET"])
def api_optimizer_progress():
    """Retorna o progresso atual da otimizacao."""
    with _optimizer_lock:
        return jsonify(dict(_optimizer_progress))


def _run_optimizer_compute(df_data, module, grid_raw, capital, min_trades, rank_by, top_n, symbol_label, interval_label, fixed_params=None):
    """Logica generica de otimizacao. Retorna (data_dict, error_str) — sem jsonify."""
    import time

    schema = getattr(module, "CONFIG_SCHEMA", [])
    validator = getattr(module, "is_valid_config", None)
    prepare = getattr(module, "prepare_optimizer_params", None)
    param_labels = _build_param_labels(schema)

    typed_grid = _parse_grid_generic(grid_raw, schema)
    combos = _generate_combos(typed_grid, validator)
    total = len(combos)

    if total == 0:
        return None, "Nenhuma combinacao gerada. Verifique o grid."
    if total > 100000:
        return None, f"Grid muito grande ({total} combinacoes). Reduza os parametros."

    # Limpa cancel ANTES de marcar running — evita race com thread anterior
    _optimizer_cancel.clear()
    with _optimizer_lock:
        _optimizer_progress["current"] = 0
        _optimizer_progress["total"] = total
        _optimizer_progress["valid"] = 0
        _optimizer_progress["status"] = "running"

    base_extra = dict(fixed_params) if fixed_params else {"initial_capital": capital}
    results = []
    t0 = time.time()
    stopped = False

    # Timeout por combo: evita travar em uma combinacao que causa loop infinito.
    # Usa thread individual por combo (daemon=True) para que um combo travado
    # nao bloqueie os seguintes (ThreadPoolExecutor max_workers=1 bloquearia).
    _COMBO_TIMEOUT_S = 60

    for i, params in enumerate(combos):
        if _optimizer_cancel.is_set():
            stopped = True
            break
        try:
            run_params = {**base_extra, **params, "_fast": True}
            if prepare:
                run_params = prepare(dict(run_params))

            _result_box = [None]
            _error_box = [None]

            def _run_single(_df=df_data.copy(), _rp=run_params, _rb=_result_box, _eb=_error_box):
                try:
                    _rb[0] = module.run(_df, _rp)
                except Exception as _e:
                    _eb[0] = _e

            _t = threading.Thread(target=_run_single, daemon=True)
            _t.start()
            _t.join(timeout=_COMBO_TIMEOUT_S)

            if _t.is_alive():
                pass  # combo travado — daemon thread sera limpo no exit
            elif _error_box[0] is not None:
                pass  # combo falhou
            else:
                result = _result_box[0]
                row = _calc_optimizer_row(result, params, param_labels)
                if row and row["Trades"] >= min_trades:
                    results.append(row)
        except Exception:
            pass
        with _optimizer_lock:
            _optimizer_progress["current"] = i + 1
            _optimizer_progress["valid"] = len(results)

    elapsed = time.time() - t0
    tested = _optimizer_progress["current"]

    if not results:
        return {
            "results": [], "total_tested": tested, "valid_count": 0,
            "elapsed": round(elapsed, 1), "best": None, "stopped": stopped,
        }, None

    results_df = pd.DataFrame(results)
    from datetime import datetime as _dt
    results_df.insert(0, "Data", _dt.now().strftime("%Y-%m-%d %H:%M"))
    results_df.insert(1, "Ativo", symbol_label)
    results_df.insert(2, "Timeframe", interval_label)
    results_df = results_df.sort_values(rank_by, ascending=False).reset_index(drop=True)
    results_df.index += 1
    results_df.index.name = "Rank"

    DATA_DIR.mkdir(exist_ok=True)
    safe_symbol = symbol_label.replace(" ", "_").replace("/", "_")
    csv_filename = f"otimizacao_{safe_symbol}_{interval_label}.csv"
    csv_path = DATA_DIR / csv_filename
    results_df.to_csv(csv_path, index=True, index_label="Rank", encoding="utf-8-sig")

    top_results = results_df.head(top_n)
    all_records = []
    for idx, row_data in top_results.iterrows():
        record = {k: _safe(v) if isinstance(v, float) else v for k, v in row_data.to_dict().items()}
        record["Rank"] = idx
        all_records.append(record)

    best_row = results_df.iloc[0]
    best = {k: _safe(v) if isinstance(v, float) else v for k, v in best_row.to_dict().items()}
    csv_string = results_df.to_csv(index=True, index_label="Rank", encoding="utf-8-sig")

    metric_cols = ["Retorno (%)", "Max DD (%)", "Trades", "Win Rate (%)", "Profit Factor", "Sharpe", "Score"]
    param_cols = [param_labels.get(k, k) for k in sorted(typed_grid.keys())]

    return {
        "results": all_records,
        "total_tested": tested,
        "valid_count": len(results),
        "elapsed": round(elapsed, 1),
        "best": best,
        "csv_filename": csv_filename,
        "csv_data": csv_string,
        "symbol": symbol_label,
        "interval": interval_label,
        "metric_columns": metric_cols,
        "param_columns": param_cols,
        "stopped": stopped,
    }, None


def _optimizer_worker(df_data, module, grid_raw, capital, min_trades, rank_by, top_n, symbol_label, interval_label, fixed_params):
    """Executa a otimizacao em background thread e armazena o resultado."""
    try:
        data, err = _run_optimizer_compute(
            df_data, module, grid_raw, capital, min_trades, rank_by, top_n,
            symbol_label, interval_label, fixed_params,
        )
        if err:
            _optimizer_result_store["data"] = None
            _optimizer_result_store["error"] = err
            with _optimizer_lock:
                _optimizer_progress["status"] = "error"
        else:
            _optimizer_result_store["data"] = data
            _optimizer_result_store["error"] = None
            with _optimizer_lock:
                _optimizer_progress["status"] = "done"
    except Exception as e:
        import traceback as _tb
        _optimizer_result_store["data"] = None
        _optimizer_result_store["error"] = str(e) + "\n" + _tb.format_exc()
        with _optimizer_lock:
            _optimizer_progress["status"] = "error"


@app.route("/api/optimizer/result", methods=["GET"])
def api_optimizer_result():
    """Retorna o resultado armazenado da ultima otimizacao."""
    with _optimizer_lock:
        status = _optimizer_progress.get("status", "idle")
    if status in ("starting", "running"):
        return jsonify({"status": status}), 202
    if _optimizer_result_store["error"]:
        return jsonify({"error": _optimizer_result_store["error"]}), 500
    if _optimizer_result_store["data"] is None:
        return jsonify({"error": "Nenhum resultado disponivel"}), 404
    return jsonify(_optimizer_result_store["data"])


@app.route("/api/optimizer/run", methods=["POST"])
def api_optimizer_run():
    """Inicia a otimizacao em background e retorna imediatamente."""
    try:
        body = request.get_json(force=True) or {}
        strategy_file = body.get("strategy_file", "depaula")
        symbol = body.get("symbol", "BTC-USD")
        symbol_label = body.get("symbol_label", symbol)
        interval = body.get("interval", "1d")
        grid_raw = body.get("grid", {})
        capital = float(body.get("capital", 1000.0))
        min_trades = int(body.get("min_trades", 5))
        rank_by = body.get("rank_by", "Score")
        top_n = int(body.get("top_n", 20))

        if body.get("data_source", "asset") != "asset":
            return jsonify({"error": "Use upload CSV via multipart"}), 400

        # Merge backtest config so non-grid params match the user's backtest settings.
        # Grid combos override grid params; everything else comes from config.
        fixed_params = dict(body.get("config", {}))
        fixed_params["initial_capital"] = capital
        if body.get("cycle_long_months"):
            fixed_params["cycle_long_months"] = body["cycle_long_months"]
        if body.get("cycle_short_months"):
            fixed_params["cycle_short_months"] = body["cycle_short_months"]

        df_data = _download_data_safe(symbol, interval)

        # Filtra por data se o usuario definiu start/end
        sd = body.get("start_date")
        ed = body.get("end_date")
        if sd:
            df_data = df_data[df_data.index >= pd.Timestamp(sd)]
        if ed:
            df_data = df_data[df_data.index <= pd.Timestamp(ed)]
        if df_data.empty:
            return jsonify({"error": "Nenhum dado no intervalo de datas selecionado"}), 400

        module = _load_strategy(strategy_file)

        _optimizer_result_store["data"] = None
        _optimizer_result_store["error"] = None
        with _optimizer_lock:
            _optimizer_progress["status"] = "starting"

        t = threading.Thread(
            target=_optimizer_worker,
            args=(df_data, module, grid_raw, capital, min_trades, rank_by, top_n,
                  symbol_label, interval, fixed_params),
            daemon=True,
        )
        t.start()

        return jsonify({"status": "started"})

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/optimizer/run-csv", methods=["POST"])
def api_optimizer_run_csv():
    """Inicia otimizacao com CSV em background e retorna imediatamente."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Arquivo CSV obrigatorio"}), 400

        file_obj = request.files["file"]
        strategy_file = request.form.get("strategy_file", "depaula")
        grid_raw = json.loads(request.form.get("grid", "{}"))
        capital = float(request.form.get("capital", 1000.0))
        min_trades = int(request.form.get("min_trades", 5))
        rank_by = request.form.get("rank_by", "Score")
        top_n = int(request.form.get("top_n", 20))

        raw = file_obj.read()
        df_data = None
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text = raw.decode(enc)
                df_data = pd.read_csv(
                    io.StringIO(text), parse_dates=["Date"], index_col="Date"
                ).sort_index()
                break
            except Exception:
                continue

        if df_data is None:
            return jsonify({"error": "Nao foi possivel ler o CSV"}), 400

        # Merge backtest config so non-grid params match the user's settings
        config_raw = request.form.get("config")
        fixed_params = json.loads(config_raw) if config_raw else {}
        fixed_params["initial_capital"] = capital
        cycle_long = request.form.get("cycle_long_months")
        cycle_short = request.form.get("cycle_short_months")
        if cycle_long:
            fixed_params["cycle_long_months"] = json.loads(cycle_long)
        if cycle_short:
            fixed_params["cycle_short_months"] = json.loads(cycle_short)

        module = _load_strategy(strategy_file)

        _optimizer_result_store["data"] = None
        _optimizer_result_store["error"] = None
        with _optimizer_lock:
            _optimizer_progress["status"] = "starting"

        t = threading.Thread(
            target=_optimizer_worker,
            args=(df_data, module, grid_raw, capital, min_trades, rank_by, top_n,
                  file_obj.filename or "CSV", "-", fixed_params),
            daemon=True,
        )
        t.start()

        return jsonify({"status": "started"})

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500




def _skew_desc(val: float) -> str:
    if val < -0.5:
        return "cauda pesada para perdas"
    elif val < -0.1:
        return "leve vies negativo"
    elif val > 0.5:
        return "cauda pesada para ganhos"
    elif val > 0.1:
        return "leve vies positivo"
    return "neutra"


def _kurt_desc(val: float) -> str:
    if val > 3:
        return "caudas muito pesadas"
    elif val > 1:
        return "caudas pesadas"
    elif val < -0.5:
        return "caudas leves"
    return "normal"


# Prop Challenge
@app.route("/api/prop-challenge/simulate", methods=["POST"])
def api_prop_challenge_simulate():
    """
    Simula desafio de mesa prop usando trades de um backtest.
    Faz Monte Carlo reamostrando trades para estimar probabilidade de aprovacao.

    Body JSON:
    {
      "strategy_file": "depaula",
      "data_source": "asset",
      "symbol": "BTC-USD",
      "symbol_label": "Bitcoin",
      "interval": "1d",
      "config": { ... },
      "account_size": 50000,
      "num_sims": 1000
    }
    """
    try:
        body = request.get_json(force=True) or {}
        strategy_file = body.get("strategy_file", "depaula") or "depaula"
        cfg_dict = body.get("config", {})
        account_size = float(body.get("account_size", 50000))
        num_sims = max(100, min(int(body.get("num_sims", 1000)), 10000))
        symbol = body.get("symbol", "")
        symbol_label = body.get("symbol_label", symbol)
        interval_label = body.get("interval", "1d")

        if not symbol:
            return jsonify({"error": "symbol obrigatorio"}), 400
        if account_size <= 0:
            return jsonify({"error": "account_size deve ser positivo"}), 400

        # Forca initial_capital = account_size para o backtest
        cfg_dict["initial_capital"] = account_size

        df_data = _download_data_safe(symbol, interval_label)
        module = _load_strategy(strategy_file)
        result_dict = module.run(df_data.copy(), cfg_dict)

        trades = result_dict.get("trades", [])
        if len(trades) < 5:
            return jsonify({"error": "Poucos trades para simular (minimo 5)"}), 400

        pnl_pcts = [float(t["pnl_pct"]) for t in trades if t.get("pnl_pct") is not None]
        if len(pnl_pcts) < 5:
            return jsonify({"error": "Poucos trades validos para simular (minimo 5)"}), 400

        rng = np.random.default_rng()  # semente aleatoria — cada execucao produz resultado diferente

        # Regras do desafio
        phase1_target = 0.10   # +10%
        phase2_target = 0.05   # +5%
        max_loss = -0.10       # -10% total
        daily_max_loss = -0.05 # -5% em um dia

        def simulate_phase(pnl_pool, target, starting_balance):
            """Simula uma fase do desafio. Retorna (passed, final_balance, equity_curve)."""
            balance = starting_balance
            curve = [balance]

            # Limite generoso para evitar loop infinito sem subestimar estrategias lentas
            max_trades = max(1000, len(pnl_pool) * 20)
            for _ in range(max_trades):
                trade_pnl_pct = float(rng.choice(pnl_pool))
                pnl_value = balance * (trade_pnl_pct / 100.0)
                balance += pnl_value
                curve.append(balance)

                # Verifica perda por trade individual (equivale a perda diaria para timeframe diario)
                if trade_pnl_pct / 100.0 <= daily_max_loss:
                    return False, balance, curve

                # Verifica perda total acumulada desde o inicio da fase
                total_change = (balance - starting_balance) / starting_balance
                if total_change <= max_loss:
                    return False, balance, curve

                # Verifica se atingiu o alvo
                if total_change >= target:
                    return True, balance, curve

            # Nao atingiu em max_trades
            return False, balance, curve

        # Monte Carlo
        phase1_pass = 0
        phase2_pass = 0
        both_pass = 0
        phase1_curves = []
        phase2_curves = []
        phase1_results = []
        phase2_results = []

        for i in range(num_sims):
            # Fase 1
            p1_passed, p1_balance, p1_curve = simulate_phase(
                pnl_pcts, phase1_target, account_size
            )
            phase1_results.append({
                "passed": p1_passed,
                "final_balance": round(p1_balance, 2),
                "pnl_pct": round((p1_balance - account_size) / account_size * 100, 2),
                "num_trades": len(p1_curve) - 1,
            })

            if p1_passed:
                phase1_pass += 1
                # Fase 2: comeca com o saldo da conta original (reseta)
                p2_passed, p2_balance, p2_curve = simulate_phase(
                    pnl_pcts, phase2_target, account_size
                )
                phase2_results.append({
                    "passed": p2_passed,
                    "final_balance": round(p2_balance, 2),
                    "pnl_pct": round((p2_balance - account_size) / account_size * 100, 2),
                    "num_trades": len(p2_curve) - 1,
                })
                if p2_passed:
                    phase2_pass += 1
                    both_pass += 1

            # Salva ate 50 curvas de exemplo para o grafico
            if len(phase1_curves) < 50:
                phase1_curves.append([round(v, 2) for v in p1_curve])
            if p1_passed and len(phase2_curves) < 50:
                phase2_curves.append([round(v, 2) for v in p2_curve])

        # Estatisticas dos trades originais
        wins = [p for p in pnl_pcts if p > 0]
        losses = [p for p in pnl_pcts if p <= 0]
        win_rate = len(wins) / len(pnl_pcts) * 100 if pnl_pcts else 0
        avg_win = float(np.mean(wins)) if wins else 0
        avg_loss = float(np.mean(losses)) if losses else 0

        # Frequencia media de trades (dias entre trades)
        avg_days_between_trades = None
        trade_dates = []
        for t in trades:
            d = t.get("entry_date", "")
            if d:
                try:
                    trade_dates.append(pd.Timestamp(d))
                except Exception:
                    pass
        if len(trade_dates) >= 2:
            trade_dates.sort()
            total_span = (trade_dates[-1] - trade_dates[0]).days
            avg_days_between_trades = total_span / (len(trade_dates) - 1) if len(trade_dates) > 1 else None

        # Tempo estimado de aprovacao por fase (em dias)
        # Baseado na media de trades dos que passaram * frequencia de trades
        p1_passed_trades = [r["num_trades"] for r in phase1_results if r["passed"]]
        p2_passed_trades = [r["num_trades"] for r in phase2_results if r["passed"]]

        p1_avg_trades = float(np.mean(p1_passed_trades)) if p1_passed_trades else None
        p2_avg_trades = float(np.mean(p2_passed_trades)) if p2_passed_trades else None
        p1_median_trades = float(np.median(p1_passed_trades)) if p1_passed_trades else None
        p2_median_trades = float(np.median(p2_passed_trades)) if p2_passed_trades else None

        def _estimate_days(num_trades, avg_interval):
            if num_trades is None or avg_interval is None:
                return None
            return round(num_trades * avg_interval, 1)

        p1_est_days = _estimate_days(p1_median_trades, avg_days_between_trades)
        p2_est_days = _estimate_days(p2_median_trades, avg_days_between_trades)
        total_est_days = None
        if p1_est_days is not None and p2_est_days is not None:
            total_est_days = round(p1_est_days + p2_est_days, 1)

        return jsonify({
            "account_size": account_size,
            "num_sims": num_sims,
            "total_trades": len(trades),
            "symbol": symbol_label,
            "interval": interval_label,
            "strategy": strategy_file,
            "trade_stats": {
                "total": len(pnl_pcts),
                "win_rate": round(win_rate, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "avg_pnl": round(float(np.mean(pnl_pcts)), 4),
                "avg_days_between_trades": round(avg_days_between_trades, 1) if avg_days_between_trades else None,
            },
            "phase1": {
                "target_pct": phase1_target * 100,
                "max_loss_pct": abs(max_loss) * 100,
                "daily_max_loss_pct": abs(daily_max_loss) * 100,
                "passed": phase1_pass,
                "failed": num_sims - phase1_pass,
                "pass_rate": round(phase1_pass / num_sims * 100, 2),
                "avg_trades_to_pass": round(p1_avg_trades, 1) if p1_avg_trades else None,
                "median_trades_to_pass": round(p1_median_trades, 1) if p1_median_trades else None,
                "est_days": p1_est_days,
            },
            "phase2": {
                "target_pct": phase2_target * 100,
                "max_loss_pct": abs(max_loss) * 100,
                "daily_max_loss_pct": abs(daily_max_loss) * 100,
                "passed": phase2_pass,
                "failed": phase1_pass - phase2_pass,
                "pass_rate": round(phase2_pass / phase1_pass * 100, 2) if phase1_pass > 0 else 0,
                "avg_trades_to_pass": round(p2_avg_trades, 1) if p2_avg_trades else None,
                "median_trades_to_pass": round(p2_median_trades, 1) if p2_median_trades else None,
                "est_days": p2_est_days,
            },
            "overall": {
                "passed": both_pass,
                "pass_rate": round(both_pass / num_sims * 100, 2),
                "est_total_days": total_est_days,
            },
            "phase1_curves": phase1_curves,
            "phase2_curves": phase2_curves,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


if __name__ == "__main__":
    print("╔════════════════════════════════════════╗")
    print("║   Backtesting API — Flask Server       ║")
    print("║   http://localhost:5000                ║")
    print("╚════════════════════════════════════════╝")
    app.run(debug=True, port=5000, host="0.0.0.0", threaded=True)
