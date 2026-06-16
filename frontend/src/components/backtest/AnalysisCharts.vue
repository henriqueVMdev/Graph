<template>
  <div>
    <!-- Toolbar: corretora + cenário + funding + botão -->
    <div class="flex flex-wrap items-end gap-3 mb-4">
      <div>
        <label class="text-xs text-gray-500 block mb-1">Corretora (candles + funding)</label>
        <select v-model="store.chartConfig.exchange" class="bg-surface-700 border border-surface-500 rounded-md text-xs text-gray-200 px-2 py-1.5">
          <option value="bybit">Bybit</option>
          <option value="hyperliquid">Hyperliquid</option>
          <option value="binance">Binance</option>
          <option value="okx">OKX</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-gray-500 block mb-1">Cenário (custo)</label>
        <select v-model="store.chartConfig.scenario" class="bg-surface-700 border border-surface-500 rounded-md text-xs text-gray-200 px-2 py-1.5">
          <option value="realista">Realista</option>
          <option value="pessimista">Pessimista</option>
        </select>
      </div>
      <label class="flex items-center gap-2 cursor-pointer pb-1.5">
        <input type="checkbox" v-model="store.chartConfig.use_funding" class="w-3.5 h-3.5 accent-accent-yellow" />
        <span class="text-xs text-gray-400">Incluir funding</span>
      </label>
      <button
        @click="store.fetchChartData()"
        :disabled="store.chartLoading || !store.selectedSymbol"
        class="btn-secondary px-4 py-2 text-xs font-semibold flex items-center gap-2 disabled:opacity-50"
      >
        <span v-if="store.chartLoading" class="dollar-loader-sm">$</span>
        {{ store.chartLoading ? 'Carregando...' : 'Carregar gráficos' }}
      </button>
    </div>

    <div v-if="store.chartData">
      <!-- Avisos (ex.: funding indisponível na rede) -->
      <div v-if="store.chartData.cost_warnings?.length" class="text-xs text-amber-300 bg-amber-900/20 rounded-lg p-2 border border-amber-800/50 mb-3">
        <div v-for="(w, i) in store.chartData.cost_warnings" :key="i">⚠ {{ w }}</div>
      </div>

      <!-- Tab bar -->
      <div class="flex flex-wrap gap-1 border-b border-surface-600 pb-1 mb-3">
        <button
          v-for="(t, i) in tabs" :key="i"
          @click="activeTab = i"
          class="px-3 py-1.5 text-xs font-medium rounded-t transition-colors"
          :class="activeTab === i ? 'bg-surface-600 text-gray-100' : 'text-gray-500 hover:text-gray-300'"
        >{{ t }}</button>
      </div>

      <div v-show="activeTab === 0">
        <div ref="priceChart" style="min-height:460px;" class="w-full"></div>
      </div>
      <div v-show="activeTab === 1">
        <div ref="equityChart" style="min-height:400px;" class="w-full"></div>
      </div>
      <div v-show="activeTab === 2">
        <div ref="fundingChart" style="min-height:360px;" class="w-full"></div>
      </div>
    </div>

    <div v-else-if="store.chartLoading" class="flex flex-col items-center justify-center h-36">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Buscando candles e indicadores...</p>
    </div>

    <div v-else-if="store.chartError" class="text-sm text-red-400 bg-red-900/20 rounded-lg p-3 border border-red-800">
      {{ store.chartError }}
    </div>

    <div v-else class="text-center text-gray-500 text-xs py-8">
      Escolha a corretora e clique em "Carregar gráficos" para ver candles, indicadores, equity e funding.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'
import { purgeChart } from '@/composables/useCharts.js'

const store = useBacktestStore()

const tabs = ['Preço & Trades', 'Equity Bruto vs Líquido', 'Funding']
const activeTab = ref(0)

const priceChart   = ref(null)
const equityChart  = ref(null)
const fundingChart  = ref(null)

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
  legend: { bgcolor: 'transparent', font: { size: 11, color: '#a0a0a0' }, orientation: 'h', x: 0, y: 1.08 },
}
const PLOT_CFG = { responsive: true, displaylogo: false, displayModeBar: false }

// ── Tab 0: Candles + MA/bandas + marcadores de trade ──────────────────────
function renderPrice() {
  if (!priceChart.value || !store.chartData) return
  const c = store.chartData.candles
  const ind = store.chartData.indicators || {}
  const trades = store.chartData.trades || []
  if (!c?.dates?.length) return

  const traces = [
    {
      type: 'candlestick', name: 'Preço', x: c.dates,
      open: c.open, high: c.high, low: c.low, close: c.close,
      increasing: { line: { color: '#26a69a' } },
      decreasing: { line: { color: '#ef5350' } },
    },
  ]
  if (ind.ma)    traces.push({ type: 'scatter', mode: 'lines', name: 'MA', x: c.dates, y: ind.ma, line: { color: '#f5c518', width: 1.5 } })
  if (ind.upper) traces.push({ type: 'scatter', mode: 'lines', name: 'Banda Sup.', x: c.dates, y: ind.upper, line: { color: 'rgba(120,160,255,0.5)', width: 1, dash: 'dot' } })
  if (ind.lower) traces.push({ type: 'scatter', mode: 'lines', name: 'Banda Inf.', x: c.dates, y: ind.lower, line: { color: 'rgba(120,160,255,0.5)', width: 1, dash: 'dot' } })

  // Marcadores de entrada (long ▲ verde / short ▼ vermelho) e saída (✕)
  const longX = [], longY = [], shortX = [], shortY = [], exitX = [], exitY = []
  for (const t of trades) {
    const ed = new Date(t.entry_ts)
    if (t.direction === 1) { longX.push(ed); longY.push(t.entry_price) }
    else { shortX.push(ed); shortY.push(t.entry_price) }
    if (t.exit_ts) { exitX.push(new Date(t.exit_ts)); exitY.push(t.exit_price) }
  }
  if (longX.length)  traces.push({ type: 'scatter', mode: 'markers', name: 'Entrada Long', x: longX, y: longY, marker: { symbol: 'triangle-up', size: 9, color: '#26a69a', line: { color: '#063', width: 1 } } })
  if (shortX.length) traces.push({ type: 'scatter', mode: 'markers', name: 'Entrada Short', x: shortX, y: shortY, marker: { symbol: 'triangle-down', size: 9, color: '#ef5350', line: { color: '#600', width: 1 } } })
  if (exitX.length)  traces.push({ type: 'scatter', mode: 'markers', name: 'Saída', x: exitX, y: exitY, marker: { symbol: 'x', size: 7, color: 'rgba(200,200,200,0.7)' } })

  Plotly.react(priceChart.value, traces, {
    ...BASE_LAYOUT, height: 460,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', rangeslider: { visible: false } },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Preço' },
    hovermode: 'x unified',
  }, PLOT_CFG)
}

// ── Tab 1: Equity bruto vs líquido ────────────────────────────────────────
function renderEquity() {
  if (!equityChart.value || !store.chartData) return
  const eq = store.chartData.equity
  if (!eq?.dates?.length) return

  const traces = [
    { type: 'scatter', mode: 'lines', name: 'Bruto', x: eq.dates, y: eq.gross, line: { color: 'rgba(120,120,120,0.8)', width: 1.5 } },
  ]
  if (eq.net) traces.push({
    type: 'scatter', mode: 'lines', name: 'Líquido (fees + funding)', x: eq.dates, y: eq.net,
    line: { color: '#f5c518', width: 2 }, fill: 'tonexty', fillcolor: 'rgba(239,83,80,0.06)',
  })

  Plotly.react(equityChart.value, traces, {
    ...BASE_LAYOUT, height: 400,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Capital ($)', tickprefix: '$' },
    hovermode: 'x unified',
  }, PLOT_CFG)
}

// ── Tab 2: Funding rate no tempo ──────────────────────────────────────────
function renderFunding() {
  if (!fundingChart.value || !store.chartData) return
  const f = store.chartData.funding
  if (!f?.dates?.length) {
    Plotly.react(fundingChart.value, [], {
      ...BASE_LAYOUT, height: 360,
      annotations: [{ xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false,
        text: 'Sem dados de funding (corretora indisponível ou funding desligado).', font: { color: '#666', size: 12 } }],
    }, PLOT_CFG)
    return
  }
  // rate vem em fração (ex.: 0.0001 = 0,01%); exibe em %.
  const pct = f.rates.map(r => r * 100)
  Plotly.react(fundingChart.value, [{
    type: 'bar', name: 'Funding', x: f.dates, y: pct,
    marker: { color: pct.map(v => v >= 0 ? 'rgba(38,166,154,0.8)' : 'rgba(239,83,80,0.8)') },
    hovertemplate: '%{x}<br>%{y:.4f}%<extra></extra>',
  }], {
    ...BASE_LAYOUT, height: 360,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'date', title: 'Data' },
    yaxis: { ...BASE_LAYOUT.yaxis, title: 'Funding rate (%)', zeroline: true, zerolinecolor: '#333' },
  }, PLOT_CFG)
}

async function renderAll() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  renderPrice()
  renderEquity()
  renderFunding()
}

watch(() => store.chartData, val => { if (val) renderAll() })

onBeforeUnmount(() => {
  purgeChart(priceChart.value)
  purgeChart(equityChart.value)
  purgeChart(fundingChart.value)
})
</script>
