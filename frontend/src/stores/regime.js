import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAssets, detectRegimeAsset, detectRegimeCsv } from '@/api/client.js'

export const useRegimeStore = defineStore('regime', () => {
  const assets = ref({})
  const isRunning = ref(false)
  const error = ref(null)
  const results = ref(null)

  // Config
  const dataSource = ref('asset')  // 'asset' | 'csv'
  const symbol = ref('')
  const symbolLabel = ref('')
  const interval = ref('1d')
  const method = ref('hmm')        // 'hmm' | 'markov_switching' | 'changepoint'
  const nStates = ref(0)           // 0 = auto
  const features = ref(['log_return', 'volatility'])
  const volWindow = ref(20)

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
    }

    try {
      let resp
      if (dataSource.value === 'csv' && csvFile) {
        resp = await detectRegimeCsv(csvFile, params)
      } else {
        resp = await detectRegimeAsset(symbol.value, interval.value, params)
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
    dataSource, symbol, symbolLabel, interval,
    method, nStates, features, volWindow,
    hasResults, fetchAssets, run, clear,
  }
})
