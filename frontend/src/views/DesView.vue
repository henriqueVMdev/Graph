<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <!-- busca -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">DES · Descrição do Ativo</h1>
      <form @submit.prevent="load" class="flex gap-2">
        <input v-model="symbolInput" placeholder="ex.: BTC"
               class="form-input !py-1.5 text-xs w-32 uppercase" />
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
          <div class="text-xs text-gray-500 font-mono">{{ d.symbol }} · {{ d.exchange }}</div>
          <div class="text-4xl font-bold font-mono text-gray-100 mt-1">
            {{ fmt(d.last) }}
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
        <div class="metric-card"><span class="metric-label">Máx 24h</span>
          <span class="metric-value text-gray-200">{{ fmt(d.high24) }}</span></div>
        <div class="metric-card"><span class="metric-label">Mín 24h</span>
          <span class="metric-value text-gray-200">{{ fmt(d.low24) }}</span></div>
        <div class="metric-card"><span class="metric-label">Volume 24h</span>
          <span class="metric-value text-gray-200">{{ fmtVol(d.vol_usd) }}</span></div>
        <div class="metric-card"><span class="metric-label">Open Interest</span>
          <span class="metric-value text-gray-200">{{ fmtVol(d.open_interest_usd ?? d.open_interest) }}</span></div>
        <div class="metric-card"><span class="metric-label">Ret 7d</span>
          <span class="metric-value" :class="pctClass(d.ret7d)">{{ fmtPct(d.ret7d) }}</span></div>
        <div class="metric-card"><span class="metric-label">Ret 30d</span>
          <span class="metric-value" :class="pctClass(d.ret30d)">{{ fmtPct(d.ret30d) }}</span></div>
        <div class="metric-card"><span class="metric-label">ATR14 (1d)</span>
          <span class="metric-value text-gray-200">{{ d.atr_pct != null ? d.atr_pct.toFixed(2) + '%' : '—' }}</span></div>
        <div class="metric-card"><span class="metric-label">Funding atual</span>
          <span class="metric-value" :class="(d.funding ?? 0) >= 0 ? 'text-gray-200' : 'text-red-400'">
            {{ d.funding != null ? (d.funding * 100).toFixed(4) + '%' : '—' }}</span></div>
      </div>

      <!-- funding 30d -->
      <div class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Funding rate — 30 dias
        </h2>
        <div ref="fundingChart" style="min-height:260px;" class="w-full"></div>
      </div>

      <!-- especificações do contrato -->
      <div class="card p-4">
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
const fundingChart = ref(null)
let Plotly = null

const d = computed(() => terminal.desData)

function load() {
  const s = symbolInput.value.trim().toUpperCase()
  if (s) terminal.fetchDes(s)
}

function quick(path) {
  const base = d.value?.base
  if (base) {
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
  if (d.value?.base) terminal.addToWatchlist(d.value.base)
  router.push('/monitor')
}

async function renderFunding() {
  const fh = d.value?.funding_hist
  if (!fundingChart.value || !fh?.dates?.length) return
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const pct = fh.rates.map((r) => r * 100)
  Plotly.react(fundingChart.value, [{
    type: 'bar', x: fh.dates.map((t) => new Date(t)), y: pct,
    marker: { color: pct.map((v) => (v >= 0 ? 'rgba(245,197,24,0.8)' : 'rgba(239,83,80,0.8)')) },
    hovertemplate: '%{x}<br>%{y:.4f}%<extra></extra>',
  }], {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 260,
    margin: { t: 10, r: 10, b: 40, l: 55 },
    xaxis: { type: 'date', gridcolor: '#1e1e1e' },
    yaxis: { title: 'Funding (%)', gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#333' },
  }, { responsive: true, displaylogo: false, displayModeBar: false })
}

watch(d, () => { if (d.value) renderFunding() })

onMounted(() => {
  if (!Object.keys(btStore.assets || {}).length) btStore.fetchAssets?.()
  const q = String(route.query.symbol || '').trim()
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
  if (q) { symbolInput.value = String(q).toUpperCase(); load() }
})
onBeforeUnmount(() => purgeChart(fundingChart.value))
</script>
