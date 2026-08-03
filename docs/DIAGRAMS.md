# Diagramas do projeto

Os diagramas abaixo usam Mermaid e podem ser renderizados no GitHub, editores compatíveis ou importados em ferramentas de diagramação. Eles refletem o código atual, não a arquitetura futura desejada.

## 1. Arquitetura de containers e integrações

```mermaid
flowchart LR
    user["Usuário"] -->|"HTTPS"| nginx["Nginx e SPA Vue"]
    nginx -->|"/api"| flask["API Flask"]
    flask --> quant["Motores quantitativos"]
    flask --> terminal["Terminal e inteligência"]
    flask --> automation["Automação e runner"]
    quant --> strategies["Estratégias Python"]
    quant --> market["Yahoo e exchanges via CCXT"]
    terminal --> publicData["Fontes públicas e premium"]
    automation --> strategies
    automation --> exchange["Bybit paper, demo ou real"]
    automation --> sqlite["SQLite de automação"]
    terminal --> localData["SQLite, JSON e Parquet"]
```

## 2. Jornada de validação de estratégia

```mermaid
flowchart TD
    idea["Hipótese de estratégia"] --> contract["Implementar schema, run e signal"]
    contract --> data["Selecionar dados, ativo e timeframe"]
    data --> optimize["Otimizar no in-sample"]
    optimize --> backtest["Executar backtest"]
    backtest --> costs["Aplicar fees, funding e stress"]
    costs --> wfa["Validar walk-forward"]
    wfa --> robust{"Robustez aceitável?"}
    robust -->|"Não"| revise["Revisar hipótese sem perseguir o OOS"]
    revise --> contract
    robust -->|"Sim"| monteCarlo["Monte Carlo e permutation test"]
    monteCarlo --> paper["Deployment paper"]
    paper --> parity{"Paridade e estabilidade?"}
    parity -->|"Não"| diagnose["Diagnosticar dados, fills e custos"]
    diagnose --> contract
    parity -->|"Sim"| demo["Exchange demo"]
    demo --> approval{"Risco aprovou?"}
    approval -->|"Não"| paper
    approval -->|"Sim"| real["Real com capital reduzido e guardrails"]
```

## 3. Sequência do backtest e WFA

```mermaid
sequenceDiagram
    actor User as Usuário
    participant UI as Vue Backtest
    participant API as Flask API
    participant Data as Market Data
    participant Strategy as Estratégia
    participant Costs as Custos
    User->>UI: Configura estratégia, ativo e parâmetros
    UI->>API: POST /backtest/run
    API->>Data: Carrega e normaliza OHLCV
    API->>Strategy: run com DataFrame e parâmetros
    Strategy-->>API: Trades, equity e métricas
    API-->>UI: Resultado do backtest
    User->>UI: Define janelas e percentual IS
    UI->>API: POST /backtest/wfa
    API->>Data: Reutiliza ou baixa OHLCV
    loop Cada janela
        API->>Strategy: Avalia IS com warm-up
        API->>Strategy: Avalia OOS com warm-up
        API->>Costs: Aplica fees e funding se habilitado
    end
    API-->>UI: WFE, janelas, curva OOS e custos
```

## 4. Sequência da automação

```mermaid
sequenceDiagram
    actor Operator as Operador
    participant UI as Vue Automação
    participant API as Automation API
    participant DB as SQLite WAL
    participant Runner as Runner
    participant Market as Exchange Market Data
    participant Strategy as signal
    participant Executor as Paper ou Bybit
    Operator->>UI: Cria e inicia deployment
    UI->>API: POST deployments e start
    API->>DB: Persiste configuração e status
    API->>Runner: Garante runner ativo
    loop Por timeframe e deployment
        Runner->>Market: Busca candles
        Market-->>Runner: OHLCV
        Runner->>Runner: Remove candle aberto e detecta novos
        Runner->>DB: Lê posição e ordem
        Runner->>Executor: Processa fills, TP, SL e fechamento
        Executor->>DB: Atualiza ordem, posição, equity e eventos
        Runner->>Strategy: Calcula sinal em candles fechados
        Strategy-->>Runner: Ordem desejada ou vazio
        Runner->>DB: Persiste próxima ordem e snapshot
    end
    UI->>API: GET deployment status
    API->>DB: Lê estado consolidado
    API-->>UI: Posição, trades, curva, eventos e comparação
```

## 5. Modelo de dados da automação

```mermaid
erDiagram
    DEPLOYMENTS ||--o{ ORDERS : possui
    DEPLOYMENTS ||--o{ POSITIONS : possui
    DEPLOYMENTS ||--o{ EQUITY_SNAPSHOTS : registra
    DEPLOYMENTS ||--o{ EVENTS : emite

    DEPLOYMENTS {
        text id PK
        text strategy_file
        text symbol
        text interval
        text mode
        text status
        real initial_capital
        real equity
        text params_json
        text guardrails_json
    }
    ORDERS {
        integer id PK
        text deployment_id FK
        text kind
        integer side
        text type
        real price
        real qty
        text status
        integer valid_candle_ts
    }
    POSITIONS {
        integer id PK
        text deployment_id FK
        integer side
        real qty
        real entry_price
        text status
        real pnl_pct
        real fees_quote
    }
    EQUITY_SNAPSHOTS {
        text deployment_id PK
        integer candle_ts PK
        real equity
    }
    EVENTS {
        integer id PK
        text deployment_id FK
        integer ts
        text level
        text type
        text message
    }
```

## 6. Estados de deployment

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Running: iniciar
    Running --> Stopped: parar
    Running --> Error: falha operacional
    Error --> Running: corrigir e reiniciar
    Error --> Stopped: abandonar
    Stopped --> Running: reiniciar
    Stopped --> [*]: excluir
```

## 7. Mapa de domínios

```mermaid
flowchart TB
    workspace["Workspace compartilhado"] --> strategyDomain["Estratégia"]
    workspace --> marketDomain["Mercados"]
    workspace --> analysisDomain["Análise"]
    workspace --> executionDomain["Execução"]
    strategyDomain --> backtest["Backtest e custos"]
    strategyDomain --> optimizer["Otimizador"]
    strategyDomain --> validation["WFA e Monte Carlo"]
    strategyDomain --> prop["Prop Challenge"]
    marketDomain --> monitoring["Monitor e screener"]
    marketDomain --> charts["Gráficos e técnica"]
    marketDomain --> intelligence["Inteligência e eventos"]
    analysisDomain --> fundamental["Empresas e screening"]
    analysisDomain --> macro["Juros e commodities"]
    analysisDomain --> alternatives["Alt data e on-chain"]
    executionDomain --> oms["OMS"]
    executionDomain --> auto["Automação"]
    executionDomain --> journal["Diário"]
    executionDomain --> agents["Agentes e HFT"]
```

## 8. Diagramas futuros recomendados

- Arquitetura alvo com API, workers, runner, PostgreSQL, Redis e observabilidade.
- Data lineage por fonte, cache, transformação, endpoint e tela.
- Threat model para execução real e gestão de segredos.
- Sequência detalhada de reconciliação com exchange.
- State machine de ordem e posição por modo.
- Matriz estratégia × suporte a backtest/optimizer/signal/Pine.
- Fluxo de incidente e kill switch.

