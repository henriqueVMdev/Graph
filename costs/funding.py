"""
Obtenção de funding rate histórico via CCXT (interface unificada) + cache local.

Confiar no funding rate que o endpoint retorna — não recalcular (regra crítica #7).
O intervalo de funding NÃO é assumido: vem dos timestamps reais do histórico.
Funding histórico não muda → cacheado em Parquet por (exchange, symbol).
"""

from __future__ import annotations

import os
import re
from decimal import Decimal

import pandas as pd

from .models import FundingEvent

_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache")


def get_exchange(name: str):
    import ccxt
    cfg = {"options": {"defaultType": "swap"}, "enableRateLimit": True}
    if name == "binance":
        return ccxt.binanceusdm({"enableRateLimit": True})
    if name == "bybit":
        return ccxt.bybit(cfg)
    if name == "okx":
        return ccxt.okx(cfg)
    raise ValueError(f"exchange não suportada: {name}")


def fetch_funding(exchange, symbol: str, since_ms: int, until_ms: int):
    """Pagina o histórico de funding até cobrir [since, until].
    Retorna lista de {'timestamp', 'fundingRate'} ordenada por tempo, sem duplicatas."""
    out = []
    cursor = since_ms
    while cursor < until_ms:
        batch = exchange.fetch_funding_rate_history(symbol, since=cursor, limit=100)
        if not batch:
            break
        out.extend(batch)
        cursor = batch[-1]["timestamp"] + 1
        if len(batch) < 100:
            break

    seen, result = set(), []
    for r in sorted(out, key=lambda x: x["timestamp"]):
        ts = r["timestamp"]
        if ts in seen or not (since_ms <= ts <= until_ms):
            continue
        seen.add(ts)
        result.append({"timestamp": ts, "fundingRate": r["fundingRate"]})
    return result


def _cache_path(exchange: str, symbol: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", f"{exchange}_{symbol}")
    return os.path.join(_CACHE_DIR, f"funding_{safe}.parquet")


def _read_cache(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    return pd.DataFrame(columns=["timestamp", "fundingRate"])


def get_funding_events(exchange_name: str, symbol: str, since_ms: int, until_ms: int,
                       use_cache: bool = True) -> list:
    """Devolve list[FundingEvent] cobrindo [since, until], usando cache local.
    Só baixa o que faltar e persiste o resultado mesclado."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = _cache_path(exchange_name, symbol)
    cached = _read_cache(path) if use_cache else pd.DataFrame(columns=["timestamp", "fundingRate"])

    have = set(cached["timestamp"].tolist()) if not cached.empty else set()
    covered = (not cached.empty
               and cached["timestamp"].min() <= since_ms
               and cached["timestamp"].max() >= until_ms)

    if not covered:
        ex = get_exchange(exchange_name)
        fetched = fetch_funding(ex, symbol, since_ms, until_ms)
        new_rows = [r for r in fetched if r["timestamp"] not in have]
        if new_rows:
            cached = pd.concat([cached, pd.DataFrame(new_rows)], ignore_index=True)
            cached = cached.drop_duplicates(subset="timestamp").sort_values("timestamp")
            if use_cache:
                cached.to_parquet(path, index=False)

    if cached.empty:
        return []

    window = cached[(cached["timestamp"] >= since_ms) & (cached["timestamp"] <= until_ms)]
    window = window.sort_values("timestamp")
    return [FundingEvent(timestamp=int(r.timestamp), rate=Decimal(str(r.fundingRate)))
            for r in window.itertuples(index=False)]


def funding_events_from_raw(raw: list) -> list:
    """Converte uma lista de dicts {'timestamp','fundingRate'} em FundingEvent."""
    return [FundingEvent(timestamp=int(r["timestamp"]),
                         rate=Decimal(str(r["fundingRate"]))) for r in raw]
