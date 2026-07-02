import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAssets, getStrategies, getChartData } from '@/api/client.js'
import { useWorkspaceStore } from '@/stores/workspace.js'

/**
 * Store da página de Análise Gráfica (estilo TradingView).
 * Ativo/timeframe/estratégia compartilhados com as demais páginas via
 * workspace; a exchange é própria (aqui os candles+funding sempre vêm de
 * corretora). Reaproveita o endpoint /api/backtest/chart-data.
 */
export const useChartStore = defineStore('chart', () => {
  // Seleção compartilhada entre páginas
  const ws = useWorkspaceStore()
  const _shared = (key) => computed({ get: () => ws[key], set: (v) => { ws[key] = v } })

  // ── Dados de seleção ───────────────────────────────────────────────────
  const assets = ref({})
  const strategies = ref([])
  const selectedStrategy = _shared('selectedStrategy')
  const params = _shared('params')

  const selectedAssetLabel = _shared('symbolLabel')
  const selectedSymbol = _shared('symbol')
  const interval = _shared('interval')
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
