import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAssets,
  getStrategies,
  runBacktestAsset,
  runBacktestCsv,
  getCorrelation,
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
  const selectedCompareLabels = ref([])

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

  /** Pré-preenche estratégia e params com dados vindos do Dashboard */
  function applyPendingParams() {
    if (!pendingParams.value) return
    const pending = pendingParams.value

    // Se veio um strategy_file, tenta pré-selecionar a estratégia
    if (pending.strategy_file && strategies.value.length > 0) {
      const strat = strategies.value.find(s => s.file === pending.strategy_file)
      if (strat) selectStrategy(strat)
    }

    // Sobrescreve params com os valores enviados (exceto strategy_file)
    const { strategy_file, ...rest } = pending
    params.value = { ...params.value, ...rest }

    pendingParams.value = null
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
    selectedCompareLabels,
    fetchAssets, fetchStrategies, selectStrategy,
    applyPendingParams, runBacktest, fetchCorrelation,
  }
})
