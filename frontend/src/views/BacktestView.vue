<template>
  <WorkspaceShell width="18rem">
    <template #sidebar>
      <BacktestSidebar />
    </template>

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
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-400">
            <span class="font-semibold text-gray-200">{{ store.results.symbol }}</span>
            <span v-if="store.results.interval !== '-'"> · {{ store.results.interval }}</span>
          </div>
          <button
            @click="sendToAutomation"
            :disabled="!store.selectedStrategy?.automatable"
            :title="store.selectedStrategy?.automatable
              ? 'Cria um deployment paper/demo com esta config'
              : 'Estratégia sem signal() — não automatizável'"
            class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-accent-yellow/15 text-accent-yellow
                   hover:bg-accent-yellow/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ⚡ Enviar para Automação
          </button>
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

        <!-- Gráficos de análise: candles + indicadores + funding + equity líquido -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Análise Gráfica · Candles, Indicadores, Funding e Equity Líquido</h2>
          <AnalysisCharts />
        </div>

        <!-- Drawdown -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Analise de Drawdown</h2>
          <DrawdownSection
            :metrics="store.results.metrics"
            :drawdown="store.results.drawdown"
          />
        </div>

        <!-- Custos: Fees + Funding (bruto vs líquido) -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Custos Reais · Fees + Funding (bruto vs líquido)</h2>
          <CostsSection />
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
</WorkspaceShell>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'
import BacktestSidebar from '@/components/backtest/BacktestSidebar.vue'
import MetricCards from '@/components/backtest/MetricCards.vue'
import RiskRadar from '@/components/backtest/RiskRadar.vue'
import EquityCurve from '@/components/backtest/EquityCurve.vue'
import MonteCarloSection from '@/components/backtest/MonteCarloSection.vue'
import CorrelationSection from '@/components/backtest/CorrelationSection.vue'
import WalkForwardSection from '@/components/backtest/WalkForwardSection.vue'
import DrawdownSection from '@/components/backtest/DrawdownSection.vue'
import CostsSection from '@/components/backtest/CostsSection.vue'
import AnalysisCharts from '@/components/backtest/AnalysisCharts.vue'

const store = useBacktestStore()
const paramsBanner = ref(false)

// ── Enviar para Automação ──────────────────────────────────────────────
import { useRouter } from 'vue-router'
import { useAutomationStore } from '@/stores/automation.js'
import WorkspaceShell from '@/components/layout/WorkspaceShell.vue'
const router = useRouter()
const autoStore = useAutomationStore()

function sendToAutomation() {
  const m = store.results?.metrics || {}
  autoStore.pendingDeployment = {
    strategy_file: store.selectedStrategy?.file,
    params: { ...store.params },
    symbol: store.selectedSymbol || store.results?.symbol,
    interval: store.interval,
    exchange: 'bybit',
    backtest_ref: {
      win_rate: m.win_rate,
      profit_factor: m.profit_factor,
      avg_win: m.avg_win,
      avg_loss: m.avg_loss,
      total_trades: m.total_trades,
      total_return: m.total_return,
      source: 'backtest',
    },
  }
  router.push('/automation')
}

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
