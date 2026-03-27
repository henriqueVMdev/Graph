import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getFiles, loadCsvByName, loadCsvUpload, filterData, getStrategy } from '@/api/client.js'

export const useDashboardStore = defineStore('dashboard', () => {
  // Estado
  const files = ref([])
  const rawRows = ref([])        // Dataset completo (sem filtros)
  const asset = ref('')
  const filters = ref({
    min_trades: 0,
    min_sharpe: null,
    return_min: null,
    return_max: null,
    top_n: 20,
    sort_by: 'score',
    sort_asc: false,
  })
  const summary = ref(null)
  const charts = ref({})
  const table = ref([])
  const bestParams = ref(null)
  const selectedRank = ref(null)
  const selectedDetail = ref(null)
  const backtestParams = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const hasData = computed(() => rawRows.value.length > 0)
  const filteredCount = computed(() => table.value.length)

  // ─── Actions ───────────────────────────────────────────────────────────────

  async function loadFileList() {
    try {
      const { data } = await getFiles()
      files.value = data.files || []
    } catch (e) {
      files.value = []
    }
  }

  async function loadCsv(source) {
    loading.value = true
    error.value = null
    try {
      let data
      if (source instanceof File) {
        const resp = await loadCsvUpload(source)
        data = resp.data
      } else {
        const resp = await loadCsvByName(source)
        data = resp.data
      }
      _applyLoadResponse(data)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    } finally {
      loading.value = false
    }
  }

  function _applyLoadResponse(data) {
    rawRows.value = data.raw_rows || []
    asset.value = data.asset || ''
    summary.value = data.summary || null
    charts.value = data.charts || {}
    table.value = data.table || []
    bestParams.value = data.best_params || null
    selectedRank.value = null
    selectedDetail.value = null
    backtestParams.value = null

    // Inicializa filtros com os ranges reais
    filters.value = {
      ...filters.value,
      min_sharpe: data.filter_ranges?.sharpe_min ?? null,
      return_min: data.filter_ranges?.return_min ?? null,
      return_max: data.filter_ranges?.return_max ?? null,
    }
  }

  let _filterTimer = null
  async function applyFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    if (!hasData.value) return

    clearTimeout(_filterTimer)
    _filterTimer = setTimeout(async () => {
      loading.value = true
      error.value = null
      try {
        const { data } = await filterData(rawRows.value, filters.value)
        summary.value = data.summary
        charts.value = data.charts
        table.value = data.table
        bestParams.value = data.best_params
        selectedRank.value = null
        selectedDetail.value = null
        backtestParams.value = null
      } catch (e) {
        error.value = e.response?.data?.error || e.message
      } finally {
        loading.value = false
      }
    }, 400)
  }

  async function selectStrategy(rank) {
    if (!hasData.value) return
    selectedRank.value = rank
    try {
      const { data } = await getStrategy(rank, rawRows.value)
      selectedDetail.value = data.detail
      backtestParams.value = data.backtest_params
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  function clearSelection() {
    selectedRank.value = null
    selectedDetail.value = null
    backtestParams.value = null
  }

  return {
    files, rawRows, asset, filters,
    summary, charts, table, bestParams,
    selectedRank, selectedDetail, backtestParams,
    loading, error, hasData, filteredCount,
    loadFileList, loadCsv, applyFilters, selectStrategy, clearSelection,
  }
})
