<template>
  <div>
    <div v-if="store.wfaResults" class="space-y-4">

      <!-- WFE badge + summary cards -->
      <div class="flex flex-wrap items-center gap-3">
        <div class="bg-surface-800 rounded-xl px-5 py-3 text-center min-w-28 border border-surface-600">
          <div class="text-xs text-gray-400 mb-0.5">WFE</div>
          <div class="text-3xl font-bold" :class="wfeColor">{{ fmt2(store.wfaResults.wfe) }}</div>
          <div class="text-[10px] mt-0.5" :class="wfeColor">{{ wfeLabel }}</div>
          <div class="text-[9px] text-gray-600 mt-0.5">&gt;0.5 aceitavel</div>
        </div>
        <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
          <div class="text-xs text-gray-500 mb-0.5">Retorno anual. OOS</div>
          <div class="text-sm font-semibold" :class="(store.wfaResults.avg_oos_annualized ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ fmtPct(store.wfaResults.avg_oos_annualized) }}
          </div>
        </div>
        <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
          <div class="text-xs text-gray-500 mb-0.5">Retorno anual. IS</div>
          <div class="text-sm font-semibold text-gray-200">{{ fmtPct(store.wfaResults.avg_is_annualized) }}</div>
        </div>
        <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
          <div class="text-xs text-gray-500 mb-0.5">Janelas validas</div>
          <div class="text-sm font-semibold text-gray-200">{{ store.wfaResults.n_valid_windows }}</div>
        </div>
      </div>

      <!-- Tab bar -->
      <div class="flex flex-wrap gap-1 border-b border-surface-600 pb-1">
        <button
          v-for="(t, i) in visibleTabs"
          :key="i"
          @click="activeTab = i"
          class="px-3 py-1.5 text-xs font-medium rounded-t transition-colors"
          :class="activeTab === i ? 'bg-surface-600 text-gray-100' : 'text-gray-500 hover:text-gray-300'"
        >{{ t }}</button>
      </div>

      <!-- Tab 0: Curva OOS -->
      <div v-show="activeTab === 0">
        <div ref="oosEquityChart" style="min-height:380px;" class="w-full"></div>
      </div>

      <!-- Tab 1: Sharpe Scatter -->
      <div v-show="activeTab === 1">
        <div ref="sharpeScatterChart" style="min-height:360px;" class="w-full"></div>
      </div>

      <!-- Tab 2: IS vs OOS barras -->
      <div v-show="activeTab === 2">
        <div class="flex gap-2 mb-3">
          <button
            v-for="m in metricOptions" :key="m.key"
            @click="selectedMetric = m.key"
            class="px-3 py-1 text-xs rounded-md border transition-colors"
            :class="selectedMetric === m.key
              ? 'bg-accent-yellow text-black border-accent-yellow'
              : 'bg-surface-600 text-gray-400 border-surface-500 hover:border-gray-400'"
          >{{ m.label }}</button>
        </div>
        <div ref="comparisonChart" style="min-height:300px;" class="w-full"></div>
      </div>

      <!-- Tab 3: Timeline + Equity overlay -->
      <div v-show="activeTab === 3">
        <div ref="timelineChart" style="min-height:400px;" class="w-full"></div>
      </div>

      <!-- Tab 4: Heatmap de Parametros (only when IS was optimized) -->
      <div v-if="hasParamHeatmap" v-show="activeTab === 4">
        <p class="text-xs text-gray-500 mb-2">
          Cor = valor otimizado por janela. Bandas horizontais consistentes indicam estabilidade.
        </p>
        <div ref="paramHeatmapChart" style="min-height:260px;" class="w-full"></div>
      </div>

    </div>

    <!-- Loading -->
    <div v-else-if="store.wfaLoading" class="flex flex-col items-center justify-center h-36">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Calculando Walk-Forward...</p>
    </div>

    <!-- Error -->
    <div v-else-if="store.wfaError" class="text-sm text-red-400 bg-red-900/20 rounded-lg p-3 border border-red-800">
      {{ store.wfaError }}
    </div>

    <!-- Empty state -->
    <div v-else class="text-center text-gray-500 text-xs py-8">
      Configure os parametros WFA na barra lateral e clique em "Executar WFA".
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'
import { purgeChart } from '@/composables/useCharts.js'

const store = useBacktestStore()

const activeTab      = ref(0)
const selectedMetric = ref('return_pct')

const metricOptions = [
  { key: 'return_pct', label: 'Retorno (%)' },
  { key: 'annualized', label: 'Retorno Anual.' },
  { key: 'sharpe',     label: 'Sharpe' },
]

const BASE_TABS    = ['Curva OOS', 'Sharpe IS vs OOS', 'Barras por Janela', 'Timeline + Equity']
const hasParamHeatmap = computed(() => (store.wfaResults?.param_keys?.length ?? 0) > 0)
const visibleTabs     = computed(() =>
  hasParamHeatmap.value ? [...BASE_TABS, 'Heatmap de Params'] : BASE_TABS
)

const oosEquityChart    = ref(null)
const sharpeScatterChart = ref(null)
const comparisonChart   = ref(null)
const timelineChart     = ref(null)
const paramHeatmapChart = ref(null)

let Plotly = null

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

// ── Formatters ────────────────────────────────────────────────────────────

function fmt2(v) {
  return v == null ? '—' : Number(v).toFixed(2)
}

function fmtPct(v) {
  if (v == null) return '—'
  const n = Number(v)
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
}

// ── WFE badge ─────────────────────────────────────────────────────────────

const wfeColor = computed(() => {
  const s = store.wfaResults?.wfe ?? 0
  if (s >= 0.7) return 'text-green-400'
  if (s >= 0.5) return 'text-accent-yellow'
  if (s >= 0.3) return 'text-orange-400'
  return 'text-red-400'
})

const wfeLabel = computed(() => {
  const s = store.wfaResults?.wfe ?? 0
  if (s >= 0.7) return 'Excelente'
  if (s >= 0.5) return 'Aceitavel'
  if (s >= 0.3) return 'Fraco'
  return 'Overfitting'
})

// ── Chart 0: OOS Equity Curve ─────────────────────────────────────────────

function renderOosEquity() {
  if (!oosEquityChart.value || !store.wfaResults) return
  const curve   = store.wfaResults.oos_equity_curve
  const windows = store.wfaResults.windows

  const trace = {
    type: 'scatter', mode: 'lines', name: 'Equity OOS',
    x: curve.dates, y: curve.values,
    line: { color: '#f5c518', width: 2 },
    fill: 'tozeroy', fillcolor: 'rgba(245,197,24,0.05)',
    hovertemplate: '<b>%{x}</b><br>$%{y:,.2f}<extra></extra>',
  }

  const shapes = windows.slice(1).map(w => ({
    type: 'line', xref: 'x', yref: 'paper',
    x0: w.oos_start, x1: w.oos_start, y0: 0, y1: 1,
    line: { color: '#2a2a2a', dash: 'dot', width: 1 },
  }))

  const annotations = windows.slice(1).map(w => ({
    xref: 'x', x: w.oos_start, yref: 'paper', y: 0.98,
    text: `J${w.window_idx + 1}`, showarrow: false,
    font: { size: 9, color: '#555' }, xanchor: 'center',
  }))

  Plotly.react(oosEquityChart.value, [trace], {
    ...BASE_LAYOUT, height: 380, shapes, annotations,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Capital ($)', tickprefix: '$' },
    hovermode: 'x unified',
  }, PLOT_CFG)
}

// ── Chart 1: Sharpe Scatter ───────────────────────────────────────────────

function renderSharpeScatter() {
  if (!sharpeScatterChart.value || !store.wfaResults) return
  const windows = store.wfaResults.windows

  const isSh  = windows.map(w => w.is_sharpe  ?? 0)
  const oosSh = windows.map(w => w.oos_sharpe ?? 0)
  const colors = windows.map(w =>
    (w.oos_sharpe ?? 0) >= (w.is_sharpe ?? 0)
      ? 'rgba(74,222,128,0.85)' : 'rgba(239,83,80,0.85)'
  )

  const allVals = [...isSh, ...oosSh].filter(isFinite)
  const lo = Math.min(...allVals, 0) - 0.3
  const hi = Math.max(...allVals, 1) + 0.3

  const diagTrace = {
    type: 'scatter', mode: 'lines', name: 'Linha 45°',
    x: [lo, hi], y: [lo, hi],
    line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dash' },
    hoverinfo: 'skip',
  }

  const scatterTrace = {
    type: 'scatter', mode: 'markers+text', name: 'Janelas',
    x: isSh, y: oosSh,
    text: windows.map(w => `J${w.window_idx + 1}`),
    textposition: 'top center',
    textfont: { size: 9, color: '#888' },
    marker: { color: colors, size: 10, line: { color: '#111', width: 1 } },
    hovertemplate: windows.map(w =>
      `<b>Janela ${w.window_idx + 1}</b><br>` +
      `IS Sharpe: ${fmt2(w.is_sharpe)}<br>` +
      `OOS Sharpe: ${fmt2(w.oos_sharpe)}<br>` +
      `OOS Retorno: ${fmtPct(w.oos_return)}<extra></extra>`
    ),
  }

  Plotly.react(sharpeScatterChart.value, [diagTrace, scatterTrace], {
    ...BASE_LAYOUT, height: 360,
    xaxis: { ...BASE_LAYOUT.xaxis, title: 'Sharpe IS', range: [lo, hi], zeroline: true, zerolinecolor: '#222' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Sharpe OOS', range: [lo, hi], zeroline: true, zerolinecolor: '#222' },
    annotations: [{
      xref: 'paper', yref: 'paper', x: 0.98, y: 0.02,
      text: 'Pontos acima da linha = boa generalizacao',
      showarrow: false, font: { size: 9, color: '#555' }, xanchor: 'right',
    }],
  }, PLOT_CFG)
}

// ── Chart 2: IS vs OOS Barras ─────────────────────────────────────────────

function renderComparison() {
  if (!comparisonChart.value || !store.wfaResults) return
  const windows = store.wfaResults.windows
  const xLabels = windows.map(w => `J${w.window_idx + 1}`)

  let isKey, oosKey, yTitle
  if (selectedMetric.value === 'sharpe') {
    isKey = 'is_sharpe'; oosKey = 'oos_sharpe'; yTitle = 'Sharpe'
  } else if (selectedMetric.value === 'annualized') {
    isKey = 'is_annualized'; oosKey = 'oos_annualized'; yTitle = 'Retorno Anual. (%)'
  } else {
    isKey = 'is_return'; oosKey = 'oos_return'; yTitle = 'Retorno (%)'
  }

  Plotly.react(comparisonChart.value, [
    {
      type: 'bar', name: 'In-Sample',
      x: xLabels, y: windows.map(w => w[isKey]),
      marker: { color: 'rgba(38,166,154,0.75)' },
      hovertemplate: '<b>IS %{x}</b><br>%{y:.2f}<extra></extra>',
    },
    {
      type: 'bar', name: 'Out-of-Sample',
      x: xLabels, y: windows.map(w => w[oosKey]),
      marker: { color: windows.map(w => (w[oosKey] ?? 0) >= 0 ? 'rgba(245,197,24,0.8)' : 'rgba(239,83,80,0.8)') },
      hovertemplate: '<b>OOS %{x}</b><br>%{y:.2f}<extra></extra>',
    },
  ], {
    ...BASE_LAYOUT, height: 300, barmode: 'group',
    yaxis: { ...BASE_LAYOUT.yaxis, title: yTitle, zeroline: true, zerolinecolor: '#333' },
    xaxis: { ...BASE_LAYOUT.xaxis, title: 'Janela' },
  }, PLOT_CFG)
}

// ── Chart 3: Timeline + Equity Overlay ───────────────────────────────────

function renderTimeline() {
  if (!timelineChart.value || !store.wfaResults) return
  const windows = store.wfaResults.windows

  // Colored bands as background shapes
  const shapes = []
  windows.forEach(w => {
    shapes.push({
      type: 'rect', xref: 'x', yref: 'paper',
      x0: w.is_start, x1: w.is_end, y0: 0, y1: 1,
      fillcolor: 'rgba(38,166,154,0.09)', line: { width: 0 },
    })
    shapes.push({
      type: 'rect', xref: 'x', yref: 'paper',
      x0: w.oos_start, x1: w.oos_end, y0: 0, y1: 1,
      fillcolor: 'rgba(245,197,24,0.07)', line: { width: 0 },
    })
  })

  // Per-window equity curves, each normalized to base=100
  const traces = []
  windows.forEach((w, idx) => {
    const isBase  = w.is_equity[0]  || 1
    const oosBase = w.oos_equity[0] || 1

    traces.push({
      type: 'scatter', mode: 'lines',
      name: idx === 0 ? 'IS (indexado)' : null,
      showlegend: idx === 0,
      legendgroup: 'is',
      x: w.is_dates,
      y: w.is_equity.map(v => v != null ? v / isBase * 100 : null),
      line: { color: 'rgba(38,166,154,0.55)', width: 1, dash: 'dot' },
      hovertemplate: `<b>IS J${w.window_idx + 1}</b> %{x}<br>%{y:.1f}<extra></extra>`,
    })

    traces.push({
      type: 'scatter', mode: 'lines',
      name: idx === 0 ? 'OOS (indexado)' : null,
      showlegend: idx === 0,
      legendgroup: 'oos',
      x: w.oos_dates,
      y: w.oos_equity.map(v => v != null ? v / oosBase * 100 : null),
      line: { color: 'rgba(245,197,24,0.8)', width: 1.5 },
      hovertemplate: `<b>OOS J${w.window_idx + 1}</b> %{x}<br>%{y:.1f}<extra></extra>`,
    })
  })

  // Window boundary markers
  const annotations = windows.map(w => ({
    xref: 'x', x: w.is_start, yref: 'paper', y: 0.99,
    text: `J${w.window_idx + 1}`, showarrow: false,
    font: { size: 9, color: '#666' }, xanchor: 'left',
  }))

  Plotly.react(timelineChart.value, traces, {
    ...BASE_LAYOUT, height: 400, shapes, annotations,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Equity indexada (base=100)' },
    hovermode: 'x unified',
    legend: { ...BASE_LAYOUT.legend, orientation: 'h', x: 0, y: 1.06 },
  }, PLOT_CFG)
}

// ── Chart 4: Parameter Stability Heatmap ─────────────────────────────────

function renderParamHeatmap() {
  if (!paramHeatmapChart.value || !store.wfaResults) return
  const paramKeys = store.wfaResults.param_keys ?? []
  if (!paramKeys.length) return

  const windowsWithParams = store.wfaResults.windows.filter(w => w.optimal_params)
  if (!windowsWithParams.length) return

  const xLabels = windowsWithParams.map(w => `J${w.window_idx + 1}`)

  // Row-wise normalization so each param's color range spans 0-1 independently
  const zRaw = paramKeys.map(pk =>
    windowsWithParams.map(w => w.optimal_params[pk] ?? 0)
  )
  const zNorm = zRaw.map(row => {
    const mn = Math.min(...row)
    const mx = Math.max(...row)
    return mx > mn ? row.map(v => (v - mn) / (mx - mn)) : row.map(() => 0.5)
  })

  // Hover shows actual values
  const hoverText = paramKeys.map((pk, ri) =>
    windowsWithParams.map((w, ci) =>
      `<b>${pk}</b><br>Janela ${w.window_idx + 1}: ${Number(zRaw[ri][ci]).toFixed(3)}`
    )
  )

  Plotly.react(paramHeatmapChart.value, [{
    type: 'heatmap',
    x: xLabels,
    y: paramKeys,
    z: zNorm,
    text: hoverText,
    hovertemplate: '%{text}<extra></extra>',
    colorscale: 'Viridis',
    showscale: true,
    colorbar: {
      title: { text: 'Valor norm.', side: 'right' },
      tickfont: { color: '#888', size: 10 },
      len: 0.8,
    },
    zmin: 0, zmax: 1,
  }], {
    ...BASE_LAYOUT,
    height: Math.max(200, paramKeys.length * 36 + 80),
    margin: { ...BASE_LAYOUT.margin, l: 110 },
    xaxis: { ...BASE_LAYOUT.xaxis, title: 'Janela' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: '', tickfont: { color: '#ccc', size: 11 } },
  }, PLOT_CFG)
}

// ── Render all ────────────────────────────────────────────────────────────

async function renderAll() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  renderOosEquity()
  renderSharpeScatter()
  renderComparison()
  renderTimeline()
  if (hasParamHeatmap.value) renderParamHeatmap()
}

// ── Watchers ─────────────────────────────────────────────────────────────

watch(() => store.wfaResults, val => { if (val) renderAll() })
watch(selectedMetric, () => { if (store.wfaResults && Plotly) renderComparison() })

// ── Cleanup ───────────────────────────────────────────────────────────────

onBeforeUnmount(() => {
  purgeChart(oosEquityChart.value)
  purgeChart(sharpeScatterChart.value)
  purgeChart(comparisonChart.value)
  purgeChart(timelineChart.value)
  purgeChart(paramHeatmapChart.value)
})
</script>
