import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAssets,
  getStrategies,
  runBacktestAsset,
  runBacktestCsv,
  getCorrelation,
  runWfa as runWfaApi,
  runCosts as runCostsApi,
  getChartData as getChartDataApi,
} from '@/api/client.js'

export const useBacktestStore = defineStore('backtest', () => {
  // ─── Assets ──────────────────────────────────────────────────────────────
  const assets = ref({})

  // ─── Strategies ──────────────────────────────────────────────────────────
  const strategies = ref([])                 // lista de estratégias disponíveis
  const selectedStrategy = ref(null)         // { file, name, description, schema }

  // params dinâmicos: populados a partir do schema da estratégia selecionada
  const params = ref({})

  // ─── Pending params (vindos do Dashboard) ────────────────────────────────
  const pendingParams = ref(null)

  // ─── Fonte de dados ───────────────────────────────────────────────────────
  const dataSource = ref('asset')            // 'asset' | 'csv'
  const selectedAssetLabel = ref('')
  const selectedSymbol = ref('')
  const interval = ref('1d')
  const csvFile = ref(null)

  // ─── Resultados ───────────────────────────────────────────────────────────
  const isRunning = ref(false)
  const results = ref(null)
  const error = ref(null)

  // ─── Correlação ───────────────────────────────────────────────────────────
  const correlationData = ref(null)
  const correlationLoading = ref(false)
  const correlationError = ref(null)

  // ─── Walk-Forward Analysis ────────────────────────────────────────────────
  const wfaResults = ref(null)
  const wfaLoading = ref(false)
  const wfaError   = ref(null)
  const wfaConfig  = ref({
    n_windows: 10, is_pct: 0.70, optimize_is_samples: 0,
    // Custos reais (fees + funding da corretora) aplicados ao forward test.
    apply_costs: false, cost_exchange: 'binance', cost_scenario: 'realista', use_funding: true,
  })

  // ─── Gráficos de análise (candles + indicadores + funding + equity) ───────
  const chartData    = ref(null)
  const chartLoading = ref(false)
  const chartError   = ref(null)
  // exchange = fonte dos candles E do funding (bybit funciona nesta rede).
  const chartConfig  = ref({ exchange: 'bybit', scenario: 'realista', use_funding: true })

  // ─── Custos (fees + funding) ──────────────────────────────────────────────
  const costsResult  = ref(null)
  const costsLoading = ref(false)
  const costsError   = ref(null)
  const costsWarnings = ref([])
  const costsConfig  = ref({
    symbol: '',                                  // símbolo CCXT (swap), ex: BTC/USDT:USDT
    exchanges: ['binance', 'bybit', 'okx'],
    scenarios: ['realista', 'pessimista'],
    use_funding: true,
  })

  // ─── Computed ─────────────────────────────────────────────────────────────

  /** Alias: expõe params como config para compatibilidade com StrategyDetail */
  const config = computed({
    get: () => params.value,
    set: (v) => { params.value = v },
  })

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function fetchAssets() {
    try {
      const { data } = await getAssets()
      assets.value = data.assets || {}
    } catch {
      assets.value = {}
    }
  }

  async function fetchStrategies() {
    try {
      const { data } = await getStrategies()
      strategies.value = data.strategies || []
      // Seleciona a primeira estratégia disponível se nenhuma estiver selecionada
      if (!selectedStrategy.value && strategies.value.length > 0) {
        selectStrategy(strategies.value[0])
      }
    } catch {
      strategies.value = []
    }
  }

  /**
   * Seleciona uma estratégia e popula params com os defaults do schema.
   * @param {object} strategy - item da lista strategies[]
   */
  function selectStrategy(strategy) {
    selectedStrategy.value = strategy
    // Coleta defaults de todos os campos do schema
    const defaults = {}
    for (const section of (strategy.schema || [])) {
      for (const field of (section.fields || [])) {
        if (field.key !== undefined && field.default !== undefined) {
          defaults[field.key] = field.default
        }
      }
    }
    // Defaults do ciclo sazonal (generico, nao depende da estrategia)
    defaults.cycle_filter = false
    defaults.cycle_long_months = [1,2,3,4,5,6,7,8,9,10,11,12]
    defaults.cycle_short_months = [1,2,3,4,5,6,7,8,9,10,11,12]
    // Mantém valores existentes que coincidem com o schema (evita reset total)
    params.value = { ...defaults, ...params.value }
  }

  /** Pré-preenche estratégia e params com dados vindos do Dashboard ou Optimizer */
  function applyPendingParams() {
    if (!pendingParams.value) return
    const pending = pendingParams.value

    // Se veio um strategy_file, tenta pré-selecionar a estratégia
    if (pending.strategy_file && strategies.value.length > 0) {
      const strat = strategies.value.find(s => s.file === pending.strategy_file)
      if (strat) selectStrategy(strat)
    }

    // Configura dados do ativo se vieram do optimizer
    if (pending._symbol) {
      dataSource.value = pending._dataSource || 'asset'
      selectedSymbol.value = pending._symbol
      selectedAssetLabel.value = pending._symbolLabel || pending._symbol
      interval.value = pending._interval || '1d'
    }

    // Sobrescreve params com os valores enviados (exceto campos internos)
    const {
      strategy_file, autoRun,
      _symbol, _symbolLabel, _interval, _dataSource, _capital,
      ...rest
    } = pending
    if (_capital) rest.initial_capital = _capital
    params.value = { ...params.value, ...rest }

    pendingParams.value = null
    return { autoRun }
  }

  async function runBacktest() {
    isRunning.value = true
    error.value = null
    results.value = null
    const stratFile = selectedStrategy.value?.file || 'depaula'
    try {
      let resp
      if (dataSource.value === 'csv' && csvFile.value) {
        resp = await runBacktestCsv(csvFile.value, params.value, stratFile)
      } else {
        if (!selectedSymbol.value) {
          error.value = 'Selecione um ativo ou carregue um CSV'
          isRunning.value = false
          return
        }
        resp = await runBacktestAsset(
          selectedSymbol.value,
          selectedAssetLabel.value,
          interval.value,
          params.value,
          stratFile,
        )
      }
      results.value = resp.data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      isRunning.value = false
    }
  }

  async function runWfa() {
    if (dataSource.value === 'csv') {
      wfaError.value = 'WFA requer um ativo (yfinance). Modo CSV nao suportado.'
      return
    }
    if (!selectedSymbol.value) {
      wfaError.value = 'Selecione um ativo para executar WFA'
      return
    }
    wfaLoading.value = true
    wfaError.value   = null
    wfaResults.value = null
    try {
      const { data } = await runWfaApi({
        symbol:        selectedSymbol.value,
        interval:      interval.value,
        strategy_file: selectedStrategy.value?.file || 'depaula',
        config:        params.value,
        n_windows:            wfaConfig.value.n_windows,
        is_pct:               wfaConfig.value.is_pct,
        optimize_is_samples:  wfaConfig.value.optimize_is_samples,
        // Custos reais da corretora aplicados ao OOS (fees + funding).
        apply_costs:          wfaConfig.value.apply_costs,
        cost_exchange:        wfaConfig.value.cost_exchange,
        cost_scenario:        wfaConfig.value.cost_scenario,
        use_funding:          wfaConfig.value.use_funding,
        cost_symbol:          inferCcxtSymbol(),
        initial_capital:      Number(params.value.initial_capital) || 1000,
      })
      wfaResults.value = data
    } catch (e) {
      wfaError.value = e.response?.data?.error || e.message
    } finally {
      wfaLoading.value = false
    }
  }

  /** Deriva um símbolo CCXT (swap USDT-M) a partir do símbolo da plataforma. */
  function inferCcxtSymbol() {
    if (costsConfig.value.symbol) return costsConfig.value.symbol
    const raw = (selectedSymbol.value || '').toUpperCase()
    const base = raw.replace(/-USD.*$/, '').replace(/USDT$/, '').replace(/[^A-Z0-9]/g, '')
    if (!base) return 'BTC/USDT:USDT'
    return `${base}/USDT:USDT`
  }

  async function runCosts() {
    const trades = results.value?.trades || []
    if (!trades.length) {
      costsError.value = 'Rode um backtest primeiro (sem trades para custear).'
      return
    }
    costsLoading.value = true
    costsError.value = null
    costsResult.value = null
    costsWarnings.value = []
    try {
      const { data } = await runCostsApi({
        trades,
        symbol: inferCcxtSymbol(),
        exchanges: costsConfig.value.exchanges,
        scenarios: costsConfig.value.scenarios,
        use_funding: costsConfig.value.use_funding,
        initial_capital: Number(params.value.initial_capital) || 1000,
        strategy_name: selectedStrategy.value?.name || 'Estratégia',
      })
      costsResult.value = data.rows || []
      costsWarnings.value = data.warnings || []
    } catch (e) {
      costsError.value = e.response?.data?.error || e.message
    } finally {
      costsLoading.value = false
    }
  }

  async function fetchChartData() {
    if (dataSource.value === 'csv') {
      chartError.value = 'Gráficos de análise requerem um ativo (candles da corretora). Modo CSV não suportado.'
      return
    }
    if (!selectedSymbol.value) {
      chartError.value = 'Selecione um ativo para ver os gráficos'
      return
    }
    chartLoading.value = true
    chartError.value = null
    chartData.value = null
    try {
      const { data } = await getChartDataApi({
        symbol:        selectedSymbol.value,
        symbol_label:  selectedAssetLabel.value,
        interval:      interval.value,
        strategy_file: selectedStrategy.value?.file || 'depaula',
        config:        params.value,
        exchange:      chartConfig.value.exchange,     // candles vêm da corretora
        cost_exchange: chartConfig.value.exchange,     // funding/fees da mesma corretora
        cost_scenario: chartConfig.value.scenario,
        use_funding:   chartConfig.value.use_funding,
        cost_symbol:   inferCcxtSymbol(),
      })
      chartData.value = data
    } catch (e) {
      chartError.value = e.response?.data?.error || e.message
    } finally {
      chartLoading.value = false
    }
  }

  async function fetchCorrelation(tickers) {
    if (Object.keys(tickers).length < 2) return
    correlationLoading.value = true
    correlationError.value = null
    try {
      const { data } = await getCorrelation(tickers)
      correlationData.value = data
    } catch (e) {
      correlationError.value = e.response?.data?.error || e.message
    } finally {
      correlationLoading.value = false
    }
  }

  return {
    assets, strategies, selectedStrategy, params, config,
    pendingParams,
    dataSource, selectedAssetLabel, selectedSymbol, interval, csvFile,
    isRunning, results, error,
    correlationData, correlationLoading, correlationError,
    wfaResults, wfaLoading, wfaError, wfaConfig,
    costsResult, costsLoading, costsError, costsWarnings, costsConfig,
    chartData, chartLoading, chartError, chartConfig,
    fetchAssets, fetchStrategies, selectStrategy,
    applyPendingParams, runBacktest, fetchCorrelation, runWfa,
    runCosts, inferCcxtSymbol, fetchChartData,
  }
})
