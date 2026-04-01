from pathlib import Path

# Diretorios
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Numero de estrategias no top-N
TOP_N = 20

# Mapeamento de colunas: portugues -> ingles (interno)
COLUMN_MAP = {
    "Rank": "rank",
<<<<<<< HEAD
    "Data": "data",
    "Ativo": "ativo",
    "Timeframe": "timeframe",
=======
>>>>>>> b093fb05d3685ea15621ce05d0392ff27b4e24a1
    "Retorno (%)": "return_pct",
    "Max DD (%)": "max_dd_pct",
    "Trades": "trades",
    "Win Rate (%)": "win_rate_pct",
    "Avg Win (%)": "avg_win_pct",
    "Avg Loss (%)": "avg_loss_pct",
    "Profit Factor": "profit_factor",
    "Sharpe": "sharpe",
<<<<<<< HEAD
    "Sortino": "sortino",
    "Calmar": "calmar",
    "Omega": "omega",
    "Sterling": "sterling",
    "Burke": "burke",
=======
>>>>>>> b093fb05d3685ea15621ce05d0392ff27b4e24a1
    "Score": "score",
    "MA": "ma",
    "Período": "periodo",
    "Lookback": "lookback",
    "Ângulo": "angulo",
    "Saída": "saida",
    "Banda (%)": "banda_pct",
    "Alvo Fixo (%)": "alvo_fixo_pct",
    "Flat": "flat",
    "Stop": "stop",
    "Stop Param": "stop_param",
    "Pullback": "pullback",
    "Entry Zone": "entry_zone",
<<<<<<< HEAD
}

# Colunas de metricas conhecidas (usadas para distinguir params de metricas)
METRIC_COLUMNS = {
    "rank", "data", "ativo", "timeframe",
    "return_pct", "max_dd_pct", "trades", "win_rate_pct",
    "avg_win_pct", "avg_loss_pct", "profit_factor", "sharpe",
    "sortino", "calmar", "omega", "sterling", "burke", "score",
=======
    "Ativo": "ativo",
>>>>>>> b093fb05d3685ea15621ce05d0392ff27b4e24a1
}

# Colunas que devem ser numericas
NUMERIC_COLUMNS = [
    "rank", "return_pct", "max_dd_pct", "trades", "win_rate_pct",
    "avg_win_pct", "avg_loss_pct", "profit_factor", "sharpe", "score",
    "lookback", "angulo", "banda_pct", "alvo_fixo_pct", "stop_param",
]

# Colunas obrigatorias (subset minimo para os graficos funcionarem)
REQUIRED_COLUMNS = [
    "Retorno (%)", "Max DD (%)", "Trades", "Win Rate (%)",
    "Profit Factor", "Sharpe", "Score",
]

# Mapeamento reverso: ingles -> portugues (para exibicao)
COLUMN_DISPLAY = {v: k for k, v in COLUMN_MAP.items()}

# Encodings para tentativa de leitura do CSV
CSV_ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
