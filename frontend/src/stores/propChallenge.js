import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAssets, getStrategies, runPropChallenge } from '@/api/client.js'

export const usePropChallengeStore = defineStore('propChallenge', () => {
  // Assets e estrategias
  const assets = ref({})
  const strategies = ref([])
  const selectedStrategy = ref(null)
  const params = ref({})

  // Dados
  const dataSource = ref('asset')
  const selectedAssetLabel = ref('')
  const selectedSymbol = ref('')
  const interval = ref('1d')

  // Prop challenge config
  const accountSize = ref(50000)
  const numSims = ref(1000)

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
    params.value = { ...defaults, ...params.value }
  }

  function applyPendingParams() {
    if (!pendingParams.value) return
    const pending = pendingParams.value

    if (pending.strategy_file && strategies.value.length > 0) {
      const strat = strategies.value.find(s => s.file === pending.strategy_file)
      if (strat) selectStrategy(strat)
    }

    if (pending._symbol) {
      dataSource.value = pending._dataSource || 'asset'
      selectedSymbol.value = pending._symbol
      selectedAssetLabel.value = pending._symbolLabel || pending._symbol
      interval.value = pending._interval || '1d'
    }

    const {
      strategy_file, autoRun,
      _symbol, _symbolLabel, _interval, _dataSource, _capital,
      ...rest
    } = pending
    params.value = { ...params.value, ...rest }

    pendingParams.value = null
    return { autoRun }
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
        config: params.value,
        account_size: accountSize.value,
        num_sims: numSims.value,
      })
      results.value = data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      isRunning.value = false
    }
  }

  return {
    assets, strategies, selectedStrategy, params,
    pendingParams,
    dataSource, selectedAssetLabel, selectedSymbol, interval,
    accountSize, numSims,
    isRunning, results, error,
    fetchAssets, fetchStrategies, selectStrategy,
    applyPendingParams, runSimulation,
  }
})
