<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
    <div class="metric-card">
      <span class="metric-label">Total Parâmetros</span>
      <span class="metric-value text-gray-100">{{ summary?.total_params ?? '-' }}</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Retorno Médio</span>
      <span class="metric-value" :class="returnClass">
        {{ formatPct(summary?.avg_return) }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Sharpe Médio</span>
      <span class="metric-value" :class="sharpeClass">
        {{ formatNum(summary?.avg_sharpe) }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Melhor Score</span>
      <span class="metric-value text-accent-yellow">
        {{ formatNum(summary?.best_score) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'

const store = useDashboardStore()
const summary = computed(() => store.summary)

const returnClass = computed(() => {
  const v = summary.value?.avg_return
  if (v == null) return 'text-gray-400'
  return v >= 0 ? 'text-accent-green-light' : 'text-accent-red-light'
})

const sharpeClass = computed(() => {
  const v = summary.value?.avg_sharpe
  if (v == null) return 'text-gray-400'
  return v >= 1 ? 'text-accent-green-light' : v >= 0 ? 'text-accent-yellow' : 'text-accent-red-light'
})

function formatPct(v) {
  if (v == null) return '-'
  const n = Number(v)
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
}

function formatNum(v) {
  if (v == null) return '-'
  return Number(v).toFixed(2)
}
</script>
