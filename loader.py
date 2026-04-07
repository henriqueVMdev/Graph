import pandas as pd
import io
from config import COLUMN_MAP, NUMERIC_COLUMNS, REQUIRED_COLUMNS, CSV_ENCODINGS

# Aliases: nomes alternativos de coluna -> nome esperado pelo COLUMN_MAP
# Cobre colunas geradas pelo otimizador (labels do CONFIG_SCHEMA)
COLUMN_ALIASES = {
    "Tipo": "MA",
    "Modo de Saída": "Saída",
    "Banda Sup (%)": "Banda (%)",
    "Ângulo Alta": "Ângulo",
    "Sair no Flat (cinza)": "Flat",
    "Tipo de Stop": "Stop",
    "ATR Mult": "Stop Param",
}


def load_csv(file) -> pd.DataFrame:
    """
    Carrega CSV de backtesting a partir de um path (str/Path) ou UploadedFile do Streamlit.
    Trata encoding, delimitador, validacao de colunas e conversao de tipos.
    """
    df = _read_with_fallback(file)
    df = _clean_columns(df)
    df = _normalize_aliases(df)
    _validate_columns(df)
    df = _rename_columns(df)
    df = _cast_numeric(df)
    return df


def _read_with_fallback(file) -> pd.DataFrame:
    """Tenta ler o CSV com diferentes encodings e delimitadores."""
    if hasattr(file, "read"):
        raw = file.read()
        if hasattr(file, "seek"):
            file.seek(0)
        return _parse_bytes(raw)

    with open(file, "rb") as f:
        raw = f.read()
    return _parse_bytes(raw)


def _parse_bytes(raw: bytes) -> pd.DataFrame:
    """Tenta parsear bytes do CSV com diferentes encodings e delimitadores.

    Detecta automaticamente se o CSV tem linhas de metadados antes do header
    real (procura a linha que contem as colunas obrigatorias).
    """
    for encoding in CSV_ENCODINGS:
        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

        for sep in [",", ";"]:
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep)
                if len(df.columns) > 1 and _has_required_cols(df):
                    return df
            except Exception:
                pass
            # Procura o header real pulando linhas de metadados
            df_skip = _try_skip_metadata(text, sep)
            if df_skip is not None:
                return df_skip

    raise ValueError(
        "Nao foi possivel ler o CSV. Verifique o encoding e o formato do arquivo."
    )


def _has_required_cols(df: pd.DataFrame) -> bool:
    """Verifica se o dataframe tem pelo menos algumas colunas obrigatorias."""
    cols = set(str(c).strip() for c in df.columns)
    checks = {"Retorno (%)", "Score", "Trades"}
    return len(checks & cols) >= 2


def _try_skip_metadata(text: str, sep: str) -> pd.DataFrame | None:
    """Tenta pular linhas de metadados no topo do CSV ate achar o header real."""
    lines = text.splitlines()
    for skip in range(1, min(20, len(lines))):
        try:
            df = pd.read_csv(io.StringIO("\n".join(lines[skip:])), sep=sep)
            if len(df.columns) > 1 and _has_required_cols(df):
                return df
        except Exception:
            continue
    return None


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espacos extras e colunas vazias geradas por delimitadores extras."""
    df.columns = df.columns.str.strip()
    # Remove colunas sem nome (Unnamed) geradas por ;; no final das linhas
    unnamed = [c for c in df.columns if str(c).startswith('Unnamed')]
    if unnamed:
        df = df.drop(columns=unnamed)
    return df


def _normalize_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas com nomes alternativos para os nomes esperados."""
    rename = {old: new for old, new in COLUMN_ALIASES.items() if old in df.columns and new not in df.columns}
    if rename:
        df = df.rename(columns=rename)
    return df


def _validate_columns(df: pd.DataFrame):
    """Valida que as colunas obrigatorias existem no DataFrame."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatorias ausentes no CSV: {', '.join(missing)}\n"
            f"Colunas encontradas: {', '.join(df.columns.tolist())}"
        )


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do portugues para ingles usando COLUMN_MAP."""
    rename_map = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    return df


def _cast_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas numericas, coercing erros para NaN."""
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
