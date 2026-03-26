<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <PropChallengeSidebar
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
      <!-- Parametros carregados banner -->
      <div v-if="paramsBanner" class="card p-3 border-accent-yellow/40 bg-accent-yellow/5 text-accent-yellow text-sm flex items-center justify-between">
        <span class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Parametros carregados do Dashboard
        </span>
        <button @click="paramsBanner = false" class="text-gray-400 hover:text-gray-200">x</button>
      </div>

      <!-- Error -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- No results placeholder -->
      <div v-if="!store.results && !store.isRunning" class="flex flex-col items-center justify-center h-64 text-center">
        <svg class="w-12 h-12 text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p class="text-gray-400 text-sm">Configure a estrategia e clique em "Simular Desafio"</p>
      </div>

      <!-- Running spinner -->
      <div v-if="store.isRunning" class="flex flex-col items-center justify-center h-64">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Simulando desafio prop...</p>
      </div>

      <!-- Results -->
      <template v-if="store.results && !store.isRunning">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-400">
            <span class="font-semibold text-gray-200">{{ store.results.symbol }}</span>
            <span v-if="store.results.interval !== '-'"> · {{ store.results.interval }}</span>
            <span> · {{ store.results.total_trades }} trades</span>
          </div>
          <div class="text-sm font-mono text-accent-yellow">
            ${{ store.results.account_size.toLocaleString() }}
          </div>
        </div>

        <!-- Probabilidade geral -->
        <div class="card p-6 text-center border-accent-yellow/30">
          <p class="text-xs text-gray-500 uppercase tracking-widest mb-2">Probabilidade de Aprovacao</p>
          <p class="text-5xl font-bold font-mono" :class="overallColor">
            {{ store.results.overall.pass_rate }}%
          </p>
          <p class="text-xs text-gray-500 mt-2">
            {{ store.results.overall.passed }} aprovados de {{ store.results.num_sims }} simulacoes
          </p>
        </div>

        <!-- Fases -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Fase 1 -->
          <div class="card p-4">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/50 text-blue-400 text-xs font-bold flex items-center justify-center">1</span>
              <h2 class="text-sm font-semibold text-gray-200">Fase 1 - Avaliacao</h2>
            </div>
            <div class="space-y-2">
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Meta</span>
                <span class="text-green-400 font-mono">+{{ store.results.phase1.target_pct }}%</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Taxa de Aprovacao</span>
                <span class="font-mono font-bold" :class="store.results.phase1.pass_rate >= 50 ? 'text-green-400' : 'text-red-400'">
                  {{ store.results.phase1.pass_rate }}%
                </span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Aprovados / Reprovados</span>
                <span class="font-mono text-gray-300">{{ store.results.phase1.passed }} / {{ store.results.phase1.failed }}</span>
              </div>
              <!-- Progress bar -->
              <div class="w-full bg-surface-600 rounded-full h-2 mt-1">
                <div
                  class="h-2 rounded-full transition-all duration-500"
                  :class="store.results.phase1.pass_rate >= 50 ? 'bg-green-500' : 'bg-red-500'"
                  :style="{ width: store.results.phase1.pass_rate + '%' }"
                />
              </div>
            </div>
          </div>

          <!-- Fase 2 -->
          <div class="card p-4">
            <div class="flex items-center gap-2 mb-3">
              <span class="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/50 text-purple-400 text-xs font-bold flex items-center justify-center">2</span>
              <h2 class="text-sm font-semibold text-gray-200">Fase 2 - Verificacao</h2>
            </div>
            <div class="space-y-2">
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Meta</span>
                <span class="text-green-400 font-mono">+{{ store.results.phase2.target_pct }}%</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Taxa de Aprovacao (dos que passaram F1)</span>
                <span class="font-mono font-bold" :class="store.results.phase2.pass_rate >= 50 ? 'text-green-400' : 'text-red-400'">
                  {{ store.results.phase2.pass_rate }}%
                </span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-gray-400">Aprovados / Reprovados</span>
                <span class="font-mono text-gray-300">{{ store.results.phase2.passed }} / {{ store.results.phase2.failed }}</span>
              </div>
              <!-- Progress bar -->
              <div class="w-full bg-surface-600 rounded-full h-2 mt-1">
                <div
                  class="h-2 rounded-full transition-all duration-500"
                  :class="store.results.phase2.pass_rate >= 50 ? 'bg-green-500' : 'bg-red-500'"
                  :style="{ width: store.results.phase2.pass_rate + '%' }"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Trade Stats -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">*</span> Estatisticas dos Trades</h2>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div class="metric-card">
              <span class="metric-value text-lg">{{ store.results.trade_stats.total }}</span>
              <span class="metric-label">Trades</span>
            </div>
            <div class="metric-card">
              <span class="metric-value text-lg" :class="store.results.trade_stats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'">
                {{ store.results.trade_stats.win_rate }}%
              </span>
              <span class="metric-label">Win Rate</span>
            </div>
            <div class="metric-card">
              <span class="metric-value text-lg text-green-400">{{ store.results.trade_stats.avg_win.toFixed(2) }}%</span>
              <span class="metric-label">Media Win</span>
            </div>
            <div class="metric-card">
              <span class="metric-value text-lg text-red-400">{{ store.results.trade_stats.avg_loss.toFixed(2) }}%</span>
              <span class="metric-label">Media Loss</span>
            </div>
            <div class="metric-card">
              <span class="metric-value text-lg" :class="store.results.trade_stats.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ store.results.trade_stats.avg_pnl.toFixed(4) }}%
              </span>
              <span class="metric-label">Media P&L</span>
            </div>
          </div>
        </div>

        <!-- Equity Curves - Phase 1 -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">*</span> Simulacoes - Fase 1</h2>
          <div ref="phase1ChartEl" class="w-full" style="height: 350px" />
        </div>

        <!-- Equity Curves - Phase 2 -->
        <div v-if="store.results.phase2_curves.length > 0" class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">*</span> Simulacoes - Fase 2</h2>
          <div ref="phase2ChartEl" class="w-full" style="height: 350px" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { usePropChallengeStore } from '@/stores/propChallenge.js'
import PropChallengeSidebar from '@/components/propchallenge/PropChallengeSidebar.vue'

const store = usePropChallengeStore()
const sidebarOpen = ref(true)
const phase1ChartEl = ref(null)
const phase2ChartEl = ref(null)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}

const overallColor = computed(() => {
  if (!store.results) return 'text-gray-400'
  const rate = store.results.overall.pass_rate
  if (rate >= 60) return 'text-green-400'
  if (rate >= 30) return 'text-accent-yellow'
  return 'text-red-400'
})

const plotLayout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  margin: { t: 10, r: 20, b: 40, l: 60 },
  font: { color: '#9ca3af', size: 10 },
  xaxis: {
    title: 'Trades',
    gridcolor: '#1f1f1f',
    zeroline: false,
  },
  yaxis: {
    title: 'Saldo (USD)',
    gridcolor: '#1f1f1f',
    zeroline: false,
  },
  showlegend: false,
}

const plotConfig = {
  responsive: true,
  displayModeBar: false,
}

function drawChart(el, curves, accountSize, targetPct) {
  if (!el || !curves.length) return
  const traces = []

  // Curvas individuais
  for (const curve of curves) {
    const lastVal = curve[curve.length - 1]
    const passed = (lastVal - accountSize) / accountSize >= targetPct
    traces.push({
      x: Array.from({ length: curve.length }, (_, i) => i),
      y: curve,
      type: 'scatter',
      mode: 'lines',
      line: {
        color: passed ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)',
        width: 1,
      },
      hoverinfo: 'skip',
    })
  }

  // Linha de meta
  const maxLen = Math.max(...curves.map(c => c.length))
  traces.push({
    x: [0, maxLen],
    y: [accountSize * (1 + targetPct), accountSize * (1 + targetPct)],
    type: 'scatter',
    mode: 'lines',
    line: { color: '#22c55e', width: 2, dash: 'dash' },
    name: `Meta +${targetPct * 100}%`,
    hoverinfo: 'name',
  })

  // Linha de perda max
  traces.push({
    x: [0, maxLen],
    y: [accountSize * 0.9, accountSize * 0.9],
    type: 'scatter',
    mode: 'lines',
    line: { color: '#ef4444', width: 2, dash: 'dash' },
    name: 'Perda Max -10%',
    hoverinfo: 'name',
  })

  // Linha inicial
  traces.push({
    x: [0, maxLen],
    y: [accountSize, accountSize],
    type: 'scatter',
    mode: 'lines',
    line: { color: '#6b7280', width: 1, dash: 'dot' },
    name: 'Inicio',
    hoverinfo: 'name',
  })

  Plotly.newPlot(el, traces, { ...plotLayout, showlegend: true }, plotConfig)
}

watch(() => store.results, async (res) => {
  if (!res) return
  await nextTick()
  drawChart(phase1ChartEl.value, res.phase1_curves, res.account_size, 0.10)
  drawChart(phase2ChartEl.value, res.phase2_curves, res.account_size, 0.05)
})

const paramsBanner = ref(false)

onMounted(async () => {
  await Promise.all([store.fetchAssets(), store.fetchStrategies()])
  if (store.pendingParams) {
    store.applyPendingParams()
    paramsBanner.value = true
  }
})
</script>
