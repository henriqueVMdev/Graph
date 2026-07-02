<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">Screener</h1>
      <span class="text-[10px] text-gray-600 font-mono">
        {{ isCrypto ? 'bybit · top por volume · atualiza 60s' : 'yahoo finance · dados ~15min' }}
      </span>
      <div class="flex-1" />
      <div class="flex rounded-lg overflow-hidden border border-surface-500">
        <button v-for="m in MARKETS" :key="m.key"
                @click="terminal.setScreenerMarket(m.key)"
                class="px-2.5 py-1 text-[11px] font-mono transition-colors"
                :class="terminal.screenerMarket === m.key
                  ? 'bg-accent-yellow text-black font-bold'
                  : 'text-gray-400 hover:text-gray-200'">
          {{ m.label }}
        </button>
      </div>
      <label v-if="isCrypto" class="text-xs text-gray-500 flex items-center gap-2">
        Volume mín ($M)
        <input v-model.number="minVolM" type="number" min="0" class="form-input !py-1 text-xs w-20" />
      </label>
      <select v-if="isCrypto" v-model="fundingFilter" class="form-select !py-1 text-xs">
        <option value="all">Funding: todos</option>
        <option value="pos">Funding positivo</option>
        <option value="neg">Funding negativo</option>
      </select>
    </div>

    <div v-if="terminal.screenerError" class="card p-3 text-xs text-red-400">
      {{ terminal.screenerError }}
    </div>

    <div v-if="terminal.screenerLoading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Calculando screener (primeira carga ~30-60s)...</p>
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full text-sm font-mono">
        <thead>
          <tr class="text-[10px] text-gray-500 uppercase tracking-wider text-right border-b border-surface-500 select-none">
            <th class="text-left px-3 py-2">#</th>
            <th class="text-left px-3 py-2">Ativo</th>
            <th v-for="c in cols" :key="c.key"
                @click="sortBy(c.key)"
                class="px-3 py-2 cursor-pointer hover:text-accent-yellow whitespace-nowrap">
              {{ c.label }}
              <span v-if="sortKey === c.key">{{ sortDir === -1 ? '▼' : '▲' }}</span>
            </th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in rows" :key="r.symbol"
              class="border-b border-surface-600/60 hover:bg-surface-600/40 transition-colors">
            <td class="px-3 py-1.5 text-left text-gray-600 text-xs">{{ i + 1 }}</td>
            <td class="px-3 py-1.5 text-left">
              <button @click="openDes(r)"
                      class="font-bold text-gray-100 hover:text-accent-yellow">{{ r.base }}</button>
            </td>
            <td class="px-3 py-1.5 text-right">{{ fmt(r.last) }}</td>
            <td class="px-3 py-1.5 text-right" :class="pctClass(r.pct24h)">{{ fmtPct(r.pct24h) }}</td>
            <td class="px-3 py-1.5 text-right" :class="pctClass(r.ret7d)">{{ fmtPct(r.ret7d) }}</td>
            <td class="px-3 py-1.5 text-right" :class="pctClass(r.ret30d)">{{ fmtPct(r.ret30d) }}</td>
            <td class="px-3 py-1.5 text-right text-gray-300">{{ r.atr_pct != null ? r.atr_pct.toFixed(2) + '%' : '—' }}</td>
            <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(r.vol_usd) }}</td>
            <td v-if="isCrypto" class="px-3 py-1.5 text-right"
                :class="(r.funding ?? 0) >= 0 ? 'text-gray-300' : 'text-red-400'">
              {{ r.funding != null ? (r.funding * 100).toFixed(4) + '%' : '—' }}
            </td>
            <td class="px-3 py-1.5 text-right whitespace-nowrap">
              <button @click="terminal.addToWatchlist(isCrypto ? r.base : r.symbol, isCrypto ? 'crypto' : 'tradfi')"
                      title="+ Watchlist"
                      class="text-gray-600 hover:text-accent-yellow text-xs px-1">👁</button>
              <button @click="toBacktest(r)" title="Backtest"
                      class="text-gray-600 hover:text-accent-yellow text-xs px-1">⚡</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'
import { useWorkspaceStore } from '@/stores/workspace.js'
import { useBacktestStore } from '@/stores/backtest.js'

const terminal = useTerminalStore()
const ws = useWorkspaceStore()
const btStore = useBacktestStore()
const router = useRouter()

const MARKETS = [
  { key: 'crypto', label: 'CRIPTO' },
  { key: 'stocks', label: 'AÇÕES' },
  { key: 'commodities', label: 'COMMOD.' },
  { key: 'forex', label: 'MOEDAS' },
  { key: 'indices', label: 'ÍNDICES' },
]

const BASE_COLS = [
  { key: 'last', label: 'Último' },
  { key: 'pct24h', label: '24h %' },
  { key: 'ret7d', label: '7d %' },
  { key: 'ret30d', label: '30d %' },
  { key: 'atr_pct', label: 'ATR14 %' },
  { key: 'vol_usd', label: 'Volume' },
]

const isCrypto = computed(() => terminal.screenerMarket === 'crypto')
const cols = computed(() =>
  isCrypto.value ? [...BASE_COLS, { key: 'funding', label: 'Funding' }] : BASE_COLS)

const sortKey = ref('vol_usd')
const sortDir = ref(-1)
const minVolM = ref(0)
const fundingFilter = ref('all')

function sortBy(key) {
  if (sortKey.value === key) sortDir.value *= -1
  else { sortKey.value = key; sortDir.value = -1 }
}

const rows = computed(() => {
  let r = terminal.screenerRows
  if (isCrypto.value) {
    if (minVolM.value > 0) r = r.filter((x) => (x.vol_usd || 0) >= minVolM.value * 1e6)
    if (fundingFilter.value === 'pos') r = r.filter((x) => (x.funding ?? 0) > 0)
    if (fundingFilter.value === 'neg') r = r.filter((x) => (x.funding ?? 0) < 0)
  }
  return [...r].sort((a, b) =>
    ((a[sortKey.value] ?? -Infinity) - (b[sortKey.value] ?? -Infinity)) * -sortDir.value * -1)
})

function openDes(r) {
  router.push({
    path: '/des',
    query: { symbol: isCrypto.value ? r.base : r.symbol, market: isCrypto.value ? 'auto' : 'tradfi' },
  })
}

function toBacktest(r) {
  if (!isCrypto.value) {
    // tradicional: ticker yfinance direto (backtest usa o fallback yfinance)
    ws.symbol = r.symbol
    ws.symbolLabel = r.label || r.base
    ws.exchange = ''
    router.push('/backtest')
    return
  }
  const base = r.base
  // resolve na lista de assets p/ preencher o workspace; senão usa o cru
  let found = null
  for (const items of Object.values(btStore.assets || {})) {
    for (const [label, ticker] of Object.entries(items)) {
      if (String(ticker).toUpperCase() === `${base}-USD`) found = { label, ticker }
    }
  }
  ws.symbol = found?.ticker || `${base}-USD`
  ws.symbolLabel = found?.label || base
  if (!ws.exchange) ws.exchange = 'bybit'
  router.push('/backtest')
}

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
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  return Math.round(v).toLocaleString('pt-BR')
}

onMounted(() => {
  terminal.startScreenerPolling()
  if (!Object.keys(btStore.assets || {}).length) btStore.fetchAssets?.()
})
onBeforeUnmount(() => terminal.stopScreenerPolling())
</script>
