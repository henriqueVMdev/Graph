import pandas as pd
import io
from config import COLUMN_MAP, NUMERIC_COLUMNS, REQUIRED_COLUMNS, CSV_ENCODINGS


def load_csv(file) -> pd.DataFrame:
    """
    Carrega CSV de backtesting a partir de um path (str/Path) ou UploadedFile do Streamlit.
    Trata encoding, delimitador, validacao de colunas e conversao de tipos.
    """
    df = _read_with_fallback(file)
    df = _clean_columns(df)
    _validate_columns(df)
    df = _rename_columns(df)
    df = _cast_numeric(df)
    return df


def _read_with_fallback(file) -> pd.DataFrame:
    """Tenta ler o CSV com diferentes encodings e delimitadores."""
    # Se for UploadedFile do Streamlit, le o conteudo como bytes
    if hasattr(file, "read"):
        raw = file.read()
        if hasattr(file, "seek"):
            file.seek(0)
        return _parse_bytes(raw)

    # Se for path de arquivo
    with open(file, "rb") as f:
        raw = f.read()
    return _parse_bytes(raw)


def _parse_bytes(raw: bytes) -> pd.DataFrame:
    """Tenta parsear bytes do CSV com diferentes encodings e delimitadores."""
    for encoding in CSV_ENCODINGS:
        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

        # Tenta com virgula primeiro, depois ponto-e-virgula
        for sep in [",", ";"]:
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue

    raise ValueError(
        "Nao foi possivel ler o CSV. Verifique o encoding e o formato do arquivo."
    )


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espacos extras dos nomes das colunas."""
    df.columns = df.columns.str.strip()
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
