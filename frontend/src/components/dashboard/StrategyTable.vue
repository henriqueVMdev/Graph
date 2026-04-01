<template>
  <div>
    <!-- Sort controls -->
    <div class="flex flex-wrap items-end gap-x-6 gap-y-2 mb-3">
      <!-- Primary sort (backend) -->
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-400 whitespace-nowrap">Top-N por:</label>
        <select
          v-model="sortBy"
          @change="onSortChange"
          class="form-select text-xs py-1"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <button
          @click="toggleSortDir"
          class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
            :class="{ 'rotate-180': sortAsc }"
            style="transition: transform 0.2s">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
          {{ sortAsc ? 'Crescente' : 'Decrescente' }}
        </button>
      </div>

      <!-- Divider -->
      <span class="text-gray-600 text-xs hidden sm:block">|</span>

      <!-- Secondary sort (client-side) -->
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-400 whitespace-nowrap">Dentro do Top, ordenar por:</label>
        <select
          v-model="subSortBy"
          class="form-select text-xs py-1"
        >
          <option value="">— Nenhum —</option>
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <button
          v-if="subSortBy"
          @click="subSortAsc = !subSortAsc"
          class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
            :class="{ 'rotate-180': subSortAsc }"
            style="transition: transform 0.2s">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
          {{ subSortAsc ? 'Crescente' : 'Decrescente' }}
        </button>
      </div>

      <!-- Count badge -->
      <span v-if="subSortBy" class="text-xs text-accent-yellow ml-auto">
        {{ displayRows.length }} resultados
      </span>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-lg border border-surface-500">
      <table class="w-full text-xs">
        <thead>
          <tr class="bg-surface-600 text-gray-400 text-left">
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-3 py-2 font-medium whitespace-nowrap select-none cursor-pointer hover:text-gray-200 transition-colors"
              @click="onHeaderClick(col.key)"
            >
              <span class="flex items-center gap-1">
                {{ col.label }}
                <svg
                  v-if="activeSubSortCol === col.key"
                  class="w-3 h-3 text-accent-yellow shrink-0"
                  :class="{ 'rotate-180': subSortAsc }"
                  style="transition: transform 0.15s"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in displayRows"
            :key="i"
            class="table-row"
            :class="{ selected: store.selectedRank === row.rank }"
            @click="onRowClick(row)"
          >
            <td v-for="col in columns" :key="col.key" class="px-3 py-2 whitespace-nowrap">
              <span v-if="col.key === 'return_pct'" :class="row.return_pct >= 0 ? 'badge-green' : 'badge-red'">
                {{ fmt(row.return_pct, 2, '%') }}
              </span>
              <span v-else-if="col.key === 'max_dd_pct'" :class="row.max_dd_pct >= 0 ? 'text-gray-300' : 'badge-red'">
                {{ fmt(row.max_dd_pct, 2, '%') }}
              </span>
              <span v-else-if="col.key === 'win_rate_pct'" class="text-gray-300">
                {{ fmt(row.win_rate_pct, 1, '%') }}
              </span>
              <span v-else-if="['profit_factor', 'sharpe', 'score'].includes(col.key)" class="text-gray-300 font-mono">
                {{ fmt(row[col.key], 2) }}
              </span>
              <span v-else class="text-gray-300">
                {{ row[col.key] ?? '-' }}
              </span>
            </td>
          </tr>
          <tr v-if="displayRows.length === 0">
            <td :colspan="columns.length" class="text-center py-6 text-gray-500">
              Nenhum resultado após os filtros aplicados
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'

const store = useDashboardStore()

const sortBy = ref('score')
const sortAsc = ref(false)
const subSortBy = ref('')
const subSortAsc = ref(false)

const sortOptions = [
  { value: 'score', label: 'Score' },
  { value: 'return', label: 'Retorno (%)' },
  { value: 'profit_factor', label: 'Profit Factor' },
  { value: 'sharpe', label: 'Sharpe' },
  { value: 'win_rate', label: 'Win Rate (%)' },
  { value: 'trades', label: 'Trades' },
  { value: 'drawdown_asc', label: 'Menor Drawdown' },
  { value: 'drawdown_desc', label: 'Maior Drawdown' },
]

// Mapeia valor do select → coluna real no row
const colMap = {
  score: 'score',
  return: 'return_pct',
  profit_factor: 'profit_factor',
  sharpe: 'sharpe',
  win_rate: 'win_rate_pct',
  trades: 'trades',
  drawdown_asc: 'max_dd_pct',
  drawdown_desc: 'max_dd_pct',
}

// Coluna real ativa no sub-sort (para destacar o header)
const activeSubSortCol = computed(() => colMap[subSortBy.value] ?? null)

// Rows re-ordenados client-side (sem nova chamada ao backend)
const displayRows = computed(() => {
  if (!subSortBy.value) return store.table
  const col = colMap[subSortBy.value] ?? subSortBy.value
  return [...store.table].sort((a, b) => {
    const va = a[col] ?? (subSortAsc.value ? Infinity : -Infinity)
    const vb = b[col] ?? (subSortAsc.value ? Infinity : -Infinity)
    return subSortAsc.value ? va - vb : vb - va
  })
})

// Colunas fixas de metricas
const metricColumns = [
  { key: 'ativo', label: 'Ativo' },
  { key: 'timeframe', label: 'TF' },
  { key: 'rank', label: 'Rank' },
  { key: 'return_pct', label: 'Retorno (%)' },
  { key: 'max_dd_pct', label: 'Max DD (%)' },
  { key: 'trades', label: 'Trades' },
  { key: 'win_rate_pct', label: 'Win Rate (%)' },
  { key: 'profit_factor', label: 'PF' },
  { key: 'sharpe', label: 'Sharpe' },
  { key: 'score', label: 'Score' },
]

// Colunas dinamicas: metricas + params detectados do CSV
const columns = computed(() => {
  const paramCols = store.paramColumns.map(key => ({
    key,
    label: key,
  }))
  // Filtra metricas que existem nos dados + adiciona params
  const firstRow = store.table[0] || {}
  const visible = metricColumns.filter(c => c.key in firstRow)
  return [...visible, ...paramCols]
})

// Clique no header ativa/alterna o sub-sort para essa coluna
function onHeaderClick(colKey) {
  // Encontra qual sortOption corresponde à coluna
  const match = Object.entries(colMap).find(([, v]) => v === colKey)
  if (!match) return
  const optKey = match[0]

  if (subSortBy.value === optKey) {
    subSortAsc.value = !subSortAsc.value
  } else {
    subSortBy.value = optKey
    subSortAsc.value = false
  }
}

function fmt(v, dec = 2, suffix = '') {
  if (v == null) return '-'
  return Number(v).toFixed(dec) + suffix
}

function onSortChange() {
  subSortBy.value = '' // reseta sub-sort ao mudar critério principal
  store.applyFilters({ sort_by: sortBy.value, sort_asc: sortAsc.value })
}

function toggleSortDir() {
  sortAsc.value = !sortAsc.value
  subSortBy.value = ''
  store.applyFilters({ sort_by: sortBy.value, sort_asc: sortAsc.value })
}

async function onRowClick(row) {
  if (row.rank != null) {
    await store.selectStrategy(row.rank)
  }
}
</script>
