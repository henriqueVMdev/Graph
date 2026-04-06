<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <OptimizerSidebar
      class="shrink-0 transition-all duration-300 overflow-hidden"
      :class="sidebarOpen ? 'w-72' : 'w-0'"
    />

    <!-- Toggle button -->
    <button
      @click="toggleSidebar"
      class="absolute top-1/2 -translate-y-1/2 z-20 w-4 h-10 flex items-center justify-center rounded-r-md bg-surface-700/60 hover:bg-surface-600/80 border-y border-r border-surface-500/50 text-gray-600 hover:text-gray-300 transition-all duration-300"
      :style="sidebarOpen ? 'left: calc(18rem - 1px)' : 'left: 0'"
      :title="sidebarOpen ? 'Recolher' : 'Expandir'"
    >
      <svg class="w-2.5 h-2.5 transition-transform duration-300" :class="sidebarOpen ? '' : 'rotate-180'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
      </svg>
    </button>

    <!-- Main content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Error -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- Placeholder -->
      <div v-if="!store.results && !store.isRunning" class="flex flex-col items-center justify-center h-64 text-center">
        <p class="text-gray-400 text-sm">Configure o grid de parametros e clique em "Rodar Otimizacao"</p>
      </div>

      <!-- Running -->
      <div v-if="store.isRunning" class="flex flex-col items-center justify-center h-64">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">
          <template v-if="store.progress.total > 0">
            Testando {{ store.progress.current }} / {{ store.progress.total }}
            ({{ store.progress.valid }} validos)
          </template>
          <template v-else>
            Preparando dados...
          </template>
        </p>
      </div>

      <!-- Results -->
      <template v-if="store.results && !store.isRunning">
        <!-- Header -->
        <div class="card p-3 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2 text-sm">
              <span class="text-xs text-gray-500">Ativo</span>
              <span class="font-semibold text-gray-200">{{ store.results.symbol || '-' }}</span>
            </div>
            <span class="text-surface-500">|</span>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-xs text-gray-500">Timeframe</span>
              <span class="font-semibold text-gray-200">{{ store.results.interval || '-' }}</span>
            </div>
            <span v-if="store.selectedStrategy" class="text-surface-500">|</span>
            <div v-if="store.selectedStrategy" class="flex items-center gap-2 text-sm">
              <span class="text-xs text-gray-500">Estrategia</span>
              <span class="font-semibold text-gray-200">{{ store.selectedStrategy.name }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="sendToBacktest()"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/30 hover:bg-green-500/20 transition"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              Testar no Backtest
            </button>
            <button
              @click="store.downloadCsv()"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30 hover:bg-accent-yellow/20 transition"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Baixar CSV ({{ store.results.valid_count }} resultados)
            </button>
          </div>
        </div>

        <!-- Metric cards -->
        <div class="grid grid-cols-4 gap-3">
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-1">Configs Testadas</div>
            <div class="text-lg font-bold text-gray-200">{{ store.results.total_tested?.toLocaleString() }}</div>
          </div>
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-1">Configs Validas</div>
            <div class="text-lg font-bold text-accent-yellow">{{ store.results.valid_count?.toLocaleString() }}</div>
          </div>
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-1">Tempo</div>
            <div class="text-lg font-bold text-gray-200">{{ store.results.elapsed }}s</div>
          </div>
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-1">Melhor {{ store.rankBy }}</div>
            <div class="text-lg font-bold text-green-400">{{ bestScore }}</div>
          </div>
        </div>

        <!-- Best config -->
        <div v-if="store.results.best" class="card p-4 overflow-hidden">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">1.</span> Melhor Configuracao</h2>
          <div class="grid grid-cols-2 gap-4">
            <div class="min-w-0">
              <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">Metricas</h3>
              <div class="divide-y divide-surface-600">
                <div v-for="col in metricCols" :key="col" class="flex justify-between items-center gap-2 py-1.5 px-2 rounded hover:bg-surface-700/50">
                  <span class="text-gray-400 text-sm truncate shrink">{{ col }}</span>
                  <span class="text-sm font-bold tabular-nums shrink-0" :class="metricValClass(col, store.results.best[col])">
                    {{ formatVal(store.results.best[col]) }}
                  </span>
                </div>
              </div>
            </div>
            <div class="min-w-0">
              <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">Parametros</h3>
              <div class="divide-y divide-surface-600">
                <div v-for="col in paramCols" :key="col" class="flex justify-between items-center gap-2 py-1.5 px-2 rounded hover:bg-surface-700/50">
                  <span class="text-gray-400 text-sm truncate shrink">{{ col }}</span>
                  <span class="text-sm font-bold text-accent-yellow tabular-nums shrink-0">
                    {{ formatVal(store.results.best[col]) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Results table -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">Top {{ store.results.results?.length }}</span> Resultados
          </h2>
          <div class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-surface-500">
                  <th class="th">#</th>
                  <th v-for="col in tableCols" :key="col" class="th">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in store.results.results" :key="row.Rank"
                  class="border-b border-surface-700 hover:bg-surface-700/50 transition">
                  <td class="td text-accent-yellow font-bold">{{ row.Rank }}</td>
                  <td v-for="col in tableCols" :key="col" class="td"
                    :class="colClass(col, row[col])">
                    {{ formatVal(row[col]) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- CSV saved notice -->
        <div v-if="store.results.csv_filename" class="text-xs text-gray-500 text-center">
          CSV salvo em: data/{{ store.results.csv_filename }}
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useOptimizerStore } from '@/stores/optimizer.js'
import OptimizerSidebar from '@/components/optimizer/OptimizerSidebar.vue'

const store = useOptimizerStore()
const router = useRouter()

// Quando a otimizacao termina, envia o melhor resultado pro backtest
watch(() => store.isRunning, (running, wasRunning) => {
  if (wasRunning && !running && store.results?.best) {
    store.sendBestToBacktest()
    router.push('/backtest')
  }
})

function sendToBacktest() {
  if (store.sendBestToBacktest()) {
    router.push('/backtest')
  }
}

const sidebarOpen = ref(true)
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}

// Colunas dinamicas vindas do resultado
const metricCols = computed(() => {
  return store.results?.metric_columns || ['Retorno (%)', 'Max DD (%)', 'Trades', 'Win Rate (%)', 'Profit Factor', 'Sharpe', 'Score']
})

const paramCols = computed(() => {
  return store.results?.param_columns || []
})

const tableCols = computed(() => {
  return [...metricCols.value, ...paramCols.value]
})

const bestScore = computed(() => {
  if (!store.results?.best) return '-'
  const val = store.results.best[store.rankBy]
  return val != null ? Number(val).toFixed(2) : '-'
})

function formatVal(v) {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'boolean') return v ? 'SIM' : 'NAO'
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(2)
  return String(v)
}

function metricValClass(col, val) {
  if (typeof val !== 'number') return 'text-gray-100'
  if (col === 'Retorno (%)' || col === 'Sharpe' || col === 'Profit Factor' || col === 'Score') {
    return val >= 0 ? 'text-green-400' : 'text-red-400'
  }
  if (col === 'Max DD (%)') return 'text-red-400'
  if (col === 'Win Rate (%)') return val >= 50 ? 'text-green-400' : 'text-amber-400'
  return 'text-gray-100'
}

function colClass(col, val) {
  if (col === 'Retorno (%)' && typeof val === 'number') {
    return val >= 0 ? 'text-green-400' : 'text-red-400'
  }
  if (col === 'Max DD (%)' && typeof val === 'number') {
    return 'text-red-400'
  }
  return 'text-gray-300'
}

onMounted(async () => {
  await Promise.all([store.fetchAssets(), store.fetchStrategies()])
})
</script>

<style scoped>
.th {
  @apply px-2 py-2 text-left text-gray-500 font-medium whitespace-nowrap;
}
.td {
  @apply px-2 py-1.5 whitespace-nowrap;
}
</style>
