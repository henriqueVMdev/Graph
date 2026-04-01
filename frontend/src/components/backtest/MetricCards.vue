<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-11 gap-2">
    <div class="metric-card">
      <span class="metric-label">Capital</span>
      <span class="metric-value text-gray-100">${{ fmtMoney(metrics.final_equity) }}</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Retorno</span>
      <span class="metric-value" :class="metrics.total_return >= 0 ? 'text-accent-green-light' : 'text-accent-red-light'">
        {{ fmtPct(metrics.total_return) }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Max DD</span>
      <span class="metric-value text-accent-red-light">{{ fmtPct(metrics.max_dd) }}</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Trades</span>
      <span class="metric-value text-gray-100">{{ metrics.total_trades ?? '-' }}</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Win Rate</span>
      <span class="metric-value" :class="metrics.win_rate >= 50 ? 'text-accent-green-light' : 'text-accent-red-light'">
        {{ fmtPct(metrics.win_rate, 1) }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Profit F.</span>
      <span class="metric-value"
        :class="metrics.profit_factor == null ? 'text-gray-400' : metrics.profit_factor >= 1.5 ? 'text-accent-green-light' : metrics.profit_factor >= 1 ? 'text-accent-yellow' : 'text-accent-red-light'"
      >
        {{ metrics.profit_factor != null ? Number(metrics.profit_factor).toFixed(2) : '∞' }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Sortino</span>
      <span class="metric-value" :class="(metrics.sortino ?? 0) >= 1 ? 'text-accent-green-light' : 'text-gray-100'">
        {{ metrics.sortino != null ? Number(metrics.sortino).toFixed(2) : '-' }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Calmar</span>
      <span class="metric-value" :class="(metrics.calmar ?? 0) >= 3 ? 'text-accent-green-light' : (metrics.calmar ?? 0) >= 1 ? 'text-accent-yellow' : 'text-gray-100'">
        {{ metrics.calmar != null ? Number(metrics.calmar).toFixed(2) : '-' }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Omega</span>
      <span class="metric-value" :class="(metrics.omega ?? 0) >= 1.5 ? 'text-accent-green-light' : (metrics.omega ?? 0) >= 1 ? 'text-accent-yellow' : 'text-accent-red-light'">
        {{ metrics.omega != null ? Number(metrics.omega).toFixed(2) : '-' }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Sterling</span>
      <span class="metric-value" :class="(metrics.sterling ?? 0) >= 3 ? 'text-accent-green-light' : (metrics.sterling ?? 0) >= 1 ? 'text-accent-yellow' : 'text-gray-100'">
        {{ metrics.sterling != null ? Number(metrics.sterling).toFixed(2) : '-' }}
      </span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Burke</span>
      <span class="metric-value" :class="(metrics.burke ?? 0) >= 1 ? 'text-accent-green-light' : 'text-gray-100'">
        {{ metrics.burke != null ? Number(metrics.burke).toFixed(2) : '-' }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  metrics: { type: Object, required: true }
})

function fmtPct(v, dec = 2) {
  if (v == null) return '-'
  const n = Number(v)
  return (n >= 0 ? '+' : '') + n.toFixed(dec) + '%'
}

function fmtMoney(v) {
  if (v == null) return '-'
  return Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
