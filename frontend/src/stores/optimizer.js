import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAssets,
  getStrategies,
  getOptimizerGrids,
  getOptimizerCount,
  runOptimizer,
  runOptimizerCsv,
  stopOptimizer,
  getOptimizerProgress,
} from '@/api/client.js'
import { useBacktestStore } from '@/stores/backtest.js'

export const useOptimizerStore = defineStore('optimizer', () => {
  // Assets
  const assets = ref({})

  // Estrategias
  const strategies = ref([])
  const selectedStrategy = ref(null)

  // Grids disponiveis do backend (por estrategia)
  const availableGrids = ref({})

  // Configuracao
  const dataSource = ref('asset')
  const selectedCategory = ref('')
  const selectedAssetLabel = ref('')
  const selectedSymbol = ref('')
  const interval = ref('1d')
  const csvFile = ref(null)
  const startDate = ref('')
  const endDate = ref('')

  // Grid
  const gridMode = ref('rapido')
  const customGrid = ref({})
  const useCustomGrid = ref(false)

  // Ciclo sazonal (params fixos, nao variam no grid)
  const cycleLongMonths = ref([1,2,3,4,5,6,7,8,9,10,11,12])
  const cycleShortMonths = ref([1,2,3,4,5,6,7,8,9,10,11,12])

  // Backtest config
  const capital = ref(1000)
  const minTrades = ref(5)
  const rankBy = ref('Score')
  const topN = ref(20)

  // Estado
  const isRunning = ref(false)
  const comboCount = ref(0)
  const results = ref(null)
  const error = ref(null)
  const progress = ref({ current: 0, total: 0, valid: 0 })
  let _progressTimer = null

  // Grid ativo (custom ou preset)
  const activeGrid = computed(() => {
    if (useCustomGrid.value) return customGrid.value
    const preset = availableGrids.value[gridMode.value]
    if (!preset) return customGrid.value

    const schema = selectedStrategy.value?.schema || []
    const typeMap = {}
    for (const section of schema) {
      for (const field of (section.fields || [])) {
        typeMap[field.key] = field.type
      }
    }

    const typed = {}
    for (const [key, vals] of Object.entries(preset)) {
      const ft = typeMap[key]
      if (ft === 'checkbox') {
        typed[key] = vals.map(v => v === 'True' || v === 'true' || v === true)
      } else if (ft === 'number') {
        typed[key] = vals.map(v => parseFloat(v))
      } else {
        typed[key] = vals.map(v => String(v))
      }
    }
    return typed
  })

  const strategyFile = computed(() => selectedStrategy.value?.file || 'depaula')

  // Actions
  async function fetchAssets() {
    try {
      const { data } = await getAssets()
      assets.value = data.assets || {}
      const categories = Object.keys(assets.value)
      if (categories.length > 0 && !selectedCategory.value) {
        selectedCategory.value = categories[0]
      }
    } catch {
      assets.value = {}
    }
  }

  async function fetchStrategies() {
    try {
      const { data } = await getStrategies()
      strategies.value = data.strategies || []
      if (!selectedStrategy.value && strategies.value.length > 0) {
        await selectStrategy(strategies.value[0])
      }
    } catch {
      strategies.value = []
    }
  }

  async function selectStrategy(strategy) {
    selectedStrategy.value = strategy
    useCustomGrid.value = false
    gridMode.value = 'rapido'
    await fetchGrids()
    _initCustomGridFromSchema()
  }

  function _initCustomGridFromSchema() {
    const schema = selectedStrategy.value?.schema || []
    const grid = {}
    for (const section of schema) {
      for (const field of (section.fields || [])) {
        if (field.type === 'select' && field.options) {
          grid[field.key] = [field.default]
        } else if (field.type === 'checkbox') {
          grid[field.key] = [field.default]
        } else if (field.type === 'number') {
          grid[field.key] = [field.default]
        }
      }
    }
    customGrid.value = grid
  }

  async function fetchGrids() {
    try {
      const { data } = await getOptimizerGrids(strategyFile.value)
      availableGrids.value = data.grids || {}
    } catch {
      availableGrids.value = {}
    }
  }

  async function updateComboCount() {
    try {
      const { data } = await getOptimizerCount(activeGrid.value, capital.value, strategyFile.value)
      comboCount.value = data.count || 0
    } catch {
      comboCount.value = 0
    }
  }

  function _startProgressPolling() {
    _stopProgressPolling()
    _progressTimer = setInterval(async () => {
      try {
        const { data } = await getOptimizerProgress()
        progress.value = data
      } catch { /* ignore */ }
    }, 500)
  }

  function _stopProgressPolling() {
    if (_progressTimer) {
      clearInterval(_progressTimer)
      _progressTimer = null
    }
  }

  async function run() {
    isRunning.value = true
    error.value = null
    results.value = null
    progress.value = { current: 0, total: 0, valid: 0 }
    _startProgressPolling()

    try {
      let resp
      if (dataSource.value === 'csv' && csvFile.value) {
        resp = await runOptimizerCsv(
          csvFile.value,
          activeGrid.value,
          capital.value,
          minTrades.value,
          rankBy.value,
          topN.value,
          strategyFile.value,
          cycleLongMonths.value,
          cycleShortMonths.value,
        )
      } else {
        resp = await runOptimizer({
          strategy_file: strategyFile.value,
          data_source: 'asset',
          symbol: selectedSymbol.value,
          symbol_label: selectedAssetLabel.value,
          interval: interval.value,
          grid: activeGrid.value,
          capital: capital.value,
          min_trades: minTrades.value,
          rank_by: rankBy.value,
          top_n: topN.value,
          start_date: startDate.value || null,
          end_date: endDate.value || null,
          cycle_long_months: cycleLongMonths.value,
          cycle_short_months: cycleShortMonths.value,
        })
      }
      results.value = resp.data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      _stopProgressPolling()
      isRunning.value = false
    }
  }

  async function stop() {
    try {
      await stopOptimizer()
    } catch { /* ignore */ }
  }

  function sendBestToBacktest() {
    if (!results.value?.best) return false
    const best = results.value.best
    const schema = selectedStrategy.value?.schema || []

    // Mapa reverso: label -> key
    const reverseMap = {}
    for (const section of schema) {
      for (const field of (section.fields || [])) {
        const label = field.label || field.key
        reverseMap[label] = field.key
      }
    }

    // Extrai params com chaves raw
    const paramLabels = results.value.param_columns || []
    const rawParams = {}
    for (const label of paramLabels) {
      const key = reverseMap[label] || label
      if (best[label] !== undefined) {
        rawParams[key] = best[label]
      }
    }

    const btStore = useBacktestStore()
    btStore.pendingParams = {
      ...rawParams,
      strategy_file: strategyFile.value,
      _symbol: selectedSymbol.value,
      _symbolLabel: selectedAssetLabel.value,
      _interval: interval.value,
      _dataSource: dataSource.value,
      _capital: capital.value,
      autoRun: true,
    }
    return true
  }

  function downloadCsv() {
    if (!results.value?.csv_data) return
    const blob = new Blob([results.value.csv_data], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `otimizacao_${results.value.symbol || 'resultado'}_${results.value.interval || ''}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    assets, strategies, selectedStrategy, availableGrids,
    dataSource, selectedCategory, selectedAssetLabel, selectedSymbol,
    interval, csvFile, startDate, endDate,
    gridMode, customGrid, useCustomGrid, activeGrid, strategyFile,
    cycleLongMonths, cycleShortMonths,
    capital, minTrades, rankBy, topN,
    isRunning, comboCount, results, error, progress,
    fetchAssets, fetchStrategies, selectStrategy, fetchGrids,
    updateComboCount, run, stop, sendBestToBacktest, downloadCsv,
  }
})
