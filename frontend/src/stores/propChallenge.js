import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAssets, getStrategies, runPropChallenge, runWfa as runWfaApi } from '@/api/client.js'
import { useWorkspaceStore } from '@/stores/workspace.js'

export const usePropChallengeStore = defineStore('propChallenge', () => {
  // Seleção compartilhada entre páginas (ativo/timeframe/fonte/estratégia)
  const ws = useWorkspaceStore()
  const _shared = (key) => computed({ get: () => ws[key], set: (v) => { ws[key] = v } })

  // Assets e estrategias
  const assets = ref({})
  const strategies = ref([])
  const selectedStrategy = _shared('selectedStrategy')
  const params = _shared('params')

  // Dados
  const dataSource = ref('asset')
  const selectedAssetLabel = _shared('symbolLabel')
  const selectedSymbol = _shared('symbol')
  const interval = _shared('interval')
  // '' = yfinance (60d p/ 15m); exchange CCXT = histórico longo (35k de 15m)
  const exchange = _shared('exchange')

  // Prop challenge config
  const accountSize = ref(50000)
  const numSims = ref(1000)

  // Custos reais da corretora (fees + funding) descontados de cada trade.
  const costConfig = ref({
    apply_costs: false, cost_exchange: 'binance', cost_scenario: 'realista', use_funding: true,
  })

  // Sizing por risco fixo: redimensiona cada trade p/ arriscar risk_pct na
  // distância real do stop (alavancagem implícita, com teto) e desconta
  // fees + funding esperados. Substitui o módulo de custos históricos.
  const riskSizing = ref({
    enabled: false, risk_pct: 1.0, lev_cap: 5.0,
    fee_maker_pct: 0.02, fee_taker_pct: 0.055,
    funding_8h_pct: 0.0032, maker_entry: true,
  })

  // ─── Walk-Forward Analysis (forward testing) ─────────────────────────────
  const wfaResults = ref(null)
  const wfaLoading = ref(false)
  const wfaError   = ref(null)
  const wfaConfig  = ref({
    n_windows: 10, is_pct: 0.70, optimize_is_samples: 0,
    apply_costs: false, cost_exchange: 'binance', cost_scenario: 'realista', use_funding: true,
  })

  // Pending params (vindos do Dashboard)
  const pendingParams = ref(null)

  // Resultados
  const isRunning = ref(false)
  const results = ref(null)
  const error = ref(null)

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
      if (!selectedStrategy.value && strategies.value.length > 0) {
        selectStrategy(strategies.value[0])
      }
    } catch {
      strategies.value = []
    }
  }

  function selectStrategy(strategy) {
    selectedStrategy.value = strategy
    const defaults = {}
    for (const section of (strategy.schema || [])) {
      for (const field of (section.fields || [])) {
        if (field.key !== undefined && field.default !== undefined) {
          defaults[field.key] = field.default
        }
      }
    }
    defaults.cycle_filter = false
    defaults.cycle_long_months = [1,2,3,4,5,6,7,8,9,10,11,12]
    defaults.cycle_short_months = [1,2,3,4,5,6,7,8,9,10,11,12]
    defaults.hour_filter = false
    defaults.allowed_hours = Array.from({ length: 24 }, (_, i) => i)
    params.value = { ...defaults, ...params.value }
  }

  function _resolveAsset(ativoName) {
    // Busca o ticker na lista de assets pelo nome (parcial, case-insensitive)
    if (!ativoName) return null
    const search = ativoName.toLowerCase().replace(/[^a-z0-9]/g, '')
    for (const category of Object.values(assets.value)) {
      for (const [label, ticker] of Object.entries(category)) {
        const labelNorm = label.toLowerCase().replace(/[^a-z0-9]/g, '')
        const tickerNorm = ticker.toLowerCase().replace(/[^a-z0-9]/g, '')
        if (labelNorm.includes(search) || search.includes(labelNorm)
            || tickerNorm.includes(search) || search.includes(tickerNorm)) {
          return { label, ticker }
        }
      }
    }
    return null
  }

  function applyPendingParams() {
    if (!pendingParams.value) return
    const pending = pendingParams.value

    if (pending.strategy_file && strategies.value.length > 0) {
      const strat = strategies.value.find(s => s.file === pending.strategy_file)
      if (strat) selectStrategy(strat)
    }

    // Resolve ativo: aceita _symbol direto (do optimizer) ou _ativo (do dashboard)
    if (pending._symbol) {
      dataSource.value = pending._dataSource || 'asset'
      selectedSymbol.value = pending._symbol
      selectedAssetLabel.value = pending._symbolLabel || pending._symbol
      interval.value = pending._interval || '1d'
    } else if (pending._ativo) {
      const found = _resolveAsset(pending._ativo)
      if (found) {
        dataSource.value = 'asset'
        selectedSymbol.value = found.ticker
        selectedAssetLabel.value = found.label
      }
    }

    const {
      strategy_file, autoRun,
      _symbol, _symbolLabel, _interval, _dataSource, _capital, _ativo,
      ...rest
    } = pending
    params.value = { ...params.value, ...rest }

    pendingParams.value = null
    return { autoRun }
  }

  /** Deriva um símbolo CCXT (swap USDT-M) a partir do símbolo da plataforma. */
  function inferCcxtSymbol() {
    const raw = (selectedSymbol.value || '').toUpperCase()
    const base = raw.replace(/-USD.*$/, '').replace(/USDT$/, '').replace(/[^A-Z0-9]/g, '')
    if (!base) return 'BTC/USDT:USDT'
    return `${base}/USDT:USDT`
  }

  async function runSimulation() {
    if (!selectedSymbol.value || !selectedStrategy.value) {
      error.value = 'Selecione um ativo e uma estrategia'
      return
    }
    isRunning.value = true
    error.value = null
    results.value = null
    try {
      const { data } = await runPropChallenge({
        strategy_file: selectedStrategy.value.file,
        data_source: 'asset',
        symbol: selectedSymbol.value,
        symbol_label: selectedAssetLabel.value,
        interval: interval.value,
        exchange: exchange.value || undefined,
        config: params.value,
        account_size: accountSize.value,
        num_sims: numSims.value,
        // Custos reais da corretora (fees + funding) descontados por trade.
        apply_costs: costConfig.value.apply_costs,
        cost_exchange: costConfig.value.cost_exchange,
        cost_scenario: costConfig.value.cost_scenario,
        use_funding: costConfig.value.use_funding,
        cost_symbol: inferCcxtSymbol(),
        risk_sizing: riskSizing.value.enabled ? { ...riskSizing.value } : undefined,
      })
      results.value = data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      isRunning.value = false
    }
  }

  async function runWfa() {
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
        exchange:      exchange.value || undefined,
        strategy_file: selectedStrategy.value?.file || 'depaula',
        config:        params.value,
        n_windows:            wfaConfig.value.n_windows,
        is_pct:               wfaConfig.value.is_pct,
        optimize_is_samples:  wfaConfig.value.optimize_is_samples,
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

  return {
    assets, strategies, selectedStrategy, params,
    pendingParams,
    dataSource, selectedAssetLabel, selectedSymbol, interval, exchange,
    accountSize, numSims, costConfig, riskSizing,
    isRunning, results, error,
    wfaResults, wfaLoading, wfaError, wfaConfig,
    fetchAssets, fetchStrategies, selectStrategy,
    applyPendingParams, runSimulation, inferCcxtSymbol, runWfa,
  }
})
