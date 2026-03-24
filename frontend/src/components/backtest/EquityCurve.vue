<template>
  <div ref="chartEl" class="w-full" style="min-height: 450px;"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { purgeChart } from '@/composables/useCharts.js'

const props = defineProps({
  equityCurve: { type: Object, required: true },
  trades: { type: Array, default: () => [] },
  initialCapital: { type: Number, default: 1000 },
})

const chartEl = ref(null)

async function render() {
  if (!chartEl.value || !props.equityCurve) return
  const Plotly = (await import('plotly.js-dist-min')).default

  const traces = []

  // Determina se a estratégia é lucrativa
  const values = props.equityCurve.values
  const profitable = values.length > 0 && values[values.length - 1] >= props.initialCapital

  const lineColor = profitable ? '#26a69a' : '#ef5350'   // TradingView teal / red
  const fillColor = profitable ? 'rgba(38,166,154,0.07)' : 'rgba(239,83,80,0.07)'

  // Equity line — verde se lucrativa, vermelho se perdedora
  traces.push({
    type: 'scatter',
    mode: 'lines',
    name: 'Equity',
    x: props.equityCurve.dates,
    y: values,
    line: { color: lineColor, width: 2 },
    fill: 'tozeroy',
    fillcolor: fillColor,
    hovertemplate: '<b>%{x}</b><br>Capital: $%{y:,.2f}<extra></extra>',
  })

  // Trade markers — bolinhas (circle)
  for (const trade of props.trades) {
    if (!trade.entry_date) continue
    const color = trade.pnl_pct >= 0 ? '#26a69a' : '#ef5350'  // TradingView teal / red

    const idx = props.equityCurve.dates.indexOf(trade.entry_date)
    const eqVal = idx >= 0 ? props.equityCurve.values[idx] : null
    if (eqVal == null) continue

    traces.push({
      type: 'scatter',
      mode: 'markers',
      x: [trade.entry_date],
      y: [eqVal],
      marker: { symbol: 'circle', size: 7, color, opacity: 0.9, line: { color: '#000', width: 0.5 } },
      showlegend: false,
      hovertemplate:
        `<b>${trade.comment}</b><br>` +
        `Entrada: $${trade.entry_price?.toFixed(2)}<br>` +
        `Saída: $${trade.exit_price?.toFixed(2)}<br>` +
        `P&L: ${trade.pnl_pct?.toFixed(2)}%<br>` +
        `Motivo: ${trade.exit_comment}<extra></extra>`,
    })
  }

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 },
    height: 450,
    autosize: true,
    margin: { t: 20, r: 20, b: 50, l: 70 },
    xaxis: {
      title: 'Data',
      gridcolor: '#1e1e1e',
      linecolor: '#2a2a2a',
      tickfont: { color: '#707070' },
    },
    yaxis: {
      title: 'Capital ($)',
      gridcolor: '#1e1e1e',
      linecolor: '#2a2a2a',
      tickprefix: '$',
      tickfont: { color: '#707070' },
    },
    hovermode: 'x unified',
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: lineColor, font: { color: '#e0e0e0' } },
    shapes: [{
      type: 'line',
      xref: 'paper',
      x0: 0, x1: 1,
      yref: 'y',
      y0: props.initialCapital,
      y1: props.initialCapital,
      line: { color: '#2a2a2a', dash: 'dot', width: 1 },
    }],
    annotations: [{
      xref: 'paper', x: 0.01,
      yref: 'y', y: props.initialCapital,
      text: `Capital Inicial: $${props.initialCapital.toLocaleString()}`,
      showarrow: false,
      font: { size: 10, color: '#505050' },
      xanchor: 'left',
    }],
  }

  await Plotly.react(chartEl.value, traces, layout, { responsive: true, displaylogo: false })
}

onMounted(render)
watch(() => [props.equityCurve, props.trades], render, { deep: true })
onBeforeUnmount(() => purgeChart(chartEl.value))
</script>
