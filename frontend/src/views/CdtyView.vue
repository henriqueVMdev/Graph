<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">CDTY · Commodities</h1>
      <span class="text-[10px] text-gray-600 font-mono">futuros CME/ICE via yahoo (~15min)</span>
      <div class="flex-1" />
      <div class="flex rounded-lg overflow-hidden border border-surface-500">
        <button v-for="t in TABS" :key="t.key" @click="setTab(t.key)"
                class="px-2.5 py-1 text-[11px] font-mono transition-colors"
                :class="tab === t.key ? 'bg-accent-yellow text-black font-bold' : 'text-gray-400 hover:text-gray-200'">
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- ══ PAINEL ══ -->
    <template v-if="tab === 'painel'">
      <div v-if="!overview" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Carregando commodities...</p>
      </div>
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div v-for="g in overview.groups" :key="g.group" class="card overflow-x-auto">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> {{ g.group }}
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="r in g.rows" :key="r.base"
                  class="border-b border-surface-600/40 hover:bg-surface-600/30">
                <td class="px-3 py-1.5">
                  <button @click="openDes(r.base)"
                          class="text-gray-100 hover:text-accent-yellow font-bold">{{ r.label }}</button>
                </td>
                <td class="px-3 py-1.5 text-right text-gray-200 font-semibold">{{ fmt(r.last) }}</td>
                <td class="px-3 py-1.5 text-right w-20" :class="pctClass(r.pct24h)">{{ fmtPct(r.pct24h) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-500">{{ fmt(r.low24) }}–{{ fmt(r.high24) }}</td>
                <td class="px-3 py-1.5 text-right">
                  <button v-if="hasCurve(r.base)" @click="toCurve(r.base)" title="Curva futura"
                          class="text-gray-600 hover:text-accent-yellow">〰</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ══ CURVAS ══ -->
    <template v-else-if="tab === 'curvas'">
      <div class="card p-4 flex flex-wrap items-end gap-3">
        <label class="text-xs text-gray-500 block">
          Commodity
          <select v-model="curveKey" @change="loadCurve" class="form-select !py-1.5 text-xs mt-1 block w-56">
            <option v-for="c in curvesMeta" :key="c.key" :value="c.key">{{ c.label }} ({{ c.unit }})</option>
          </select>
        </label>
        <span v-if="curve?.structure" class="text-xs font-mono px-2 py-1 rounded mb-0.5"
              :class="curve.structure === 'contango'
                ? 'bg-blue-900/40 text-blue-300' : 'bg-amber-900/40 text-amber-300'">
          {{ curve.structure.toUpperCase() }}
        </span>
      </div>

      <div v-if="curveLoading" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Buscando contratos futuros...</p>
      </div>

      <template v-else-if="curve">
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">◆</span>
            Curva futura — {{ curve.label }} ({{ curve.unit }})
          </h2>
          <div ref="curveChart" style="min-height:280px;" class="w-full"></div>
        </div>

        <div class="card overflow-x-auto">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Spreads entre vencimentos (calendário)
          </div>
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="text-left px-3 py-2">Par</th>
                <th class="px-3 py-2">Spread</th>
                <th class="px-3 py-2">Leitura</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in curve.spreads" :key="s.pair" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5 text-gray-200">{{ s.pair }}</td>
                <td class="px-3 py-1.5 text-right font-bold"
                    :class="s.value > 0 ? 'text-amber-300' : 'text-blue-300'">
                  {{ s.value > 0 ? '+' : '' }}{{ s.value }}</td>
                <td class="px-3 py-1.5 text-right text-gray-500">
                  {{ s.value > 0 ? 'backwardation (curto > longo)' : 'contango (longo > curto)' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>

    <!-- ══ CLIMA ══ -->
    <template v-else-if="tab === 'clima'">
      <div v-if="!wx" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Consultando met.no para as regiões produtoras...</p>
      </div>
      <template v-else>
        <p class="text-[10px] text-gray-600 font-mono">
          {{ wx.source }} · impacto potencial em safra por região · flags: seca &lt;5mm/7d · chuva &gt;80mm/7d · calor ≥35°C
        </p>
        <p class="text-[10px] text-gray-600">
          leitura simplificada de oferta × demanda — não considera o calendário da safra (ex.: seca durante a colheita pode até ajudar; o dano real é na floração/enchimento do grão)
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div v-for="r in wx.rows" :key="r.region" class="card p-4">
            <div class="text-sm font-semibold text-gray-200">{{ r.region }}</div>
            <div class="text-[10px] text-gray-500 font-mono mb-2">{{ r.crops }}</div>
            <div class="flex items-baseline gap-3 font-mono">
              <span class="text-2xl font-bold"
                    :class="r.precip_7d_mm < 5 ? 'text-amber-300' : r.precip_7d_mm > 80 ? 'text-blue-300' : 'text-gray-200'">
                {{ r.precip_7d_mm }}<span class="text-xs">mm</span></span>
              <span class="text-xs text-gray-500">7 dias</span>
              <span class="text-sm text-gray-400">máx {{ r.tmax_7d }}°C</span>
            </div>
            <div class="mt-2 flex gap-1 flex-wrap">
              <span v-for="f in r.flags" :key="f"
                    class="text-[9px] font-mono px-1.5 py-0.5 rounded uppercase"
                    :class="f === 'seca' ? 'bg-amber-900/50 text-amber-300'
                      : f === 'calor extremo' ? 'bg-red-900/50 text-red-300'
                      : 'bg-blue-900/50 text-blue-300'">{{ f }}</span>
              <span v-if="!r.flags.length" class="text-[9px] font-mono px-1.5 py-0.5 rounded
                    bg-surface-600/60 text-gray-500 uppercase">normal</span>
            </div>
            <p v-if="r.impact" class="mt-2 text-[10px] leading-relaxed"
               :class="r.flags.length ? 'text-amber-200/70' : 'text-gray-600'">{{ r.impact }}</p>
          </div>
        </div>
      </template>
    </template>

    <!-- ══ FRETE ══ -->
    <template v-else-if="tab === 'frete'">
      <div v-if="!ship" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Carregando frete & shipping...</p>
      </div>
      <template v-else>
        <p class="text-[10px] text-gray-600 font-mono">{{ ship.note }}</p>
        <div class="card overflow-x-auto">
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="text-left px-3 py-2">Ativo</th>
                <th class="text-left px-3 py-2">Nome</th>
                <th class="text-left px-3 py-2">Segmento</th>
                <th class="px-3 py-2">Último</th>
                <th class="px-3 py-2">Dia %</th>
                <th class="px-3 py-2">Faixa dia</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in ship.rows" :key="r.base" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5">
                  <button @click="openDes(r.base)"
                          class="text-gray-100 hover:text-accent-yellow font-bold">{{ r.base }}</button>
                </td>
                <td class="px-3 py-1.5 text-gray-400">{{ r.label }}</td>
                <td class="px-3 py-1.5 text-gray-500">{{ r.segment }}</td>
                <td class="px-3 py-1.5 text-right text-gray-200">{{ fmt(r.last) }}</td>
                <td class="px-3 py-1.5 text-right" :class="pctClass(r.pct24h)">{{ fmtPct(r.pct24h) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-500">{{ fmt(r.low24) }}–{{ fmt(r.high24) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>

    <!-- ══ ESTOQUES (EIA) ══ -->
    <template v-else-if="tab === 'estoques'">
      <div v-if="!inv" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Consultando EIA...</p>
      </div>
      <div v-else-if="!inv.configured" class="card p-5 text-sm text-gray-400 leading-relaxed">
        <span class="text-accent-yellow font-semibold">Estoques · Produção · Demanda (EIA)</span><br />
        {{ inv.howto }}
      </div>
      <template v-else>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div v-for="s in inv.series" :key="s.id" class="card p-4">
            <h2 class="text-sm font-semibold text-gray-200 mb-1">
              <span class="text-accent-yellow">◆</span> {{ s.label }}
            </h2>
            <template v-if="!s.error">
              <div class="text-xl font-bold font-mono text-gray-100 mb-2">
                {{ s.now?.toLocaleString('pt-BR') }} <span class="text-xs text-gray-500">{{ s.unit }}</span>
              </div>
              <MiniSeries :dates="s.dates" :values="s.values" />
            </template>
            <p v-else class="text-xs text-red-400">série indisponível</p>
          </div>
        </div>
      </template>
    </template>

    <!-- ══ NOTÍCIAS ══ -->
    <template v-else-if="tab === 'noticias'">
      <div class="flex flex-wrap gap-2">
        <button v-for="c in NEWS_CHIPS" :key="c.label" @click="loadNews(c.q)"
                class="px-2 py-0.5 text-[11px] font-mono rounded border transition-colors"
                :class="newsQ === c.q
                  ? 'border-accent-yellow text-accent-yellow'
                  : 'border-surface-500 text-gray-400 hover:text-gray-200'">
          {{ c.label }}
        </button>
      </div>
      <div v-if="newsLoading" class="flex flex-col items-center py-10">
        <div class="dollar-loader mb-3">$</div>
      </div>
      <div v-else class="card divide-y divide-surface-600/50">
        <a v-for="n in newsItems" :key="n.link" :href="n.link" target="_blank" rel="noopener"
           class="flex items-baseline gap-3 px-4 py-2.5 hover:bg-surface-600/40 transition-colors group">
          <span class="text-[10px] font-mono w-14 shrink-0 text-gray-600">{{ rel(n.ts) }}</span>
          <span class="text-[10px] font-mono w-20 shrink-0 uppercase text-orange-300/80">{{ n.source }}</span>
          <span class="text-sm text-gray-300 group-hover:text-gray-100 leading-snug">{{ n.title }}</span>
        </a>
        <div v-if="!newsItems.length" class="text-center text-xs text-gray-600 py-10">
          nenhuma notícia p/ esse filtro agora
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, h, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  getCdtyOverview, getCdtyCurves, getCdtyCurve,
  getCdtyWeather, getCdtyShipping, getCdtyInventories, getNews,
} from '@/api/client.js'
import { purgeChart } from '@/composables/useCharts.js'

const router = useRouter()

const TABS = [
  { key: 'painel', label: 'PAINEL' },
  { key: 'curvas', label: 'CURVAS FUTURAS' },
  { key: 'clima', label: 'CLIMA & SAFRAS' },
  { key: 'frete', label: 'FRETE & SHIPPING' },
  { key: 'estoques', label: 'ESTOQUES (EIA)' },
  { key: 'noticias', label: 'NOTÍCIAS' },
]
const tab = ref('painel')

const overview = ref(null)
const curvesMeta = ref([])
const curveKey = ref('CL')
const curve = ref(null)
const curveLoading = ref(false)
const curveChart = ref(null)
const wx = ref(null)
const ship = ref(null)
const inv = ref(null)
let Plotly = null
let overviewTimer = null

const NEWS_CHIPS = [
  { label: 'TODAS', q: '' },
  { label: 'PETRÓLEO & GÁS', q: 'oil|crude|opec|gas|lng|petro' },
  { label: 'METAIS', q: 'gold|silver|copper|mining|metal|lithium|nickel' },
  { label: 'GRÃOS & SOFTS', q: 'corn|wheat|soy|coffee|sugar|cocoa|cotton|grain|crop' },
  { label: 'ENERGIA', q: 'energy|power|electric|solar|nuclear' },
]
const newsItems = ref([])
const newsLoading = ref(false)
const newsQ = ref('')

function setTab(t) {
  tab.value = t
  if (t === 'clima' && !wx.value) loadWeather()
  if (t === 'frete' && !ship.value) loadShipping()
  if (t === 'estoques' && !inv.value) loadInventories()
  if (t === 'curvas' && !curve.value) loadCurve()
  if (t === 'noticias' && !newsItems.value.length) loadNews('')
}

function hasCurve(base) {
  return curvesMeta.value.some((c) => `${c.key}=F` === base)
}
function toCurve(base) {
  curveKey.value = base.replace('=F', '')
  tab.value = 'curvas'
  loadCurve()
}
function openDes(base) {
  router.push({ path: '/des', query: { symbol: base, market: 'tradfi' } })
}

async function loadOverview() {
  try {
    const { data } = await getCdtyOverview()
    if (data.groups) overview.value = data
  } catch { /* próximo ciclo */ }
}

async function loadCurve() {
  curveLoading.value = true
  try {
    const { data } = await getCdtyCurve(curveKey.value)
    if (!data.error) {
      curve.value = data
      curveLoading.value = false     // conteúdo é v-else-if do loader
      await renderCurve()
    }
  } finally {
    curveLoading.value = false
  }
}

async function renderCurve() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  if (!curveChart.value || !curve.value?.points?.length) return
  const pts = curve.value.points
  const traces = [{
    type: 'scatter', mode: 'lines+markers', name: 'Curva',
    x: pts.map((p) => p.month), y: pts.map((p) => p.price),
    line: { color: '#f5c518', width: 2 }, marker: { size: 7 },
    text: pts.map((p) => p.code),
    hovertemplate: '%{text} · %{x}<br>%{y}<extra></extra>',
  }]
  const shapes = []
  if (curve.value.spot) {
    shapes.push({ type: 'line', x0: 0, x1: 1, xref: 'paper',
                  y0: curve.value.spot, y1: curve.value.spot,
                  line: { color: '#667788', width: 1, dash: 'dot' } })
  }
  Plotly.react(curveChart.value, traces, {
    template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 }, height: 280,
    margin: { t: 10, r: 10, b: 40, l: 55 },
    xaxis: { title: 'Vencimento', gridcolor: '#1e1e1e' },
    yaxis: { title: curve.value.unit, gridcolor: '#1e1e1e' },
    shapes,
    annotations: curve.value.spot ? [{
      x: 0, xref: 'paper', y: curve.value.spot, text: 'spot (=F)',
      showarrow: false, font: { size: 10, color: '#667788' }, xanchor: 'left', yanchor: 'bottom',
    }] : [],
  }, { responsive: true, displaylogo: false, displayModeBar: false })
}

async function loadWeather() {
  try { const { data } = await getCdtyWeather(); if (data.rows) wx.value = data } catch { /* */ }
}
async function loadShipping() {
  try { const { data } = await getCdtyShipping(); if (data.rows) ship.value = data } catch { /* */ }
}
async function loadInventories() {
  try { const { data } = await getCdtyInventories(); inv.value = data } catch { /* */ }
}
async function loadNews(q) {
  newsQ.value = q
  newsLoading.value = true
  try {
    const { data } = await getNews('commodities', q)
    newsItems.value = data.items || []
  } finally {
    newsLoading.value = false
  }
}

// mini-gráfico de série (SVG puro)
const MiniSeries = (props) => {
  const v = (props.values || []).filter((x) => x != null)
  if (v.length < 2) return h('div')
  const min = Math.min(...v), max = Math.max(...v)
  const range = max - min || 1
  const w = 320, hgt = 60
  const d = v.map((p, i) =>
    `${(i / (v.length - 1)) * w},${hgt - ((p - min) / range) * (hgt - 4) - 2}`).join(' ')
  return h('svg', { width: '100%', height: hgt, viewBox: `0 0 ${w} ${hgt}`, preserveAspectRatio: 'none' }, [
    h('polyline', { points: d, fill: 'none', stroke: '#f5c518', 'stroke-width': 1.3 }),
  ])
}
MiniSeries.props = { dates: Array, values: Array }

function pctClass(v) {
  return (v ?? 0) >= 0 ? 'text-accent-yellow' : 'text-red-400'
}
function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: v < 10 ? 3 : 2 })
}
function fmtPct(v) {
  return v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}
function rel(ts) {
  if (!ts) return '—'
  const m = Math.max(0, Math.round((Date.now() - ts) / 60000))
  if (m < 60) return `${m}min`
  const hh = Math.round(m / 60)
  return hh < 48 ? `${hh}h` : `${Math.round(hh / 24)}d`
}

onMounted(async () => {
  loadOverview()
  overviewTimer = setInterval(loadOverview, 60000)
  try {
    const { data } = await getCdtyCurves()
    curvesMeta.value = data.curves || []
  } catch { /* */ }
})
onBeforeUnmount(() => {
  if (overviewTimer) clearInterval(overviewTimer)
  purgeChart(curveChart.value)
})
</script>
