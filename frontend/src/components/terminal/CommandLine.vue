<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm"
         @click.self="close">
      <div class="max-w-2xl mx-auto mt-[12vh] rounded-xl border border-accent-yellow/50
                  bg-black shadow-yellow-glow overflow-hidden">
        <!-- input -->
        <div class="flex items-center gap-3 px-4 py-3 border-b border-surface-600">
          <span class="text-accent-yellow font-mono font-bold text-sm">&gt;</span>
          <input
            ref="inputEl"
            v-model="query"
            @keydown.enter.prevent="go"
            @keydown.esc.prevent="close"
            placeholder="ex.: BTC 15M BT · OURO DES · EURUSD MON · SCR · NEWS"
            class="flex-1 bg-transparent font-mono text-base text-accent-yellow uppercase
                   placeholder:normal-case placeholder:text-gray-600 focus:outline-none"
            spellcheck="false" autocomplete="off"
          />
          <span class="text-[10px] text-gray-600 font-mono border border-surface-500
                       rounded px-1.5 py-0.5">ENTER = GO</span>
        </div>

        <!-- preview do parse -->
        <div v-if="query.trim()" class="px-4 py-3 font-mono text-sm">
          <div v-if="parsed.func" class="flex items-center gap-2 text-gray-200">
            <span class="text-accent-yellow">→</span>
            <span class="text-gray-100 font-semibold">{{ parsed.funcLabel }}</span>
            <span v-if="parsed.symbolLabel" class="text-gray-400">
              · {{ parsed.symbolLabel }}
            </span>
            <span v-if="parsed.tf" class="text-gray-400">· {{ parsed.tf }}</span>
            <span v-if="parsed.exchange" class="text-gray-500">· {{ parsed.exchange }}</span>
          </div>
          <div v-else class="text-gray-600 text-xs">
            função não reconhecida — termine com um código (BT, DES, MON, SCR...)
          </div>
        </div>

        <!-- ajuda -->
        <div v-else class="px-4 py-3 grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1
                           font-mono text-[11px] text-gray-500">
          <div v-for="f in FUNCS" :key="f.codes[0]" class="flex gap-2">
            <span class="text-accent-yellow w-14">{{ f.codes.join('/') }}</span>
            <span>{{ f.label }}</span>
          </div>
          <div class="col-span-full mt-1 text-gray-700">
            [SÍMBOLO] [TIMEFRAME] FUNÇÃO — ex.: SOL 1H REG · DOGE MON · BTC BYBIT BT
          </div>
          <div class="col-span-full text-gray-700">
            mercado tradicional: OURO DES · EURUSD MON · AAPL TRAD DES · SPX DES
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace.js'
import { useBacktestStore } from '@/stores/backtest.js'
import { useTerminalStore } from '@/stores/terminal.js'

const router = useRouter()
const ws = useWorkspaceStore()
const btStore = useBacktestStore()
const terminal = useTerminalStore()

const open = ref(false)
const query = ref('')
const inputEl = ref(null)

const FUNCS = [
  { codes: ['BT'], label: 'Backtesting', route: '/backtest' },
  { codes: ['OPT'], label: 'Otimizador', route: '/optimizer' },
  { codes: ['REG'], label: 'Regimes', route: '/regime' },
  { codes: ['PC', 'PROP'], label: 'Prop Challenge', route: '/prop-challenge' },
  { codes: ['G', 'GP'], label: 'Gráfico', route: '/grafico' },
  { codes: ['AUTO'], label: 'Automação', route: '/automation' },
  { codes: ['J'], label: 'Diário', route: '/journal' },
  { codes: ['PAR'], label: 'Parâmetros', route: '/dashboard' },
  { codes: ['MON', 'W'], label: 'Monitor', route: '/monitor' },
  { codes: ['SCR'], label: 'Screener', route: '/screener' },
  { codes: ['EQS'], label: 'Screening fundamentalista', route: '/eqs' },
  { codes: ['DES'], label: 'Descrição do ativo', route: '/des' },
  { codes: ['N', 'NEWS'], label: 'Notícias', route: '/news' },
  { codes: ['ALRT'], label: 'Alertas', route: '/alerts' },
]
const FUNC_BY_CODE = Object.fromEntries(
  FUNCS.flatMap((f) => f.codes.map((c) => [c, f])))

const TFS = ['1M', '5M', '15M', '30M', '1H', '2H', '4H', '1D', '1WK']
const EXCHANGES = ['BYBIT', 'BINANCE', 'OKX', 'HYPERLIQUID']

// mercado tradicional: aliases (espelho do backend tradfi_data.ALIASES)
// e formatos yfinance (GC=F, EURUSD=X, ^GSPC, DX-Y.NYB)
const TRADFI_ALIASES = new Set([
  'OURO', 'GOLD', 'PRATA', 'SILVER', 'COBRE', 'COPPER', 'PETROLEO', 'OIL',
  'WTI', 'BRENT', 'GAS', 'NATGAS', 'MILHO', 'CORN', 'TRIGO', 'WHEAT',
  'SOJA', 'CAFE', 'COFFEE', 'ACUCAR', 'SUGAR', 'CACAU', 'ALGODAO',
  'SPX', 'SP500', 'DJI', 'DOW', 'NASDAQ', 'NDX', 'RUSSELL', 'VIX',
  'IBOV', 'IBOVESPA', 'DAX', 'NIKKEI', 'DXY',
  'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
  'USDBRL', 'DOLAR', 'EURBRL', 'EURGBP', 'EURJPY', 'USDMXN', 'USDCNY',
])

function isTradfiToken(t) {
  return TRADFI_ALIASES.has(t) || t.includes('=') || t.startsWith('^') || t.includes('.')
}

function resolveSymbol(token) {
  // procura na lista de assets do backend (label ou ticker)
  const t = token.toUpperCase()
  for (const [, items] of Object.entries(btStore.assets || {})) {
    for (const [label, ticker] of Object.entries(items || {})) {
      const tick = String(ticker).toUpperCase()
      if (tick === t || tick === `${t}-USD` || label.toUpperCase().includes(`(${t})`)) {
        return { label, ticker }
      }
    }
  }
  return null
}

const parsed = computed(() => {
  const tokens = query.value.trim().toUpperCase().split(/\s+/).filter(Boolean)
  if (!tokens.length) return {}
  const funcCode = tokens[tokens.length - 1]
  const func = FUNC_BY_CODE[funcCode]
  let tf = null, exchange = null, symbol = null, symbolLabel = null, base = null
  let market = null
  for (const tok of tokens.slice(0, -1)) {
    if (TFS.includes(tok)) { tf = tok.toLowerCase(); continue }
    if (EXCHANGES.includes(tok)) { exchange = tok.toLowerCase(); continue }
    if (tok === 'TRAD' || tok === 'US') { market = 'tradfi'; continue }
    const hit = resolveSymbol(tok)
    if (hit) { symbol = hit.ticker; symbolLabel = hit.label; base = tok }
    else {
      base = tok; symbol = null; symbolLabel = tok
      if (isTradfiToken(tok)) market = 'tradfi'
    }
  }
  return {
    func, funcLabel: func?.label, route: func?.route,
    tf, exchange, symbol, symbolLabel: market === 'tradfi' && symbolLabel
      ? `${symbolLabel} · tradicional` : symbolLabel,
    base, market,
  }
})

function go() {
  const p = parsed.value
  if (!p.func) return
  // aplica seleção compartilhada
  if (p.symbol) { ws.symbol = p.symbol; ws.symbolLabel = p.symbolLabel }
  if (p.tf) ws.interval = p.tf
  if (p.exchange) ws.exchange = p.exchange
  // rotas do terminal recebem o ativo por query (base crua serve p/ DES/monitor)
  if (p.route === '/des' && (p.base || ws.symbol)) {
    router.push({
      path: '/des',
      query: {
        symbol: p.base || ws.symbol.replace(/-USD.*$/, ''),
        market: p.market || 'auto',
      },
    })
  } else if (p.route === '/monitor' && p.base) {
    terminal.addToWatchlist(p.base, p.market || 'crypto')
    router.push('/monitor')
  } else {
    router.push(p.route)
  }
  close()
}

function close() {
  open.value = false
  query.value = ''
}

async function show() {
  open.value = true
  if (!Object.keys(btStore.assets || {}).length) btStore.fetchAssets?.()
  await nextTick()
  inputEl.value?.focus()
}

function onKey(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    open.value ? close() : show()
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

defineExpose({ show })
</script>
