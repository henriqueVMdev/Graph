# API HTTP

## 1. Convenções

- Prefixo público: `/api`.
- JSON é o formato padrão; uploads de CSV usam `multipart/form-data`.
- Sucesso normalmente retorna HTTP 200 com objeto JSON.
- Criação de deployment retorna `{ "id": "..." }`.
- Erros normalmente retornam `{ "error": "mensagem" }`, com 400, 404, 409 ou 500.
- Não há autenticação ou versionamento `/v1` no estado atual.
- Alguns endpoints podem levar 180–300 segundos.

Esta é uma referência de grupos, não um schema OpenAPI exaustivo. Os contratos definitivos estão nos handlers e em `frontend/src/api/client.js`.

## 2. Dashboard de otimização

| Método | Endpoint | Função |
|---|---|---|
| GET | `/api/files` | Lista CSVs disponíveis |
| POST | `/api/load` | Carrega CSV por nome ou upload |
| POST | `/api/filter` | Filtra resultados de otimização |
| POST | `/api/filter-chart` | Prepara gráfico filtrado |
| POST | `/api/strategy` | Retorna detalhe por ranking |

## 3. Backtest e validação

| Método | Endpoint | Função |
|---|---|---|
| GET | `/api/backtest/assets` | Catálogo de ativos |
| GET | `/api/backtest/exchanges` | Exchanges suportadas |
| GET | `/api/backtest/strategies` | Descobre estratégias e schemas |
| POST | `/api/backtest/run` | Backtest por ativo ou CSV |
| POST | `/api/backtest/chart-data` | Candles, indicadores, funding e equity |
| POST | `/api/backtest/costs` | Recalcula fees/funding |
| POST | `/api/backtest/wfa` | Walk-forward IS/OOS |
| POST | `/api/backtest/correlation` | Correlação entre tickers |
| POST | `/api/backtest/montecarlo` | Projeção GBM da equity |
| POST | `/api/backtest/validate` | Monte Carlo e permutation tests |

Exemplo mínimo de WFA:

```json
{
  "symbol": "BTCUSDT",
  "interval": "15m",
  "exchange": "bybit",
  "strategy_file": "mm9_pullback",
  "config": { "initial_capital": 10000 },
  "n_windows": 10,
  "is_pct": 0.7,
  "optimize_is_samples": 40,
  "apply_costs": true,
  "cost_exchange": "bybit",
  "cost_scenario": "realista",
  "use_funding": true
}
```

## 4. Otimizador, prop e regimes

| Método | Endpoint | Função |
|---|---|---|
| GET | `/api/optimizer/grids` | Grid permitido pela estratégia |
| POST | `/api/optimizer/count` | Conta combinações |
| POST | `/api/optimizer/run` | Inicia otimização por ativo |
| POST | `/api/optimizer/run-csv` | Inicia por CSV |
| GET | `/api/optimizer/progress` | Progresso do job em memória |
| POST | `/api/optimizer/stop` | Solicita interrupção |
| GET | `/api/optimizer/result` | Resultado final |
| POST | `/api/prop-challenge/simulate` | Simula desafio de prop firm |
| POST | `/api/regime/detect` | Detecta regime por ativo ou CSV |

## 5. Diário

| Método | Endpoint | Função |
|---|---|---|
| GET | `/api/journal` | Estado, trades e métricas |
| POST | `/api/journal/capital` | Define capital inicial |
| POST | `/api/journal/trade` | Cria trade manual |
| PUT | `/api/journal/trade/{id}` | Atualiza trade |
| DELETE | `/api/journal/trade/{id}` | Remove trade |
| POST | `/api/journal/sync` | Sincroniza exchanges configuradas |

## 6. Automação

| Método | Endpoint | Função |
|---|---|---|
| GET/POST | `/api/automation/deployments` | Lista/cria deployments |
| POST | `/api/automation/deployments/{id}/start` | Inicia |
| POST | `/api/automation/deployments/{id}/stop` | Para; opcionalmente fecha posição |
| DELETE | `/api/automation/deployments/{id}` | Exclui se parado |
| GET | `/api/automation/deployments/{id}/status` | Posição, ordem, trades, curva e eventos |
| GET | `/api/automation/accounts` | Perfis reais configurados |
| GET | `/api/automation/runner/status` | Saúde lógica do runner |

Exemplo de deployment paper:

```json
{
  "name": "MM9 BTC paper",
  "strategy_file": "mm9_pullback",
  "params": {},
  "symbol": "BTCUSDT",
  "interval": "15m",
  "exchange": "bybit",
  "mode": "paper",
  "initial_capital": 10000,
  "guardrails": {
    "daily_loss_pct": 2,
    "max_loss_pct": 8,
    "max_notional": 2000
  }
}
```

## 7. Terminal

Todos abaixo usam o prefixo `/api/terminal`:

- Mercado: `GET /watch`, `/spark`, `/screener`, `/des`, `/rates`, `/book`.
- Opções/gráficos: `GET /options`, `/options/surface`; `POST /options/strategy`, `/chart`.
- Alternativos: `GET /alt/indicators`, `/alt/supplychain`, `/alt/traffic`, `/alt/climate`, `/alt/sectors`, `/alt/cryptomicro`, `/alt/onchain`, `/alt/onchain/coin`.
- OMS: `GET /oms/accounts`, `/oms/blotter`, `/oms/tca`; `POST /oms/pretrade`, `/oms/orders`, `/oms/reset`; `DELETE /oms/orders/{id}`.
- Commodities: `GET /cdty/overview`, `/cdty/curves`, `/cdty/curve`, `/cdty/weather`, `/cdty/shipping`, `/cdty/inventories`.
- Fundamental: `GET /ea`, `/eqs/meta`, `/eqs/funds`; `POST /eqs/equity`.
- Conteúdo/inteligência: `GET /news`, `/seasonality`, `/intelligence`, `/intelligence/ranking`, `/intelligence/tracking`, `/calendar`, `/liquidity`.
- Portfólio: `POST /portfolio-lab`.
- Alertas: `GET/POST /alerts`, `DELETE /alerts/{id}`.

## 8. Agentes, HFT e Degen

- Agentes: CRUD em `/api/agents`, execução em `/api/agents/{id}/run`, skills e decisões de propostas.
- HFT: `/api/hft/status`, `/start`, `/stop`, `/config`, `/reset`.
- Degen: `/api/degen/chains`, `/tokens` e `/hype`.

## 9. Evolução recomendada

- Gerar OpenAPI 3.1 e tipos TypeScript/Python.
- Validar payloads com schemas declarativos.
- Introduzir `/api/v1` antes de clientes externos.
- Paginar coleções e padronizar envelope, erro e id de correlação.
- Documentar idempotência para criação/ordens e usar chaves idempotentes.

