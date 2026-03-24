<template>
  <div>
    <h2 class="text-sm font-semibold text-gray-200 mb-3"><span class="text-accent-yellow">◆</span> Análise Visual</h2>

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

    <!-- Charts -->
    <div v-show="activeTab === 0">
      <ScatterChart
        ref="chart0"
        v-if="charts.return_vs_drawdown"
        :chartJson="charts.return_vs_drawdown"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este gráfico</p>
    </div>
    <div v-show="activeTab === 1">
      <ScatterChart
        ref="chart1"
        v-if="charts.return_vs_sharpe"
        :chartJson="charts.return_vs_sharpe"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este gráfico</p>
    </div>
    <div v-show="activeTab === 2">
      <ScatterChart
        ref="chart2"
        v-if="charts.return_vs_trades"
        :chartJson="charts.return_vs_trades"
        @point-clicked="onPointClicked"
      />
      <p v-else class="text-gray-500 text-sm text-center py-8">Dados insuficientes para este gráfico</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'
import ScatterChart from './ScatterChart.vue'

const store = useDashboardStore()
const charts = computed(() => store.charts)
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

async function onPointClicked(rank) {
  await store.selectStrategy(rank)
  // Scroll to detail
  setTimeout(() => {
    document.querySelector('.strategy-detail-anchor')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}
</script>
