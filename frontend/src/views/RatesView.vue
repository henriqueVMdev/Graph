<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">FI · Juros & Crédito</h1>
      <span class="text-[10px] text-gray-600 font-mono">treasuries US via yahoo · atualiza 15 min</span>
      <div class="flex-1" />
      <button @click="load" class="btn-secondary !py-1.5 text-xs">↻ Atualizar</button>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <div v-if="loading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Carregando curvas...</p>
    </div>

    <template v-else-if="d">
      <!-- cards macro -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <div v-for="p in d.points" :key="p.label" class="metric-card">
          <span class="metric-label">Treasury {{ p.label }}</span>
          <span class="metric-value text-gray-200">{{ p.now?.toFixed(2) }}%</span>
          <span class="text-[10px] font-mono" :class="delta(p) >= 0 ? 'text-accent-yellow' : 'text-red-400'">
            {{ delta(p) >= 0 ? '+' : '' }}{{ delta(p).toFixed(0) }} bps 1m
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-label">VIX</span>
          <span class="metric-value" :class="(d.vix ?? 0) > 25 ? 'text-red-400' : 'text-gray-200'">
            {{ d.vix?.toFixed(2) ?? '—' }}</span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- curva -->
        <div class="card p-4 lg:col-span-2">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">◆</span> Curva de juros US — hoje · 1 mês · 1 ano atrás
          </h2>
          <div ref="curveChart" style="min-height:300px;" class="w-full"></div>
        </div>

        <!-- inclinações + crédito -->
        <div class="space-y-4">
          <div class="card p-4">
            <h2 class="text-sm font-semibold text-gray-200 mb-2">
              <span class="text-accent-yellow">◆</span> Inclinação da curva
            </h2>
            <div class="space-y-2 text-sm font-mono">
              <div class="flex justify-between">
                <span class="text-gray-500">10a − 2a</span>
                <span :class="(d.spread_10y2y ?? 0) < 0 ? 'text-red-400 font-bold' : 'text-gray-200'">
                  {{ d.spread_10y2y != null ? d.spread_10y2y.toFixed(2) + ' pp' : '—' }}
                  {{ (d.spread_10y2y ?? 0) < 0 ? '· INVERTIDA' : '' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">10a − 3m</span>
                <span :class="(d.spread_10y3m ?? 0) < 0 ? 'text-red-400 font-bold' : 'text-gray-200'">
                  {{ d.spread_10y3m != null ? d.spread_10y3m.toFixed(2) + ' pp' : '—' }}
                  {{ (d.spread_10y3m ?? 0) < 0 ? '· INVERTIDA' : '' }}
                </span>
              </div>
            </div>
            <p class="text-[10px] text-gray-600 mt-2">curva invertida historicamente antecede recessões</p>
          </div>

          <div class="card p-4">
            <h2 class="text-sm font-semibold text-gray-200 mb-2">
              <span class="text-accent-yellow">◆</span> Spreads de crédito
              <span class="text-[9px] font-mono px-1 py-0.5 rounded ml-1"
                    :class="credit?.source === 'fred'
                      ? 'bg-green-900/40 text-green-300' : 'bg-amber-900/40 text-amber-300'">
                {{ credit?.source === 'fred' ? 'FRED (OAS oficial)' : 'proxy via ETFs' }}
              </span>
            </h2>
            <div class="space-y-2 text-sm font-mono">
              <div class="flex justify-between">
                <span class="text-gray-500">High Yield {{ credit?.source === 'proxy_etf' ? '(HYG−5a)' : 'OAS' }}</span>
                <span class="text-gray-200">{{ creditNow('hy') }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Invest. Grade {{ credit?.source === 'proxy_etf' ? '(LQD−10a)' : 'OAS' }}</span>
                <span class="text-gray-200">{{ creditNow('ig') }}</span>
              </div>
            </div>
            <p v-if="credit?.source === 'proxy_etf'" class="text-[10px] text-gray-600 mt-2 leading-snug">
              FRED indisponível nesta rede — proxy = yield de distribuição do ETF menos treasury de
              duration equivalente (subestima o OAS real; útil como direção, não como nível)
            </p>
          </div>
        </div>
      </div>

      <!-- histórico FRED (se disponível) -->
      <div v-if="credit?.source === 'fred'" class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-3">
          <span class="text-accent-yellow">◆</span> Spreads de crédito — 12 meses (OAS, ICE BofA)
        </h2>
        <div ref="creditChart" style="min-height:260px;" class="w-full"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { getRates } from '@/api/client.js'
import { purgeChart } from '@/composables/useCharts.js'

const d = ref(null)
const credit = ref(null)
const loading = ref(false)
const error = ref(null)
const curveChart = ref(null)
const creditChart = ref(null)
let Plotly = null

function delta(p) {
  return p.now != null && p.m1 != null ? (p.now - p.m1) * 100 : 0
}

function creditNow(key) {
  const c = credit.value?.[key]
  if (!c || c.now == null) return '—'
  return c.now.toFixed(2) + ' pp'
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const { data } = await getRates()
    if (data.error) { error.value = data.error; return }
    credit.value = data.credit
    d.value = data
    // o conteúdo é v-else-if do loader: baixar a flag ANTES do render
    // para as divs dos gráficos existirem no nextTick
    loading.value = false
    await render()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function render() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  await nextTick()
  const pts = d.value?.points || []
  if (curveChart.value && pts.length) {
    const x = pts.map((p) => p.label)
    const mk = (key, name, color, dash) => ({
      type: 'scatter', mode: 'lines+markers', x, y: pts.map((p) => p[key]),
      name, line: { color, width: key === 'now' ? 2.5 : 1.2, dash }, marker: { size: 6 },
    })
    Plotly.react(curveChart.value, [
      mk('now', 'Hoje', '#f5c518'),
      mk('m1', '1 mês atrás', '#8899aa', 'dot'),
      mk('y1', '1 ano atrás', '#556677', 'dash'),
    ], {
      template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
      font: { color: '#d0d0d0', size: 11 }, height: 300,
      margin: { t: 10, r: 10, b: 40, l: 45 },
      xaxis: { title: 'Vencimento', gridcolor: '#1e1e1e' },
      yaxis: { title: 'Yield (%)', gridcolor: '#1e1e1e' },
      legend: { orientation: 'h', y: 1.12 },
    }, { responsive: true, displaylogo: false, displayModeBar: false })
  }
  const c = credit.value
  if (creditChart.value && c?.source === 'fred') {
    Plotly.react(creditChart.value, [
      { type: 'scatter', mode: 'lines', x: c.hy.dates, y: c.hy.values,
        name: 'High Yield OAS', line: { color: '#ef5350', width: 1.5 } },
      { type: 'scatter', mode: 'lines', x: c.ig.dates, y: c.ig.values,
        name: 'IG OAS', line: { color: '#f5c518', width: 1.5 } },
    ], {
      template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
      font: { color: '#d0d0d0', size: 11 }, height: 260,
      margin: { t: 10, r: 10, b: 40, l: 45 },
      xaxis: { type: 'date', gridcolor: '#1e1e1e' },
      yaxis: { title: 'Spread (pp)', gridcolor: '#1e1e1e' },
      legend: { orientation: 'h', y: 1.15 },
    }, { responsive: true, displaylogo: false, displayModeBar: false })
  }
}

onMounted(load)
onBeforeUnmount(() => { purgeChart(curveChart.value); purgeChart(creditChart.value) })
</script>
