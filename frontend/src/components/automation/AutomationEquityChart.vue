<template>
  <div ref="chartEl" class="w-full h-full min-h-[240px]" />
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { getPlotly } from '@/composables/plotly.js'

let Plotly = null

const props = defineProps({
  curve: { type: Object, default: () => ({ dates: [], values: [] }) },
  initialCapital: { type: Number, default: 0 },
})

const chartEl = ref(null)

async function build() {
  if (!chartEl.value) return
  if (!Plotly) Plotly = await getPlotly()

  const x = props.curve?.dates || []
  const y = props.curve?.values || []
  const up = y.length && y[y.length - 1] >= props.initialCapital
  const color = up ? '#f5c518' : '#f87171'

  const trace = {
    type: 'scatter',
    mode: 'lines',
    x,
    y,
    fill: 'tozeroy',
    fillcolor: up ? 'rgba(245,197,24,0.08)' : 'rgba(248,113,113,0.08)',
    line: { color, width: 2 },
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
    shapes: props.initialCapital
      ? [{
          type: 'line', x0: 0, x1: 1, xref: 'paper',
          y0: props.initialCapital, y1: props.initialCapital,
          line: { color: 'rgba(156,163,175,0.4)', width: 1, dash: 'dot' },
        }]
      : [],
    showlegend: false,
  }

  Plotly.react(chartEl.value, [trace], layout, { displayModeBar: false, responsive: true })
}

onMounted(build)
watch(() => [props.curve, props.initialCapital], build, { deep: true })
onBeforeUnmount(() => {
  if (chartEl.value && Plotly) Plotly.purge(chartEl.value)
})
</script>
