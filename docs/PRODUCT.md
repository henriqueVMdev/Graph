# Produto e regras de negócio

## 1. Objetivo

O Graph reduz a fragmentação do processo quantitativo. Em vez de usar ferramentas separadas para observar o mercado, testar hipóteses, controlar custos, validar robustez e acompanhar execução, o usuário percorre esse ciclo em um workspace compartilhado.

O produto não é uma corretora nem uma fonte oficial de recomendação. É uma ferramenta de pesquisa e suporte à decisão; qualquer operação real continua sujeita a risco de mercado, dados, software, liquidez e terceiros.

## 2. Usuários e resultados esperados

| Perfil | Necessidade | Resultado no Graph |
|---|---|---|
| Quant/researcher | Transformar hipótese em evidência | Estratégia reproduzível, backtest, OOS e testes estatísticos |
| Trader discricionário | Contextualizar preço e regime | Terminal, gráficos, notícias, calendário e inteligência multifator |
| Trader sistemático | Operar a mesma lógica validada | Contrato `signal()` e deployments paper/demo/real |
| Operador de prop challenge | Medir risco de violar regras | Simulação de desafio e Monte Carlo |
| Gestor de risco | Ver exposição e degradação | Custos, drawdown, WFE, guardrails e live vs backtest |
| Desenvolvedor | Adicionar fonte ou estratégia | Interfaces modulares e endpoints REST |

## 3. Jornada principal

1. Selecionar estratégia, ativo, timeframe e fonte de candles.
2. Configurar parâmetros e filtros de horário/sazonalidade.
3. Rodar backtest e analisar retorno, risco, trades e equity.
4. Aplicar fees, funding e cenários pessimistas.
5. Validar estabilidade por WFA, Monte Carlo e permutation tests.
6. Otimizar sem escolher parâmetros apenas pelo retorno bruto.
7. Simular regras de prop firm quando aplicável.
8. Criar deployment paper; promover para demo/real somente após validação operacional.
9. Comparar resultado realizado com referência do backtest e registrar eventos.

## 4. Módulos do app

### Estratégia e validação

| Tela | Rota | Função |
|---|---|---|
| Parâmetros | `/dashboard` | Carrega resultados de otimização, filtra e inspeciona melhores combinações |
| Backtesting | `/backtest` | Executa estratégia, métricas, equity, drawdown, custos, WFA, Monte Carlo e correlação |
| Otimizador | `/optimizer` | Gera combinações, acompanha progresso, ranqueia e envia parâmetros ao backtest |
| Regimes | `/regime` | Detecta estados de mercado para interpretação ou filtro |
| Prop Challenge | `/prop-challenge` | Simula metas e limites de perda com risco e forward testing |
| Gráficos | `/grafico`, `/tech` | Visualização de preço, sinais e indicadores |

### Mercados e inteligência

| Tela | Rota | Função |
|---|---|---|
| Monitor/Screener | `/monitor`, `/screener` | Watchlist e varredura por preço, volume e funding |
| Central de sinais | `/intelligence` | Score multifator, ranking, divergências e tracking forward |
| Notícias/Calendário | `/news`, `/calendar` | Contexto de eventos e notícias |
| Sazonalidade | `/seasonality` | Padrões normalizados por horizonte e mês |
| Portfolio Lab | `/portfolio-lab` | Correlação e métricas de carteira |

### Fundamental, macro e alternativos

`/eqs`, `/ea`, `/rates`, `/omon`, `/book`, `/cdty`, `/alt`, `/des` e `/degenerado` agregam screening, fundamentos, juros/crédito, opções, book, commodities, dados alternativos e pesquisa de tokens.

### Execução e acompanhamento

| Tela | Rota | Função |
|---|---|---|
| Trading | `/trade` | OMS paper, pre-trade, ordens, blotter e TCA |
| Automação | `/automation` | Cria e gerencia deployments paper/demo/real |
| Diário | `/journal` | Registra e sincroniza trades de exchanges |
| Agentes IA | `/agentes` | Agentes configuráveis e propostas via gateways opcionais |
| HFT On-chain | `/hft` | Motor experimental em estado local |

## 5. Regras quantitativas e decisões de negócio

### 5.1 Causalidade antes de performance

- O sistema deve usar somente informações disponíveis até o instante avaliado.
- Candles em formação são descartados no runner; sinais são calculados em candles fechados.
- Estratégias posicionais sinalizam no fechamento e executam na abertura seguinte.
- WFA inclui warm-up anterior à janela para indicadores, mas mede métricas apenas dentro da janela avaliada.
- Scripts em `research/` registram experimentos, paridade e validação temporal.

Motivo: um backtest com lookahead ou janela fria pode parecer melhor e não ser reproduzível em execução.

### 5.2 OOS como gate de robustez

- WFA divide cada bloco temporal entre IS e OOS.
- A última janela absorve barras restantes, evitando descartar os dados mais recentes.
- Se habilitada, a otimização IS amostra o grid com seed determinística por janela.
- Com custos ativos, a seleção IS prioriza Sharpe líquido.
- Janelas sem trades mínimos suficientes não entram na agregação.
- WFE usa razões OOS/IS quando IS anualizado é positivo e limita outliers entre -2 e 5.

O rótulo atual considera WFE acima de 0,5 aceitável, mas isso é uma heurística de produto, não uma garantia estatística.

### 5.3 Custos fazem parte da tese

- Fees e funding podem ser aplicados por exchange e cenário.
- Cenário pessimista representa funding maior e slippage adicional.
- Estratégias de alto giro não devem ser escolhidas apenas pelo resultado bruto.
- Funding é associado aos timestamps efetivamente abrangidos pela posição.

### 5.4 Paridade entre pesquisa e execução

Uma estratégia automatizável expõe `signal(df, params)`. O retorno deve conter:

`side`, `type`, `price`, `valid_bars`, `tp_pct`, `sl_pct`, `max_bars`, `fill_rule` e `exposure`.

- `limit` exige preço e `fill_rule='cross'`.
- `market` exige `price=None` e `fill_rule='open'`.
- `exit_on_flip` permite fechar posição quando o sinal desejado muda.
- O runner e os testes de paridade buscam preservar as mesmas regras de fill, fees e saída do backtest.

### 5.5 Segurança operacional

- Paper é o modo padrão para descoberta operacional.
- Real exige perfil `personal` ou `prop` e chaves correspondentes.
- Não é permitido mais de um deployment real ativo para o mesmo símbolo e conta.
- Guardrails podem limitar perda diária, perda total e notional.
- Parar um deployment pode manter ou fechar a posição explicitamente.
- Chaves reais devem ter permissão de trade e nunca de saque.

### 5.6 Inteligência explicável

Fatores votam -1, 0 ou +1; score, confiança e cobertura são separados. Proxies e heurísticas devem ser rotulados. Sinais diários são persistidos sem reescrita e avaliados posteriormente em D+7/D+30 para reduzir viés retrospectivo.

## 6. Métricas e interpretação

| Métrica | Uso | Atenção |
|---|---|---|
| Retorno total/anualizado | Crescimento | Não descreve caminho ou liquidez |
| Sharpe | Retorno ajustado à volatilidade | Sensível à anualização e distribuição |
| Max drawdown | Queda pico-vale | Histórico não limita perdas futuras |
| Profit factor | Ganhos brutos/perdas brutas | Instável com poucos trades |
| Win rate | Frequência de acertos | Deve ser lida com payoff médio |
| WFE | Retenção de performance fora da amostra | Heurística agregada; veja dispersão por janela |
| Probabilidade MC | Distribuição simulada | Depende do modelo e amostra histórica |
| Custo líquido | Arrasto de fees/funding | Pode mudar por tier, liquidez e exchange |

## 7. Critério recomendado de promoção

Este fluxo é uma política sugerida, ainda não implementada como workflow obrigatório:

1. Backtest sem erros de dados e com amostra mínima definida pela equipe.
2. Custos reais e stress pessimista aceitáveis.
3. OOS positivo/estável em múltiplas janelas, sem depender de um único período.
4. Parâmetros estáveis no heatmap e lógica economicamente explicável.
5. Monte Carlo e prop rules dentro do orçamento de risco.
6. Paridade automatizada aprovada.
7. Paper por período mínimo; depois demo; real com capital reduzido e guardrails.
8. Monitoramento contínuo de live vs backtest e kill switch operacional.

## 8. Fora de escopo e limitações

- Não há garantia de qualidade, continuidade ou licença comercial das fontes gratuitas.
- Alguns dados têm rate limit, atraso, fallback ou cobertura parcial.
- Monte Carlo por GBM não captura integralmente caudas, mudanças de regime ou impacto de mercado.
- Backtest em OHLCV não conhece a sequência intrabar real.
- O app não substitui reconciliação financeira, compliance ou controles de uma instituição regulada.
- Autenticação, autorização e isolamento multiusuário não existem no estado atual.

