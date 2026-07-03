<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">BOOK · Ofertas & Negócios</h1>
      <span class="text-[10px] text-gray-600 font-mono">
        cripto: L2 bybit ao vivo (3s) · tradicional: bid/ask top-of-book (yahoo)
      </span>
      <div class="flex-1" />
      <form @submit.prevent="start" class="flex gap-2">
        <select v-model="market" class="form-select !py-1.5 text-xs">
          <option value="crypto">Cripto</option>
          <option value="tradfi">Tradicional</option>
        </select>
        <input v-model="symbolInput" :placeholder="market === 'crypto' ? 'ex.: BTC' : 'ex.: AAPL'"
               class="form-input !py-1.5 text-xs w-32 uppercase" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs">Abrir</button>
      </form>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <!-- tradfi: top-of-book -->
    <template v-if="d && d.market === 'tradfi'">
      <div class="card p-5">
        <div class="text-xs text-gray-500 font-mono mb-3">{{ d.yf_symbol }} · último {{ fmt(d.last) }}</div>
        <div class="grid grid-cols-2 gap-4 max-w-xl">
          <div class="text-center p-4 rounded-lg bg-surface-600/40 border border-green-800/40">
            <div class="text-[10px] text-gray-500 uppercase">Bid</div>
            <div class="text-3xl font-bold font-mono text-green-400">{{ fmt(d.bid) }}</div>
            <div class="text-xs text-gray-500 font-mono mt-1">{{ d.bid_size != null ? d.bid_size + ' lotes' : '' }}</div>
          </div>
          <div class="text-center p-4 rounded-lg bg-surface-600/40 border border-red-800/40">
            <div class="text-[10px] text-gray-500 uppercase">Ask</div>
            <div class="text-3xl font-bold font-mono text-red-400">{{ fmt(d.ask) }}</div>
            <div class="text-xs text-gray-500 font-mono mt-1">{{ d.ask_size != null ? d.ask_size + ' lotes' : '' }}</div>
          </div>
        </div>
        <div class="text-xs text-gray-500 font-mono mt-3">
          spread {{ spreadTradfi }} · volume dia {{ fmtVol(d.volume) }}
        </div>
        <p class="text-[10px] text-gray-600 mt-2">{{ d.note }}</p>
      </div>
    </template>

    <!-- cripto: L2 + tape -->
    <template v-else-if="d">
      <div class="flex items-baseline gap-4 font-mono">
        <span class="text-xs text-gray-500">{{ d.pair }}</span>
        <span class="text-2xl font-bold text-gray-100">{{ fmt(mid) }}</span>
        <span class="text-xs text-gray-500">spread {{ spread }}</span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- book -->
        <div class="card p-3 lg:col-span-2">
          <div class="grid grid-cols-2 gap-3">
            <!-- bids -->
            <div>
              <div class="text-[10px] text-green-400 uppercase font-semibold mb-1 text-right">Compra (bids)</div>
              <div v-for="[p, q] in d.bids" :key="'b' + p"
                   class="relative flex justify-between text-xs font-mono py-0.5 px-1">
                <div class="absolute inset-y-0 right-0 bg-green-900/30"
                     :style="{ width: depthPct(q, maxBid) }"></div>
                <span class="relative text-gray-400">{{ fmtQty(q) }}</span>
                <span class="relative text-green-400 font-semibold">{{ fmt(p) }}</span>
              </div>
            </div>
            <!-- asks -->
            <div>
              <div class="text-[10px] text-red-400 uppercase font-semibold mb-1">Venda (asks)</div>
              <div v-for="[p, q] in d.asks" :key="'a' + p"
                   class="relative flex justify-between text-xs font-mono py-0.5 px-1">
                <div class="absolute inset-y-0 left-0 bg-red-900/30"
                     :style="{ width: depthPct(q, maxAsk) }"></div>
                <span class="relative text-red-400 font-semibold">{{ fmt(p) }}</span>
                <span class="relative text-gray-400">{{ fmtQty(q) }}</span>
              </div>
            </div>
          </div>
          <div class="mt-2 text-[10px] text-gray-600 font-mono text-center">
            pressão compradora: {{ buyPressure }}% do book visível
          </div>
        </div>

        <!-- tape -->
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-1">Negócios recentes</div>
          <div class="max-h-[420px] overflow-y-auto">
            <div v-for="(t, i) in d.trades" :key="i"
                 class="flex justify-between text-[11px] font-mono py-0.5 border-b border-surface-600/30">
              <span class="text-gray-600 w-14">{{ tsFmt(t.ts) }}</span>
              <span :class="t.side === 'buy' ? 'text-green-400' : 'text-red-400'" class="w-10">
                {{ t.side === 'buy' ? 'COMPRA' : 'VENDA' }}</span>
              <span class="text-gray-300">{{ fmt(t.price) }}</span>
              <span class="text-gray-500">{{ fmtQty(t.qty) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="text-center text-gray-600 text-sm py-16">
      Informe um ativo — ou command line: <span class="font-mono text-accent-yellow">BTC BOOK</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getBook } from '@/api/client.js'

const route = useRoute()
const symbolInput = ref('')
const market = ref('crypto')
const d = ref(null)
const loading = ref(false)
const error = ref(null)
let timer = null

const mid = computed(() => {
  if (!d.value?.bids?.length || !d.value?.asks?.length) return null
  return (d.value.bids[0][0] + d.value.asks[0][0]) / 2
})
const spread = computed(() => {
  if (!d.value?.bids?.length || !d.value?.asks?.length) return '—'
  const s = d.value.asks[0][0] - d.value.bids[0][0]
  return `${fmt(s)} (${(s / d.value.asks[0][0] * 100).toFixed(4)}%)`
})
const spreadTradfi = computed(() => {
  if (d.value?.bid == null || d.value?.ask == null) return '—'
  return fmt(d.value.ask - d.value.bid)
})
const maxBid = computed(() => Math.max(...(d.value?.bids || [[0, 0]]).map((x) => x[1])))
const maxAsk = computed(() => Math.max(...(d.value?.asks || [[0, 0]]).map((x) => x[1])))
const buyPressure = computed(() => {
  const b = (d.value?.bids || []).reduce((s, x) => s + x[1], 0)
  const a = (d.value?.asks || []).reduce((s, x) => s + x[1], 0)
  return b + a > 0 ? Math.round(b / (b + a) * 100) : 50
})

function depthPct(q, max) {
  return (max > 0 ? Math.min(100, q / max * 100) : 0) + '%'
}

async function fetchBook() {
  const s = symbolInput.value.trim().toUpperCase()
  if (!s) return
  try {
    const { data } = await getBook(s, 'bybit', market.value)
    if (data.error) { error.value = data.error; return }
    d.value = data
    error.value = null
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
}

function start() {
  stop()
  d.value = null
  loading.value = true
  fetchBook().finally(() => { loading.value = false })
  // tradfi é ~15min atrasado; poll só faz sentido p/ cripto
  if (market.value === 'crypto') timer = setInterval(fetchBook, 3000)
}

function stop() {
  if (timer) { clearInterval(timer); timer = null }
}

function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: v < 1 ? 6 : 2 })
}
function fmtQty(v) {
  if (v == null) return '—'
  return v >= 1000 ? (v / 1000).toFixed(1) + 'K' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 3 })
}
function fmtVol(v) {
  if (v == null) return '—'
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  return Math.round(v).toLocaleString('pt-BR')
}
function tsFmt(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('pt-BR', { hour12: false })
}

onMounted(() => {
  const q = String(route.query.symbol || '').trim()
  const m = String(route.query.market || '').trim()
  if (m === 'tradfi') market.value = 'tradfi'
  if (q) { symbolInput.value = q.toUpperCase(); start() }
})
onBeforeUnmount(stop)
</script>
