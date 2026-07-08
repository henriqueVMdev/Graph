# MM9 Pullback Maker — documentação da estratégia

**Ativo/timeframe:** perps USDT na Bybit, gráfico de **15 minutos** · long e short
**Implementações:** `strategies/mm9_pullback.py` (app) · `mm9_pullback_maker.pine` (TradingView) · parâmetros em `mm9_pullback_maker.yaml`
**Validação:** 1 ano de dados Bybit (jul/2025→jul/2026), fees + funding reais, sem lookahead — forward OOS BTC: WR 81,5%, PF 1,66, +0,148%/trade na janela 19-00h.

---

## 1. A ideia em uma frase

Em tendência estabelecida, **comprar o recuo até a média de 9 períodos com ordem limite (maker)** e sair rápido num alvo curto — cobrando o "pedágio" de quem atravessa o spread, em vez de pagá-lo.

## 2. Por que isso funciona (a origem do edge)

A pesquisa que originou a estratégia descobriu duas coisas, nesta ordem:

1. **O cruzamento puro da MM9 não tem edge.** Entrar a mercado quando o preço cruza a média de 9 ganha 73% das vezes num alvo/stop assimétrico — mas o acaso ganha 75% com a mesma geometria. Com taxa taker nas duas pontas (0,11% ida-volta na Bybit), **tudo** ficou negativo. O sinal, sozinho, é ruído.

2. **O que sobrevive aos custos é o *jeito de entrar*, não o sinal.** Trocando a entrada a mercado por uma **limite descansando na EMA9**, três coisas mudam de uma vez:
   - você paga taxa **maker** (0,02%) em vez de taker (0,055%) na entrada — e no alvo também;
   - você compra o recuo **abaixo** do preço corrente, ou seja, entra melhor por construção;
   - você só é executado quando alguém *vende com agressão* até a sua ordem — capturando o desconto de liquidez imediata que esse vendedor paga.

   O edge líquido da estratégia (~+0,15%/trade no forward) tem a mesma ordem de grandeza da economia de custos + desconto de fill. **É uma estratégia de microestrutura disfarçada de estratégia de tendência**: a tendência serve para escolher o lado; o dinheiro vem de ser maker no lugar certo.

Por isso a regra de ouro operacional: **executada com ordens a mercado, esta estratégia não existe.** Qualquer implementação (bot, TV, manual) precisa de entrada limite e alvo limite.

## 3. Anatomia de um trade (long; short é o espelho)

### 3.1 Filtros — decidem SE e PARA QUE LADO (avaliados no candle fechado)

| # | Filtro | Regra (long) | Por quê |
|---|---|---|---|
| 1 | Tendência 15m | EMA50 > EMA200 **e** Close > EMA200 | só compra recuo em tendência de alta estrutural; elimina pullbacks em mercado lateral/baixista, onde "recuo" costuma ser o início da reversão |
| 2 | Tendência 1h | EMA9 do 1h subindo (vs hora anterior) | o timeframe acima precisa concordar; recuo de 15m contra o fluxo do 1h é onde os stops moram. **Anti-lookahead**: usa somente horas FECHADAS — o bucket do 1h só é conhecido 1h depois de abrir (o resample+ffill ingênuo vaza até 45min de futuro e inflava o resultado ~40%) |
| 3 | Preço esticado | Close > EMA9 | garante que existe recuo a ser comprado: a limite fica ABAIXO do mercado. Sem isso a ordem seria marketável (viraria taker) |
| 4 | Volatilidade | rank do ATR14% ≥ 0,5 na janela de 4 dias (384 barras) | o alvo é 0,5% — em vol baixa o preço não anda isso em poucas velas e o trade morre no time-stop; em vol alta o recuo até a EMA9 acontece E o repique alcança o alvo. Seleciona o regime em que a geometria fecha |
| 5 | Horário | entrada apenas com fill entre **19h e 00h Brasília** (22h–03h UTC) | janela validada empiricamente: melhora o PF de 1,16 (24h) para 1,66 no BTC. Coincide com o fim do pregão de NY + rolagem para a Ásia, período de repique técnico com menos fluxo direcional. Vale SÓ para entradas; as saídas descansam na exchange 24/7 |

### 3.2 Gatilho e entrada

- Com todos os filtros verdes no candle recém-fechado, coloca-se **ordem limite de compra no valor da EMA9 daquele candle**.
- **Validade de 1 candle (15 min)**: se o próximo candle não executar, a ordem é reposicionada na EMA9 nova (se o setup persistir) ou cancelada (se sumiu). A limite "persegue" a média, nunca fica órfã.
- **Fill exige o preço ATRAVESSAR a limite** (Low < limite, estrito) — não basta encostar. É a simulação honesta da fila do book: quem encosta e volta raramente executa uma maker recém-colocada. (O TradingView preenche no toque; por isso ele é estruturalmente otimista aqui.)
- Na Bybit real, a ordem vai como **PostOnly** (garante maker; se fosse cruzar o book, é rejeitada em vez de virar taker).

### 3.3 Saídas — três, com hierarquia

| Saída | Mecânica | Tipo | Racional |
|---|---|---|---|
| **Alvo** +0,5% | ordem limite anexada, server-side | maker | curto de propósito: o repique pós-recuo em vol alta percorre 0,5% com frequência; ~15% dos trades saem no MESMO candle da entrada — e esses fills rápidos são >50% do lucro total |
| **Stop** −1,5% | stop market anexado, server-side | taker | 3× o alvo. Parece invertido, mas com WR ~77-81% a matemática fecha: 0,77×0,5 − 0,23×1,5 > 0. O stop largo evita ser tirado pelo ruído do 15m antes do repique |
| **Time-stop** 48 barras (12h) | fecha a mercado no fechamento da 48ª vela | taker | trade que não foi nem no alvo nem no stop em 12h perdeu a tese (o regime de vol que o justificou acabou); libera capital e corta a cauda de funding |
| Regra de desempate | **TP e SL no mesmo candle = LOSS** | — | sem dados intra-candle não dá para saber o que veio primeiro; a validação assume o pior. O TV decide pela forma da barra (otimista) |

TP e SL ficam **anexados na exchange** (tpslMode Full): sobrevivem a PC desligado, queda de internet e reinício do bot.

### 3.4 Sizing

- **Risco fixo por trade**: 1% da conta no stop cheio → exposição = 1%/1,5% = **0,67× o equity** (alavancagem implícita < 1: sem risco de liquidação).
- Teto de alavancagem 2× (nunca atingido com os defaults).
- Compounding sobre o equity corrente.

## 4. Números validados (sem lookahead, janela 19-00h, líquido de custos)

| Símbolo | WR forward | PF forward | Obs |
|---|---|---|---|
| BTC | 81,5% | 1,66 | +0,148%/trade |
| DOGE | 85,1% | 1,78 | |
| ETH | 82,2% | 1,46 | |
| SOL | 80,2% | 1,39 | |
| XRP | — | 0,98 | **morto no stress — não operar** |

- Cenário stress (funding 1,5×, slippage 0,05% nos stops): BTC PF 1,26, +0,074%/trade — sobrevive.
- Prop challenge (Monte Carlo, forward-only): BTC solo @ 1% de risco = **98,6% de aprovação** (~29 dias); cesta top8 @ 0,5% = 96-98% (~12 dias). Correlação treino→forward entre símbolos ≈ **zero**: escolher o "melhor" símbolo pelo treino é miragem — diversificar ou ficar no BTC.
- Funding médio Bybit +0,0032%/8h: irrelevante para holds de horas.

## 5. Por que o TradingView dá resultado diferente do app

Medido em 1 ano de BTC (mesmos dados Bybit), com o `.pine` já corrigido:

| Backtest | trades | WR | PF | retorno 1a |
|---|---|---|---|---|
| App (tela = **bruto**, sem custos) | 269 | 76,6% | 1,51 | **+25,1%** |
| App com comissão do TV (0,025%/ponta) | 269 | 75,8% | 1,29 | +14,3% |
| TV emulado semanticamente (toque, forma da barra, sessão no setup, comissão) | 257 | 75,5% | 1,30 | **+13,7%** |

Leitura: **com o pine corrigido, o TV deve mostrar ≈ metade do retorno da tela do app — e isso está CERTO.** A tela do app é bruta; o TV desconta comissão. As demais diferenças de semântica (fill no toque vs atravessar, TP/SL no mesmo candle, borda da janela) praticamente se cancelam (+14,3% vs +13,7%). Para comparar de verdade: ligue os custos no app (ou o sizing por risco fixo no Prop Challenge) e compare com o TV — ambos ~+14%.

Se o TV mostrar algo MUITO longe de ~+13-14%/1,30 PF no ano, o problema é operacional, nesta ordem: (1) script antigo colado (o fix do `strategy.exit` junto da entrada é o que captura os ganhos de mesmo candle — >50% do lucro); (2) símbolo errado — precisa ser `BYBIT:BTCUSDT.P`; (3) período diferente — plano do TV limita o histórico de 15m (~2 meses no free); use o mesmo 1 ano.

Correções aplicadas no `.pine` (2026-07-04): bracket registrado JUNTO da entrada (antes o candle do fill ficava sem TP/SL e o TV perdia 41 trades = 54% do lucro); comissão 0,0375→0,025%/ponta (real maker-dominante); time-stop no fechamento via `process_orders_on_close`.

## 6. Armadilhas conhecidas (para quem for mexer)

1. **Lookahead do 1h**: nunca use `resample('1h') + ffill` ingênuo para filtro de timeframe maior — o bucket vaza futuro. O valor do 1h só existe em `bucket_start + 1h`.
2. **Timestamps em pandas 3.x**: `index.astype(int64)//10**6` NÃO dá ms (resolução µs). Use `(index - Timestamp(0)).total_seconds()*1000`. Esse bug já zerou o funding em grids inteiros.
3. **TP/SL no mesmo candle**: qualquer reimplementação deve decidir a regra ANTES de olhar resultado. Aqui: LOSS.
4. **Janela de horário**: restringe entradas pela hora do candle do FILL (UTC {22,23,0,1,2}); sair fora da janela é permitido e esperado.
5. **Sem entrada limite não há estratégia** (seção 2).

## 7. Referências no repositório

- `RELATORIO_prop_challenge.md` — relatório completo da pesquisa
- `research/` — scripts finais + `download_data.py` + 6 regras de honestidade
- `research/tv_emulation_mm9.py` — emulador da semântica do TV usado na seção 5
- Automação: módulo `automation/` executa esta estratégia via `signal()` (paper/demo/real) com a MESMA semântica do backtest
