<template>
  <div class="space-y-4">

    <!-- Metric cards: 5 drawdown KPIs -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">

      <div class="metric-card">
        <span class="metric-label">Max Drawdown</span>
        <span class="metric-value text-accent-red-light">
          {{ fmtPct(metrics.max_dd) }}
        </span>
      </div>

      <div class="metric-card">
        <span class="metric-label">Recovery Factor</span>
        <span class="metric-value"
          :class="rf == null ? 'text-gray-500'
            : rf >= 3 ? 'text-accent-green-light'
            : rf >= 1 ? 'text-accent-yellow'
            : 'text-accent-red-light'"
        >
          {{ rf != null ? Number(rf).toFixed(2) : '—' }}
        </span>
      </div>

      <div class="metric-card">
        <span class="metric-label">Ulcer Index</span>
        <span class="metric-value"
          :class="ui == null ? 'text-gray-500'
            : ui <= 5 ? 'text-accent-green-light'
            : ui <= 15 ? 'text-accent-yellow'
            : 'text-accent-red-light'"
        >
          {{ ui != null ? Number(ui).toFixed(2) + '%' : '—' }}
        </span>
      </div>

      <div class="metric-card">
        <span class="metric-label">DD Medio</span>
        <span class="metric-value text-accent-red-light">
          {{ fmtPct(metrics.avg_dd) }}
        </span>
      </div>

      <div class="metric-card">
        <span class="metric-label">Episodios DD</span>
        <span class="metric-value text-gray-100">
          {{ metrics.n_dd_episodes ?? '—' }}
          <span v-if="metrics.avg_dd_length != null" class="text-xs text-gray-500 ml-1">
            (~{{ Math.round(metrics.avg_dd_length) }} barras)
          </span>
        </span>
      </div>

    </div>

    <!-- Drawdown area chart + episode markers -->
    <div ref="chartEl" style="min-height:300px;" class="w-full"></div>

    <!-- Episode table -->
    <div v-if="drawdown.episodes && drawdown.episodes.length" class="overflow-x-auto">
      <table class="w-full text-xs text-gray-400 border-collapse">
        <thead>
          <tr class="border-b border-surface-600 text-gray-500 text-left">
            <th class="py-1.5 pr-4">#</th>
            <th class="py-1.5 pr-4">Inicio</th>
            <th class="py-1.5 pr-4">Fim</th>
            <th class="py-1.5 pr-4 text-right">Fundo</th>
            <th class="py-1.5 text-right">Duracao</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(ep, i) in sortedEpisodes"
            :key="i"
            class="border-b border-surface-700/50 hover:bg-surface-800/50 transition-colors"
            :class="i === 0 ? 'text-accent-red-light' : ''"
          >
            <td class="py-1.5 pr-4 text-gray-600">{{ i + 1 }}</td>
            <td class="py-1.5 pr-4">{{ ep.start }}</td>
            <td class="py-1.5 pr-4">{{ ep.end }}</td>
            <td class="py-1.5 pr-4 text-right font-mono"
              :class="ep.trough <= -20 ? 'text-accent-red-light' : ep.trough <= -10 ? 'text-accent-yellow' : 'text-gray-300'"
            >
              {{ ep.trough != null ? ep.trough.toFixed(2) + '%' : '—' }}
            </td>
            <td class="py-1.5 text-right font-mono text-gray-300">{{ ep.length_bars }} barras</td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  metrics:  { type: Object, required: true },
  drawdown: { type: Object, required: true },
})

const chartEl = ref(null)

// ── Computed helpers ──────────────────────────────────────────────────────

const rf = computed(() => props.metrics.recovery_factor)
const ui = computed(() => props.metrics.ulcer_index)

const sortedEpisodes = computed(() => {
  if (!props.drawdown.episodes) return []
  return [...props.drawdown.episodes].sort((a, b) => (a.trough ?? 0) - (b.trough ?? 0))
})

function fmtPct(v) {
  if (v == null) return '—'
  const n = Number(v)
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
}

// ── Chart ─────────────────────────────────────────────────────────────────

function buildChart() {
  if (!chartEl.value || !props.drawdown?.dates?.length) return

  const ddTrace = {
    type: 'scatter',
    mode: 'lines',
    name: 'Drawdown',
    x: props.drawdown.dates,
    y: props.drawdown.values,
    fill: 'tozeroy',
    fillcolor: 'rgba(239,83,80,0.15)',
    line: { color: 'rgba(239,83,80,0.8)', width: 1.5 },
    hovertemplate: '<b>%{x}</b><br>%{y:.2f}%<extra></extra>',
  }

  // Max drawdown reference line
  const maxVal = props.metrics.max_dd
  const avgVal = props.metrics.avg_dd

  const shapes = []
  const annotations = []

  if (maxVal != null) {
    shapes.push({
      type: 'line', xref: 'paper', yref: 'y',
      x0: 0, x1: 1, y0: maxVal, y1: maxVal,
      line: { color: 'rgba(239,83,80,0.5)', dash: 'dot', width: 1 },
    })
    annotations.push({
      xref: 'paper', x: 0.01, yref: 'y', y: maxVal,
      text: `Max DD ${maxVal.toFixed(2)}%`,
      showarrow: false,
      font: { size: 9, color: 'rgba(239,83,80,0.7)' },
      xanchor: 'left', yanchor: 'top',
    })
  }

  if (avgVal != null) {
    shapes.push({
      type: 'line', xref: 'paper', yref: 'y',
      x0: 0, x1: 1, y0: avgVal, y1: avgVal,
      line: { color: 'rgba(245,197,24,0.45)', dash: 'dash', width: 1 },
    })
    annotations.push({
      xref: 'paper', x: 0.01, yref: 'y', y: avgVal,
      text: `DD Medio ${avgVal.toFixed(2)}%`,
      showarrow: false,
      font: { size: 9, color: 'rgba(245,197,24,0.6)' },
      xanchor: 'left', yanchor: 'top',
    })
  }

  // Episode trough markers
  const epX = (props.drawdown.episodes ?? []).map(e => {
    // Find the date closest to the trough within the episode
    if (!e.start || !e.end) return e.start
    const slice = props.drawdown.dates.filter(d => d >= e.start && d <= e.end)
    if (!slice.length) return e.start
    let minIdx = 0
    let minVal = Infinity
    slice.forEach((d, i) => {
      const idx = props.drawdown.dates.indexOf(d)
      const v = props.drawdown.values[idx] ?? 0
      if (v < minVal) { minVal = v; minIdx = i }
    })
    return slice[minIdx]
  })
  const epY = (props.drawdown.episodes ?? []).map(e => e.trough)

  const epTrace = {
    type: 'scatter',
    mode: 'markers',
    name: 'Fundo do episodio',
    x: epX,
    y: epY,
    marker: { color: '#ef5350', size: 6, symbol: 'triangle-down', line: { color: '#111', width: 1 } },
    hovertemplate: '<b>Fundo</b> %{x}<br>%{y:.2f}%<extra></extra>',
  }

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 },
    height: 300,
    margin: { t: 10, r: 20, b: 50, l: 60 },
    shapes,
    annotations,
    xaxis: {
      type: 'date',
      title: 'Data',
      gridcolor: '#1e1e1e',
      linecolor: '#2a2a2a',
      tickfont: { color: '#707070' },
    },
    yaxis: {
      title: 'Drawdown (%)',
      gridcolor: '#1e1e1e',
      linecolor: '#2a2a2a',
      tickfont: { color: '#707070' },
      ticksuffix: '%',
    },
    hovermode: 'x unified',
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#ef5350', font: { color: '#e0e0e0' } },
    legend: { bgcolor: 'transparent', font: { size: 11, color: '#a0a0a0' }, orientation: 'h', x: 0, y: 1.06 },
  }

  Plotly.react(chartEl.value, [ddTrace, epTrace], layout, {
    responsive: true,
    displaylogo: false,
    displayModeBar: false,
  })
}

onMounted(buildChart)
watch(() => props.drawdown, buildChart, { deep: true })
onBeforeUnmount(() => {
  if (chartEl.value) Plotly.purge(chartEl.value)
})
</script>
