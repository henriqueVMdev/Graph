<template>
  <div ref="el" class="w-full h-full"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useChartStore } from '@/stores/chart.js'
import { getPlotly } from '@/composables/plotly.js'

const store = useChartStore()
const el = ref(null)
let Plotly = null

const BASE_LAYOUT = {
  paper_bgcolor: '#000000',
  plot_bgcolor: '#080808',
  font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 },
  margin: { t: 16, r: 60, b: 36, l: 12 },
  hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
  legend: { bgcolor: 'transparent', font: { size: 11, color: '#a0a0a0' }, orientation: 'h', x: 0, y: 1.06 },
}
const PLOT_CFG = {
  responsive: true, displaylogo: false, scrollZoom: true, displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
}

async function render() {
  if (!Plotly) Plotly = await getPlotly()
  await nextTick()
  if (!el.value || !store.chartData) return
  const c = store.chartData.candles
  if (!c?.dates?.length) return
  const ind = store.chartData.indicators || {}
  const trades = store.chartData.trades || []
  const ov = store.overlays

  const traces = [{
    type: 'candlestick', name: 'Preço', x: c.dates,
    open: c.open, high: c.high, low: c.low, close: c.close,
    increasing: { line: { color: '#26a69a' } }, decreasing: { line: { color: '#ef5350' } },
    yaxis: 'y',
  }]

  if (ov.volume && c.volume) {
    traces.push({
      type: 'bar', name: 'Volume', x: c.dates, y: c.volume, yaxis: 'y2', hoverinfo: 'skip',
      marker: { color: c.close.map((cl, i) => cl >= c.open[i] ? 'rgba(38,166,154,0.3)' : 'rgba(239,83,80,0.3)') },
    })
  }
  if (ov.indicators && ind.ma) traces.push({ type: 'scatter', mode: 'lines', name: 'MA', x: c.dates, y: ind.ma, line: { color: '#f5c518', width: 1.5 } })
  if (ov.indicators && ind.ma_slow) traces.push({ type: 'scatter', mode: 'lines', name: 'MM Lenta', x: c.dates, y: ind.ma_slow, line: { color: '#42a5f5', width: 1.5 } })

  if (ov.markers) {
    const longX = [], longY = [], shortX = [], shortY = [], exitX = [], exitY = []
    for (const t of trades) {
      const ed = new Date(t.entry_ts)
      if (t.direction === 1) { longX.push(ed); longY.push(t.entry_price) }
      else { shortX.push(ed); shortY.push(t.entry_price) }
      if (t.exit_ts) { exitX.push(new Date(t.exit_ts)); exitY.push(t.exit_price) }
    }
    if (longX.length) traces.push({ type: 'scatter', mode: 'markers', name: 'Entrada Long', x: longX, y: longY, marker: { symbol: 'triangle-up', size: 10, color: '#26a69a', line: { color: '#063', width: 1 } } })
    if (shortX.length) traces.push({ type: 'scatter', mode: 'markers', name: 'Entrada Short', x: shortX, y: shortY, marker: { symbol: 'triangle-down', size: 10, color: '#ef5350', line: { color: '#600', width: 1 } } })
    if (exitX.length) traces.push({ type: 'scatter', mode: 'markers', name: 'Saída', x: exitX, y: exitY, marker: { symbol: 'x', size: 8, color: 'rgba(200,200,200,0.8)' } })
  }

  // Stop / Alvo por trade como segmentos horizontais (entrada → saída)
  const shapes = []
  if (ov.stops) {
    for (const t of trades) {
      if (t.entry_ts && t.exit_ts && t.stop_price != null && t.target_price != null) {
        const x0 = new Date(t.entry_ts), x1 = new Date(t.exit_ts)
        shapes.push({ type: 'line', xref: 'x', yref: 'y', x0, x1, y0: t.stop_price, y1: t.stop_price, line: { color: 'rgba(239,83,80,0.7)', width: 1, dash: 'dot' } })
        shapes.push({ type: 'line', xref: 'x', yref: 'y', x0, x1, y0: t.target_price, y1: t.target_price, line: { color: 'rgba(38,166,154,0.7)', width: 1, dash: 'dot' } })
      }
    }
  }

  const volMax = (ov.volume && c.volume?.length) ? Math.max(...c.volume) : 1
  const layout = {
    ...BASE_LAYOUT, autosize: true, shapes, dragmode: 'pan', hovermode: 'x',
    xaxis: {
      type: 'date', gridcolor: '#161616', linecolor: '#2a2a2a', tickfont: { color: '#707070' },
      rangeslider: { visible: false }, showspikes: true, spikemode: 'across', spikethickness: 1, spikecolor: '#555', spikedash: 'solid',
    },
    yaxis: { gridcolor: '#161616', linecolor: '#2a2a2a', tickfont: { color: '#707070' }, side: 'right', domain: [0, 1] },
    yaxis2: { overlaying: 'y', side: 'left', showgrid: false, visible: false, range: [0, volMax * 4] },
  }
  Plotly.react(el.value, traces, layout, PLOT_CFG)
}

watch(() => store.chartData, render)
watch(() => store.overlays, render, { deep: true })

onMounted(() => { if (store.chartData) render() })
onBeforeUnmount(async () => {
  if (el.value) { const P = await getPlotly(); P.purge(el.value) }
})
</script>
