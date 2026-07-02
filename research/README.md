# Pesquisa — MM9 Pullback Maker / Prop Challenge

Scripts que geraram os números do `RELATORIO_prop_challenge.md` (raiz do
projeto) e do `strategies/mm9_pullback_maker.yaml`.

## Reprodução

```bash
py research/download_data.py     # 12 perps Bybit: 15m 1 ano + funding -> research/data/
py research/research5_fix.py     # BTC..DOGE: 24h vs janela 19-00h BRT (fix de lookahead)
py research/research6_multi.py   # 12 simbolos na janela + ranking de TREINO
py research/prop_mc_combo.py     # fronteira solo/cesta x risco (MC, forward-only)
py research/combo_low_risk.py    # cestas grandes x risco baixo
```

## Regras de honestidade embutidas (não relaxar)

1. **Sem lookahead**: filtros no candle anterior; slope 1h só com horas
   FECHADAS (bucket disponível em `start + 1h` — nunca `resample+ffill` cru).
2. **Fill maker exige atravessar** a limite (`Low < limite`), não só tocar.
3. **TP e SL no mesmo candle = LOSS.**
4. Custos Bybit reais (maker 0.02% / taker 0.055%) + funding histórico real;
   cenário stress = funding 1.5x + slippage 0.05% nas saídas a mercado.
5. **Seleção de cesta APENAS com dados de TREINO** (70%); o Monte Carlo do
   prop challenge avalia apenas o FORWARD (30%).
6. Monte Carlo por **bootstrap de dias inteiros** (preserva a correlação
   entre trades do mesmo dia/símbolos simultâneos); violação da perda
   diária de -5% reprova.

`research/data/` é gerado e não deve ir para o git.
