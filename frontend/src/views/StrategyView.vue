<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">OSA · Simulador de Estratégias</h1>
      <span class="text-[10px] text-gray-600 font-mono">payoff · precificação Black-Scholes · greeks · cenários</span>
      <div class="flex-1" />
      <form @submit.prevent="loadChain" class="flex gap-2">
        <input v-model="symbolInput" placeholder="ex.: AAPL (opcional)"
               class="form-input !py-1.5 text-xs w-36 uppercase" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs"
                :disabled="chainLoading">{{ chainLoading ? '...' : 'Puxar chain' }}</button>
      </form>
    </div>

    <!-- parâmetros -->
    <div class="card p-4 space-y-3">
      <div class="flex flex-wrap items-end gap-3">
        <label class="text-xs text-gray-500 block">Spot
          <input v-model.number="spot" type="number" step="any"
                 class="form-input !py-1.5 text-xs w-28 mt-1 block" /></label>
        <label class="text-xs text-gray-500 block">Dias até vencimento
          <input v-model.number="dte" type="number" min="0"
                 class="form-input !py-1.5 text-xs w-24 mt-1 block" /></label>
        <label class="text-xs text-gray-500 block">IV padrão (%)
          <input v-model.number="ivDefault" type="number" step="any"
                 class="form-input !py-1.5 text-xs w-24 mt-1 block" /></label>
        <label v-if="chain" class="text-xs text-gray-500 block">Vencimento (chain)
          <select v-model="chainExpiry" @change="loadChain(chainExpiry)"
                  class="form-select !py-1.5 text-xs mt-1 block">
            <option v-for="e in chain.expiries" :key="e" :value="e">{{ e }}</option>
          </select></label>
        <div class="flex-1" />
        <button @click="run" :disabled="!legs.length || running"
                class="btn-primary !py-1.5 text-xs disabled:opacity-50">▶ Calcular</button>
      </div>

      <!-- presets -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-[10px] text-gray-600 uppercase tracking-wider">Estruturas</span>
        <button v-for="p in PRESETS" :key="p.label" @click="applyPreset(p)"
                class="px-2 py-0.5 text-[11px] font-mono rounded border border-surface-500
                       text-gray-400 hover:text-accent-yellow hover:border-accent-yellow/50">
          {{ p.label }}</button>
      </div>

      <!-- pernas -->
      <table class="w-full text-xs font-mono" v-if="legs.length">
        <thead>
          <tr class="text-[10px] text-gray-500 uppercase text-left border-b border-surface-500">
            <th class="py-1.5 pr-2">Lado</th>
            <th class="py-1.5 pr-2">Tipo</th>
            <th class="py-1.5 pr-2">Strike</th>
            <th class="py-1.5 pr-2">Qtd</th>
            <th class="py-1.5 pr-2">Prêmio pago/recebido</th>
            <th class="py-1.5 pr-2">IV % (opcional)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(l, i) in legs" :key="i" class="border-b border-surface-600/40">
            <td class="py-1 pr-2">
              <select v-model="l.side" class="form-select !py-1 text-xs">
                <option value="buy">Compra</option><option value="sell">Venda</option>
              </select></td>
            <td class="py-1 pr-2">
              <select v-model="l.kind" class="form-select !py-1 text-xs">
                <option value="call">Call</option><option value="put">Put</option>
                <option value="stock">Ativo (spot)</option>
              </select></td>
            <td class="py-1 pr-2">
              <input v-if="l.kind !== 'stock'" v-model.number="l.strike" type="number" step="any"
                     class="form-input !py-1 text-xs w-24" @change="fillPremium(l)" />
              <span v-else class="text-gray-600">—</span></td>
            <td class="py-1 pr-2">
              <input v-model.number="l.qty" type="number" min="0" step="any"
                     class="form-input !py-1 text-xs w-16" /></td>
            <td class="py-1 pr-2">
              <input v-model.number="l.premium" type="number" step="any"
                     class="form-input !py-1 text-xs w-24" /></td>
            <td class="py-1 pr-2">
              <input v-if="l.kind !== 'stock'" v-model.number="l.iv" type="number" step="any"
                     class="form-input !py-1 text-xs w-20" placeholder="auto" /></td>
            <td class="py-1 text-right">
              <button @click="legs.splice(i, 1)" class="text-gray-600 hover:text-red-400">✕</button></td>
          </tr>
        </tbody>
      </table>
      <button @click="addLeg()" class="btn-secondary !py-1 text-[11px]">+ Perna</button>
      <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
    </div>

    <template v-if="res">
      <!-- métricas -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <div class="metric-card"><span class="metric-label">Custo líquido</span>
          <span class="metric-value" :class="res.cost >= 0 ? 'text-red-400' : 'text-accent-yellow'">
            {{ res.cost >= 0 ? '-' : '+' }}{{ Math.abs(res.cost).toFixed(2) }}</span></div>
        <div class="metric-card"><span class="metric-label">Máx ganho</span>
          <span class="metric-value text-accent-yellow">
            {{ res.unbounded_gain ? 'ilimitado' : res.max_gain.toFixed(2) }}</span></div>
        <div class="metric-card"><span class="metric-label">Máx perda</span>
          <span class="metric-value text-red-400">
            {{ res.unbounded_loss ? 'ilimitada' : res.max_loss.toFixed(2) }}</span></div>
        <div class="metric-card"><span class="metric-label">Breakevens</span>
          <span class="metric-value text-gray-200 !text-sm">{{ res.breakevens.join(' · ') || '—' }}</span></div>
        <div class="metric-card"><span class="metric-label">Valor teórico (BS)</span>
          <span class="metric-value text-gray-200">{{ res.theo_total.toFixed(2) }}</span></div>
        <div class="metric-card"><span class="metric-label">Taxa r usada</span>
          <span class="metric-value text-gray-200">{{ res.risk_free }}%</span></div>
      </div>

      <!-- payoff -->
      <div class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Payoff no vencimento vs P&L teórico hoje
        </h2>
        <div ref="payoffChart" style="min-height:300px;" class="w-full"></div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- greeks líquidos -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">◆</span> Greeks líquidos (risco da posição)
          </h2>
          <table class="w-full text-sm font-mono">
            <tbody>
              <tr v-for="(g, k) in GREEK_LABELS" :key="k" class="border-b border-surface-600/40">
                <td class="py-1.5 text-gray-500">{{ g.label }} <span class="text-gray-700">({{ g.hint }})</span></td>
                <td class="py-1.5 text-right font-bold"
                    :class="res.net_greeks[k] >= 0 ? 'text-accent-yellow' : 'text-red-400'">
                  {{ res.net_greeks[k] }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- cenários -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">◆</span> Matriz de cenários — P&L (spot × tempo)
          </h2>
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="text-left py-1.5 px-2"></th>
                <th v-for="s in res.spot_shifts" :key="s" class="py-1.5 px-2">
                  {{ s > 0 ? '+' : '' }}{{ (s * 100).toFixed(0) }}%</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="sc in res.scenarios" :key="sc.when" class="border-b border-surface-600/40">
                <td class="py-1.5 px-2 text-gray-500">{{ sc.when }}</td>
                <td v-for="(v, j) in sc.pnl" :key="j" class="py-1.5 px-2 text-right font-bold"
                    :class="v >= 0 ? 'text-accent-yellow' : 'text-red-400'">{{ v }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getOptionsChain, evalStrategy } from '@/api/client.js'
import { purgeChart } from '@/composables/useCharts.js'

const route = useRoute()
const symbolInput = ref('')
const spot = ref(100)
const dte = ref(30)
const ivDefault = ref(30)
const legs = ref([])
const res = ref(null)
const error = ref(null)
const running = ref(false)
const chain = ref(null)
const chainExpiry = ref('')
const chainLoading = ref(false)
const payoffChart = ref(null)
let Plotly = null

const GREEK_LABELS = {
  delta: { label: 'Delta Δ', hint: 'exposição direcional' },
  gamma: { label: 'Gamma Γ', hint: 'convexidade do delta' },
  theta: { label: 'Theta Θ', hint: 'decaimento por dia' },
  vega: { label: 'Vega ν', hint: 'sensib. a 1% de vol' },
  rho: { label: 'Rho ρ', hint: 'sensib. a 1pp de juros' },
}

const PRESETS = [
  { label: 'CALL COMPRADA', mk: (s) => [leg('buy', 'call', rnd(s * 1.02))] },
  { label: 'PUT PROTETIVA', mk: (s) => [leg('buy', 'stock'), leg('buy', 'put', rnd(s * 0.95))] },
  { label: 'BULL CALL SPREAD', mk: (s) => [leg('buy', 'call', rnd(s)), leg('sell', 'call', rnd(s * 1.05))] },
  { label: 'BEAR PUT SPREAD', mk: (s) => [leg('buy', 'put', rnd(s)), leg('sell', 'put', rnd(s * 0.95))] },
  { label: 'STRADDLE', mk: (s) => [leg('buy', 'call', rnd(s)), leg('buy', 'put', rnd(s))] },
  { label: 'STRANGLE', mk: (s) => [leg('buy', 'call', rnd(s * 1.05)), leg('buy', 'put', rnd(s * 0.95))] },
  { label: 'IRON CONDOR', mk: (s) => [
    leg('sell', 'put', rnd(s * 0.95)), leg('buy', 'put', rnd(s * 0.90)),
    leg('sell', 'call', rnd(s * 1.05)), leg('buy', 'call', rnd(s * 1.10))] },
  { label: 'COVERED CALL', mk: (s) => [leg('buy', 'stock'), leg('sell', 'call', rnd(s * 1.05))] },
]

function leg(side, kind, strike = null) {
  return { side, kind, strike, qty: 1, premium: null, iv: null }
}
function rnd(v) {
  return Math.round(v * 2) / 2
}

function applyPreset(p) {
  legs.value = p.mk(spot.value || 100)
  legs.value.forEach(fillPremium)
  run()
}

function addLeg() {
  legs.value.push(leg('buy', 'call', rnd((spot.value || 100) * 1.02)))
  fillPremium(legs.value[legs.value.length - 1])
}

// prêmio automático: mid da chain se carregada, senão vazio (usuário preenche)
function fillPremium(l) {
  if (l.kind === 'stock') { l.premium = spot.value; return }
  if (!chain.value || l.strike == null) return
  const side = l.kind === 'call' ? chain.value.calls : chain.value.puts
  const hit = side?.find((r) => r.strike === l.strike)
    || side?.reduce((best, r) => (!best || Math.abs(r.strike - l.strike) < Math.abs(best.strike - l.strike) ? r : best), null)
  if (hit) {
    l.strike = hit.strike
    l.premium = hit.bid != null && hit.ask != null && hit.ask > 0
      ? Math.round((hit.bid + hit.ask) / 2 * 100) / 100 : hit.last
    if (hit.iv != null) l.iv = Math.round(hit.iv * 1000) / 10
  }
}

async function loadChain(exp) {
  const s = symbolInput.value.trim().toUpperCase()
  if (!s) return
  chainLoading.value = true
  error.value = null
  try {
    const { data } = await getOptionsChain(s, exp || undefined)
    if (data.error) { error.value = data.error; return }
    chain.value = data
    chainExpiry.value = data.expiry
    spot.value = Math.round(data.spot * 100) / 100
    dte.value = data.dte
    if (data.atm_iv) ivDefault.value = data.atm_iv
    legs.value.forEach(fillPremium)
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    chainLoading.value = false
  }
}

async function run() {
  if (!legs.value.length) return
  running.value = true
  error.value = null
  try {
    const { data } = await evalStrategy({
      spot: spot.value, dte: dte.value, iv_default: ivDefault.value,
      legs: legs.value.map((l) => ({ ...l })),
    })
    if (data.error) { error.value = data.error; return }
    res.value = data
    await render()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    running.value = false
  }
}

async function render() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  if (!payoffChart.value || !res.value) return
  const r = res.value
  Plotly.react(payoffChart.value, [
    { type: 'scatter', mode: 'lines', name: 'Payoff no vencimento',
      x: r.s_grid, y: r.payoff, line: { color: '#f5c518', width: 2 } },
    { type: 'scatter', mode: 'lines', name: 'P&L teórico hoje (BS)',
      x: r.s_grid, y: r.pnl_now, line: { color: '#8899aa', width: 1.3, dash: 'dot' } },
  ], {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 300,
    margin: { t: 10, r: 10, b: 40, l: 55 },
    xaxis: { title: 'Preço do ativo', gridcolor: '#1e1e1e' },
    yaxis: { title: 'P&L', gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#445' },
    legend: { orientation: 'h', y: 1.12 },
    shapes: [
      { type: 'line', x0: r.spot, x1: r.spot, y0: 0, y1: 1, yref: 'paper',
        line: { color: '#667788', width: 1, dash: 'dot' } },
      ...r.breakevens.map((b) => ({
        type: 'line', x0: b, x1: b, y0: 0, y1: 1, yref: 'paper',
        line: { color: '#4caf7d', width: 1, dash: 'dash' } })),
    ],
  }, { responsive: true, displaylogo: false, displayModeBar: false })
}

onMounted(() => {
  const q = String(route.query.symbol || '').trim()
  if (q) { symbolInput.value = q.toUpperCase(); loadChain() }
})
onBeforeUnmount(() => purgeChart(payoffChart.value))
</script>
