<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">OMON · Opções</h1>
      <span class="text-[10px] text-gray-600 font-mono">chain via yahoo (~15min) · ações, ETFs e índices US</span>
      <div class="flex-1" />
      <form @submit.prevent="load()" class="flex gap-2 items-center">
        <input v-model="symbolInput" placeholder="ex.: AAPL, SPY, TSLA"
               class="form-input !py-1.5 text-xs w-36 uppercase" />
        <select v-if="d?.expiries?.length" v-model="expiry" @change="load(expiry)"
                class="form-select !py-1.5 text-xs">
          <option v-for="e in d.expiries" :key="e" :value="e">{{ e }}</option>
        </select>
        <button type="submit" class="btn-secondary !py-1.5 text-xs">Carregar</button>
      </form>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <div v-if="loading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Carregando chain de {{ symbolInput.toUpperCase() }}...</p>
    </div>

    <template v-else-if="d">
      <!-- cards -->
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <div class="metric-card"><span class="metric-label">Spot</span>
          <span class="metric-value text-gray-200">{{ fmt(d.spot) }}</span></div>
        <div class="metric-card"><span class="metric-label">Vencimento</span>
          <span class="metric-value text-gray-200 !text-sm">{{ d.expiry }} ({{ d.dte }}d)</span></div>
        <div class="metric-card"><span class="metric-label">IV ATM</span>
          <span class="metric-value text-accent-yellow">{{ d.atm_iv != null ? d.atm_iv.toFixed(1) + '%' : '—' }}</span></div>
        <div class="metric-card"><span class="metric-label">Vol histórica 30d</span>
          <span class="metric-value text-gray-200">{{ d.hist_vol30 != null ? d.hist_vol30.toFixed(1) + '%' : '—' }}</span></div>
        <div class="metric-card"><span class="metric-label">IV / HV</span>
          <span class="metric-value" :class="ivHvClass">{{ ivHv }}</span></div>
      </div>

      <!-- smile -->
      <div class="card p-4">
        <div class="flex items-center gap-3 mb-3">
          <h2 class="text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Volatilidade implícita por strike (smile)
          </h2>
          <div class="flex-1" />
          <button @click="toStrategy" class="btn-secondary !py-1 text-[11px]">⚙ Simular estratégia (OSA)</button>
          <button @click="loadSurface" :disabled="surfaceLoading"
                  class="btn-secondary !py-1 text-[11px] disabled:opacity-50">
            {{ surfaceLoading ? 'montando…' : surface ? '↻ Superfície' : '▦ Superfície de vol' }}
          </button>
        </div>
        <div ref="smileChart" style="min-height:260px;" class="w-full"></div>
      </div>

      <!-- superfície de volatilidade -->
      <div v-if="surface" class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Superfície de volatilidade — IV% por moneyness × vencimento
        </h2>
        <div ref="surfaceChart" style="min-height:340px;" class="w-full"></div>
      </div>

      <!-- chain -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div v-for="side in SIDES" :key="side.key" class="card overflow-x-auto">
          <div class="px-3 pt-2 text-xs font-semibold"
               :class="side.key === 'calls' ? 'text-accent-yellow' : 'text-red-400'">
            {{ side.label }} ({{ d[side.key].length }})
          </div>
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="px-2 py-1.5">Strike</th>
                <th class="px-2 py-1.5">Último</th>
                <th class="px-2 py-1.5">Bid</th>
                <th class="px-2 py-1.5">Ask</th>
                <th class="px-2 py-1.5">Vol</th>
                <th class="px-2 py-1.5">OI</th>
                <th class="px-2 py-1.5">IV</th>
                <th class="px-2 py-1.5" title="Black-Scholes">Teo</th>
                <th class="px-2 py-1.5">Δ</th>
                <th class="px-2 py-1.5">Γ</th>
                <th class="px-2 py-1.5" title="por dia">Θ</th>
                <th class="px-2 py-1.5" title="por 1% de vol">ν</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in d[side.key]" :key="r.strike"
                  class="border-b border-surface-600/40 text-right"
                  :class="r.itm ? 'bg-surface-600/30' : ''">
                <td class="px-2 py-1 font-bold"
                    :class="r.itm ? (side.key === 'calls' ? 'text-accent-yellow' : 'text-red-400') : 'text-gray-300'">
                  {{ r.strike }}</td>
                <td class="px-2 py-1 text-gray-300">{{ r.last ?? '—' }}</td>
                <td class="px-2 py-1 text-gray-400">{{ r.bid ?? '—' }}</td>
                <td class="px-2 py-1 text-gray-400">{{ r.ask ?? '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.volume != null ? Math.round(r.volume) : '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.oi != null ? Math.round(r.oi) : '—' }}</td>
                <td class="px-2 py-1 text-gray-300">{{ r.iv != null ? (r.iv * 100).toFixed(1) + '%' : '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.theo != null ? r.theo.toFixed(2) : '—' }}</td>
                <td class="px-2 py-1 text-gray-300">{{ r.delta != null ? r.delta.toFixed(2) : '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.gamma != null ? r.gamma.toFixed(4) : '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.theta != null ? r.theta.toFixed(3) : '—' }}</td>
                <td class="px-2 py-1 text-gray-500">{{ r.vega != null ? r.vega.toFixed(3) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="text-center text-gray-600 text-sm py-16">
      Informe um ticker com opções listadas (EUA) — ou command line:
      <span class="font-mono text-accent-yellow">AAPL OMON</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOptionsChain, getVolSurface } from '@/api/client.js'
import { purgeChart } from '@/composables/useCharts.js'

const route = useRoute()
const router = useRouter()
const symbolInput = ref('')
const expiry = ref('')
const d = ref(null)
const loading = ref(false)
const error = ref(null)
const smileChart = ref(null)
const surface = ref(null)
const surfaceLoading = ref(false)
const surfaceChart = ref(null)
let Plotly = null

function toStrategy() {
  router.push({ path: '/osa', query: { symbol: d.value?.symbol || symbolInput.value } })
}

async function loadSurface() {
  surfaceLoading.value = true
  try {
    const { data } = await getVolSurface(symbolInput.value.trim().toUpperCase())
    if (data.error) { error.value = data.error; return }
    surface.value = data
    await renderSurface()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    surfaceLoading.value = false
  }
}

async function renderSurface() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const s = surface.value
  if (!surfaceChart.value || !s?.iv_grid?.length) return
  Plotly.react(surfaceChart.value, [{
    type: 'heatmap',
    x: s.moneyness.map((m) => (m * 100).toFixed(0) + '%'),
    y: s.expiries.map((e, i) => `${e} (${s.dtes[i]}d)`),
    z: s.iv_grid,
    colorscale: [[0, '#101010'], [0.5, '#8a6d13'], [1, '#f5c518']],
    hovertemplate: 'moneyness %{x} · %{y}<br>IV %{z}%<extra></extra>',
    colorbar: { title: 'IV %', tickfont: { color: '#d0d0d0' } },
  }], {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 340,
    margin: { t: 10, r: 10, b: 40, l: 110 },
    xaxis: { title: 'Moneyness (strike / spot)' },
    yaxis: { autorange: 'reversed' },
  }, { responsive: true, displaylogo: false, displayModeBar: false })
}

const SIDES = [
  { key: 'calls', label: 'CALLS' },
  { key: 'puts', label: 'PUTS' },
]

const ivHv = computed(() => {
  if (!d.value?.atm_iv || !d.value?.hist_vol30) return '—'
  return (d.value.atm_iv / d.value.hist_vol30).toFixed(2) + 'x'
})
const ivHvClass = computed(() => {
  if (!d.value?.atm_iv || !d.value?.hist_vol30) return 'text-gray-200'
  return d.value.atm_iv > d.value.hist_vol30 ? 'text-red-400' : 'text-accent-yellow'
})

async function load(exp) {
  const s = symbolInput.value.trim().toUpperCase()
  if (!s) return
  if (surface.value && surface.value.symbol !== s) surface.value = null
  loading.value = true
  error.value = null
  try {
    const { data } = await getOptionsChain(s, exp || undefined)
    if (data.error) { error.value = data.error; d.value = null; return }
    d.value = data
    expiry.value = data.expiry
    // conteúdo é v-else-if do loader: baixar a flag antes do render
    loading.value = false
    await renderSmile()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
    d.value = null
  } finally {
    loading.value = false
  }
}

async function renderSmile() {
  if (!d.value) return
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  // ref só existe depois do DOM trocar o loader pelo conteúdo
  await nextTick()
  if (!smileChart.value) return
  const mk = (rows, name, color) => {
    const pts = rows.filter((r) => r.iv != null && r.strike != null)
    return { type: 'scatter', mode: 'lines+markers', name,
             x: pts.map((r) => r.strike), y: pts.map((r) => r.iv * 100),
             line: { color, width: 1.5 }, marker: { size: 4 } }
  }
  const shapes = d.value.spot ? [{
    type: 'line', x0: d.value.spot, x1: d.value.spot, y0: 0, y1: 1,
    yref: 'paper', line: { color: '#667788', width: 1, dash: 'dot' },
  }] : []
  Plotly.react(smileChart.value, [
    mk(d.value.calls, 'Calls', '#f5c518'),
    mk(d.value.puts, 'Puts', '#ef5350'),
  ], {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 260,
    margin: { t: 10, r: 10, b: 40, l: 45 },
    xaxis: { title: 'Strike', gridcolor: '#1e1e1e' },
    yaxis: { title: 'IV (%)', gridcolor: '#1e1e1e' },
    legend: { orientation: 'h', y: 1.15 },
    shapes,
    annotations: d.value.spot ? [{
      x: d.value.spot, y: 1, yref: 'paper', text: 'spot', showarrow: false,
      font: { size: 10, color: '#667788' }, yanchor: 'bottom',
    }] : [],
  }, { responsive: true, displaylogo: false, displayModeBar: false })
}

function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}

onMounted(() => {
  const q = String(route.query.symbol || '').trim()
  if (q) { symbolInput.value = q.toUpperCase(); load() }
})
onBeforeUnmount(() => { purgeChart(smileChart.value); purgeChart(surfaceChart.value) })
</script>
