<template>
  <div>
    <div class="flex gap-6 items-center">
      <div ref="chartEl" class="w-1/2 shrink-0" style="height:300px"></div>
      <div class="flex-1 space-y-2">
        <div
          v-for="(label, i) in LABELS" :key="label"
          class="flex items-center justify-between px-3 py-2.5 rounded-lg bg-surface-800/60 border border-surface-600/50"
        >
          <div class="flex-1 min-w-0 mr-3">
            <div class="text-xs text-gray-400 mb-1">{{ label }}</div>
            <div class="h-1 bg-surface-600 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="barColor(KEYS[i])"
                :style="{ width: barWidth(KEYS[i]) + '%' }"
              />
            </div>
          </div>
          <span class="text-base font-bold font-mono shrink-0" :class="valueClass(KEYS[i])">
            {{ metrics[KEYS[i]] != null ? Number(metrics[KEYS[i]]).toFixed(2) : '-' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  metrics: { type: Object, required: true },
})

const chartEl = ref(null)

const LABELS = ['Sharpe', 'Sortino', 'Calmar', 'Omega', 'Sterling', 'Burke']
const KEYS   = ['sharpe', 'sortino', 'calmar', 'omega', 'sterling', 'burke']

const CAPS = { sharpe: 5, sortino: 8, calmar: 10, omega: 4, sterling: 10, burke: 5 }

const THRESHOLDS = {
  sharpe:  { good: 1.5, ok: 1 },
  sortino: { good: 2,   ok: 1 },
  calmar:  { good: 3,   ok: 1 },
  omega:   { good: 1.5, ok: 1 },
  sterling:{ good: 3,   ok: 1 },
  burke:   { good: 1,   ok: 0.5 },
}

function valueClass(key) {
  const v = props.metrics[key]
  if (v == null) return 'text-gray-500'
  const t = THRESHOLDS[key]
  if (v >= t.good) return 'text-green-400'
  if (v >= t.ok)   return 'text-accent-yellow'
  return 'text-red-400'
}

function barColor(key) {
  const v = props.metrics[key]
  if (v == null) return 'bg-surface-500'
  const t = THRESHOLDS[key]
  if (v >= t.good) return 'bg-green-500'
  if (v >= t.ok)   return 'bg-accent-yellow'
  return 'bg-red-500'
}

function barWidth(key) {
  const v = props.metrics[key]
  if (v == null || v <= 0) return 0
  const cap = CAPS[key] || 5
  return Math.min(v / cap * 100, 100)
}

function normalize(val, key) {
  if (val == null) {
    // null para omega/profit_factor = sem perdas = maximo
    if (key === 'omega') return 100
    return 0
  }
  if (val === 0) return 0
  const caps = {
    sharpe: 5, sortino: 8, calmar: 10,
    omega: 4, sterling: 10, burke: 5,
  }
  const cap = caps[key] || 5
  return Math.min(Math.max(val, 0), cap) / cap * 100
}

function buildChart() {
  if (!chartEl.value || !props.metrics) return

  const values = KEYS.map(k => normalize(props.metrics[k], k))
  values.push(values[0])
  const labels = [...LABELS, LABELS[0]]

  const rawValues = KEYS.map(k => {
    const v = props.metrics[k]
    if (v == null) return (k === 'omega') ? '∞' : '0'
    return Number(v).toFixed(2)
  })
  rawValues.push(rawValues[0])

  const hoverText = labels.map((l, i) => `${l}: ${rawValues[i]}`)

  const trace = {
    type: 'scatterpolar',
    r: values,
    theta: labels,
    fill: 'toself',
    fillcolor: 'rgba(245, 197, 24, 0.15)',
    line: { color: '#f5c518', width: 2 },
    marker: { color: '#f5c518', size: 5 },
    text: hoverText,
    hoverinfo: 'text',
    name: 'Estrategia',
  }

  const layout = {
    polar: {
      bgcolor: '#080808',
      radialaxis: {
        visible: true,
        range: [0, 100],
        showticklabels: false,
        gridcolor: '#1e1e1e',
        linecolor: '#2a2a2a',
      },
      angularaxis: {
        gridcolor: '#1e1e1e',
        linecolor: '#2a2a2a',
        tickfont: { color: '#d0d0d0', size: 12 },
      },
    },
    paper_bgcolor: '#000000',
    font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif' },
    margin: { t: 30, r: 40, b: 30, l: 40 },
    showlegend: false,
    hoverlabel: {
      bgcolor: '#0f0f0f',
      bordercolor: '#f5c518',
      font: { color: '#e0e0e0' },
    },
  }

  Plotly.react(chartEl.value, [trace], layout, {
    responsive: true,
    displayModeBar: false,
  })
}

onMounted(buildChart)
watch(() => props.metrics, buildChart, { deep: true })

onBeforeUnmount(() => {
  if (chartEl.value) Plotly.purge(chartEl.value)
})
</script>
