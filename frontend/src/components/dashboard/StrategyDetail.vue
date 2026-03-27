<template>
  <div class="strategy-detail-anchor">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-200">
        Detalhes do Parâmetro
        <span v-if="detail?.rank" class="text-gray-400 font-normal ml-1">— Rank {{ detail.rank }}</span>
      </h2>
      <div class="flex items-center gap-2">
        <button
          @click="sendToBacktest"
          class="btn-primary flex items-center gap-1.5 text-xs"
        >
          Enviar para Backtesting
        </button>
        <button
          @click="sendToProp"
          class="btn-secondary flex items-center gap-1.5 text-xs"
        >
          Enviar para Prop Challenge
        </button>
        <button @click="store.clearSelection()" class="text-gray-500 hover:text-gray-300 text-lg leading-none">✕</button>
      </div>
    </div>

    <!-- Success message -->
    <Transition name="fade">
      <div v-if="sentMessage" class="mb-3 text-xs text-accent-green-light flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        {{ sentMessage }}
      </div>
    </Transition>

    <!-- Parameters grid -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-2 text-xs">
      <div v-for="(val, key) in displayParams" :key="key" class="flex gap-1">
        <span class="text-gray-500 shrink-0">{{ formatKey(key) }}:</span>
        <span class="text-gray-200 font-medium break-all">{{ formatVal(val) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard.js'
import { useBacktestStore } from '@/stores/backtest.js'
import { usePropChallengeStore } from '@/stores/propChallenge.js'

const store = useDashboardStore()
const btStore = useBacktestStore()
const propStore = usePropChallengeStore()
const router = useRouter()
const sentMessage = ref('')

const detail = computed(() => store.selectedDetail)

// Exibe todos os campos exceto internos vazios
const displayParams = computed(() => {
  if (!detail.value) return {}
  const skip = new Set(['__index__'])
  const result = {}
  for (const [k, v] of Object.entries(detail.value)) {
    if (!skip.has(k)) result[k] = v
  }
  return result
})

const KEY_DISPLAY = {
  rank: 'Rank', return_pct: 'Retorno (%)', max_dd_pct: 'Max DD (%)',
  trades: 'Trades', win_rate_pct: 'Win Rate (%)', avg_win_pct: 'Avg Win (%)',
  avg_loss_pct: 'Avg Loss (%)', profit_factor: 'Profit Factor', sharpe: 'Sharpe',
  score: 'Score', ma: 'MA', periodo: 'Período', lookback: 'Lookback',
  angulo: 'Ângulo', saida: 'Saída', banda_pct: 'Banda (%)',
  alvo_fixo_pct: 'Alvo Fixo (%)', flat: 'Flat', stop: 'Stop',
  stop_param: 'Stop Param', pullback: 'Pullback', entry_zone: 'Entry Zone',
  ativo: 'Ativo',
}

function formatKey(k) {
  return KEY_DISPLAY[k] || k
}

function formatVal(v) {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'number') return Number(v).toFixed(4)
  if (typeof v === 'boolean') return v ? 'Sim' : 'Não'
  return String(v)
}

function sendToBacktest() {
  if (!store.backtestParams) return
  btStore.pendingParams = { ...store.backtestParams, strategy_file: 'depaula' }
  sentMessage.value = 'Parametros enviados para Backtesting Live'
  setTimeout(() => {
    router.push('/backtest')
  }, 600)
}

function sendToProp() {
  if (!store.backtestParams) return
  const ativo = detail.value?.ativo || store.asset || ''
  propStore.pendingParams = {
    ...store.backtestParams,
    strategy_file: 'depaula',
    _ativo: ativo,
  }
  sentMessage.value = 'Parametros enviados para Prop Challenge'
  setTimeout(() => {
    router.push('/prop-challenge')
  }, 600)
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
