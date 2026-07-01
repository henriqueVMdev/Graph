<template>
  <div ref="chartEl" class="w-full h-full min-h-[260px]" />
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { getPlotly } from '@/composables/plotly.js'

let Plotly = null

const props = defineProps({
  curve: { type: Array, default: () => [] },
  capitalInicial: { type: Number, default: 0 },
})

const chartEl = ref(null)

async function build() {
  if (!chartEl.value) return
  if (!Plotly) Plotly = await getPlotly()

  const pts = props.curve || []
  const x = pts.map((p, i) => p.date || `#${i + 1}`)
  const y = pts.map((p) => p.capital)

  // Inclui o ponto inicial para a curva começar no capital base
  if (pts.length) {
    x.unshift('Início')
    y.unshift(props.capitalInicial)
  }

  const up = y.length && y[y.length - 1] >= props.capitalInicial
  const color = up ? '#f5c518' : '#f87171'

  const trace = {
    type: 'scatter',
    mode: 'lines',
    x,
    y,
    fill: 'tozeroy',
    fillcolor: up ? 'rgba(245,197,24,0.08)' : 'rgba(248,113,113,0.08)',
    line: { color, width: 2, shape: 'spline', smoothing: 0.4 },
    hovertemplate: '<b>%{x}</b><br>$ %{y:,.2f}<extra></extra>',
  }

  const layout = {
    margin: { l: 56, r: 16, t: 12, b: 36 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#9ca3af', family: 'Inter, sans-serif', size: 11 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.04)', zeroline: false },
    yaxis: {
      gridcolor: 'rgba(255,255,255,0.04)', zeroline: false,
      tickprefix: '$ ', tickformat: ',.0f',
    },
    shapes: props.capitalInicial
      ? [{
          type: 'line', x0: 0, x1: 1, xref: 'paper',
          y0: props.capitalInicial, y1: props.capitalInicial,
          line: { color: 'rgba(156,163,175,0.4)', width: 1, dash: 'dot' },
        }]
      : [],
    showlegend: false,
  }

  Plotly.react(chartEl.value, [trace], layout, { displayModeBar: false, responsive: true })
}

onMounted(build)
watch(() => [props.curve, props.capitalInicial], build, { deep: true })
onBeforeUnmount(() => {
  if (chartEl.value && Plotly) Plotly.purge(chartEl.value)
})
</script>
