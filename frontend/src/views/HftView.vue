<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">

    <!-- Header -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-lg font-bold text-gray-100">
        <span class="text-accent-yellow">◆</span> HFT On-chain
        <span class="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-600 text-gray-400 ml-1">{{ status?.mode || 'paper' }}</span>
      </h1>
      <span v-if="status?.halted" class="text-xs px-2 py-1 rounded bg-accent-red/15 text-accent-red-light">⛔ stop diário atingido</span>
      <div class="flex-1" />
      <button v-if="!status?.running" @click="start" class="px-3 py-1.5 text-xs rounded-md bg-accent-yellow/15 text-accent-yellow hover:bg-accent-yellow/25 font-medium">▶ Ligar motor</button>
      <template v-else>
        <span class="flex items-center gap-1.5 text-xs text-accent-yellow/80">
          <span class="w-2 h-2 rounded-full bg-accent-yellow animate-pulse" /> RODANDO
        </span>
        <button @click="stop(false)" class="px-3 py-1.5 text-xs rounded-md border border-surface-600 text-gray-400 hover:text-gray-200">Parar</button>
        <button @click="stop(true)" class="px-3 py-1.5 text-xs rounded-md border border-accent-red/40 text-accent-red-light">Parar + fechar posições</button>
      </template>
    </div>

    <!-- Stats -->
    <div v-if="status" class="flex flex-wrap gap-3">
      <div class="stat"><div class="lbl">Equity (est.)</div><div class="val text-accent-yellow">${{ status.equity_est }}</div></div>
      <div class="stat"><div class="lbl">Capital livre</div><div class="val">${{ status.capital }}</div></div>
      <div class="stat"><div class="lbl">PnL hoje</div><div class="val" :class="status.day_pnl >= 0 ? 'text-accent-green' : 'text-accent-red-light'">${{ status.day_pnl }}</div></div>
      <div class="stat"><div class="lbl">Posições</div><div class="val">{{ Object.keys(status.positions).length }}/{{ status.config.max_positions }}</div></div>
      <div class="stat"><div class="lbl">Watchlist</div><div class="val">{{ status.watchlist_size }}</div></div>
      <div class="stat"><div class="lbl">Trades</div><div class="val">{{ status.n_trades }}</div></div>
      <div class="stat"><div class="lbl">Chain</div><div class="val text-xs pt-1.5">{{ status.chain }}</div></div>
    </div>

    <div class="grid lg:grid-cols-2 gap-4">
      <!-- Posições -->
      <div class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-2"><span class="text-accent-yellow">◆</span> Posições abertas</h2>
        <div v-if="!status || !Object.keys(status.positions).length" class="text-xs text-gray-600">Nenhuma posição</div>
        <div v-for="(p, addr) in status?.positions || {}" :key="addr" class="flex justify-between text-xs py-1.5 border-b border-surface-700/50">
          <span class="font-semibold text-gray-200">{{ p.symbol }}</span>
          <span class="font-mono text-gray-400">${{ p.usd_in }} @ {{ p.entry.toPrecision(4) }}</span>
          <span class="text-gray-600">{{ Math.round((Date.now()/1000 - p.opened_at) / 60) }}min</span>
        </div>

        <h2 class="text-sm font-semibold text-gray-200 mt-4 mb-2"><span class="text-accent-yellow">◆</span> Config</h2>
        <div class="grid grid-cols-2 gap-2">
          <label v-for="f in CFG_FIELDS" :key="f.key" class="text-[10px] text-gray-500">
            {{ f.label }}
            <input v-model.number="cfg[f.key]" type="number" :step="f.step || 1" class="inp mt-0.5" />
          </label>
        </div>
        <button @click="saveCfg" class="mt-2 px-3 py-1.5 text-xs rounded-md bg-accent-yellow/15 text-accent-yellow hover:bg-accent-yellow/25 font-medium">Salvar config</button>
      </div>

      <!-- Trades -->
      <div class="card p-4">
        <h2 class="text-sm font-semibold text-gray-200 mb-2"><span class="text-accent-yellow">◆</span> Últimos trades</h2>
        <div v-if="!status?.trades?.length" class="text-xs text-gray-600">Nenhum trade ainda</div>
        <div v-for="(t, i) in [...(status?.trades || [])].reverse()" :key="i" class="flex justify-between text-xs py-1.5 border-b border-surface-700/50">
          <span class="font-semibold text-gray-200 w-20 truncate">{{ t.symbol }}</span>
          <span class="font-mono" :class="t.pnl >= 0 ? 'text-accent-green' : 'text-accent-red-light'">${{ t.pnl }} ({{ t.pnl_pct }}%)</span>
          <span class="text-gray-600">{{ t.held_min }}min</span>
          <span class="text-gray-500">{{ t.reason }}</span>
        </div>
      </div>
    </div>

    <!-- Eventos -->
    <div class="card p-4">
      <h2 class="text-sm font-semibold text-gray-200 mb-2"><span class="text-accent-yellow">◆</span> Log</h2>
      <div v-for="(e, i) in [...(status?.events || [])].reverse()" :key="i" class="text-[11px] font-mono py-0.5"
           :class="{ 'text-accent-yellow': e.kind === 'entry', 'text-accent-green': e.kind === 'exit', 'text-accent-red-light': ['error','guardrail'].includes(e.kind), 'text-gray-500': !['entry','exit','error','guardrail'].includes(e.kind) }">
        {{ new Date(e.ts * 1000).toLocaleTimeString('pt-BR') }} [{{ e.kind }}] {{ e.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import api from '@/api/client.js'

const status = ref(null)
const cfg = reactive({})
let timer = null

const CFG_FIELDS = [
  { key: 'min_liquidity_usd', label: 'Liquidez mín ($)' },
  { key: 'min_pool_age_h', label: 'Idade mín pool (h)' },
  { key: 'min_buy_ratio', label: 'Buy ratio mín', step: 0.01 },
  { key: 'min_vol_accel', label: 'Aceleração mín (x)', step: 0.1 },
  { key: 'take_profit_pct', label: 'Take profit (%)', step: 0.5 },
  { key: 'stop_loss_pct', label: 'Stop loss (%)', step: 0.5 },
  { key: 'max_hold_min', label: 'Hold máx (min)' },
  { key: 'position_usd', label: 'Tamanho posição ($)' },
  { key: 'max_positions', label: 'Posições máx' },
  { key: 'daily_loss_stop_usd', label: 'Stop diário ($)' },
  { key: 'tick_interval_s', label: 'Tick (s)' },
]

async function refresh() {
  const { data } = await api.get('/hft/status')
  status.value = data
  if (!Object.keys(cfg).length) Object.assign(cfg, data.config)
}

async function start() { await api.post('/hft/start'); refresh() }
async function stop(close) { await api.post('/hft/stop', { close_positions: close }); refresh() }
async function saveCfg() { await api.post('/hft/config', { ...cfg }); refresh() }

onMounted(() => { refresh(); timer = setInterval(refresh, 4000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.stat { @apply bg-surface-800 rounded-lg px-4 py-2.5 border border-surface-600 min-w-24; }
.lbl { @apply text-[10px] text-gray-500; }
.val { @apply text-base font-bold text-gray-200; }
.inp { @apply w-full bg-surface-900 border border-surface-600 rounded px-2 py-1 text-xs text-gray-200 focus:outline-none focus:border-accent-yellow/50; }
</style>
