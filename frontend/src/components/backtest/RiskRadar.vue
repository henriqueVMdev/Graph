<template>
  <div ref="chartEl" style="width:100%;height:380px"></div>
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

function normalize(val, key) {
  if (val == null || val === 0) return 0
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
    return v != null ? Number(v).toFixed(2) : '0'
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
