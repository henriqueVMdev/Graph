# Documentação do Graph

O Graph é um terminal quantitativo e laboratório de estratégias. O produto reúne pesquisa, dados de mercado, backtesting, otimização, validação fora da amostra, análise de risco, execução simulada/real e acompanhamento em uma aplicação web.

Esta documentação descreve o estado observado no código. Quando uma capacidade é experimental, depende de terceiros ou ainda não está pronta para produção, isso é indicado explicitamente.

## Mapa da documentação

| Documento | Público principal | Conteúdo |
|---|---|---|
| [Produto e regras de negócio](PRODUCT.md) | Produto, research, quant, risco | Personas, módulos, fluxos, métricas e decisões de negócio |
| [Arquitetura técnica](ARCHITECTURE.md) | Engenharia | Stack, componentes, dados, estratégia, concorrência e integrações |
| [API](API.md) | Frontend e integrações | Grupos de endpoints, contratos e convenções |
| [Operação e produção](OPERATIONS.md) | DevOps e suporte | Setup, configuração, deploy, persistência, segurança e runbooks |
| [Diagramas](DIAGRAMS.md) | Todos | Diagramas Mermaid editáveis e catálogo de diagramas futuros |

## Resumo executivo

- SPA em Vue 3 consumindo uma API Flask pelo prefixo `/api`.
- Motores quantitativos em Python/Pandas/NumPy/SciPy, com Plotly e Lightweight Charts na visualização.
- Dados vindos principalmente de Yahoo Finance, exchanges via CCXT e fontes públicas macro, on-chain e fundamentais.
- Estratégias plugáveis em `strategies/`, descobertas dinamicamente e configuradas por schema.
- Caminho operacional: pesquisar → otimizar → backtestar → validar → simular risco/prop → automatizar → auditar.
- Persistência local distribuída entre SQLite e JSON; caches em memória e disco.
- Docker Compose disponível, mas o estado atual exige hardening antes de exposição pública ou uso real contínuo.

## Glossário

| Termo | Significado no projeto |
|---|---|
| IS | In-sample: trecho usado para calibrar/otimizar |
| OOS | Out-of-sample: trecho não usado na calibração |
| WFA | Walk-Forward Analysis: repetição temporal de IS e OOS |
| WFE | Eficiência walk-forward, razão média entre desempenho OOS e IS elegível |
| OHLCV | Open, High, Low, Close e Volume |
| OMS | Order Management System |
| TCA | Transaction Cost Analysis |
| Guardrail | Limite operacional que interrompe ou restringe execução |
| Deployment | Instância de estratégia ligada a ativo, timeframe, modo e capital |
| Paper/demo/real | Simulação local, exchange demo e conta real |

## Fonte de verdade e manutenção

O código é a fonte de verdade. Mudanças em rotas, variáveis de ambiente, estratégia, persistência ou deploy devem atualizar estes documentos no mesmo pull request. Diagramas Mermaid ficam versionados para permitir revisão por diff.

