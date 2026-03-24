"""
Flask REST API — Backtesting Strategy Dashboard
Substitui o Streamlit como servidor. Mantém toda lógica Python intacta.

Iniciar: python server.py
"""

import io
import json
import math
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

    # yfinance não suporta intervalo "4h" — converte para "1h"
    yf_interval = interval if interval != "4h" else "1h"

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period="max", interval=yf_interval)

    if df.empty:
        raise ValueError(f"Nenhum dado retornado para '{yf_symbol}' (intervalo={yf_interval})")

    # Garante colunas padrão
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Remove timezone do índice (backtesting.py não lida com tz-aware index em todos os cenários)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

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
    df = df.where(pd.notnull(df), None)
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
        summary["avg_return"] = _safe(float(df["return_pct"].mean()))
    else:
        summary["avg_return"] = None
    if "sharpe" in df.columns and len(df) > 0:
        summary["avg_sharpe"] = _safe(float(df["sharpe"].mean()))
    else:
        summary["avg_sharpe"] = None
    if "score" in df.columns and len(df) > 0:
        summary["best_score"] = _safe(float(df["score"].max()))
    else:
        summary["best_score"] = None
    return summary


def _build_charts(df: pd.DataFrame) -> dict:
    """Gera os 3 gráficos scatter como JSON Plotly."""
    charts = {}
    if all(c in df.columns for c in ["max_dd_pct", "return_pct", "score"]):
        fig = plot_return_vs_drawdown(df)
        charts["return_vs_drawdown"] = json.loads(fig.to_json())
    if all(c in df.columns for c in ["sharpe", "return_pct", "win_rate_pct"]):
        fig = plot_return_vs_sharpe(df)
        charts["return_vs_sharpe"] = json.loads(fig.to_json())
    if all(c in df.columns for c in ["trades", "return_pct", "profit_factor"]):
        fig = plot_return_vs_trades(df)
        charts["return_vs_trades"] = json.loads(fig.to_json())
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
                    series.index = series.index.tz_localize(None).normalize()
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
            skew_val = float(ret.skew())
            kurt_val = float(ret.kurtosis())
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
        from monte_carlo_project.monte_carlo      import MonteCarlo
        from monte_carlo_project.permutation_test import PermutationTestEquity
        from monte_carlo_project.report           import generate as gen_report
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

        ic = float(metrics_in.get("initial_capital", eq_values[0]))

        # ── Monte Carlo ──────────────────────────────────────────────────────
        mc = MonteCarlo(initial_capital=ic, seed=seed)

        reshuffle_r        = mc.reshuffle(trades,        n_sims=n_sims)
        resample_r         = mc.resample(trades,         n_sims=n_sims)
        randomized_r       = mc.randomized(trades,       n_sims=n_sims)
        return_alteration_r = mc.return_alteration(eq_values, eq_dates, n_sims=n_sims)

        # ── Permutation Test (equity-curve based) ────────────────────────────
        pt          = PermutationTestEquity(seed=seed)
        perm_result = pt.run(eq_values, trades, n_perms=n_perms)

        # ── Métricas originais enriquecidas ──────────────────────────────────
        arr_eq    = np.array(eq_values, dtype=float)
        rets_eq   = np.diff(arr_eq) / arr_eq[:-1]
        sharpe    = float(rets_eq.mean() / rets_eq.std() * np.sqrt(252)) if len(rets_eq) > 1 and rets_eq.std() > 0 else 0.0

        pnls      = [t.get("pnl_pct", 0) for t in trades]
        wins      = [p for p in pnls if p > 0]
        losses    = [p for p in pnls if p <= 0]
        win_rate  = float(metrics_in.get("win_rate", len(wins) / len(pnls) * 100 if pnls else 0))
        avg_win   = float(np.mean(wins))   if wins   else 0.0
        avg_loss  = float(np.mean(losses)) if losses else 0.0
        expectancy = win_rate / 100 * avg_win + (1 - win_rate / 100) * avg_loss

        original = {
            **{k: _safe(v) for k, v in metrics_in.items()},
            "sharpe":     _safe(sharpe),
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

    # Sharpe simplificado
    pnls = [t["pnl_pct"] for t in trades if t.get("pnl_pct") is not None]
    if len(pnls) > 1 and np.std(pnls) > 0:
        sharpe = float(np.mean(pnls) / np.std(pnls) * np.sqrt(len(pnls)))
    else:
        sharpe = 0.0

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


def _run_optimizer_generic(df_data, module, grid_raw, capital, min_trades, rank_by, top_n, symbol_label, interval_label):
    """Logica generica de otimizacao que funciona com qualquer estrategia."""
    import time

    schema = getattr(module, "CONFIG_SCHEMA", [])
    validator = getattr(module, "is_valid_config", None)
    prepare = getattr(module, "prepare_optimizer_params", None)
    param_labels = _build_param_labels(schema)

    typed_grid = _parse_grid_generic(grid_raw, schema)
    combos = _generate_combos(typed_grid, validator)
    total = len(combos)

    if total == 0:
        return jsonify({"error": "Nenhuma combinacao gerada. Verifique o grid."}), 400
    if total > 100000:
        return jsonify({"error": f"Grid muito grande ({total} combinacoes). Reduza os parametros."}), 400

    # Adicionar capital aos parametros se a estrategia suportar
    base_extra = {"initial_capital": capital}

    results = []
    t0 = time.time()

    for params in combos:
        try:
            run_params = {**base_extra, **params}
            if prepare:
                run_params = prepare(dict(run_params))
            result = module.run(df_data.copy(), run_params)
            row = _calc_optimizer_row(result, params, param_labels)
            if row and row["Trades"] >= min_trades:
                results.append(row)
        except Exception:
            pass

    elapsed = time.time() - t0

    if not results:
        return jsonify({
            "results": [], "total_tested": total, "valid_count": 0,
            "elapsed": round(elapsed, 1), "best": None,
        })

    results_df = pd.DataFrame(results)
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

    # Colunas de metricas e parametros para o frontend
    metric_cols = ["Retorno (%)", "Max DD (%)", "Trades", "Win Rate (%)", "Profit Factor", "Sharpe", "Score"]
    param_cols = [param_labels.get(k, k) for k in sorted(typed_grid.keys())]

    return jsonify({
        "results": all_records,
        "total_tested": total,
        "valid_count": len(results),
        "elapsed": round(elapsed, 1),
        "best": best,
        "csv_filename": csv_filename,
        "csv_data": csv_string,
        "symbol": symbol_label,
        "interval": interval_label,
        "metric_columns": metric_cols,
        "param_columns": param_cols,
    })


@app.route("/api/optimizer/run", methods=["POST"])
def api_optimizer_run():
    """Roda a otimizacao completa para qualquer estrategia."""
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

        df_data = _download_data_safe(symbol, interval)
        module = _load_strategy(strategy_file)

        return _run_optimizer_generic(
            df_data, module, grid_raw, capital, min_trades, rank_by, top_n,
            symbol_label, interval,
        )

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/optimizer/run-csv", methods=["POST"])
def api_optimizer_run_csv():
    """Roda otimizacao com dados de CSV upload para qualquer estrategia."""
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

        module = _load_strategy(strategy_file)

        return _run_optimizer_generic(
            df_data, module, grid_raw, capital, min_trades, rank_by, top_n,
            file_obj.filename or "CSV", "-",
        )

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


if __name__ == "__main__":
    print("╔════════════════════════════════════════╗")
    print("║   Backtesting API — Flask Server       ║")
    print("║   http://localhost:5000                ║")
    print("╚════════════════════════════════════════╝")
    app.run(debug=True, port=5000, host="0.0.0.0")
