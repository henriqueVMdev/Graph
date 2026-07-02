<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">EQS · Screening Fundamentalista</h1>
      <span class="text-[10px] text-gray-600 font-mono">yahoo screener · mercado global · dados ~15min</span>
      <div class="flex-1" />
      <div class="flex rounded-lg overflow-hidden border border-surface-500">
        <button v-for="t in TABS" :key="t.key" @click="tab = t.key"
                class="px-3 py-1 text-[11px] font-mono transition-colors"
                :class="tab === t.key
                  ? 'bg-accent-yellow text-black font-bold'
                  : 'text-gray-400 hover:text-gray-200'">
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- ══ AÇÕES ══ -->
    <template v-if="tab === 'equity'">
      <div class="card p-4 space-y-3">
        <!-- presets -->
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-[10px] text-gray-600 uppercase tracking-wider">Presets</span>
          <button v-for="p in PRESETS" :key="p.label" @click="applyPreset(p)"
                  class="px-2 py-0.5 text-[11px] font-mono rounded border border-surface-500
                         text-gray-400 hover:text-accent-yellow hover:border-accent-yellow/50 transition-colors">
            {{ p.label }}
          </button>
          <button @click="clearFilters"
                  class="px-2 py-0.5 text-[11px] font-mono rounded border border-surface-600
                         text-gray-600 hover:text-red-400 transition-colors">limpar</button>
        </div>

        <!-- país / setor / opções -->
        <div class="flex flex-wrap items-end gap-3">
          <label class="text-xs text-gray-500 block">
            País
            <select v-model="region" class="form-select !py-1.5 text-xs mt-1 block w-44">
              <option value="">Global (todos)</option>
              <option v-for="r in meta.regions" :key="r.key" :value="r.key">{{ r.label }}</option>
            </select>
          </label>
          <label class="text-xs text-gray-500 block">
            Setor
            <select v-model="sector" class="form-select !py-1.5 text-xs mt-1 block w-52">
              <option value="">Todos os setores</option>
              <option v-for="s in meta.sectors" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <label class="text-xs text-gray-500 block">
            Ordenar por
            <select v-model="sort" class="form-select !py-1.5 text-xs mt-1 block w-36">
              <option value="mcap">Market cap</option>
              <option value="pe">P/E</option>
              <option value="div_yield">Div. yield</option>
              <option value="avg_vol">Volume</option>
              <option value="pct_change">Variação dia</option>
            </select>
          </label>
          <label class="text-xs text-gray-500 flex items-center gap-1.5 pb-2">
            <input type="checkbox" v-model="includeOtc" class="accent-yellow-400" />
            incluir OTC
          </label>
          <div class="flex-1" />
          <button @click="run" :disabled="loading"
                  class="btn-primary !py-1.5 text-xs disabled:opacity-50">
            {{ loading ? 'Filtrando...' : '▶ Rodar screening' }}
          </button>
        </div>

        <!-- métricas min/max -->
        <details class="group" open>
          <summary class="text-[10px] text-gray-600 uppercase tracking-wider cursor-pointer select-none
                          hover:text-gray-400">
            Filtros por métrica (min / max) — múltiplos · crescimento · margem · dívida · dividendos · liquidez
          </summary>
          <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-x-4 gap-y-2 mt-2">
            <div v-for="m in meta.metrics" :key="m.key" class="text-[11px]">
              <div class="text-gray-500 font-mono mb-0.5">
                {{ m.label }} <span class="text-gray-700">({{ m.unit }})</span>
              </div>
              <div class="flex gap-1">
                <input v-model.number="ranges[m.key].min" type="number" step="any" placeholder="min"
                       class="form-input !py-1 !px-1.5 text-[11px] w-full"
                       :class="hasValue(m.key) ? '!border-accent-yellow/60' : ''" />
                <input v-model.number="ranges[m.key].max" type="number" step="any" placeholder="max"
                       class="form-input !py-1 !px-1.5 text-[11px] w-full"
                       :class="hasValue(m.key) ? '!border-accent-yellow/60' : ''" />
              </div>
            </div>
          </div>
          <p class="text-[10px] text-gray-700 mt-2 font-mono">
            market cap em $ (ex.: 1000000000 = $1B) · vol. médio em ações/dia · % direto (ex.: margem 15 = 15%)
          </p>
        </details>
      </div>

      <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

      <div v-if="loading" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Consultando o screener global...</p>
      </div>

      <div v-else-if="rows.length" class="card overflow-x-auto">
        <div class="px-3 pt-2 text-[10px] text-gray-600 font-mono">
          {{ totalMatches }} empresas casam com o filtro no Yahoo · exibindo {{ rows.length }} ·
          score = oportunidade relativa dentro do grupo filtrado (valor + dividendo + momento)
        </div>
        <table class="w-full text-sm font-mono">
          <thead>
            <tr class="text-[10px] text-gray-500 uppercase tracking-wider text-right border-b border-surface-500 select-none">
              <th class="text-left px-3 py-2">#</th>
              <th class="text-left px-3 py-2">Ativo</th>
              <th class="text-left px-3 py-2">Empresa</th>
              <th v-for="c in EQ_COLS" :key="c.key" @click="sortBy(c.key)"
                  class="px-3 py-2 cursor-pointer hover:text-accent-yellow whitespace-nowrap">
                {{ c.label }}
                <span v-if="sortKey === c.key">{{ sortDir === -1 ? '▼' : '▲' }}</span>
              </th>
              <th class="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in sortedRows" :key="r.symbol"
                class="border-b border-surface-600/60 hover:bg-surface-600/40 transition-colors">
              <td class="px-3 py-1.5 text-left text-gray-600 text-xs">{{ r.rank }}</td>
              <td class="px-3 py-1.5 text-left">
                <button @click="openDes(r.symbol)"
                        class="font-bold text-gray-100 hover:text-accent-yellow">{{ r.symbol }}</button>
              </td>
              <td class="px-3 py-1.5 text-left text-gray-400 text-xs max-w-44 truncate">{{ r.name }}</td>
              <td class="px-3 py-1.5 text-right">{{ fmt(r.last) }}</td>
              <td class="px-3 py-1.5 text-right" :class="pctClass(r.pct_change)">{{ fmtPct(r.pct_change) }}</td>
              <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(r.mcap) }}</td>
              <td class="px-3 py-1.5 text-right text-gray-300">{{ r.pe != null ? r.pe.toFixed(1) : '—' }}</td>
              <td class="px-3 py-1.5 text-right text-gray-300">{{ r.pb != null ? r.pb.toFixed(2) : '—' }}</td>
              <td class="px-3 py-1.5 text-right text-gray-300">{{ r.div_yield != null ? r.div_yield.toFixed(2) + '%' : '—' }}</td>
              <td class="px-3 py-1.5 text-right" :class="pctClass(r.chg_52w)">{{ fmtPct(r.chg_52w) }}</td>
              <td class="px-3 py-1.5 text-right text-gray-500">{{ fmtVol(r.avg_vol) }}</td>
              <td class="px-3 py-1.5 text-right">
                <div class="flex items-center justify-end gap-1.5"
                     :title="`valor ${r.score_valor ?? '—'} · dividendo ${r.score_div ?? '—'} · momento ${r.score_momento ?? '—'}`">
                  <div class="w-12 h-1.5 rounded bg-surface-600 overflow-hidden">
                    <div class="h-full bg-accent-yellow" :style="{ width: (r.score || 0) + '%' }"></div>
                  </div>
                  <span class="text-gray-300 w-9 text-right">{{ r.score != null ? r.score.toFixed(0) : '—' }}</span>
                </div>
              </td>
              <td class="px-3 py-1.5 text-right whitespace-nowrap">
                <button @click="terminal.addToWatchlist(r.symbol, 'tradfi')" title="+ Watchlist"
                        class="text-gray-600 hover:text-accent-yellow text-xs px-1">👁</button>
                <button @click="openDes(r.symbol)" title="DES"
                        class="text-gray-600 hover:text-accent-yellow text-xs px-1">📋</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="ran" class="text-center text-gray-600 text-sm py-12">
        nenhuma empresa casa com esses filtros — afrouxe algum limite
      </div>
      <div v-else class="text-center text-gray-600 text-sm py-12">
        escolha um preset ou defina filtros e clique em <span class="text-accent-yellow font-mono">▶ Rodar screening</span>
      </div>
    </template>

    <!-- ══ FUNDOS / ETFs / BONDS ══ -->
    <template v-else>
      <div class="card p-4 flex flex-wrap items-end gap-3">
        <label class="text-xs text-gray-500 block">
          Screen pronto (Yahoo)
          <select v-model="fundScreen" @change="runFunds" class="form-select !py-1.5 text-xs mt-1 block w-72">
            <option v-for="s in meta.fund_screens" :key="s.key" :value="s.key">{{ s.label }}</option>
          </select>
        </label>
        <span class="text-[10px] text-gray-600 font-mono pb-2">
          bonds são cobertos via ETFs/fundos de renda fixa (bond ETFs · high yield)
        </span>
      </div>

      <div v-if="fundError" class="card p-3 text-xs text-red-400">{{ fundError }}</div>

      <div v-if="fundLoading" class="flex flex-col items-center py-16">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Carregando fundos...</p>
      </div>

      <div v-else-if="fundRows.length" class="card overflow-x-auto">
        <div class="px-3 pt-2 text-[10px] text-gray-600 font-mono">
          {{ fundTotal }} no universo · exibindo {{ fundRows.length }}
        </div>
        <table class="w-full text-sm font-mono">
          <thead>
            <tr class="text-[10px] text-gray-500 uppercase tracking-wider text-right border-b border-surface-500">
              <th class="text-left px-3 py-2">Ativo</th>
              <th class="text-left px-3 py-2">Nome</th>
              <th class="text-left px-3 py-2">Tipo</th>
              <th class="px-3 py-2">Último</th>
              <th class="px-3 py-2">Dia %</th>
              <th class="px-3 py-2">52s %</th>
              <th class="px-3 py-2">Patrimônio</th>
              <th class="px-3 py-2">Taxa adm</th>
              <th class="px-3 py-2">Vol 3m</th>
              <th class="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in fundRows" :key="r.symbol"
                class="border-b border-surface-600/60 hover:bg-surface-600/40 transition-colors">
              <td class="px-3 py-1.5 text-left">
                <button @click="openDes(r.symbol)"
                        class="font-bold text-gray-100 hover:text-accent-yellow">{{ r.symbol }}</button>
              </td>
              <td class="px-3 py-1.5 text-left text-gray-400 text-xs max-w-56 truncate">{{ r.name }}</td>
              <td class="px-3 py-1.5 text-left text-[10px] text-gray-500">{{ r.quote_type }}</td>
              <td class="px-3 py-1.5 text-right">{{ fmt(r.last) }}</td>
              <td class="px-3 py-1.5 text-right" :class="pctClass(r.pct_change)">{{ fmtPct(r.pct_change) }}</td>
              <td class="px-3 py-1.5 text-right" :class="pctClass(r.chg_52w)">{{ fmtPct(r.chg_52w) }}</td>
              <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(r.net_assets) }}</td>
              <td class="px-3 py-1.5 text-right text-gray-400">{{ r.expense_ratio != null ? r.expense_ratio.toFixed(2) + '%' : '—' }}</td>
              <td class="px-3 py-1.5 text-right text-gray-500">{{ fmtVol(r.avg_vol) }}</td>
              <td class="px-3 py-1.5 text-right whitespace-nowrap">
                <button @click="terminal.addToWatchlist(r.symbol, 'tradfi')" title="+ Watchlist"
                        class="text-gray-600 hover:text-accent-yellow text-xs px-1">👁</button>
                <button @click="openDes(r.symbol)" title="DES"
                        class="text-gray-600 hover:text-accent-yellow text-xs px-1">📋</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getEqsMeta, runEqsScreen, getEqsFunds } from '@/api/client.js'
import { useTerminalStore } from '@/stores/terminal.js'

const router = useRouter()
const terminal = useTerminalStore()

const TABS = [
  { key: 'equity', label: 'AÇÕES' },
  { key: 'funds', label: 'FUNDOS · ETFs · BONDS' },
]
const tab = ref('equity')

const meta = ref({ regions: [], sectors: [], metrics: [], fund_screens: [] })

// ── filtros de ações ──
const region = ref('us')
const sector = ref('')
const sort = ref('mcap')
const includeOtc = ref(false)
const ranges = reactive({})

const PRESETS = [
  { label: 'VALUE', set: { pe: { max: 15 }, pb: { max: 2 }, mcap: { min: 2e9 } } },
  { label: 'GROWTH', set: { rev_growth: { min: 20 }, eps_growth: { min: 15 }, mcap: { min: 2e9 } } },
  { label: 'DIVIDENDOS', set: { div_yield: { min: 4 }, mcap: { min: 2e9 }, debt_equity: { max: 150 } } },
  { label: 'QUALIDADE', set: { roe: { min: 15 }, net_margin: { min: 10 }, net_debt_ebitda: { max: 2 } } },
  { label: 'SMALL CAPS LÍQUIDAS', set: { mcap: { min: 3e8, max: 2e9 }, avg_vol: { min: 500000 } } },
  { label: 'DEEP VALUE', set: { pe: { max: 8 }, pb: { max: 1 }, div_yield: { min: 2 } } },
]

const rows = ref([])
const totalMatches = ref(null)
const loading = ref(false)
const error = ref(null)
const ran = ref(false)
const sortKey = ref('')
const sortDir = ref(-1)

const EQ_COLS = [
  { key: 'last', label: 'Último' },
  { key: 'pct_change', label: 'Dia %' },
  { key: 'mcap', label: 'Mkt cap' },
  { key: 'pe', label: 'P/E' },
  { key: 'pb', label: 'P/B' },
  { key: 'div_yield', label: 'DY' },
  { key: 'chg_52w', label: '52s %' },
  { key: 'avg_vol', label: 'Vol 3m' },
  { key: 'score', label: 'Score' },
]

const sortedRows = computed(() => {
  if (!sortKey.value) return rows.value
  return [...rows.value].sort((a, b) =>
    ((a[sortKey.value] ?? -Infinity) - (b[sortKey.value] ?? -Infinity)) * sortDir.value)
})

function sortBy(key) {
  if (sortKey.value === key) sortDir.value *= -1
  else { sortKey.value = key; sortDir.value = -1 }
}

function hasValue(key) {
  const r = ranges[key]
  return r && (r.min != null && r.min !== '' || r.max != null && r.max !== '')
}

function applyPreset(p) {
  clearFilters()
  for (const [k, v] of Object.entries(p.set)) {
    if (ranges[k]) Object.assign(ranges[k], v)
  }
  run()
}

function clearFilters() {
  for (const k of Object.keys(ranges)) { ranges[k].min = null; ranges[k].max = null }
}

function buildMetrics() {
  const out = {}
  for (const [k, r] of Object.entries(ranges)) {
    const min = r.min !== '' && r.min != null ? Number(r.min) : null
    const max = r.max !== '' && r.max != null ? Number(r.max) : null
    if (min != null || max != null) out[k] = { ...(min != null && { min }), ...(max != null && { max }) }
  }
  return out
}

async function run() {
  loading.value = true
  error.value = null
  try {
    const { data } = await runEqsScreen({
      regions: region.value ? [region.value] : [],
      sectors: sector.value ? [sector.value] : [],
      metrics: buildMetrics(),
      sort: sort.value,
      include_otc: includeOtc.value,
      size: 100,
    })
    if (data.error) { error.value = data.error; rows.value = [] }
    else { rows.value = data.rows || []; totalMatches.value = data.total_matches }
    sortKey.value = ''
    ran.value = true
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

// ── fundos ──
const fundScreen = ref('top_etfs_us')
const fundRows = ref([])
const fundTotal = ref(null)
const fundLoading = ref(false)
const fundError = ref(null)

async function runFunds() {
  fundLoading.value = true
  fundError.value = null
  try {
    const { data } = await getEqsFunds(fundScreen.value)
    if (data.error) { fundError.value = data.error; fundRows.value = [] }
    else { fundRows.value = data.rows || []; fundTotal.value = data.total_matches }
  } catch (e) {
    fundError.value = e.response?.data?.error || e.message
  } finally {
    fundLoading.value = false
  }
}

watch(tab, (t) => {
  if (t === 'funds' && !fundRows.value.length && !fundLoading.value) runFunds()
})

function openDes(symbol) {
  router.push({ path: '/des', query: { symbol, market: 'tradfi' } })
}

function pctClass(v) {
  return (v ?? 0) >= 0 ? 'text-accent-yellow' : 'text-red-400'
}
function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: v < 1 ? 4 : 2 })
}
function fmtPct(v) {
  return v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}
function fmtVol(v) {
  if (v == null) return '—'
  if (v >= 1e12) return (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K'
  return Math.round(v).toLocaleString('pt-BR')
}

onMounted(async () => {
  try {
    const { data } = await getEqsMeta()
    meta.value = data
    for (const m of data.metrics || []) {
      if (!ranges[m.key]) ranges[m.key] = { min: null, max: null }
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
})
</script>
