import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAssets, getStrategies, getChartData } from '@/api/client.js'

/**
 * Store da página de Análise Gráfica (estilo TradingView).
 * Independente do store de Backtest: seleções e gráfico próprios.
 * Reaproveita o endpoint /api/backtest/chart-data (com apply_costs:false p/
 * carregar rápido — candles + indicadores + marcadores, sem funding).
 */
export const useChartStore = defineStore('chart', () => {
  // ── Dados de seleção ───────────────────────────────────────────────────
  const assets = ref({})
  const strategies = ref([])
  const selectedStrategy = ref(null)        // { file, name, description, schema }
  const params = ref({})                    // params dinâmicos (do schema)

  const selectedAssetLabel = ref('')
  const selectedSymbol = ref('')
  const interval = ref('1d')
  const exchange = ref('bybit')             // corretora dos candles

  // ── Opções de visualização ─────────────────────────────────────────────
  const renderer = ref('tv')                // 'tv' (Lightweight Charts) | 'plotly'
  const overlays = ref({ indicators: true, markers: true, stops: true, volume: true })

  // ── Resultado ───────────────────────────────────────────────────────────
  const chartData = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // ── Ações ─────────────────────────────────────────────────────────────────
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

  /** Seleciona estratégia e popula params com os defaults do schema. */
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
    defaults.cycle_long_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    defaults.cycle_short_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    params.value = { ...defaults }
  }

  async function fetchChart() {
    if (!selectedSymbol.value) {
      error.value = 'Selecione um ativo para carregar o gráfico'
      return
    }
    loading.value = true
    error.value = null
    chartData.value = null
    try {
      const { data } = await getChartData({
        symbol: selectedSymbol.value,
        symbol_label: selectedAssetLabel.value,
        interval: interval.value,
        strategy_file: selectedStrategy.value?.file || 'depaula',
        config: params.value,
        exchange: exchange.value,
        apply_costs: false,   // análise visual: rápido, sem baixar funding
      })
      chartData.value = data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      loading.value = false
    }
  }

  return {
    assets, strategies, selectedStrategy, params,
    selectedAssetLabel, selectedSymbol, interval, exchange,
    renderer, overlays,
    chartData, loading, error,
    fetchAssets, fetchStrategies, selectStrategy, fetchChart,
  }
})
