import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAssets, detectRegimeAsset, detectRegimeCsv } from '@/api/client.js'
import { useWorkspaceStore } from '@/stores/workspace.js'

export const useRegimeStore = defineStore('regime', () => {
  // Seleção compartilhada entre páginas (ativo/timeframe/fonte)
  const ws = useWorkspaceStore()
  const _shared = (key) => computed({ get: () => ws[key], set: (v) => { ws[key] = v } })

  const assets = ref({})
  const isRunning = ref(false)
  const error = ref(null)
  const results = ref(null)

  // Config
  const dataSource = ref('asset')  // 'asset' | 'csv'
  const symbol = _shared('symbol')
  const symbolLabel = _shared('symbolLabel')
  const interval = _shared('interval')
  // '' = yfinance (60d p/ 15m); exchange CCXT = histórico longo (35k de 15m)
  const exchange = _shared('exchange')
  const method = ref('hmm')        // 'hmm' | 'markov_switching' | 'changepoint'
  const nStates = ref(0)           // 0 = auto
  const features = ref(['log_return', 'volatility'])
  const volWindow = ref(20)
  // true = probabilidades filtradas (tempo real, sem lookahead);
  // false = suavizadas (descrição histórica com a série inteira)
  const causal = ref(true)

  const hasResults = computed(() => results.value !== null)

  async function fetchAssets() {
    try {
      const { data } = await getAssets()
      assets.value = data.assets || {}
    } catch { assets.value = {} }
  }

  async function run(csvFile = null) {
    isRunning.value = true
    error.value = null
    results.value = null

    const params = {
      method: method.value,
      n_states: nStates.value,
      features: features.value,
      vol_window: volWindow.value,
      causal: causal.value,
    }

    try {
      let resp
      if (dataSource.value === 'csv' && csvFile) {
        resp = await detectRegimeCsv(csvFile, params)
      } else {
        resp = await detectRegimeAsset(symbol.value, interval.value, params, exchange.value)
      }
      results.value = resp.data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      isRunning.value = false
    }
  }

  function clear() {
    results.value = null
    error.value = null
  }

  return {
    assets, isRunning, error, results,
    dataSource, symbol, symbolLabel, interval, exchange,
    method, nStates, features, volWindow, causal,
    hasResults, fetchAssets, run, clear,
  }
})
