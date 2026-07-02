<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">Monitor de Mercado</h1>
      <span class="text-[10px] text-gray-600 font-mono">bybit perp · atualiza 5s</span>
      <div class="flex-1" />
      <form @submit.prevent="add" class="flex gap-2">
        <input v-model="newSymbol" placeholder="adicionar (ex.: SUI)"
               class="form-input !py-1.5 text-xs w-40" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs">+ Adicionar</button>
      </form>
    </div>

    <div v-if="terminal.watchError" class="card p-3 text-xs text-red-400">
      {{ terminal.watchError }}
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm font-mono">
        <thead>
          <tr class="text-[10px] text-gray-500 uppercase tracking-wider text-right border-b border-surface-500">
            <th class="text-left px-3 py-2">Ativo</th>
            <th class="px-3 py-2">Último</th>
            <th class="px-3 py-2">24h %</th>
            <th class="px-3 py-2">Máx 24h</th>
            <th class="px-3 py-2">Mín 24h</th>
            <th class="px-3 py-2">Volume ($)</th>
            <th class="px-3 py-2">Funding</th>
            <th class="px-3 py-2">24h (15m)</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in terminal.watchRows" :key="r.base"
              class="border-b border-surface-600/60 hover:bg-surface-600/40 transition-colors">
            <td class="px-3 py-2 text-left">
              <button @click="openDes(r.base)"
                      class="font-bold text-gray-100 hover:text-accent-yellow">{{ r.base }}</button>
            </td>
            <td class="px-3 py-2 text-right font-semibold transition-colors duration-500"
                :class="flash[r.base]">{{ fmt(r.last) }}</td>
            <td class="px-3 py-2 text-right"
                :class="(r.pct24h ?? 0) >= 0 ? 'text-accent-yellow' : 'text-red-400'">
              {{ fmtPct(r.pct24h) }}
            </td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmt(r.high24) }}</td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmt(r.low24) }}</td>
            <td class="px-3 py-2 text-right text-gray-400">{{ fmtVol(r.vol_usd) }}</td>
            <td class="px-3 py-2 text-right"
                :class="(r.funding ?? 0) >= 0 ? 'text-gray-300' : 'text-red-400'">
              {{ fmtFunding(r.funding) }}
            </td>
            <td class="px-3 py-2">
              <Sparkline :points="terminal.sparks[r.base]" />
            </td>
            <td class="px-3 py-2 text-right whitespace-nowrap">
              <button @click="alertFor(r)" title="Criar alerta"
                      class="text-gray-600 hover:text-accent-yellow text-xs px-1">⏰</button>
              <button @click="terminal.removeFromWatchlist(r.base)" title="Remover"
                      class="text-gray-600 hover:text-red-400 text-xs px-1">✕</button>
            </td>
          </tr>
          <tr v-if="!terminal.watchRows.length">
            <td colspan="9" class="text-center text-xs text-gray-600 py-8">
              Watchlist vazia — adicione um símbolo acima ou via command line (Ctrl+K: "SUI MON").
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, h } from 'vue'
import { useRouter } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'

const terminal = useTerminalStore()
const router = useRouter()
const newSymbol = ref('')
const flash = ref({})           // base -> classe de flash
const lastPrices = {}

// flash verde/vermelho quando o preço muda
watch(() => terminal.watchRows, (rows) => {
  for (const r of rows) {
    const prev = lastPrices[r.base]
    if (prev != null && r.last != null && r.last !== prev) {
      flash.value = { ...flash.value, [r.base]: r.last > prev ? 'text-green-400' : 'text-red-400' }
      setTimeout(() => { flash.value = { ...flash.value, [r.base]: '' } }, 600)
    }
    lastPrices[r.base] = r.last
  }
}, { deep: true })

function add() {
  if (newSymbol.value.trim()) {
    terminal.addToWatchlist(newSymbol.value)
    terminal.fetchSpark(newSymbol.value.trim().toUpperCase())
    newSymbol.value = ''
  }
}

function openDes(base) {
  router.push({ path: '/des', query: { symbol: base } })
}

function alertFor(r) {
  router.push({ path: '/alerts', query: { symbol: r.base, price: r.last } })
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
  const min = Math.min(...pts), max = Math.max(...pts)
  const range = max - min || 1
  const w = 96, hgt = 24
  const d = pts.map((p, i) =>
    `${(i / (pts.length - 1)) * w},${hgt - ((p - min) / range) * (hgt - 2) - 1}`).join(' ')
  const up = pts[pts.length - 1] >= pts[0]
  return h('svg', { width: w, height: hgt, class: 'block ml-auto' }, [
    h('polyline', {
      points: d, fill: 'none',
      stroke: up ? '#f5c518' : '#ef5350', 'stroke-width': 1.2,
    }),
  ])
}
Sparkline.props = { points: Array }

onMounted(() => terminal.startWatchPolling())
onBeforeUnmount(() => terminal.stopWatchPolling())
</script>
