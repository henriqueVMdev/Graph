import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getJournal,
  setJournalCapital,
  addTrade as apiAddTrade,
  updateTrade as apiUpdateTrade,
  deleteTrade as apiDeleteTrade,
  syncJournal as apiSyncJournal,
} from '@/api/client.js'

export const useJournalStore = defineStore('journal', () => {
  const trades = ref([])
  const capitalInicial = ref(0)
  const stats = ref(null)
  const loading = ref(false)
  const saving = ref(false)
  const syncing = ref(false)
  const syncResult = ref(null)
  const error = ref(null)

  function _apply(data) {
    if (data.trades) trades.value = data.trades
    if (data.capital_inicial != null) capitalInicial.value = data.capital_inicial
    if (data.stats) stats.value = data.stats
  }

  async function load() {
    loading.value = true
    error.value = null
    try {
      const { data } = await getJournal()
      _apply(data)
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
    } finally {
      loading.value = false
    }
  }

  async function saveCapital(value) {
    saving.value = true
    error.value = null
    try {
      const { data } = await setJournalCapital(Number(value) || 0)
      stats.value = data.stats
      capitalInicial.value = data.capital_inicial
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
    } finally {
      saving.value = false
    }
  }

  async function addTrade(trade) {
    saving.value = true
    error.value = null
    try {
      const { data } = await apiAddTrade(trade)
      trades.value = [data.trade, ...trades.value]
      stats.value = data.stats
      return true
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
      return false
    } finally {
      saving.value = false
    }
  }

  async function editTrade(id, patch) {
    saving.value = true
    error.value = null
    try {
      const { data } = await apiUpdateTrade(id, patch)
      const i = trades.value.findIndex((t) => t.id === id)
      if (i !== -1) trades.value[i] = data.trade
      stats.value = data.stats
      return true
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
      return false
    } finally {
      saving.value = false
    }
  }

  async function removeTrade(id) {
    saving.value = true
    error.value = null
    try {
      const { data } = await apiDeleteTrade(id)
      trades.value = trades.value.filter((t) => t.id !== id)
      stats.value = data.stats
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
    } finally {
      saving.value = false
    }
  }

  async function sync(payload = {}) {
    syncing.value = true
    error.value = null
    syncResult.value = null
    try {
      const { data } = await apiSyncJournal(payload)
      if (data.trades) trades.value = data.trades
      if (data.stats) stats.value = data.stats
      syncResult.value = {
        added: data.added,
        updated: data.updated,
        by_exchange: data.by_exchange || {},
        warnings: data.warnings || [],
      }
      return true
    } catch (e) {
      error.value = e?.response?.data?.error || e.message
      return false
    } finally {
      syncing.value = false
    }
  }

  return {
    trades, capitalInicial, stats, loading, saving, syncing, syncResult, error,
    load, saveCapital, addTrade, editTrade, removeTrade, sync,
  }
})
