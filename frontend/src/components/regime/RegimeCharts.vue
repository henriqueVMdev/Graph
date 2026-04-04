<template>
  <div class="space-y-4">

    <!-- Tab bar -->
    <div class="flex flex-wrap gap-1 border-b border-surface-600 pb-1">
      <button
        v-for="(t, i) in tabs"
        :key="i"
        @click="activeTab = i"
        class="px-3 py-1.5 text-xs font-medium rounded-t transition-colors"
        :class="activeTab === i ? 'bg-surface-600 text-gray-100' : 'text-gray-500 hover:text-gray-300'"
      >{{ t }}</button>
    </div>

    <!-- Tab 0: Price chart with regime backgrounds -->
    <div v-show="activeTab === 0">
      <div ref="priceChart" style="min-height:420px;" class="w-full"></div>
    </div>

    <!-- Tab 1: Regime performance table -->
    <div v-show="activeTab === 1">
      <div class="overflow-x-auto rounded-lg border border-surface-500">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-surface-600 text-gray-400 text-left">
              <th class="px-3 py-2 font-medium">Regime</th>
              <th class="px-3 py-2 font-medium">% Tempo</th>
              <th class="px-3 py-2 font-medium">Barras</th>
              <th class="px-3 py-2 font-medium">Retorno Total</th>
              <th class="px-3 py-2 font-medium">Ret. Anual.</th>
              <th class="px-3 py-2 font-medium">Sharpe</th>
              <th class="px-3 py-2 font-medium">Max DD</th>
              <th class="px-3 py-2 font-medium">Win Rate</th>
              <th class="px-3 py-2 font-medium">Volatilidade</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(metrics, regime) in results.metrics_by_regime"
              :key="regime"
              class="border-t border-surface-600 hover:bg-surface-700/50"
            >
              <td class="px-3 py-2 font-semibold">
                <span class="inline-flex items-center gap-1.5">
                  <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: regimeColor(regime) }" />
                  {{ regimeLabel(regime) }}
                </span>
              </td>
              <td class="px-3 py-2 text-gray-300">{{ metrics.pct_time }}%</td>
              <td class="px-3 py-2 text-gray-300">{{ metrics.count_bars }}</td>
              <td class="px-3 py-2" :class="metrics.total_return >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ fmtPct(metrics.total_return) }}
              </td>
              <td class="px-3 py-2" :class="metrics.annualized_return >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ fmtPct(metrics.annualized_return) }}
              </td>
              <td class="px-3 py-2 text-gray-300 font-mono">{{ metrics.sharpe }}</td>
              <td class="px-3 py-2 text-red-400">{{ fmtPct(metrics.max_drawdown) }}</td>
              <td class="px-3 py-2 text-gray-300">{{ metrics.win_rate }}%</td>
              <td class="px-3 py-2 text-gray-300">{{ fmtPct(metrics.volatility) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: Transition probability heatmap -->
    <div v-show="activeTab === 2">
      <div ref="transitionChart" style="min-height:350px;" class="w-full"></div>
    </div>

    <!-- Tab 3: Rolling regime probability area chart -->
    <div v-show="activeTab === 3">
      <template v-if="results.regime_probs">
        <div ref="rollingChart" style="min-height:380px;" class="w-full"></div>
      </template>
      <div v-else class="text-center text-gray-500 text-xs py-8">
        Probabilidades rolling só disponíveis com os métodos HMM e Markov Switching.
      </div>
    </div>

    <!-- BIC scores (if available) -->
    <div v-if="results.bic_scores && results.bic_scores.length > 0" class="card p-3">
      <p class="text-xs text-gray-400 mb-2 font-medium">Seleção de Estados (BIC)</p>
      <div class="flex gap-3 text-xs">
        <div
          v-for="b in results.bic_scores"
          :key="b.n"
          class="bg-surface-700 rounded-lg px-3 py-2 text-center"
          :class="b.n === results.n_states ? 'border border-accent-yellow' : 'border border-surface-500'"
        >
          <div class="text-gray-500">{{ b.n }} estados</div>
          <div class="font-mono text-gray-300">{{ b.bic.toLocaleString() }}</div>
          <div v-if="b.n === results.n_states" class="text-[10px] text-accent-yellow mt-0.5">selecionado</div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRegimeStore } from '@/stores/regime.js'
import { purgeChart } from '@/composables/useCharts.js'

const store = useRegimeStore()
const results = computed(() => store.results)

const activeTab = ref(0)
const tabs = ['Preço + Regimes', 'Performance por Regime', 'Matriz de Transição', 'Probabilidades Rolling']

const priceChart = ref(null)
const transitionChart = ref(null)
const rollingChart = ref(null)

let Plotly = null

const REGIME_COLORS = {
  bull: 'rgba(74,222,128,0.8)',
  bear: 'rgba(239,83,80,0.8)',
  sideways: 'rgba(245,197,24,0.8)',
  low_vol: 'rgba(96,165,250,0.8)',
  mid_vol: 'rgba(245,197,24,0.8)',
  high_vol: 'rgba(239,83,80,0.8)',
}
const REGIME_BG = {
  bull: 'rgba(74,222,128,0.08)',
  bear: 'rgba(239,83,80,0.08)',
  sideways: 'rgba(245,197,24,0.06)',
  low_vol: 'rgba(96,165,250,0.06)',
  mid_vol: 'rgba(245,197,24,0.06)',
  high_vol: 'rgba(239,83,80,0.08)',
}
const REGIME_LABELS = {
  bull: 'Bull (Alta)',
  bear: 'Bear (Baixa)',
  sideways: 'Sideways (Lateral)',
  low_vol: 'Low Vol (Calmo)',
  mid_vol: 'Mid Vol (Moderado)',
  high_vol: 'High Vol (Turbulento)',
}

function regimeColor(r) { return REGIME_COLORS[r] || '#888' }
function regimeLabel(r) { return REGIME_LABELS[r] || r }
function fmtPct(v) {
  if (v == null) return '—'
  return (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%'
}

const BASE_LAYOUT = {
  template: 'plotly_dark',
  paper_bgcolor: '#000000',
  plot_bgcolor: '#080808',
  font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 },
  margin: { t: 20, r: 20, b: 50, l: 75 },
  xaxis: { gridcolor: '#1e1e1e', linecolor: '#2a2a2a', tickfont: { color: '#707070' } },
  yaxis: { gridcolor: '#1e1e1e', linecolor: '#2a2a2a', tickfont: { color: '#707070' } },
  hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
  legend: { bgcolor: 'transparent', font: { size: 11, color: '#a0a0a0' } },
}
const PLOT_CFG = { responsive: true, displaylogo: false, displayModeBar: false }

// ── Chart 0: Price with regime-colored backgrounds ─────────────────────────

function renderPriceChart() {
  if (!priceChart.value || !results.value) return
  const r = results.value

  // Build regime background shapes
  const shapes = []
  let segStart = 0
  for (let i = 1; i <= r.regimes.length; i++) {
    if (i === r.regimes.length || r.regimes[i] !== r.regimes[i - 1]) {
      const regime = r.regimes[segStart]
      shapes.push({
        type: 'rect', xref: 'x', yref: 'paper',
        x0: r.dates[segStart], x1: r.dates[i - 1],
        y0: 0, y1: 1,
        fillcolor: REGIME_BG[regime] || 'rgba(128,128,128,0.05)',
        line: { width: 0 },
      })
      segStart = i
    }
  }

  // Price line
  const trace = {
    type: 'scatter', mode: 'lines', name: 'Preço',
    x: r.dates, y: r.prices,
    line: { color: '#d0d0d0', width: 1.5 },
    hovertemplate: '<b>%{x}</b><br>$%{y:,.2f}<extra></extra>',
  }

  // Regime colored dots (sparse for legend)
  const regimeTraces = []
  const uniqueRegimes = [...new Set(r.regimes)]
  for (const regime of uniqueRegimes) {
    const indices = r.regimes.map((reg, idx) => reg === regime ? idx : -1).filter(i => i >= 0)
    if (indices.length === 0) continue
    regimeTraces.push({
      type: 'scatter', mode: 'markers',
      name: REGIME_LABELS[regime] || regime,
      x: indices.filter((_, j) => j % Math.max(1, Math.floor(indices.length / 50)) === 0).map(i => r.dates[i]),
      y: indices.filter((_, j) => j % Math.max(1, Math.floor(indices.length / 50)) === 0).map(i => r.prices[i]),
      marker: { color: REGIME_COLORS[regime] || 'rgba(128,128,128,0.8)', size: 4, opacity: 0.6 },
      hoverinfo: 'skip',
    })
  }

  Plotly.react(priceChart.value, [trace, ...regimeTraces], {
    ...BASE_LAYOUT, height: 420, shapes,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Preço' },
    hovermode: 'x unified',
    legend: { ...BASE_LAYOUT.legend, orientation: 'h', x: 0, y: 1.06 },
  }, PLOT_CFG)
}

// ── Chart 2: Transition probability heatmap ────────────────────────────────

function renderTransitionChart() {
  if (!transitionChart.value || !results.value) return
  const r = results.value

  const stateLabels = r.state_names.map(s => REGIME_LABELS[s] || s)

  // Custom hover text
  const hoverText = r.transition_matrix.map((row, ri) =>
    row.map((val, ci) =>
      `<b>${stateLabels[ri]} → ${stateLabels[ci]}</b><br>${val}%`
    )
  )

  // Annotation text on cells
  const annotations = []
  r.transition_matrix.forEach((row, ri) => {
    row.forEach((val, ci) => {
      annotations.push({
        x: stateLabels[ci], y: stateLabels[ri],
        text: `${val}%`,
        showarrow: false,
        font: { color: val > 50 ? '#000' : '#fff', size: 14, family: 'monospace' },
      })
    })
  })

  Plotly.react(transitionChart.value, [{
    type: 'heatmap',
    x: stateLabels,
    y: stateLabels,
    z: r.transition_matrix,
    text: hoverText,
    hovertemplate: '%{text}<extra></extra>',
    colorscale: [
      [0, '#0d1117'],
      [0.3, '#1a3a5c'],
      [0.6, '#f5c518'],
      [1, '#ff4444'],
    ],
    showscale: true,
    colorbar: {
      title: { text: '%', side: 'right' },
      tickfont: { color: '#888', size: 10 },
    },
    zmin: 0, zmax: 100,
  }], {
    ...BASE_LAYOUT, height: 350, annotations,
    margin: { ...BASE_LAYOUT.margin, l: 120, b: 80 },
    xaxis: { ...BASE_LAYOUT.xaxis, title: 'Estado Destino', tickfont: { color: '#ccc', size: 12 } },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Estado Origem', tickfont: { color: '#ccc', size: 12 }, autorange: 'reversed' },
  }, PLOT_CFG)
}

// ── Chart 3: Rolling regime probability stacked area ───────────────────────

function renderRollingChart() {
  if (!rollingChart.value || !results.value || !results.value.regime_probs) return
  const r = results.value

  const traces = Object.entries(r.regime_probs).map(([regime, probs]) => ({
    type: 'scatter', mode: 'lines',
    name: REGIME_LABELS[regime] || regime,
    x: r.dates,
    y: probs,
    stackgroup: 'one',
    fillcolor: (REGIME_COLORS[regime] || 'rgba(128,128,128,0.5)').replace('0.8', '0.4'),
    line: { color: REGIME_COLORS[regime] || '#888', width: 0.5 },
    hovertemplate: `<b>${REGIME_LABELS[regime] || regime}</b>: %{y:.1%}<extra></extra>`,
  }))

  Plotly.react(rollingChart.value, traces, {
    ...BASE_LAYOUT, height: 380,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Probabilidade', range: [0, 1], tickformat: '.0%' },
    hovermode: 'x unified',
    legend: { ...BASE_LAYOUT.legend, orientation: 'h', x: 0, y: 1.06 },
  }, PLOT_CFG)
}

// ── Render all ────────────────────────────────────────────────────────────

async function renderAll() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  renderPriceChart()
  renderTransitionChart()
  renderRollingChart()
}

watch(results, val => { if (val) renderAll() }, { immediate: true })

watch(activeTab, async () => {
  if (!Plotly || !results.value) return
  await new Promise(r => setTimeout(r, 50))
  if (activeTab.value === 0 && priceChart.value) Plotly.Plots.resize(priceChart.value)
  if (activeTab.value === 2 && transitionChart.value) Plotly.Plots.resize(transitionChart.value)
  if (activeTab.value === 3 && rollingChart.value) Plotly.Plots.resize(rollingChart.value)
})

onBeforeUnmount(() => {
  purgeChart(priceChart.value)
  purgeChart(transitionChart.value)
  purgeChart(rollingChart.value)
})
</script>
