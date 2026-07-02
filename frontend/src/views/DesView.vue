<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <!-- busca -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">DES · Descrição do Ativo</h1>
      <form @submit.prevent="load" class="flex gap-2">
        <select v-model="marketInput" class="form-select !py-1.5 text-xs">
          <option value="auto">Auto</option>
          <option value="crypto">Cripto</option>
          <option value="tradfi">Tradicional</option>
        </select>
        <input v-model="symbolInput" placeholder="ex.: BTC, AAPL, OURO"
               class="form-input !py-1.5 text-xs w-36 uppercase" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs">Carregar</button>
      </form>
    </div>

    <div v-if="terminal.desLoading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Carregando {{ symbolInput.toUpperCase() }}...</p>
    </div>

    <div v-else-if="terminal.desError" class="card p-3 text-xs text-red-400">
      {{ terminal.desError }}
    </div>

    <template v-else-if="d">
      <!-- cabeçalho: preço grande estilo terminal -->
      <div class="card p-5 flex flex-wrap items-end gap-6">
        <div>
          <div class="text-xs text-gray-500 font-mono">
            {{ d.symbol }} · {{ isTradfi ? (d.exchange_name || 'yahoo') : d.exchange }}
            <span v-if="isTradfi" class="ml-1.5 text-[9px] px-1 py-0.5 rounded
                  bg-blue-900/40 text-blue-300 border border-blue-800/50">TRAD</span>
          </div>
          <div v-if="isTradfi && d.name" class="text-sm text-gray-300 mt-1">{{ d.name }}</div>
          <div class="text-4xl font-bold font-mono text-gray-100 mt-1">
            {{ fmt(d.last) }}
            <span v-if="isTradfi && d.currency && d.currency !== 'USD'"
                  class="text-sm text-gray-500">{{ d.currency }}</span>
            <span class="text-lg ml-2" :class="pctClass(d.pct24h)">{{ fmtPct(d.pct24h) }}</span>
          </div>
        </div>
        <div class="flex-1" />
        <div class="flex gap-2">
          <button @click="quick('/backtest')" class="btn-secondary !py-1.5 text-xs">⚡ Backtest</button>
          <button @click="quick('/grafico')" class="btn-secondary !py-1.5 text-xs">📈 Gráfico</button>
          <button @click="quick('/regime')" class="btn-secondary !py-1.5 text-xs">〰 Regimes</button>
          <button @click="toMonitor" class="btn-secondary !py-1.5 text-xs">👁 Monitor</button>
        </div>
      </div>

      <!-- grid de stats -->
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        <div class="metric-card"><span class="metric-label">{{ isTradfi ? 'Máx dia' : 'Máx 24h' }}</span>
          <span class="metric-value text-gray-200">{{ fmt(d.high24) }}</span></div>
        <div class="metric-card"><span class="metric-label">{{ isTradfi ? 'Mín dia' : 'Mín 24h' }}</span>
          <span class="metric-value text-gray-200">{{ fmt(d.low24) }}</span></div>
        <div class="metric-card"><span class="metric-label">{{ isTradfi ? 'Volume' : 'Volume 24h' }}</span>
          <span class="metric-value text-gray-200">{{ fmtVol(d.vol_usd) }}</span></div>
        <div v-if="!isTradfi" class="metric-card"><span class="metric-label">Open Interest</span>
          <span class="metric-value text-gray-200">{{ fmtVol(d.open_interest_usd ?? d.open_interest) }}</span></div>
        <div v-else class="metric-card"><span class="metric-label">Market Cap</span>
          <span class="metric-value text-gray-200">{{ fmtVol(d.market_cap) }}</span></div>
        <div class="metric-card"><span class="metric-label">Ret 7d</span>
          <span class="metric-value" :class="pctClass(d.ret7d)">{{ fmtPct(d.ret7d) }}</span></div>
        <div class="metric-card"><span class="metric-label">Ret 30d</span>
          <span class="metric-value" :class="pctClass(d.ret30d)">{{ fmtPct(d.ret30d) }}</span></div>
        <div class="metric-card"><span class="metric-label">ATR14 (1d)</span>
          <span class="metric-value text-gray-200">{{ d.atr_pct != null ? d.atr_pct.toFixed(2) + '%' : '—' }}</span></div>
        <div v-if="!isTradfi" class="metric-card"><span class="metric-label">Funding atual</span>
          <span class="metric-value" :class="(d.funding ?? 0) >= 0 ? 'text-gray-200' : 'text-red-400'">
            {{ d.funding != null ? (d.funding * 100).toFixed(4) + '%' : '—' }}</span></div>
        <div v-else class="metric-card"><span class="metric-label">52 semanas</span>
          <span class="metric-value text-gray-200 !text-xs">
            {{ d.week52_low != null ? fmt(d.week52_low) + ' – ' + fmt(d.week52_high) : '—' }}</span></div>
      </div>

      <!-- fundamentos (só tradicional) -->
      <div v-if="isTradfi && (d.sector || d.pe != null || d.dividend_yield != null)" class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Fundamentos
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-xs font-mono">
          <div v-for="f in fundamentals" :key="f.label"
               class="flex justify-between border-b border-surface-600/40 py-1">
            <span class="text-gray-500">{{ f.label }}</span>
            <span class="text-gray-300">{{ f.value }}</span>
          </div>
        </div>
        <p v-if="d.summary" class="text-[11px] text-gray-500 mt-3 leading-relaxed">
          {{ d.summary }}<span v-if="d.summary.length >= 600">…</span>
        </p>
      </div>

      <!-- gráfico: funding 30d (cripto) ou preço 6m (tradicional) -->
      <div class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span>
          {{ isTradfi ? 'Preço — 6 meses (diário)' : 'Funding rate — 30 dias' }}
        </h2>
        <div ref="fundingChart" style="min-height:260px;" class="w-full"></div>
      </div>

      <!-- especificações do contrato (só cripto) -->
      <div v-if="!isTradfi" class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Especificações (exchange)
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-xs font-mono">
          <div class="flex justify-between border-b border-surface-600/40 py-1">
            <span class="text-gray-500">Qty mínima</span>
            <span class="text-gray-300">{{ d.min_qty ?? '—' }}</span></div>
          <div class="flex justify-between border-b border-surface-600/40 py-1">
            <span class="text-gray-500">Notional mín</span>
            <span class="text-gray-300">{{ d.min_notional ?? '—' }}</span></div>
          <div class="flex justify-between border-b border-surface-600/40 py-1">
            <span class="text-gray-500">Contract size</span>
            <span class="text-gray-300">{{ d.contract_size ?? '—' }}</span></div>
          <div class="flex justify-between border-b border-surface-600/40 py-1">
            <span class="text-gray-500">Fees mk/tk</span>
            <span class="text-gray-300">
              {{ d.fees?.maker != null ? (d.fees.maker * 100).toFixed(3) + '% / ' + (d.fees.taker * 100).toFixed(3) + '%' : '—' }}
            </span></div>
        </div>
      </div>
    </template>

    <div v-else class="text-center text-gray-600 text-sm py-16">
      Informe um símbolo acima ou use o command line: <span class="font-mono text-accent-yellow">BTC DES</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'
import { useWorkspaceStore } from '@/stores/workspace.js'
import { useBacktestStore } from '@/stores/backtest.js'
import { purgeChart } from '@/composables/useCharts.js'

const route = useRoute()
const router = useRouter()
const terminal = useTerminalStore()
const ws = useWorkspaceStore()
const btStore = useBacktestStore()

const symbolInput = ref('')
const marketInput = ref('auto')
const fundingChart = ref(null)
let Plotly = null

const d = computed(() => terminal.desData)
const isTradfi = computed(() => d.value?.kind === 'tradfi')

const fundamentals = computed(() => {
  if (!d.value) return []
  const x = d.value
  const rows = [
    ['Setor', x.sector], ['Indústria', x.industry],
    ['P/E', x.pe != null ? x.pe.toFixed(1) : null],
    ['P/E projetado', x.forward_pe != null ? x.forward_pe.toFixed(1) : null],
    ['EPS', x.eps != null ? x.eps.toFixed(2) : null],
    ['Div. yield', x.dividend_yield != null ? x.dividend_yield.toFixed(2) + '%' : null],
    ['Beta', x.beta != null ? x.beta.toFixed(2) : null],
    ['Volume médio', x.avg_volume != null ? fmtVol(x.avg_volume) : null],
  ]
  return rows.filter(([, v]) => v != null).map(([label, value]) => ({ label, value }))
})

function load() {
  const s = symbolInput.value.trim().toUpperCase()
  if (s) terminal.fetchDes(s, marketInput.value)
}

function quick(path) {
  const base = d.value?.base
  if (base && isTradfi.value) {
    // tradicional: ticker yfinance direto (backtest/gráfico usam yfinance)
    ws.symbol = d.value.symbol
    ws.symbolLabel = d.value.name || d.value.label || base
    ws.exchange = ''
  } else if (base) {
    let found = null
    for (const items of Object.values(btStore.assets || {})) {
      for (const [label, ticker] of Object.entries(items)) {
        if (String(ticker).toUpperCase() === `${base}-USD`) found = { label, ticker }
      }
    }
    ws.symbol = found?.ticker || `${base}-USD`
    ws.symbolLabel = found?.label || base
    if (!ws.exchange) ws.exchange = 'bybit'
  }
  router.push(path)
}

function toMonitor() {
  if (d.value?.base) {
    terminal.addToWatchlist(
      isTradfi.value ? d.value.symbol : d.value.base,
      isTradfi.value ? 'tradfi' : 'crypto',
    )
  }
  router.push('/monitor')
}

async function renderFunding() {
  if (!fundingChart.value) return
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()

  const layoutBase = {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 260,
    margin: { t: 10, r: 10, b: 40, l: 55 },
    xaxis: { type: 'date', gridcolor: '#1e1e1e' },
  }
  const cfg = { responsive: true, displaylogo: false, displayModeBar: false }

  if (isTradfi.value) {
    const ph = d.value?.price_hist
    if (!ph?.dates?.length) return
    Plotly.react(fundingChart.value, [{
      type: 'scatter', mode: 'lines',
      x: ph.dates.map((t) => new Date(t)), y: ph.closes,
      line: { color: '#f5c518', width: 1.5 },
      hovertemplate: '%{x}<br>%{y:,.2f}<extra></extra>',
    }], {
      ...layoutBase,
      yaxis: { title: 'Preço', gridcolor: '#1e1e1e', autorange: true },
    }, cfg)
    return
  }

  const fh = d.value?.funding_hist
  if (!fh?.dates?.length) return
  const pct = fh.rates.map((r) => r * 100)
  Plotly.react(fundingChart.value, [{
    type: 'bar', x: fh.dates.map((t) => new Date(t)), y: pct,
    marker: { color: pct.map((v) => (v >= 0 ? 'rgba(245,197,24,0.8)' : 'rgba(239,83,80,0.8)')) },
    hovertemplate: '%{x}<br>%{y:.4f}%<extra></extra>',
  }], {
    ...layoutBase,
    yaxis: { title: 'Funding (%)', gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#333' },
  }, cfg)
}

watch(d, () => { if (d.value) renderFunding() })

onMounted(() => {
  if (!Object.keys(btStore.assets || {}).length) btStore.fetchAssets?.()
  const q = String(route.query.symbol || '').trim()
  const qm = String(route.query.market || '').trim()
  if (qm) marketInput.value = qm
  if (q) { symbolInput.value = q.toUpperCase(); load() }
  else if (ws.symbol) {
    symbolInput.value = ws.symbol.replace(/-USD.*$/, '').toUpperCase()
    load()
  } else if (d.value) {
    symbolInput.value = d.value.base
    renderFunding()
  }
})
watch(() => route.query.symbol, (q) => {
  if (q) {
    const qm = String(route.query.market || '').trim()
    if (qm) marketInput.value = qm
    symbolInput.value = String(q).toUpperCase()
    load()
  }
})
onBeforeUnmount(() => purgeChart(fundingChart.value))

function pctClass(v) {
  return (v ?? 0) >= 0 ? 'text-accent-yellow' : 'text-red-400'
}
function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: v < 1 ? 6 : 2 })
}
function fmtPct(v) {
  return v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}
function fmtVol(v) {
  if (v == null) return '—'
  if (v >= 1e12) return (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  return Math.round(v).toLocaleString('pt-BR')
}
</script>
