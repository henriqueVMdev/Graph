<template>
  <div>
    <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Analise Visual</h2>

    <!-- Tab buttons -->
    <div class="flex gap-1 mb-4 border-b border-surface-500 pb-2">
      <button
        v-for="(tab, i) in tabs"
        :key="i"
        class="tab-btn"
        :class="{ active: activeTab === i }"
        @click="activeTab = i"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 0: Retorno vs Drawdown -->
    <div v-show="activeTab === 0">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Retorno min (%):</span>
          <input type="number" v-model="f0.returnMin" class="chart-filter-input" placeholder="-" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Max DD ate (%):</span>
          <input type="number" v-model="f0.ddMax" class="chart-filter-input" placeholder="-" />
        </div>
        <button @click="applyFilter(0)" :disabled="loading0" class="filter-btn">
          <span v-if="loading0" class="dollar-loader-sm text-[10px]">$</span>
          <span v-else>Filtrar</span>
        </button>
        <button v-if="isFiltered0" @click="clearFilter(0)" class="filter-clear-btn">Limpar</button>
        <span v-if="count0 != null" class="text-[10px] text-gray-600">{{ count0 }} pontos</span>
      </div>
      <ScatterChart
        ref="chart0"
        v-if="display0"
        :chartJson="display0"
        :key="key0"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este grafico</p>
    </div>

    <!-- Tab 1: Retorno vs Sharpe -->
    <div v-show="activeTab === 1">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Retorno min (%):</span>
          <input type="number" v-model="f1.returnMin" class="chart-filter-input" placeholder="-" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Sharpe min:</span>
          <input type="number" v-model="f1.sharpeMin" class="chart-filter-input" step="0.1" placeholder="-" />
        </div>
        <button @click="applyFilter(1)" :disabled="loading1" class="filter-btn">
          <span v-if="loading1" class="dollar-loader-sm text-[10px]">$</span>
          <span v-else>Filtrar</span>
        </button>
        <button v-if="isFiltered1" @click="clearFilter(1)" class="filter-clear-btn">Limpar</button>
        <span v-if="count1 != null" class="text-[10px] text-gray-600">{{ count1 }} pontos</span>
      </div>
      <ScatterChart
        ref="chart1"
        v-if="display1"
        :chartJson="display1"
        :key="key1"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este grafico</p>
    </div>

    <!-- Tab 2: Retorno vs Trades -->
    <div v-show="activeTab === 2">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Retorno min (%):</span>
          <input type="number" v-model="f2.returnMin" class="chart-filter-input" placeholder="-" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Trades min:</span>
          <input type="number" v-model="f2.tradesMin" class="chart-filter-input" placeholder="-" />
        </div>
        <button @click="applyFilter(2)" :disabled="loading2" class="filter-btn">
          <span v-if="loading2" class="dollar-loader-sm text-[10px]">$</span>
          <span v-else>Filtrar</span>
        </button>
        <button v-if="isFiltered2" @click="clearFilter(2)" class="filter-clear-btn">Limpar</button>
        <span v-if="count2 != null" class="text-[10px] text-gray-600">{{ count2 }} pontos</span>
      </div>
      <ScatterChart
        ref="chart2"
        v-if="display2"
        :chartJson="display2"
        :key="key2"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este grafico</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'
import { filterChart } from '@/api/client.js'
import ScatterChart from './ScatterChart.vue'

const store = useDashboardStore()
const activeTab = ref(0)

const chart0 = ref(null)
const chart1 = ref(null)
const chart2 = ref(null)
const chartRefs = [chart0, chart1, chart2]

watch(activeTab, async (i) => {
  await nextTick()
  chartRefs[i]?.value?.resize()
})

const tabs = [
  { label: 'Retorno vs Drawdown' },
  { label: 'Retorno vs Sharpe' },
  { label: 'Retorno vs Trades' },
]

// Inputs do usuario
const f0 = reactive({ returnMin: '', ddMax: '' })
const f1 = reactive({ returnMin: '', sharpeMin: '' })
const f2 = reactive({ returnMin: '', tradesMin: '' })

// Estado dos displays
const display0 = ref(null)
const display1 = ref(null)
const display2 = ref(null)
const count0 = ref(null)
const count1 = ref(null)
const count2 = ref(null)
const isFiltered0 = ref(false)
const isFiltered1 = ref(false)
const isFiltered2 = ref(false)
const loading0 = ref(false)
const loading1 = ref(false)
const loading2 = ref(false)
const key0 = ref(0)
const key1 = ref(0)
const key2 = ref(0)

// Sync com o store quando carrega dados novos
watch(() => store.charts.return_vs_drawdown, (v) => {
  if (!isFiltered0.value) { display0.value = v; key0.value++ }
}, { immediate: true })
watch(() => store.charts.return_vs_sharpe, (v) => {
  if (!isFiltered1.value) { display1.value = v; key1.value++ }
}, { immediate: true })
watch(() => store.charts.return_vs_trades, (v) => {
  if (!isFiltered2.value) { display2.value = v; key2.value++ }
}, { immediate: true })

function parseNum(v) {
  if (v === '' || v === null || v === undefined) return null
  const n = Number(v)
  return isNaN(n) ? null : n
}

async function applyFilter(tab) {
  const rows = store.rawRows
  if (!rows.length) return

  if (tab === 0) {
    const rMin = parseNum(f0.returnMin)
    const dMax = parseNum(f0.ddMax)
    if (rMin === null && dMax === null) return
    loading0.value = true
    try {
      const { data } = await filterChart(rows, 'return_vs_drawdown', {
        return_min: rMin,
        dd_max: dMax,
      })
      display0.value = data.chart
      count0.value = data.count
      isFiltered0.value = true
      key0.value++
    } finally {
      loading0.value = false
    }
  } else if (tab === 1) {
    const rMin = parseNum(f1.returnMin)
    const sMin = parseNum(f1.sharpeMin)
    if (rMin === null && sMin === null) return
    loading1.value = true
    try {
      const { data } = await filterChart(rows, 'return_vs_sharpe', {
        return_min: rMin,
        sharpe_min: sMin,
      })
      display1.value = data.chart
      count1.value = data.count
      isFiltered1.value = true
      key1.value++
    } finally {
      loading1.value = false
    }
  } else if (tab === 2) {
    const rMin = parseNum(f2.returnMin)
    const tMin = parseNum(f2.tradesMin)
    if (rMin === null && tMin === null) return
    loading2.value = true
    try {
      const { data } = await filterChart(rows, 'return_vs_trades', {
        return_min: rMin,
        trades_min: tMin,
      })
      display2.value = data.chart
      count2.value = data.count
      isFiltered2.value = true
      key2.value++
    } finally {
      loading2.value = false
    }
  }
}

function clearFilter(tab) {
  if (tab === 0) {
    f0.returnMin = ''; f0.ddMax = ''
    display0.value = store.charts.return_vs_drawdown
    count0.value = null; isFiltered0.value = false; key0.value++
  } else if (tab === 1) {
    f1.returnMin = ''; f1.sharpeMin = ''
    display1.value = store.charts.return_vs_sharpe
    count1.value = null; isFiltered1.value = false; key1.value++
  } else if (tab === 2) {
    f2.returnMin = ''; f2.tradesMin = ''
    display2.value = store.charts.return_vs_trades
    count2.value = null; isFiltered2.value = false; key2.value++
  }
}

async function onPointClicked(rank) {
  await store.selectStrategy(rank)
  setTimeout(() => {
    document.querySelector('.strategy-detail-anchor')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}
</script>

<style scoped>
.chart-filter-input {
  @apply bg-surface-700 border border-surface-500 rounded px-2 py-1 text-xs text-gray-300 w-20
         focus:border-accent-yellow/50 focus:outline-none;
}
.filter-btn {
  @apply px-3 py-1 text-[10px] font-semibold rounded bg-accent-yellow/15 text-accent-yellow
         border border-accent-yellow/30 hover:bg-accent-yellow/25 transition-colors
         disabled:opacity-50 min-w-[50px] text-center;
}
.filter-clear-btn {
  @apply px-2 py-1 text-[10px] text-gray-500 hover:text-gray-300 transition-colors;
}
</style>
