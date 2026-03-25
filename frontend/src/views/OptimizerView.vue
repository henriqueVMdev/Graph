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
        <svg class="w-12 h-12 text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
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
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-400">
            <span class="font-semibold text-gray-200">{{ store.results.symbol }}</span>
            <span v-if="store.results.interval !== '-'"> / {{ store.results.interval }}</span>
            <span v-if="store.selectedStrategy" class="text-gray-500"> - {{ store.selectedStrategy.name }}</span>
          </div>
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
        <div v-if="store.results.best" class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">1.</span> Melhor Configuracao</h2>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">Metricas</h3>
              <div class="space-y-1">
                <div v-for="col in metricCols" :key="col" class="flex justify-between text-sm">
                  <span class="text-gray-500">{{ col }}</span>
                  <span class="text-gray-200 font-medium">{{ formatVal(store.results.best[col]) }}</span>
                </div>
              </div>
            </div>
            <div>
              <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">Parametros</h3>
              <div class="space-y-1">
                <div v-for="col in paramCols" :key="col" class="flex justify-between text-sm">
                  <span class="text-gray-500">{{ col }}</span>
                  <span class="text-gray-200 font-medium">{{ formatVal(store.results.best[col]) }}</span>
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
  const pShort = paramCols.value.slice(0, 4)
  return [...metricCols.value, ...pShort]
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
