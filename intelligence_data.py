"""Decision layer combining on-chain signals, divergences and source health.

BTC usa o modelo on-chain profundo (research/analyze_btc_onchain_signals).
Demais ativos cruzam as fontes que o app já coleta: técnica (yfinance),
sazonalidade, e — para cripto — funding/OI de perps e perfil CoinGecko.
Cada fator vota -1/0/+1; o cruzamento entre fatores gera as divergências e a
validação usa o histórico do próprio ativo (forward returns), não opinião.
"""
from __future__ import annotations
import time

_CACHE = {}


def analyze(symbol="BTC"):
    sym = (symbol or "BTC").upper().replace("-USD", "")
    hit = _CACHE.get(sym)
    if hit and time.time() - hit[0] < 900:
        return hit[1]
    out = _btc() if sym == "BTC" else _generic(symbol, sym)
    _CACHE[sym] = (time.time(), out)
    return out


def _fwd_stats(close, mask, days=21):
    """Retorno médio e taxa de acerto N dias à frente quando a condição valeu."""
    fwd = (close.shift(-days) / close - 1).where(mask).dropna()
    if len(fwd) < 20:
        return None
    return {"samples": int(mask.sum()), "valid_30d": int(len(fwd)),
            "return_30d_pct": round(float(fwd.mean() * 100), 2),
            "win_rate_30d_pct": round(float((fwd > 0).mean() * 100), 1),
            "return_90d_pct": None}


def _generic(raw, sym):
    import pandas as pd
    import yfinance as yf
    from technical_data import _sma, _rsi
    from onchain_data import _CG_IDS

    crypto = sym in _CG_IDS or "-USD" in (raw or "").upper()
    if crypto:
        yf_sym = f"{sym}-USD"
    else:
        try:
            import tradfi_data
            yf_sym = tradfi_data.resolve(sym)
        except Exception:
            yf_sym = sym

    factors, reasons, divergences, health = [], [], [], []
    validation = {}
    close = price = ret30 = None
    trend_up = None

    # ── fator 1-3: técnica (tendência, momentum, RSI) ────────────────────
    try:
        h = yf.Ticker(yf_sym).history(period="5y", interval="1d", auto_adjust=True)
        close = h["Close"].dropna()
        if len(close) < 220:
            raise ValueError(f"histórico insuficiente ({len(close)} pregões)")
        health.append({"source": f"Yahoo Finance ({yf_sym})", "status": "ok"})
    except Exception as e:
        close = None
        health.append({"source": f"Yahoo Finance ({yf_sym})", "status": "error",
                       "detail": str(e)[:80]})

    if close is not None:
        price = float(close.iloc[-1])
        sma200 = _sma(close, 200)
        rsi_series = _rsi(close)
        rsi = float(rsi_series.iloc[-1])
        ret30 = float(close.pct_change(21, fill_method=None).iloc[-1] * 100)
        above = close > sma200
        trend_up = bool(above.iloc[-1])

        factors.append(1 if trend_up else -1)
        reasons.append(f"Tendência: preço {'acima' if trend_up else 'abaixo'} da SMA200 "
                       f"({(price / float(sma200.iloc[-1]) - 1) * 100:+.1f}%)")
        valid = sma200.notna()
        s = _fwd_stats(close, (above if trend_up else ~above) & valid)
        if s:
            validation["Tendência atual (fwd 30d)"] = s

        factors.append(1 if ret30 > 5 else -1 if ret30 < -5 else 0)
        reasons.append(f"Momentum 30d: {ret30:+.1f}%")

        factors.append(1 if rsi < 30 else -1 if rsi > 70 else 0)
        reasons.append(f"RSI(14): {rsi:.0f}"
                       + (" — sobrevendido" if rsi < 30 else " — sobrecomprado" if rsi > 70 else ""))
        if rsi > 70 or rsi < 30:
            s = _fwd_stats(close, rsi_series > 70 if rsi > 70 else rsi_series < 30)
            if s:
                validation[f"RSI {'>70' if rsi > 70 else '<30'} (fwd 30d)"] = s
        if rsi > 70 and ret30 > 5:
            divergences.append({"severity": "warning",
                                "title": "Preço esticado com RSI sobrecomprado",
                                "detail": f"30d {ret30:+.1f}%, RSI {rsi:.0f}"})
        if rsi < 30 and ret30 < -5:
            divergences.append({"severity": "opportunity",
                                "title": "Queda forte com RSI sobrevendido",
                                "detail": f"30d {ret30:+.1f}%, RSI {rsi:.0f}"})

    # ── fator 4: sazonalidade do mês corrente ────────────────────────────
    try:
        import seasonality_data
        sea = seasonality_data.analyze(yf_sym)
        month = pd.Timestamp.now("UTC").month
        m = next(x for x in sea["monthly_stats"] if x["month"] == month)
        if m["avg_pct"] is not None and m["samples"] >= 5:
            win = m["win_rate_pct"] or 50
            factors.append(1 if m["avg_pct"] > 0 and win >= 55
                           else -1 if m["avg_pct"] < 0 and win <= 45 else 0)
            reasons.append(f"Sazonalidade do mês: média {m['avg_pct']:+.2f}%, "
                           f"acerto {win:.0f}% em {m['samples']} anos")
            validation["Sazonalidade (mês atual)"] = {
                "samples": m["samples"], "valid_30d": m["samples"],
                "return_30d_pct": m["avg_pct"], "win_rate_30d_pct": win,
                "return_90d_pct": None}
            if trend_up is True and win <= 40:
                divergences.append({"severity": "warning",
                                    "title": "Tendência de alta em mês historicamente fraco",
                                    "detail": f"acerto histórico de {win:.0f}% no mês {month}"})
            if trend_up is False and win >= 60:
                divergences.append({"severity": "opportunity",
                                    "title": "Tendência de baixa em mês historicamente forte",
                                    "detail": f"acerto histórico de {win:.0f}% no mês {month}"})
        health.append({"source": sea["source"] + " (sazonalidade)", "status": "ok"})
    except Exception as e:
        health.append({"source": "Sazonalidade", "status": "error", "detail": str(e)[:80]})

    # ── fator 5 (cripto): funding contrário + atividade dev ─────────────
    oi_usd = None
    if crypto:
        try:
            import onchain_data
            c = onchain_data.coin(sym)
            d = c.get("deriv") or {}
            f = d.get("funding_pct")
            oi_usd = d.get("oi_usd")
            if f is not None:
                factors.append(1 if f < 0 else -1 if f >= 0.03 else 0)
                reasons.append(f"Funding perp Bybit: {f:+.4f}%/8h"
                               + (" — shorts pagando (contrário altista)" if f < 0
                                  else " — longs lotados (contrário baixista)" if f >= 0.03 else ""))
                if ret30 is not None:
                    if f >= 0.03 and ret30 > 10:
                        divergences.append({"severity": "warning",
                                            "title": "Alta sustentada por alavancagem comprada cara",
                                            "detail": f"funding {f:+.4f}%/8h com preço {ret30:+.1f}% em 30d"})
                    if f < 0 and ret30 < -10:
                        divergences.append({"severity": "opportunity",
                                            "title": "Queda com shorts pagando funding",
                                            "detail": f"funding {f:+.4f}%/8h com preço {ret30:+.1f}% em 30d"})
            dev = (c.get("profile") or {}).get("dev") or {}
            if dev.get("commits_4w") == 0:
                divergences.append({"severity": "warning",
                                    "title": "Atividade de desenvolvimento zerada (4 semanas)",
                                    "detail": "CoinGecko developer data — projeto pode estar abandonado"})
            errs = c.get("errors") or []
            health.append({"source": "CoinGecko/Bybit (cripto)",
                           "status": "ok" if not errs else "partial",
                           "detail": "; ".join(errs)[:80]})
        except Exception as e:
            health.append({"source": "CoinGecko/Bybit (cripto)", "status": "error",
                           "detail": str(e)[:80]})

    # ── score = soma dos votos; confiança = concordância entre fatores ──
    if not factors:
        raise ValueError(f"nenhuma fonte disponível para {sym}")
    score = sum(factors)
    n = len(factors)
    expected = 5 if crypto else 4
    label = "COMPRA" if score >= 2 else "VENDA" if score <= -2 else "NEUTRO"
    return {"symbol": sym,
            "signal": {"label": label, "score": float(score),
                       "confidence": round(abs(score) / n * 100, 1),
                       "confidence_basis": "concordância entre os fatores disponíveis",
                       "coverage_pct": round(n / expected * 100, 1),
                       "reasons": reasons, "price": price,
                       "date": str(close.index[-1].date()) if close is not None else None},
            "validation": validation, "divergences": divergences, "health": health,
            "liquidity": {"open_interest_usd": oi_usd, "pi_top_distance_pct": None},
            "ts": int(time.time() * 1000)}


def _btc():
    from btc_onchain_metrics import payload
    from research.analyze_btc_onchain_signals import build_frame, score_history, summarize
    data = payload()
    frame = score_history(build_frame(data))
    summary = summarize(frame)
    ready_frame = frame[frame.model_ready]
    if ready_frame.empty:
        raise ValueError('métricas sem histórico comum suficiente')
    last = ready_frame.iloc[-1]
    available = list((data.get("series") or {}).keys())
    reasons = [x.strip() for x in str(last.reasons).split(';') if x.strip()]
    divergences = []
    price = frame.price
    specs = (("nupl", "NUPL", "absolute"), ("sth_mvrv", "STH-MVRV", "from_one"),
             ("sth_sopr", "STH-SOPR", "from_one"), ("exchange_whale_ratio", "Whale Ratio", "relative"),
             ("estimated_leverage_ratio", "Leverage", "relative"))
    for col, label, mode in specs:
        if col not in frame or frame[col].dropna().empty:
            continue
        pchg = price.pct_change(30, fill_method=None).iloc[-1]
        series = frame[col]
        if mode == "absolute":
            mchg = series.diff(30).iloc[-1]; threshold = .05; display = f"{mchg:+.3f}"
        elif mode == "from_one":
            mchg = (series - 1).diff(30).iloc[-1]; threshold = .03; display = f"{mchg:+.3f} vs 1"
        else:
            mchg = series.pct_change(30, fill_method=None).iloc[-1]; threshold = .05; display = f"{mchg * 100:+.1f}%"
        if pchg > 0.05 and mchg < -threshold:
            divergences.append({"severity": "warning", "title": f"Preço ↑ / {label} deteriorando",
                                "detail": f"30d: preço {pchg * 100:.1f}%, métrica {display}"})
        if pchg < -0.05 and mchg > threshold:
            divergences.append({"severity": "opportunity", "title": f"Preço ↓ / {label} melhorando",
                                "detail": f"30d: preço {pchg * 100:.1f}%, métrica {display}"})
    unavailable = data.get("unavailable") or []
    health = [{"source": "Binance/Bybit/OKX Open Interest", "status": "ok" if data.get("open_interest") else "error"},
              {"source": "Binance Pi Cycle", "status": "ok" if data.get("pi_cycle") else "error"},
              {"source": "Glassnode/CryptoQuant", "status": "ok" if available else "missing_credentials",
               "detail": f"{len(available)} séries ativas; {len(unavailable)} indisponíveis"}]
    hist = summary["historical"]
    validation = {k: {"samples": v["events"], "valid_30d": v["valid_30d"],
                      "return_30d_pct": v["avg_forward_30d_pct"],
                      "win_rate_30d_pct": v["favorable_30d_pct"],
                      "return_90d_pct": v["avg_forward_90d_pct"]} for k, v in hist.items()}
    current_stats = hist.get(last.signal) or {}
    n = current_stats.get("valid_30d", 0); rate = current_stats.get("favorable_30d_pct")
    # Shrink small samples toward 50%; this is historical calibration, not a forecast probability.
    confidence = (round(50 + (rate - 50) * n / (n + 20), 1)
                  if last.signal in ("COMPRA", "VENDA") and rate is not None and n else 0)
    scoring_ids = {"nupl", "sth_mvrv", "sth_sopr", "exchange_whale_ratio",
                   "estimated_leverage_ratio", "retail_demand_30d"}
    coverage = round((1 + len(scoring_ids & set(available))) / 7 * 100, 1)
    return {"symbol": "BTC", "signal": {"label": last.signal, "score": float(last.score),
            "confidence": confidence, "confidence_basis": "30d favorable rate, shrunk toward 50%",
            "coverage_pct": coverage, "reasons": reasons, "date": str(ready_frame.index[-1].date()), "price": float(last.price)},
            "validation": validation, "divergences": divergences, "health": health,
            "liquidity": {"open_interest_usd": (data.get("open_interest") or {}).get("total_usd"),
                          "pi_top_distance_pct": float((last.price / frame.pi_350dma_x2.iloc[-1] - 1) * 100)},
            "unavailable": unavailable, "ts": int(time.time() * 1000)}


if __name__ == "__main__":
    for s in ("PETR4.SA", "ETH", "GC=F"):
        r = analyze(s)
        sig = r["signal"]
        assert sig["label"] in ("COMPRA", "VENDA", "NEUTRO") and len(sig["reasons"]) >= 2, r
        print(f"{s}: {sig['label']} score={sig['score']} conf={sig['confidence']}% "
              f"cobertura={sig['coverage_pct']}% | {len(r['divergences'])} divergências | "
              f"{len(r['validation'])} validações")
