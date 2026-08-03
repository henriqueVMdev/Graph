<template>
  <div class="h-[calc(100dvh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">Monitor de Mercado</h1>
      <span class="text-[11px] text-gray-500 font-mono">cripto: bybit perp · tradicional: yahoo (~15min) · atualiza 5s</span>
      <div class="flex-1" />
      <form @submit.prevent="add" class="flex gap-2">
        <select v-model="newMarket" class="form-select !py-1.5 text-xs">
          <option value="crypto">Cripto</option>
          <option value="tradfi">Tradicional</option>
        </select>
        <input v-model="newSymbol" :placeholder="newMarket === 'crypto' ? 'ex.: SUI' : 'ex.: AAPL, OURO, EURUSD'"
               class="form-input !py-1.5 text-xs w-44" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs">+ Adicionar</button>
      </form>
    </div>

    <div v-if="terminal.watchError" class="card p-3 text-xs text-accent-red-light">
      {{ terminal.watchError }}
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm font-mono">
        <thead>
          <tr class="text-[11px] text-gray-400 uppercase tracking-wider text-right border-b border-surface-500">
            <th scope="col" class="text-left px-3 py-2">Ativo</th>
            <th scope="col" class="px-3 py-2">Último</th>
            <th scope="col" class="px-3 py-2">24h %</th>
            <th scope="col" class="px-3 py-2">Máx 24h</th>
            <th scope="col" class="px-3 py-2">Mín 24h</th>
            <th scope="col" class="px-3 py-2">Volume ($)</th>
            <th scope="col" class="px-3 py-2">Funding</th>
            <th scope="col" class="px-3 py-2">24h (15m)</th>
            <th scope="col" class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in terminal.watchRows" :key="rowKey(r)"
              class="border-b border-surface-600/60 hover:bg-surface-600/40 transition-colors">
            <td class="px-3 py-2 text-left">
              <button @click="openDes(r)"
                      class="font-bold text-gray-100 hover:text-accent-yellow">{{ r.base }}</button>
              <span v-if="r.market === 'tradfi'" class="ml-1.5 text-[11px] font-mono px-1 py-0.5
                    rounded bg-blue-900/40 text-blue-300 border border-blue-800/50 align-middle"
                    :title="r.label">TRAD</span>
            </td>
            <td class="px-3 py-2 text-right font-semibold transition-colors duration-500"
                :class="flash[rowKey(r)]">{{ fmt(r.last) }}</td>
            <td class="px-3 py-2 text-right"
                :class="(r.pct24h ?? 0) >= 0 ? 'text-accent-yellow' : 'text-accent-red-light'">
              {{ fmtPct(r.pct24h) }}
            </td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmt(r.high24) }}</td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmt(r.low24) }}</td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmtVol(r.vol_usd) }}</td>
            <td class="px-3 py-2 text-right"
                :class="(r.funding ?? 0) >= 0 ? 'text-gray-300' : 'text-accent-red-light'">
              {{ fmtFunding(r.funding) }}
            </td>
            <td class="px-3 py-2">
              <Sparkline :points="terminal.sparks[rowKey(r)]" />
            </td>
            <td class="px-3 py-2 text-right whitespace-nowrap">
              <button @click="openBook(r)" title="Book de ofertas"
                      class="text-gray-500 hover:text-accent-yellow text-xs px-1">📖</button>
              <button @click="alertFor(r)" title="Criar alerta"
                      class="text-gray-500 hover:text-accent-yellow text-xs px-1">⏰</button>
              <button @click="terminal.removeFromWatchlist(r.base, r.market)" title="Remover"
                      class="text-gray-500 hover:text-accent-red-light text-xs px-1">✕</button>
            </td>
          </tr>
          <tr v-if="!terminal.watchRows.length">
            <td colspan="9" class="text-center text-xs text-gray-500 py-8">
              Watchlist vazia — adicione um símbolo acima ou via command line (Ctrl+K: "SUI MON").
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { DIRECAO } from '@/composables/chartTheme.js'
import { ref, watch, onMounted, onBeforeUnmount, h } from 'vue'
import { useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'
import { maxOf, minOf } from '@/utils.js'

const terminal = useTerminalStore()
const router = useRouter()
const newSymbol = ref('')
const newMarket = ref('crypto')
const flash = ref({})           // rowKey -> classe de flash
const lastPrices = {}

function rowKey(r) {
  return `${r.market || 'crypto'}:${r.base}`
}

// flash verde/vermelho quando o preço muda
watch(() => terminal.watchRows, (rows) => {
  for (const r of rows) {
    const k = rowKey(r)
    const prev = lastPrices[k]
    if (prev != null && r.last != null && r.last !== prev) {
      flash.value = { ...flash.value, [k]: r.last > prev ? 'text-accent-yellow' : 'text-accent-red-light' }
      setTimeout(() => { flash.value = { ...flash.value, [k]: '' } }, 600)
    }
    lastPrices[k] = r.last
  }
}, { deep: true })

function add() {
  if (newSymbol.value.trim()) {
    terminal.addToWatchlist(newSymbol.value, newMarket.value)
    newSymbol.value = ''
  }
}

function openDes(r) {
  router.push({ path: '/des', query: { symbol: r.base, market: r.market || 'auto' } })
}

function alertFor(r) {
  router.push({ path: '/alerts', query: { symbol: r.base, price: r.last, market: r.market || 'crypto' } })
}

function openBook(r) {
  router.push({ path: '/book', query: { symbol: r.base, market: r.market || 'crypto' } })
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
function fmtFunding(v) {
  return v == null ? '—' : (v * 100).toFixed(4) + '%'
}

// Sparkline inline (SVG puro, sem lib)
const Sparkline = (props) => {
  const pts = props.points
  if (!pts || pts.length < 2) return h('div', { class: 'w-24 h-6' })
  const min = minOf(pts), max = maxOf(pts)
  const range = max - min || 1
  const w = 96, hgt = 24
  const d = pts.map((p, i) =>
    `${(i / (pts.length - 1)) * w},${hgt - ((p - min) / range) * (hgt - 2) - 1}`).join(' ')
  const up = pts[pts.length - 1] >= pts[0]
  return h('svg', { width: w, height: hgt, class: 'block ml-auto' }, [
    h('polyline', {
      points: d, fill: 'none',
      stroke: up ? '#f5c518' : DIRECAO.baixa, 'stroke-width': 1.2,
    }),
  ])
}
Sparkline.props = { points: Array }

onMounted(() => terminal.startWatchPolling())
onBeforeUnmount(() => terminal.stopWatchPolling())
</script>
