<template>
  <div class="rounded-xl border border-surface-500 bg-surface-700 p-4 space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm text-gray-200 font-semibold">Novo deployment</h3>
      <button @click="store.showForm = false; store.pendingDeployment = null"
              class="text-gray-500 hover:text-gray-300 text-sm">✕</button>
    </div>

    <div v-if="fromValidation"
         class="text-[11px] text-accent-yellow/80 bg-accent-yellow/5 border border-accent-yellow/20 rounded-lg px-2.5 py-1.5">
      Config validada recebida — WR esperada
      {{ fromValidation.win_rate != null ? fromValidation.win_rate + '%' : '—' }}
    </div>

    <!-- Estratégia -->
    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Estratégia</label>
      <select v-model="form.strategy_file" @change="onStrategyChange"
              class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-44">
        <option v-for="st in store.strategies" :key="st.file" :value="st.file"
                :disabled="!st.automatable">
          {{ st.name }}{{ st.automatable ? '' : ' (sem signal)' }}
        </option>
      </select>
    </div>

    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Símbolo</label>
      <input v-model="form.symbol" placeholder="BTC"
             class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-44" />
    </div>

    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Timeframe</label>
      <select v-model="form.interval"
              class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-44">
        <option v-for="tf in ['5m','15m','30m','1h','4h']" :key="tf" :value="tf">{{ tf }}</option>
      </select>
    </div>

    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Modo</label>
      <select v-model="form.mode"
              class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-44">
        <option value="paper">Paper (simulado local)</option>
        <option value="demo">Bybit Demo (ordens reais)</option>
      </select>
    </div>

    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Capital inicial ($)</label>
      <div class="w-44">
        <NumInput v-model="form.initial_capital" :min="100" :step="1000" />
      </div>
    </div>

    <!-- Parâmetros da estratégia -->
    <div class="border-t border-surface-600 pt-3">
      <SchemaFields :schema="schema" :params="form.params" :hidden="['initial_capital']" />
    </div>

    <div v-if="store.error" class="text-xs text-red-400">{{ store.error }}</div>

    <button @click="submit" :disabled="store.isLoading"
            class="w-full py-2 rounded-lg text-xs font-semibold bg-accent-yellow/15 text-accent-yellow
                   hover:bg-accent-yellow/25 transition-colors disabled:opacity-50">
      {{ store.isLoading ? 'Criando...' : 'Criar deployment' }}
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { useAutomationStore } from '@/stores/automation.js'
import NumInput from '@/components/NumInput.vue'
import SchemaFields from '@/components/common/SchemaFields.vue'

const store = useAutomationStore()
const pending = store.pendingDeployment

const form = reactive({
  strategy_file: pending?.strategy_file || 'mm9_pullback',
  symbol: pending?.symbol || 'BTC',
  interval: pending?.interval || '15m',
  exchange: pending?.exchange || 'bybit',
  mode: 'paper',
  initial_capital: 10000,
  params: { ...(pending?.params || {}) },
})

const fromValidation = computed(() => pending?.backtest_ref || null)

const schema = computed(() =>
  store.strategies.find((s) => s.file === form.strategy_file)?.schema || [])

function applyDefaults() {
  for (const section of schema.value) {
    for (const f of section.fields) {
      if (!(f.key in form.params) && f.default !== undefined) {
        form.params[f.key] = f.default
      }
    }
  }
}

function onStrategyChange() {
  form.params = {}
  applyDefaults()
}

onMounted(async () => {
  if (!store.strategies.length) await store.fetchStrategies()
  applyDefaults()
})

async function submit() {
  await store.create({
    name: `${form.strategy_file} ${form.symbol} ${form.interval} (${form.mode})`,
    strategy_file: form.strategy_file,
    params: { ...form.params, initial_capital: form.initial_capital },
    symbol: form.symbol.trim().toUpperCase(),
    interval: form.interval,
    exchange: form.exchange,
    mode: form.mode,
    initial_capital: form.initial_capital,
    backtest_ref: pending?.backtest_ref || null,
  })
}
</script>
