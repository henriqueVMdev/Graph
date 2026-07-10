"""Decision layer combining on-chain signals, divergences and source health."""
from __future__ import annotations
import time

_CACHE = {}

def analyze(symbol="BTC"):
    sym=(symbol or "BTC").upper().replace("-USD","")
    hit=_CACHE.get(sym)
    if hit and time.time()-hit[0]<900:return hit[1]
    if sym!="BTC":
        import seasonality_data
        s=seasonality_data.analyze(symbol)
        best=s["best_months"][0]; worst=s["worst_months"][0]
        out={"symbol":symbol,"signal":{"label":"NEUTRO","score":0,"confidence":25,
             "reasons":[f"Melhor mês histórico: {best['month']} ({best['avg_pct']}%)",
                        f"Pior mês histórico: {worst['month']} ({worst['avg_pct']}%)"]},
             "validation":{},"divergences":[],"health":[{"source":s['source'],"status":"ok"}],"ts":int(time.time()*1000)}
    else: out=_btc()
    _CACHE[sym]=(time.time(),out);return out

def _btc():
    from btc_onchain_metrics import payload
    from research.analyze_btc_onchain_signals import build_frame,score_history,summarize
    data=payload(); frame=score_history(build_frame(data)); summary=summarize(frame)
    ready_frame=frame[frame.model_ready]
    if ready_frame.empty: raise ValueError('métricas sem histórico comum suficiente')
    last=ready_frame.iloc[-1]; available=list((data.get("series") or {}).keys())
    reasons=[x.strip() for x in str(last.reasons).split(';') if x.strip()]
    divergences=[]
    price=frame.price
    specs=(("nupl","NUPL","absolute"),("sth_mvrv","STH-MVRV","from_one"),
           ("sth_sopr","STH-SOPR","from_one"),("exchange_whale_ratio","Whale Ratio","relative"),
           ("estimated_leverage_ratio","Leverage","relative"))
    for col,label,mode in specs:
        if col not in frame or frame[col].dropna().empty:continue
        pchg=price.pct_change(30,fill_method=None).iloc[-1]
        series=frame[col]
        if mode=="absolute": mchg=series.diff(30).iloc[-1]; threshold=.05; display=f"{mchg:+.3f}"
        elif mode=="from_one": mchg=(series-1).diff(30).iloc[-1]; threshold=.03; display=f"{mchg:+.3f} vs 1"
        else: mchg=series.pct_change(30,fill_method=None).iloc[-1]; threshold=.05; display=f"{mchg*100:+.1f}%"
        if pchg>0.05 and mchg < -threshold:divergences.append({"severity":"warning","title":f"Preço ↑ / {label} deteriorando","detail":f"30d: preço {pchg*100:.1f}%, métrica {display}"})
        if pchg<-0.05 and mchg > threshold:divergences.append({"severity":"opportunity","title":f"Preço ↓ / {label} melhorando","detail":f"30d: preço {pchg*100:.1f}%, métrica {display}"})
    unavailable=data.get("unavailable") or []
    health=[{"source":"Binance/Bybit/OKX Open Interest","status":"ok" if data.get("open_interest") else "error"},
            {"source":"Binance Pi Cycle","status":"ok" if data.get("pi_cycle") else "error"},
            {"source":"Glassnode/CryptoQuant","status":"ok" if available else "missing_credentials",
             "detail":f"{len(available)} séries ativas; {len(unavailable)} indisponíveis"}]
    hist=summary["historical"]
    validation={k:{"samples":v["events"],"valid_30d":v["valid_30d"],
                   "return_30d_pct":v["avg_forward_30d_pct"],
                   "win_rate_30d_pct":v["favorable_30d_pct"],
                   "return_90d_pct":v["avg_forward_90d_pct"]} for k,v in hist.items()}
    current_stats=hist.get(last.signal) or {}
    n=current_stats.get("valid_30d",0); rate=current_stats.get("favorable_30d_pct")
    # Shrink small samples toward 50%; this is historical calibration, not a forecast probability.
    confidence=(round(50+(rate-50)*n/(n+20),1)
                if last.signal in ("COMPRA","VENDA") and rate is not None and n else 0)
    scoring_ids={"nupl","sth_mvrv","sth_sopr","exchange_whale_ratio",
                 "estimated_leverage_ratio","retail_demand_30d"}
    coverage=round((1+len(scoring_ids & set(available)))/7*100,1)
    return {"symbol":"BTC","signal":{"label":last.signal,"score":float(last.score),
            "confidence":confidence,"confidence_basis":"30d favorable rate, shrunk toward 50%",
            "coverage_pct":coverage,"reasons":reasons,"date":str(ready_frame.index[-1].date()),"price":float(last.price)},
            "validation":validation,"divergences":divergences,"health":health,
            "liquidity":{"open_interest_usd":(data.get("open_interest") or {}).get("total_usd"),
                         "pi_top_distance_pct":float((last.price/frame.pi_350dma_x2.iloc[-1]-1)*100)},
            "unavailable":unavailable,"ts":int(time.time()*1000)}
