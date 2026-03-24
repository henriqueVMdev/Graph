<template>
  <div>
    <!-- Asset selector — cascata categoria → ativo -->
    <div class="mb-4">
      <label class="text-xs text-gray-400 block mb-2">Selecione ativos para comparar:</label>
      <div class="flex flex-wrap gap-2 items-center">

        <!-- Slot: categoria + ativo em cascata -->
        <div v-for="(slot, si) in slots" :key="si" class="flex items-center gap-1.5">

          <!-- Separador entre slots -->
          <span v-if="si > 0" class="text-gray-600 text-xs select-none">vs</span>

          <div class="flex flex-col gap-1">
            <!-- 1º select: Categoria -->
            <select
              v-model="slot.catName"
              @change="slot.label = null; slot.ticker = null; syncStoreLabels()"
              class="bg-surface-700 border border-surface-500 text-gray-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-accent-yellow transition-colors appearance-none cursor-pointer"
              style="min-width:150px;"
            >
              <option value="" disabled>Categoria...</option>
              <option v-for="cat in categoryNames" :key="cat" :value="cat">{{ cat }}</option>
            </select>

            <!-- 2º select: Ativo (desabilitado até ter categoria) -->
            <select
              v-model="slot.label"
              :disabled="!slot.catName"
              @change="slot.ticker = store.assets[slot.catName]?.[slot.label]; syncStoreLabels()"
              class="border text-xs rounded-lg px-2.5 py-1.5 focus:outline-none transition-colors appearance-none"
              :class="slot.catName
                ? 'bg-surface-700 border-surface-500 text-gray-200 focus:border-accent-yellow cursor-pointer'
                : 'bg-surface-800 border-surface-700 text-gray-600 cursor-not-allowed'"
              style="min-width:150px;"
            >
              <option value="" disabled>Ativo...</option>
              <option
                v-for="(_, label) in (store.assets[slot.catName] || {})"
                :key="label" :value="label"
              >{{ label }}</option>
            </select>
          </div>

          <!-- Botão remover slot (só a partir do 3º) -->
          <button
            v-if="si >= 2"
            @click="removeSlot(si)"
            class="text-gray-600 hover:text-red-400 transition-colors text-base leading-none mt-1"
            title="Remover"
          >×</button>

        </div>

        <!-- Botão adicionar ativo -->
        <button
          v-if="slots.length < 6"
          @click="addSlot"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-dashed border-surface-500 text-gray-500 hover:text-gray-300 hover:border-surface-400 transition-colors mt-auto"
        >
          <span class="text-base leading-none">+</span> ativo
        </button>

      </div>
    </div>

    <div v-if="selectedSlotCount < 2" class="text-xs text-gray-500 py-4 text-center">
      Selecione pelo menos 2 ativos para ver a correlação
    </div>

    <div v-else>
      <button
        @click="loadCorrelation"
        :disabled="store.correlationLoading"
        class="btn-secondary text-xs mb-4 flex items-center gap-1.5"
      >
        {{ store.correlationLoading ? 'Carregando...' : 'Atualizar Análise' }}
      </button>

      <div v-if="store.correlationError" class="text-xs text-accent-red-light mb-3">
        {{ store.correlationError }}
      </div>

      <!-- Primeiro carregamento -->
      <div v-if="!store.correlationData && store.correlationLoading"
        class="flex flex-col items-center justify-center gap-3" style="min-height:420px;">
        <div class="corr-dollar-loader">$</div>
        <span class="text-xs text-gray-500">Carregando dados...</span>
      </div>

      <template v-if="store.correlationData">
        <!-- Tabs -->
        <div class="flex flex-wrap gap-1 mb-4 border-b border-surface-500 pb-2">
          <button class="tab-btn" :class="{ active: tab === 'corr' }" @click="tab = 'corr'">
            Matriz de Correlação
          </button>
          <button class="tab-btn" :class="{ active: tab === 'scatter' }" @click="tab = 'scatter'">
            Correlação Entre Ativos
          </button>
          <button class="tab-btn" :class="{ active: tab === 'coef' }" @click="tab = 'coef'">
            Coeficiente de Correlação
          </button>
          <button class="tab-btn" :class="{ active: tab === 'dist' }" @click="tab = 'dist'">
            Distribuição de Retornos
          </button>
        </div>

        <!-- Correlation heatmap -->
        <div v-show="tab === 'corr'">
          <div class="relative">
            <div ref="corrEl" style="min-height: 400px;"></div>
            <div v-if="store.correlationLoading" class="corr-overlay"><div class="corr-dollar-loader">$</div></div>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            Valores próximos de +1 indicam ativos que se movem juntos.
            Valores próximos de -1 indicam movimentos opostos (diversificação).
          </p>
        </div>

        <!-- Scatter correlation -->
        <div v-show="tab === 'scatter'">
          <div v-if="availableLabels.length > 2" class="flex gap-4 mb-4 items-end">
            <div class="flex flex-col gap-1">
              <label class="text-xs text-gray-400">Ativo X</label>
              <select
                v-model="pairA"
                @change="renderScatter(store.correlationData)"
                class="bg-surface-600 border border-surface-500 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent-yellow"
              >
                <option v-for="label in availableLabels" :key="label" :value="label">{{ label }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-xs text-gray-400">Ativo Y</label>
              <select
                v-model="pairB"
                @change="renderScatter(store.correlationData)"
                class="bg-surface-600 border border-surface-500 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent-yellow"
              >
                <option v-for="label in availableLabels" :key="label" :value="label">{{ label }}</option>
              </select>
            </div>
          </div>
          <div class="relative">
            <div ref="scatterEl" style="min-height: 420px;"></div>
            <div v-if="store.correlationLoading" class="corr-overlay"><div class="corr-dollar-loader">$</div></div>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            Cada ponto representa um dia de trading. A linha mostra a regressão linear entre os retornos diários.
          </p>
        </div>

        <!-- Rolling correlation coefficient -->
        <div v-show="tab === 'coef'">
          <div class="flex flex-wrap gap-4 mb-4 items-end">
            <!-- Pair selector -->
            <template v-if="availableLabels.length > 2">
              <div class="flex flex-col gap-1">
                <label class="text-xs text-gray-400">Ativo A</label>
                <select
                  v-model="pairA"
                  @change="renderCorrCoef(store.correlationData)"
                  class="bg-surface-600 border border-surface-500 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent-yellow"
                >
                  <option v-for="label in availableLabels" :key="label" :value="label">{{ label }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-xs text-gray-400">Ativo B</label>
                <select
                  v-model="pairB"
                  @change="renderCorrCoef(store.correlationData)"
                  class="bg-surface-600 border border-surface-500 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent-yellow"
                >
                  <option v-for="label in availableLabels" :key="label" :value="label">{{ label }}</option>
                </select>
              </div>
            </template>

            <!-- Window selector -->
            <div class="flex flex-col gap-1">
              <label class="text-xs text-gray-400">Janela (dias)</label>
              <div class="flex gap-1">
                <button
                  v-for="w in [20, 30, 60, 90]"
                  :key="w"
                  @click="corrWindow = w; renderCorrCoef(store.correlationData)"
                  class="px-2.5 py-1 text-xs rounded border transition-colors"
                  :class="corrWindow === w
                    ? 'bg-accent-yellow/15 border-accent-yellow text-accent-yellow'
                    : 'border-surface-400 text-gray-500 hover:border-accent-yellow/40 hover:text-gray-300'"
                >{{ w }}</button>
              </div>
            </div>
          </div>

          <div class="relative">
            <div ref="coefEl" style="min-height: 420px;"></div>
            <div v-if="store.correlationLoading" class="corr-overlay"><div class="corr-dollar-loader">$</div></div>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            Correlação de Pearson calculada em janela móvel de {{ corrWindow }} dias.
            Região verde indica correlação positiva; vermelha, negativa.
          </p>
        </div>

        <!-- Return distribution -->
        <div v-show="tab === 'dist'">
          <div class="relative">
            <div ref="distEl" style="min-height: 450px;"></div>
            <div v-if="store.correlationLoading" class="corr-overlay"><div class="corr-dollar-loader">$</div></div>
          </div>

          <!-- Stats table -->
          <div class="mt-4 rounded-lg border border-surface-500" style="overflow: visible;">
            <table class="w-full text-xs">
              <thead>
                <tr class="bg-surface-600 text-gray-400 text-left">
                  <th class="px-3 py-2 font-medium">Ativo</th>
                  <th class="px-3 py-2 font-medium">
                    <span class="dist-info-wrap">Retorno Médio (%)
                      <span class="dist-info-icon">?</span>
                      <div class="dist-tooltip">Média dos retornos diários do ativo no período selecionado. Valores positivos indicam que o ativo subiu em média por dia; negativos indicam queda.</div>
                    </span>
                  </th>
                  <th class="px-3 py-2 font-medium">
                    <span class="dist-info-wrap">Volatilidade (%)
                      <span class="dist-info-icon">?</span>
                      <div class="dist-tooltip">Desvio padrão dos retornos diários. Mede o quanto o preço oscila — quanto maior, mais arriscado e imprevisível é o ativo. Uma volatilidade alta pode significar tanto grandes ganhos quanto grandes perdas.</div>
                    </span>
                  </th>
                  <th class="px-3 py-2 font-medium">
                    <span class="dist-info-wrap">Skewness
                      <span class="dist-info-icon">?</span>
                      <div class="dist-tooltip">Assimetria da distribuição dos retornos. Valor positivo (cauda à direita) indica que ganhos extremos são mais prováveis que perdas extremas. Valor negativo (cauda à esquerda) indica o contrário — o ativo tem tendência a quedas abruptas.</div>
                    </span>
                  </th>
                  <th class="px-3 py-2 font-medium">
                    <span class="dist-info-wrap">Kurtosis
                      <span class="dist-info-icon">?</span>
                      <div class="dist-tooltip">Curtose da distribuição. Valores altos indicam "caudas pesadas" — eventos extremos (crashes ou ralis) ocorrem com mais frequência do que uma distribuição normal preveria. Kurtosis &gt; 3 é chamada de leptocúrtica e é comum em ativos financeiros.</div>
                    </span>
                  </th>
                  <th class="px-3 py-2 font-medium">
                    <span class="dist-info-wrap">Sharpe (anual)
                      <span class="dist-info-icon">?</span>
                      <div class="dist-tooltip">Retorno anualizado dividido pela volatilidade anualizada. Mede o retorno obtido por unidade de risco. Sharpe &gt; 1 é considerado bom; &gt; 2 é excelente. Valores negativos indicam que o ativo perdeu dinheiro ajustado ao risco.</div>
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(d, label) in store.correlationData.distributions"
                  :key="label"
                  class="border-b border-surface-500 last:border-0"
                >
                  <td class="px-3 py-2 text-gray-200 font-medium">{{ label }}</td>
                  <td class="px-3 py-2 font-mono" :class="d.stats.mean >= 0 ? 'badge-green' : 'badge-red'">
                    {{ fmtN(d.stats.mean, 4) }}
                  </td>
                  <td class="px-3 py-2 font-mono text-gray-300">{{ fmtN(d.stats.std, 4) }}</td>
                  <td class="px-3 py-2 font-mono text-gray-300">
                    {{ fmtN(d.stats.skew, 3) }}
                    <span class="text-gray-500 ml-1">{{ d.skew_desc }}</span>
                  </td>
                  <td class="px-3 py-2 font-mono text-gray-300">
                    {{ fmtN(d.stats.kurtosis, 3) }}
                    <span class="text-gray-500 ml-1">{{ d.kurt_desc }}</span>
                  </td>
                  <td class="px-3 py-2 font-mono"
                    :class="d.stats.sharpe_annual >= 1 ? 'badge-green' : d.stats.sharpe_annual >= 0 ? 'text-accent-yellow' : 'badge-red'">
                    {{ fmtN(d.stats.sharpe_annual, 2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'

const store = useBacktestStore()
const tab = ref('corr')
const corrEl = ref(null)
const distEl = ref(null)
const scatterEl = ref(null)
const coefEl = ref(null)
const pairA = ref(null)
const pairB = ref(null)
const corrWindow = ref(30)

// ── Category-based slot selector ─────────────────────────────────────────────

const categoryNames = computed(() => Object.keys(store.assets))

function makeSlot() {
  return { catName: '', label: null, ticker: null }
}

const slots = ref([makeSlot(), makeSlot()])

function addSlot() {
  slots.value.push(makeSlot())
}

function removeSlot(si) {
  slots.value.splice(si, 1)
  syncStoreLabels()
}

function syncStoreLabels() {
  store.selectedCompareLabels = slots.value
    .filter(s => s.label)
    .map(s => s.label)
}

const selectedSlotCount = computed(() => slots.value.filter(s => s.label).length)

// ─────────────────────────────────────────────────────────────────────────────

const availableLabels = computed(() => {
  if (!store.correlationData?.returns_aligned) return []
  return Object.keys(store.correlationData.returns_aligned)
})

async function loadCorrelation() {
  const tickers = {}
  for (const slot of slots.value) {
    if (slot.label && slot.ticker) tickers[slot.label] = slot.ticker
  }
  await store.fetchCorrelation(tickers)
}

watch(() => store.correlationData, async (data) => {
  if (!data) return
  const labels = Object.keys(data.returns_aligned || {})
  if (labels.length >= 2) {
    pairA.value = labels[0]
    pairB.value = labels[1]
  }
  await renderCorrelation(data)
  await renderDistribution(data)
  await renderScatter(data)
  await renderCorrCoef(data)
})

watch(tab, async () => {
  if (!store.correlationData) return
  if (tab.value === 'corr') await renderCorrelation(store.correlationData)
  if (tab.value === 'dist') await renderDistribution(store.correlationData)
  if (tab.value === 'scatter') await renderScatter(store.correlationData)
  if (tab.value === 'coef') await renderCorrCoef(store.correlationData)
})

// ── Pearson / rolling correlation ──────────────────────────────────────────

function pearson(x, y) {
  const n = x.length
  if (n < 2) return null
  let sumX = 0, sumY = 0
  for (let i = 0; i < n; i++) { sumX += x[i]; sumY += y[i] }
  const mx = sumX / n, my = sumY / n
  let num = 0, dx2 = 0, dy2 = 0
  for (let i = 0; i < n; i++) {
    const dx = x[i] - mx, dy = y[i] - my
    num += dx * dy; dx2 += dx * dx; dy2 += dy * dy
  }
  const denom = Math.sqrt(dx2 * dy2)
  return denom === 0 ? 0 : num / denom
}

function rollingCorr(x, y, window) {
  const result = new Array(x.length).fill(null)
  for (let i = window - 1; i < x.length; i++) {
    result[i] = pearson(x.slice(i - window + 1, i + 1), y.slice(i - window + 1, i + 1))
  }
  return result
}

// ── Render functions ────────────────────────────────────────────────────────

// Regressão linear simples
function linReg(x, y) {
  const n = x.length
  if (n < 2) return { slope: 0, intercept: 0 }
  const sumX = x.reduce((a, b) => a + b, 0)
  const sumY = y.reduce((a, b) => a + b, 0)
  const sumXY = x.reduce((a, v, i) => a + v * y[i], 0)
  const sumXX = x.reduce((a, v) => a + v * v, 0)
  const denom = n * sumXX - sumX * sumX
  if (denom === 0) return { slope: 0, intercept: sumY / n }
  const slope = (n * sumXY - sumX * sumY) / denom
  const intercept = (sumY - slope * sumX) / n
  return { slope, intercept }
}

async function renderCorrelation(data) {
  if (!corrEl.value || !data?.correlation) return
  const Plotly = (await import('plotly.js-dist-min')).default
  const { labels, matrix } = data.correlation

  const trace = {
    type: 'heatmap',
    z: matrix,
    x: labels,
    y: labels,
    colorscale: [
      [0,   '#ef4444'],  // -1 → vermelho
      [0.5, '#f5c518'],  //  0 → amarelo
      [1,   '#22c55e'],  // +1 → verde
    ],
    zmin: -1, zmax: 1,
    text: matrix.map(row => row.map(v => v?.toFixed(2) ?? '')),
    texttemplate: '%{text}',
    textfont: { size: 13, color: '#e6edf3' },
    hovertemplate: '<b>%{x}</b> vs <b>%{y}</b><br>Correlação: %{z:.3f}<extra></extra>',
  }

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 },
    height: 420,
    autosize: true,
    margin: { t: 20, r: 20, b: 80, l: 80 },
    xaxis: { side: 'bottom', tickangle: -30, gridcolor: '#1e1e1e' },
    yaxis: { tickangle: 0, gridcolor: '#1e1e1e' },
  }

  await Plotly.react(corrEl.value, [trace], layout, { responsive: true, displaylogo: false })
}

async function renderScatter(data) {
  if (!scatterEl.value || !data?.returns_aligned) return
  const a = pairA.value
  const b = pairB.value
  if (!a || !b || a === b) return

  const xData = data.returns_aligned[a]
  const yData = data.returns_aligned[b]
  if (!xData || !yData) return

  const Plotly = (await import('plotly.js-dist-min')).default

  const labels = data.correlation.labels
  const idxA = labels.indexOf(a)
  const idxB = labels.indexOf(b)
  const corrVal = idxA >= 0 && idxB >= 0 ? data.correlation.matrix[idxA][idxB] : null

  const { slope, intercept } = linReg(xData, yData)
  const xMin = Math.min(...xData)
  const xMax = Math.max(...xData)
  const regX = [xMin, xMax]
  const regY = [slope * xMin + intercept, slope * xMax + intercept]

  const lineColor = corrVal == null ? '#f5c518' : corrVal >= 0 ? '#66c2a5' : '#fc8d62'
  const dates = data.dates ?? []

  const traces = [
    {
      type: 'scatter',
      mode: 'markers',
      x: xData,
      y: yData,
      customdata: dates,
      marker: { size: 4, color: '#22c55e', opacity: 0.45, line: { width: 0 } },
      name: `${a} vs ${b}`,
      hovertemplate: `%{customdata}<br><b>${a}</b>: %{x:.2f}%<br><b>${b}</b>: %{y:.2f}%<extra></extra>`,
    },
    {
      type: 'scatter',
      mode: 'lines',
      x: regX,
      y: regY,
      line: { color: lineColor, width: 2, dash: 'dash' },
      name: 'Regressão Linear',
      hoverinfo: 'skip',
    },
  ]

  const corrLabel = corrVal != null ? corrVal.toFixed(3) : '-'
  const corrDesc = corrVal == null ? '' : corrVal >= 0.7 ? ' (forte positiva)' : corrVal <= -0.7 ? ' (forte negativa)' : corrVal >= 0.3 ? ' (moderada positiva)' : corrVal <= -0.3 ? ' (moderada negativa)' : ' (fraca)'

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 },
    height: 420,
    autosize: true,
    margin: { t: 50, r: 20, b: 60, l: 60 },
    xaxis: { title: `Retorno Diário — ${a} (%)`, gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#2a2a2a', zerolinewidth: 1 },
    yaxis: { title: `Retorno Diário — ${b} (%)`, gridcolor: '#1e1e1e', zeroline: true, zerolinecolor: '#2a2a2a', zerolinewidth: 1 },
    hovermode: 'closest',
    legend: { bgcolor: 'rgba(0,0,0,0.8)', bordercolor: '#2a2a2a' },
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#444', font: { color: '#e0e0e0' } },
    annotations: [{
      x: 0.02, y: 0.98, xref: 'paper', yref: 'paper',
      text: `Correlação: <b>${corrLabel}</b>${corrDesc}`,
      showarrow: false,
      font: { size: 12, color: lineColor },
      bgcolor: 'rgba(0,0,0,0.75)', bordercolor: '#333', borderwidth: 1, borderpad: 5, align: 'left',
    }],
  }

  await Plotly.react(scatterEl.value, traces, layout, { responsive: true, displaylogo: false })
}

async function renderCorrCoef(data) {
  if (!coefEl.value || !data?.returns_aligned) return
  const a = pairA.value
  const b = pairB.value
  if (!a || !b || a === b) return

  const xData = data.returns_aligned[a]
  const yData = data.returns_aligned[b]
  const dates = data.dates ?? []
  if (!xData || !yData || xData.length < corrWindow.value) return

  const Plotly = (await import('plotly.js-dist-min')).default

  const rolling = rollingCorr(xData, yData, corrWindow.value)

  // Separa regiões positiva e negativa para fill colorido
  const datesValid = dates.slice(corrWindow.value - 1)
  const rollValid  = rolling.slice(corrWindow.value - 1)

  // Série principal
  const lineTrace = {
    type: 'scatter',
    mode: 'lines',
    x: dates,
    y: rolling,
    line: { color: '#378ADD', width: 2 },
    name: `Correlação ${corrWindow.value}d`,
    hovertemplate: '<b>%{x}</b><br>Correlação: <b>%{y:.3f}</b><extra></extra>',
  }

  // Fill positivo (verde)
  const posY = rollValid.map(v => (v !== null && v > 0) ? v : 0)
  const posTrace = {
    type: 'scatter',
    mode: 'none',
    x: datesValid,
    y: posY,
    fill: 'tozeroy',
    fillcolor: 'rgba(55,138,221,0.15)',
    hoverinfo: 'skip',
    showlegend: false,
  }

  // Fill negativo (vermelho)
  const negY = rollValid.map(v => (v !== null && v < 0) ? v : 0)
  const negTrace = {
    type: 'scatter',
    mode: 'none',
    x: datesValid,
    y: negY,
    fill: 'tozeroy',
    fillcolor: 'rgba(55,138,221,0.10)',
    hoverinfo: 'skip',
    showlegend: false,
  }

  // Linha estática de correlação total (valor único)
  const corrLabels = data.correlation.labels
  const idxA = corrLabels.indexOf(a)
  const idxB = corrLabels.indexOf(b)
  const totalCorr = idxA >= 0 && idxB >= 0 ? data.correlation.matrix[idxA][idxB] : null

  const shapes = [
    // Linha zero
    { type: 'line', x0: dates[0], x1: dates.at(-1), y0: 0, y1: 0, line: { color: '#444', width: 1, dash: 'dot' } },
    // Linhas de referência ±0.5
    { type: 'line', x0: dates[0], x1: dates.at(-1), y0: 0.5,  y1: 0.5,  line: { color: '#22c55e', width: 1, dash: 'dot', opacity: 0.4 } },
    { type: 'line', x0: dates[0], x1: dates.at(-1), y0: -0.5, y1: -0.5, line: { color: '#ef4444', width: 1, dash: 'dot', opacity: 0.4 } },
  ]

  const annotations = totalCorr != null ? [{
    x: 0.01, y: 0.97, xref: 'paper', yref: 'paper',
    text: `Correlação total: <b>${totalCorr.toFixed(3)}</b>`,
    showarrow: false,
    font: { size: 11, color: '#f5c518' },
    bgcolor: 'rgba(0,0,0,0.7)', bordercolor: '#333', borderwidth: 1, borderpad: 4, align: 'left',
  }] : []

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 },
    height: 420,
    autosize: true,
    margin: { t: 30, r: 20, b: 60, l: 60 },
    xaxis: { gridcolor: '#1e1e1e', type: 'category', nticks: 10, tickangle: -30 },
    yaxis: { title: 'Coeficiente de Correlação', gridcolor: '#1e1e1e', range: [-1.05, 1.05],
             tickvals: [-1, -0.5, 0, 0.5, 1] },
    hovermode: 'x unified',
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
    legend: { bgcolor: 'rgba(0,0,0,0.8)', bordercolor: '#2a2a2a' },
    shapes,
    annotations,
  }

  await Plotly.react(coefEl.value, [posTrace, negTrace, lineTrace], layout, { responsive: true, displaylogo: false })
}

async function renderDistribution(data) {
  if (!distEl.value || !data?.distributions) return
  const Plotly = (await import('plotly.js-dist-min')).default
  const traces = []

  for (const [col, d] of Object.entries(data.distributions)) {
    const color = d.color || '#66c2a5'

    traces.push({
      type: 'histogram',
      x: d.returns,
      name: col,
      opacity: 0.6,
      nbinsx: 50,
      marker: { color },
      histnorm: 'probability density',
      hovertemplate: '<b>%{x:.2f}%</b><br>Densidade: %{y:.4f}<extra>' + col + '</extra>',
    })

    traces.push({
      type: 'scatter',
      x: d.pdf_x,
      y: d.pdf_y,
      mode: 'lines',
      name: `${col} (Normal)`,
      line: { color, width: 2, dash: 'dash' },
      hovertemplate: '<b>%{x:.2f}%</b><br>PDF: %{y:.4f}<extra>' + col + ' (Normal)</extra>',
    })
  }

  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: '#000000',
    plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', size: 11 },
    height: 450,
    autosize: true,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    xaxis: { title: 'Retorno Diário (%)', gridcolor: '#1e1e1e' },
    yaxis: { title: 'Densidade', gridcolor: '#1e1e1e' },
    barmode: 'overlay',
    hovermode: 'x unified',
    legend: { bgcolor: 'rgba(0,0,0,0.8)', bordercolor: '#2a2a2a' },
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
  }

  await Plotly.react(distEl.value, traces, layout, { responsive: true, displaylogo: false })
}

function fmtN(v, dec = 2) {
  if (v == null) return '-'
  return Number(v).toFixed(dec)
}
</script>

<style scoped>
@keyframes corr-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(245,197,24,.8);  border-color: #f5c518; color: #f5c518; background: #000; }
  50%  { box-shadow: 0 0 24px 8px rgba(245,197,24,.25); border-color: #f5c518; color: #000;   background: #f5c518; }
  100% { box-shadow: 0 0 0 0 rgba(245,197,24,.8);  border-color: #f5c518; color: #f5c518; background: #000; }
}
.corr-dollar-loader {
  width: 72px; height: 72px;
  border-radius: 16px;
  border: 2px solid #f5c518;
  background: #000;
  color: #f5c518;
  font-size: 2.4rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  animation: corr-pulse 1.4s ease-in-out infinite;
  font-family: 'Inter', system-ui, sans-serif;
}
/* Garante que o tooltip não seja cortado pela tabela */
:deep(table) { overflow: visible; }
:deep(thead), :deep(th) { overflow: visible; position: relative; }

/* Distribution table header tooltips */
.dist-info-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.dist-info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 1px solid #555;
  color: #666;
  font-size: 8px;
  font-weight: 700;
  cursor: default;
  flex-shrink: 0;
  line-height: 1;
}
.dist-tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  width: 230px;
  background: #0d0d12;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 10px;
  color: #bbb;
  line-height: 1.5;
  text-align: left;
  z-index: 50;
  pointer-events: none;
  transition: opacity 0.15s;
  white-space: normal;
  font-weight: 400;
}
.dist-info-wrap:hover .dist-tooltip {
  visibility: visible;
  opacity: 1;
}

.corr-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,.75);
  backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  z-index: 10;
}
</style>
