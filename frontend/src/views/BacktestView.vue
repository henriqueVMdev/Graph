<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <BacktestSidebar
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
      <!-- Parâmetros carregados banner -->
      <div v-if="paramsBanner" class="card p-3 border-accent-yellow/40 bg-accent-yellow/5 text-accent-yellow text-sm flex items-center justify-between">
        <span class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Parametros carregados automaticamente
        </span>
        <button @click="paramsBanner = false" class="text-gray-400 hover:text-gray-200">✕</button>
      </div>

      <!-- Error -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- No results placeholder -->
      <div v-if="!store.results && !store.isRunning" class="flex flex-col items-center justify-center h-64 text-center">
        <p class="text-gray-400 text-sm">Configure os parâmetros e clique em "Executar Backtest"</p>
      </div>

      <!-- Running spinner -->
      <div v-if="store.isRunning" class="flex flex-col items-center justify-center h-64">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Executando backtest...</p>
      </div>

      <!-- Results -->
      <template v-if="store.results && !store.isRunning">
        <div class="text-sm text-gray-400">
          <span class="font-semibold text-gray-200">{{ store.results.symbol }}</span>
          <span v-if="store.results.interval !== '-'"> · {{ store.results.interval }}</span>
        </div>

        <!-- Metric cards -->
        <MetricCards :metrics="store.results.metrics" />

        <!-- Risk Radar -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Radar de Risco</h2>
          <RiskRadar :metrics="store.results.metrics" />
        </div>

        <!-- Equity curve -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Oscilação de Capital</h2>
          <EquityCurve
            :equityCurve="store.results.equity_curve"
            :trades="store.results.trades"
            :initialCapital="store.results.metrics.initial_capital"
          />
        </div>

        <!-- Walk-Forward Analysis -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Walk-Forward Analysis</h2>
          <WalkForwardSection />
        </div>

        <!-- Monte Carlo -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Monte Carlo · Simulação de Capital</h2>
          <MonteCarloSection :equityCurve="store.results.equity_curve" />
        </div>

        <!-- Correlation section -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Correlação e Distribuição de Retornos</h2>
          <CorrelationSection />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const sidebarOpen = ref(true)
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}
import { useBacktestStore } from '@/stores/backtest.js'
import BacktestSidebar from '@/components/backtest/BacktestSidebar.vue'
import MetricCards from '@/components/backtest/MetricCards.vue'
import RiskRadar from '@/components/backtest/RiskRadar.vue'
import EquityCurve from '@/components/backtest/EquityCurve.vue'
import MonteCarloSection from '@/components/backtest/MonteCarloSection.vue'
import CorrelationSection from '@/components/backtest/CorrelationSection.vue'
import WalkForwardSection from '@/components/backtest/WalkForwardSection.vue'

const store = useBacktestStore()
const paramsBanner = ref(false)

onMounted(async () => {
  await Promise.all([store.fetchAssets(), store.fetchStrategies()])
  if (store.pendingParams) {
    const flags = store.applyPendingParams()
    paramsBanner.value = true
    if (flags?.autoRun) {
      store.runBacktest()
    }
  }
})
</script>
