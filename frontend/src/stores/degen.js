import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getDegenChains, getDegenTokens, getDegenHype } from '@/api/client.js'

export const useDegenStore = defineStore('degen', () => {
  const chains = ref({})
  const chain = ref('robinhood')
  const kind = ref('trending')   // 'trending' | 'new'
  const tokens = ref([])
  const updatedAt = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const autoRefresh = ref(true)

  // Hype Radar
  const hypeToken = ref(null)     // token da tabela selecionado
  const hype = ref(null)          // resultado da análise
  const hypeLoading = ref(false)
  const hypeError = ref(null)

  let timer = null

  const hasTokens = computed(() => tokens.value.length > 0)

  async function fetchChains() {
    try {
      const { data } = await getDegenChains()
      chains.value = data.chains || {}
    } catch { chains.value = {} }
  }

  async function fetchTokens() {
    loading.value = true
    error.value = null
    try {
      const { data } = await getDegenTokens(chain.value, kind.value)
      tokens.value = data.tokens || []
      updatedAt.value = data.updated_at ? new Date(data.updated_at * 1000) : new Date()
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      loading.value = false
    }
  }

  function setChain(c) {
    chain.value = c
    fetchTokens()
  }

  function setKind(k) {
    kind.value = k
    fetchTokens()
  }

  function startAutoRefresh() {
    stopAutoRefresh()
    if (autoRefresh.value) {
      timer = setInterval(fetchTokens, 60000)
    }
  }

  function stopAutoRefresh() {
    if (timer) { clearInterval(timer); timer = null }
  }

  function toggleAutoRefresh() {
    autoRefresh.value = !autoRefresh.value
    startAutoRefresh()
  }

  async function fetchHype(token) {
    hypeToken.value = token
    hype.value = null
    hypeError.value = null
    hypeLoading.value = true
    try {
      const { data } = await getDegenHype(chain.value, token.token_address, token.symbol)
      hype.value = data
    } catch (e) {
      hypeError.value = e.response?.data?.error || e.message
    } finally {
      hypeLoading.value = false
    }
  }

  function closeHype() {
    hypeToken.value = null
    hype.value = null
    hypeError.value = null
  }

  return {
    chains, chain, kind, tokens, updatedAt, loading, error, autoRefresh,
    hypeToken, hype, hypeLoading, hypeError,
    hasTokens, fetchChains, fetchTokens, setChain, setKind,
    startAutoRefresh, stopAutoRefresh, toggleAutoRefresh,
    fetchHype, closeHype,
  }
})
