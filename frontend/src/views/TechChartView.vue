<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">GT · Análise Técnica</h1>
      <span class="text-[10px] text-gray-600 font-mono">multi-ativo · cripto + tradicional no mesmo gráfico</span>
      <div class="flex-1" />
      <div class="flex rounded-lg overflow-hidden border border-surface-500">
        <button v-for="t in TABS" :key="t.key" @click="tab = t.key"
                class="px-2.5 py-1 text-[11px] font-mono transition-colors"
                :class="tab === t.key ? 'bg-accent-yellow text-black font-bold' : 'text-gray-400 hover:text-gray-200'">
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- controles comuns -->
    <div class="card p-3 flex flex-wrap items-end gap-3">
      <label class="text-xs text-gray-500 block">Timeframe
        <select v-model="interval" class="form-select !py-1.5 text-xs mt-1 block">
          <option value="15m">15m (intraday)</option>
          <option value="30m">30m</option>
          <option value="1h">1h</option>
          <option value="4h">4h</option>
          <option value="1d">Diário</option>
          <option value="1wk">Semanal</option>
          <option value="1mo">Mensal</option>
        </select></label>
      <label class="text-xs text-gray-500 block">Barras
        <input v-model.number="bars" type="number" min="30" max="3000"
               class="form-input !py-1.5 text-xs w-24 mt-1 block" /></label>

      <!-- GRÁFICO: ativo único -->
      <template v-if="tab === 'grafico'">
        <label class="text-xs text-gray-500 block">Mercado
          <select v-model="single.market" class="form-select !py-1.5 text-xs mt-1 block">
            <option value="crypto">Cripto</option>
            <option value="tradfi">Tradicional</option>
          </select></label>
        <label class="text-xs text-gray-500 block">Ativo
          <input v-model="single.s" :placeholder="single.market === 'crypto' ? 'BTC' : 'AAPL, OURO…'"
                 class="form-input !py-1.5 text-xs w-32 uppercase mt-1 block" /></label>
        <button @click="runSingle" :disabled="loading" class="btn-primary !py-1.5 text-xs disabled:opacity-50">
          {{ loading ? '...' : '▶ Plotar' }}</button>
      </template>

      <!-- COMPARAR: vários ativos -->
      <template v-else-if="tab === 'comparar'">
        <label class="text-xs text-gray-500 block">Mercado
          <select v-model="addMarket" class="form-select !py-1.5 text-xs mt-1 block">
            <option value="crypto">Cripto</option>
            <option value="tradfi">Tradicional</option>
          </select></label>
        <label class="text-xs text-gray-500 block">Adicionar ativo
          <input v-model="addSymbol" @keydown.enter.prevent="addToCompare"
                 :placeholder="addMarket === 'crypto' ? 'ETH' : 'SPX, OURO…'"
                 class="form-input !py-1.5 text-xs w-32 uppercase mt-1 block" /></label>
        <button @click="addToCompare" class="btn-secondary !py-1.5 text-xs">+</button>
        <button @click="runCompare" :disabled="cmpList.length < 2 || loading"
                class="btn-primary !py-1.5 text-xs disabled:opacity-50">
          {{ loading ? '...' : '▶ Comparar' }}</button>
      </template>

      <!-- SPREAD: exatamente 2 -->
      <template v-else-if="tab === 'spread'">
        <template v-for="(leg, i) in spreadLegs" :key="i">
          <label class="text-xs text-gray-500 block">{{ i === 0 ? 'Ativo A' : 'Ativo B' }}
            <div class="flex gap-1 mt-1">
              <select v-model="leg.market" class="form-select !py-1.5 text-xs">
                <option value="crypto">C</option><option value="tradfi">T</option>
              </select>
              <input v-model="leg.s" class="form-input !py-1.5 text-xs w-28 uppercase" />
            </div></label>
        </template>
        <label class="text-xs text-gray-500 block">Janela corr
          <input v-model.number="corrWindow" type="number" min="10"
                 class="form-input !py-1.5 text-xs w-20 mt-1 block" /></label>
        <button @click="runSpread" :disabled="loading" class="btn-primary !py-1.5 text-xs disabled:opacity-50">
          {{ loading ? '...' : '▶ Spread' }}</button>
      </template>

      <!-- CONTRATOS -->
      <template v-else>
        <label class="text-xs text-gray-500 block">Commodity
          <select v-model="cKey" @change="loadContracts" class="form-select !py-1.5 text-xs mt-1 block w-44">
            <option v-for="c in curvesMeta" :key="c.key" :value="c.key">{{ c.label }}</option>
          </select></label>
        <label class="text-xs text-gray-500 block">Contrato A
          <select v-model="contractA" class="form-select !py-1.5 text-xs mt-1 block">
            <option v-for="p in contracts" :key="p.symbol" :value="p.symbol">{{ p.code }} · {{ p.month }}</option>
          </select></label>
        <label class="text-xs text-gray-500 block">Contrato B
          <select v-model="contractB" class="form-select !py-1.5 text-xs mt-1 block">
            <option v-for="p in contracts" :key="p.symbol" :value="p.symbol">{{ p.code }} · {{ p.month }}</option>
          </select></label>
        <button @click="runContracts" :disabled="!contractA || !contractB || loading"
                class="btn-primary !py-1.5 text-xs disabled:opacity-50">
          {{ loading ? '...' : '▶ Comparar contratos' }}</button>
      </template>
    </div>

    <!-- estudos (só aba gráfico) -->
    <div v-if="tab === 'grafico'" class="card p-3 space-y-2">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-[10px] text-gray-600 uppercase tracking-wider">Estudos</span>
        <button v-for="st in STUDY_CHIPS" :key="st.label" @click="toggleStudy(st)"
                class="px-2 py-0.5 text-[11px] font-mono rounded border transition-colors"
                :class="isActive(st) ? 'border-accent-yellow text-accent-yellow' : 'border-surface-500 text-gray-400 hover:text-gray-200'">
          {{ st.label }}</button>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-[10px] text-gray-600 uppercase tracking-wider">Custom</span>
        <input v-model="customExpr" placeholder='ex.: EMA(close,9) - EMA(close,21) · ROC(close,10) · (close - MIN(low,20)) / (MAX(high,20) - MIN(low,20)) * 100'
               class="form-input !py-1 text-[11px] flex-1 min-w-64 font-mono" @keydown.enter.prevent="addCustom" />
        <button @click="addCustom" class="btn-secondary !py-1 text-[11px]">+ Estudo</button>
        <span v-for="(c, i) in customs" :key="i"
              class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-600/60 text-gray-300">
          {{ c.expr.slice(0, 28) }} <button @click="customs.splice(i, 1); runSingle()" class="text-gray-500 hover:text-red-400 ml-1">✕</button></span>
      </div>
      <p class="text-[10px] text-gray-700 font-mono">
        funções: SMA EMA RSI STD MAX MIN ROC SHIFT ABS LOG DIFF · variáveis: open high low close volume
      </p>
      <p v-if="studyErrors.length" class="text-xs text-red-400">{{ studyErrors.join(' · ') }}</p>
    </div>

    <!-- chips da comparação -->
    <div v-if="tab === 'comparar' && cmpList.length" class="flex flex-wrap gap-2">
      <span v-for="(a, i) in cmpList" :key="i"
            class="text-[11px] font-mono px-2 py-0.5 rounded border border-surface-500 text-gray-300">
        {{ a.s }} <span class="text-gray-600">· {{ a.market === 'crypto' ? 'cripto' : 'trad' }}</span>
        <button @click="cmpList.splice(i, 1)" class="text-gray-500 hover:text-red-400 ml-1">✕</button></span>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>
    <div v-if="loading" class="flex flex-col items-center py-12">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Calculando...</p>
    </div>

    <!-- ══ resultados: GRÁFICO ══ -->
    <template v-if="tab === 'grafico' && singleData && !loading">
      <div class="card p-3">
        <div ref="mainChart" style="min-height:380px;" class="w-full"></div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">Volume financeiro ($)</div>
        <div ref="volChart" style="min-height:130px;" class="w-full"></div>
      </div>
      <div v-for="(p, i) in singleData.panels" :key="p.name + i" class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">{{ p.name }}</div>
        <div :ref="(el) => setPanelRef(el, i)" style="min-height:150px;" class="w-full"></div>
      </div>
    </template>

    <!-- ══ resultados: COMPARAR ══ -->
    <template v-if="tab === 'comparar' && cmpData && !loading">
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">
          Retornos acumulados (%) — {{ cmpData.n_common }} candles em comum
        </div>
        <div ref="cumChart" style="min-height:320px;" class="w-full"></div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">Matriz de correlação (retornos)</div>
        <div ref="corrChart" style="min-height:280px;" class="w-full"></div>
      </div>
    </template>

    <!-- ══ resultados: SPREAD / CONTRATOS ══ -->
    <template v-if="(tab === 'spread' || tab === 'contratos') && spreadData && !loading">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div class="metric-card"><span class="metric-label">Par</span>
          <span class="metric-value text-gray-200 !text-sm">{{ spreadData.spread?.pair }}</span></div>
        <div class="metric-card"><span class="metric-label">Spread atual</span>
          <span class="metric-value text-accent-yellow">{{ lastOf(spreadData.spread?.diff) }}</span></div>
        <div class="metric-card"><span class="metric-label">Razão atual</span>
          <span class="metric-value text-gray-200">{{ lastOf(spreadData.spread?.ratio, 4) }}</span></div>
        <div class="metric-card"><span class="metric-label">Correlação total</span>
          <span class="metric-value text-gray-200">{{ spreadData.corr_matrix?.matrix?.[0]?.[1] ?? '—' }}</span></div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">Retornos acumulados (%)</div>
        <div ref="spCumChart" style="min-height:260px;" class="w-full"></div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">Spread (A − B)</div>
          <div ref="spDiffChart" style="min-height:220px;" class="w-full"></div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">Razão (A / B)</div>
          <div ref="spRatioChart" style="min-height:220px;" class="w-full"></div>
        </div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase font-semibold px-1">
          Correlação móvel ({{ spreadData.roll_corr?.window }} barras)
        </div>
        <div ref="spCorrChart" style="min-height:180px;" class="w-full"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { postChart, getCdtyCurves, getCdtyCurve } from '@/api/client.js'
import { purgeChart } from '@/composables/useCharts.js'

const route = useRoute()

const TABS = [
  { key: 'grafico', label: 'GRÁFICO' },
  { key: 'comparar', label: 'COMPARAR' },
  { key: 'spread', label: 'SPREAD & CORR' },
  { key: 'contratos', label: 'CONTRATOS' },
]
const tab = ref('grafico')
const interval = ref('1d')
const bars = ref(300)
const loading = ref(false)
const error = ref(null)
let Plotly = null

const PALETTE = ['#f5c518', '#4dabf7', '#69db7c', '#ef5350', '#b197fc', '#ffa94d', '#63e6be', '#f783ac']
const LAYOUT = (h) => ({
  template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
  font: { color: '#d0d0d0', size: 10 }, height: h,
  margin: { t: 8, r: 10, b: 30, l: 50 },
  xaxis: { type: 'date', gridcolor: '#1e1e1e', rangeslider: { visible: false } },
  yaxis: { gridcolor: '#1e1e1e' },
  legend: { orientation: 'h', y: 1.08 },
})
const CFG = { responsive: true, displaylogo: false, displayModeBar: false }

// ── GRÁFICO ──
const single = reactive({ s: 'BTC', market: 'crypto' })
const STUDY_CHIPS = [
  { label: 'SMA 20', st: { type: 'sma', n: 20 } },
  { label: 'SMA 50', st: { type: 'sma', n: 50 } },
  { label: 'SMA 200', st: { type: 'sma', n: 200 } },
  { label: 'EMA 9', st: { type: 'ema', n: 9 } },
  { label: 'EMA 21', st: { type: 'ema', n: 21 } },
  { label: 'Bollinger (20,2)', st: { type: 'bb', n: 20, k: 2 } },
  { label: 'RSI 14', st: { type: 'rsi', n: 14 } },
  { label: 'MACD', st: { type: 'macd' } },
]
const activeStudies = ref([{ type: 'ema', n: 9 }, { type: 'sma', n: 50 }, { type: 'rsi', n: 14 }])
const customs = ref([])
const customExpr = ref('')
const singleData = ref(null)
const studyErrors = ref([])
const mainChart = ref(null)
const volChart = ref(null)
const panelRefs = ref([])

function setPanelRef(el, i) {
  if (el) panelRefs.value[i] = el
}
function keyOf(st) {
  return `${st.type}:${st.n || ''}:${st.k || ''}`
}
function isActive(chip) {
  return activeStudies.value.some((s) => keyOf(s) === keyOf(chip.st))
}
function toggleStudy(chip) {
  const k = keyOf(chip.st)
  const i = activeStudies.value.findIndex((s) => keyOf(s) === k)
  if (i >= 0) activeStudies.value.splice(i, 1)
  else activeStudies.value.push({ ...chip.st })
  runSingle()
}
function addCustom() {
  const e = customExpr.value.trim()
  if (!e) return
  customs.value.push({ type: 'custom', expr: e, name: e.slice(0, 40) })
  customExpr.value = ''
  runSingle()
}

async function runSingle() {
  if (!single.s.trim()) return
  loading.value = true
  error.value = null
  try {
    const { data } = await postChart({
      symbols: [{ s: single.s.trim().toUpperCase(), market: single.market }],
      interval: interval.value, bars: bars.value,
      studies: [...activeStudies.value, ...customs.value],
    })
    if (data.error) { error.value = data.error; return }
    singleData.value = data
    studyErrors.value = data.study_errors || []
    await renderSingle()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function renderSingle() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const d = singleData.value
  if (!mainChart.value || !d) return
  const x = d.ts.map((t) => new Date(t))
  const traces = [{
    type: 'candlestick', x, open: d.open, high: d.high, low: d.low, close: d.close,
    name: d.symbol, increasing: { line: { color: '#f5c518' } },
    decreasing: { line: { color: '#ef5350' } },
  }]
  d.overlays.forEach((o, i) => traces.push({
    type: 'scatter', mode: 'lines', x, y: o.values, name: o.name,
    line: { width: 1.2, color: PALETTE[(i + 1) % PALETTE.length], dash: o.dash || 'solid' },
  }))
  Plotly.react(mainChart.value, traces, LAYOUT(380), CFG)

  if (volChart.value) {
    Plotly.react(volChart.value, [{
      type: 'bar', x, y: d.vol_fin, name: 'Vol $',
      marker: { color: d.close.map((c, i) => (i > 0 && c >= d.close[i - 1] ? 'rgba(245,197,24,0.55)' : 'rgba(239,83,80,0.55)')) },
    }], LAYOUT(130), CFG)
  }

  await nextTick()
  d.panels.forEach((p, i) => {
    const el = panelRefs.value[i]
    if (!el) return
    const tr = p.series.map((s, j) => (s.bar
      ? { type: 'bar', x, y: s.values, name: s.name,
          marker: { color: s.values.map((v) => ((v ?? 0) >= 0 ? 'rgba(245,197,24,0.6)' : 'rgba(239,83,80,0.6)')) } }
      : { type: 'scatter', mode: 'lines', x, y: s.values, name: s.name,
          line: { width: 1.2, color: PALETTE[j % PALETTE.length] } }))
    const ly = LAYOUT(150)
    if (p.kind === 'rsi') {
      ly.shapes = [30, 70].map((lvl) => ({
        type: 'line', x0: 0, x1: 1, xref: 'paper', y0: lvl, y1: lvl,
        line: { color: '#445', width: 1, dash: 'dot' } }))
      ly.yaxis.range = [0, 100]
    }
    Plotly.react(el, tr, ly, CFG)
  })
}

// ── COMPARAR ──
const cmpList = ref([{ s: 'BTC', market: 'crypto' }, { s: 'SPX', market: 'tradfi' }, { s: 'OURO', market: 'tradfi' }])
const addSymbol = ref('')
const addMarket = ref('tradfi')
const cmpData = ref(null)
const cumChart = ref(null)
const corrChart = ref(null)

function addToCompare() {
  const s = addSymbol.value.trim().toUpperCase()
  if (s && !cmpList.value.some((a) => a.s === s)) {
    cmpList.value.push({ s, market: addMarket.value })
  }
  addSymbol.value = ''
}

async function runCompare() {
  loading.value = true
  error.value = null
  try {
    const { data } = await postChart({
      mode: 'compare', symbols: cmpList.value,
      interval: interval.value, bars: bars.value,
    })
    if (data.error) { error.value = data.error; return }
    cmpData.value = data
    await renderCompare()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function renderCompare() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const d = cmpData.value
  if (!cumChart.value || !d) return
  const x = d.ts.map((t) => new Date(t))
  Plotly.react(cumChart.value, d.names.map((n, i) => ({
    type: 'scatter', mode: 'lines', x, y: d.cumret[n], name: n,
    line: { width: 1.6, color: PALETTE[i % PALETTE.length] },
  })), { ...LAYOUT(320), yaxis: { gridcolor: '#1e1e1e', title: '%', zeroline: true, zerolinecolor: '#445' } }, CFG)

  if (corrChart.value) {
    const m = d.corr_matrix
    Plotly.react(corrChart.value, [{
      type: 'heatmap', x: m.labels, y: m.labels, z: m.matrix,
      zmin: -1, zmax: 1,
      colorscale: [[0, '#ef5350'], [0.5, '#101010'], [1, '#f5c518']],
      texttemplate: '%{z}', textfont: { size: 11 },
      hovertemplate: '%{y} × %{x}: %{z}<extra></extra>',
    }], { ...LAYOUT(280), xaxis: {}, yaxis: { autorange: 'reversed' }, margin: { t: 8, r: 10, b: 40, l: 90 } }, CFG)
  }
}

// ── SPREAD ──
const spreadLegs = ref([{ s: 'BTC', market: 'crypto' }, { s: 'ETH', market: 'crypto' }])
const corrWindow = ref(30)
const spreadData = ref(null)
const spCumChart = ref(null)
const spDiffChart = ref(null)
const spRatioChart = ref(null)
const spCorrChart = ref(null)

async function runSpreadWith(symbols) {
  loading.value = true
  error.value = null
  try {
    const { data } = await postChart({
      mode: 'compare', symbols,
      interval: interval.value, bars: bars.value, corr_window: corrWindow.value,
    })
    if (data.error) { error.value = data.error; return }
    spreadData.value = data
    await renderSpread()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

function runSpread() {
  runSpreadWith(spreadLegs.value.map((l) => ({ s: l.s.trim().toUpperCase(), market: l.market })))
}

async function renderSpread() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const d = spreadData.value
  if (!d?.spread) return
  const xc = d.ts.map((t) => new Date(t))
  const xs = d.spread.ts.map((t) => new Date(t))

  if (spCumChart.value) {
    Plotly.react(spCumChart.value, d.names.map((n, i) => ({
      type: 'scatter', mode: 'lines', x: xc, y: d.cumret[n], name: n,
      line: { width: 1.6, color: PALETTE[i % PALETTE.length] },
    })), { ...LAYOUT(260), yaxis: { gridcolor: '#1e1e1e', title: '%', zeroline: true, zerolinecolor: '#445' } }, CFG)
  }
  if (spDiffChart.value) {
    Plotly.react(spDiffChart.value, [{
      type: 'scatter', mode: 'lines', x: xs, y: d.spread.diff, name: 'A−B',
      line: { width: 1.4, color: '#f5c518' }, fill: 'tozeroy', fillcolor: 'rgba(245,197,24,0.08)',
    }], { ...LAYOUT(220), yaxis: { gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#445' } }, CFG)
  }
  if (spRatioChart.value) {
    Plotly.react(spRatioChart.value, [{
      type: 'scatter', mode: 'lines', x: xs, y: d.spread.ratio, name: 'A/B',
      line: { width: 1.4, color: '#4dabf7' },
    }], LAYOUT(220), CFG)
  }
  if (spCorrChart.value && d.roll_corr) {
    Plotly.react(spCorrChart.value, [{
      type: 'scatter', mode: 'lines', x: xc, y: d.roll_corr.values, name: 'corr',
      line: { width: 1.4, color: '#69db7c' },
    }], { ...LAYOUT(180), yaxis: { gridcolor: '#1e1e1e', range: [-1, 1], zeroline: true, zerolinecolor: '#445' } }, CFG)
  }
}

// ── CONTRATOS ──
const curvesMeta = ref([])
const cKey = ref('CL')
const contracts = ref([])
const contractA = ref('')
const contractB = ref('')

async function loadContracts() {
  try {
    const { data } = await getCdtyCurve(cKey.value)
    contracts.value = data.points || []
    contractA.value = contracts.value[0]?.symbol || ''
    contractB.value = contracts.value[Math.min(3, contracts.value.length - 1)]?.symbol || ''
  } catch { /* usuário tenta de novo */ }
}

function runContracts() {
  runSpreadWith([
    { s: contractA.value, market: 'tradfi' },
    { s: contractB.value, market: 'tradfi' },
  ])
}

function lastOf(arr, dec = 3) {
  const v = (arr || []).filter((x) => x != null).at(-1)
  return v != null ? Number(v).toFixed(dec) : '—'
}

onMounted(async () => {
  const q = String(route.query.symbol || '').trim()
  if (q) single.s = q.toUpperCase()
  runSingle()
  try {
    const { data } = await getCdtyCurves()
    curvesMeta.value = data.curves || []
  } catch { /* aba contratos recarrega */ }
})
onBeforeUnmount(() => {
  [mainChart, volChart, cumChart, corrChart, spCumChart, spDiffChart, spRatioChart, spCorrChart]
    .forEach((r) => purgeChart(r.value))
  panelRefs.value.forEach(purgeChart)
})
</script>
