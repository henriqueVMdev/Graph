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
              class="border rounded-lg text-xs px-2 py-1.5 w-44"
              :class="form.mode === 'real'
                ? 'bg-red-950/40 border-red-500/60 text-red-300'
                : 'bg-surface-600 border-surface-400 text-gray-100'">
        <option value="paper">Paper (simulado local)</option>
        <option value="demo">Bybit Demo (ordens reais)</option>
        <option value="real">Bybit REAL (dinheiro real)</option>
      </select>
    </div>

    <!-- Modo real: aviso + conta -->
    <template v-if="form.mode === 'real'">
      <div class="text-[11px] text-red-300 bg-red-950/40 border border-red-500/40 rounded-lg px-2.5 py-2">
        ⚠ Ordens com <b>dinheiro real</b> na Bybit mainnet. TP/SL ficam
        server-side na exchange. Proteções extras são opcionais abaixo.
      </div>
      <div class="flex items-center justify-between gap-2">
        <label class="text-xs text-gray-400">Conta</label>
        <select v-model="form.account"
                class="bg-surface-600 border border-surface-400 rounded-lg text-xs text-gray-100 px-2 py-1.5 w-44">
          <option :value="null" disabled>Selecione a conta</option>
          <option v-for="a in store.accounts" :key="a.id" :value="a.id" :disabled="!a.configured">
            {{ a.id === 'prop' ? 'Prop firm' : 'Pessoal' }}{{ a.configured ? '' : ' (sem chaves no .env)' }}
          </option>
        </select>
      </div>
    </template>

    <div class="flex items-center justify-between gap-2">
      <label class="text-xs text-gray-400">Capital inicial ($)</label>
      <div class="w-44">
        <NumInput v-model="form.initial_capital" :min="100" :step="1000" />
      </div>
    </div>

    <!-- Proteções opcionais (default: tudo desligado — só o stop da estratégia) -->
    <div class="border-t border-surface-600 pt-3 space-y-2">
      <p class="text-[10px] text-gray-500 uppercase tracking-widest">
        Proteções (opcional — padrão desligado)
      </p>

      <div class="flex items-center justify-between gap-2">
        <label class="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" v-model="guard.dailyOn" class="w-3.5 h-3.5 accent-accent-yellow" />
          Perda diária máx (%)
        </label>
        <div class="w-24" :class="!guard.dailyOn ? 'opacity-40 pointer-events-none' : ''">
          <NumInput v-model="guard.daily_loss_pct" :min="0.1" :max="50" :step="0.5" />
        </div>
      </div>

      <div class="flex items-center justify-between gap-2">
        <label class="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" v-model="guard.maxOn" class="w-3.5 h-3.5 accent-accent-yellow" />
          Perda total máx (%)
        </label>
        <div class="w-24" :class="!guard.maxOn ? 'opacity-40 pointer-events-none' : ''">
          <NumInput v-model="guard.max_loss_pct" :min="0.5" :max="90" :step="1" />
        </div>
      </div>

      <div class="flex items-center justify-between gap-2">
        <label class="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" v-model="guard.check_balance" class="w-3.5 h-3.5 accent-accent-yellow" />
          Checar saldo antes de enviar <span class="text-gray-600">(só real)</span>
        </label>
      </div>

      <div class="flex items-center justify-between gap-2">
        <label class="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" v-model="guard.notionalOn" class="w-3.5 h-3.5 accent-accent-yellow" />
          Teto de notional ($)
        </label>
        <div class="w-24" :class="!guard.notionalOn ? 'opacity-40 pointer-events-none' : ''">
          <NumInput v-model="guard.max_notional" :min="10" :step="100" />
        </div>
      </div>
    </div>

    <!-- Parâmetros da estratégia -->
    <div class="border-t border-surface-600 pt-3">
      <SchemaFields :schema="schema" :params="form.params" :hidden="['initial_capital']" />
    </div>

    <div v-if="store.error" class="text-xs text-red-400">{{ store.error }}</div>

    <button @click="submit" :disabled="store.isLoading || (form.mode === 'real' && !form.account)"
            class="w-full py-2 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
            :class="form.mode === 'real'
              ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30'
              : 'bg-accent-yellow/15 text-accent-yellow hover:bg-accent-yellow/25'">
      {{ store.isLoading ? 'Criando...'
         : form.mode === 'real' ? 'Criar deployment REAL' : 'Criar deployment' }}
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
  account: null,
  initial_capital: 10000,
  params: { ...(pending?.params || {}) },
})

// Proteções opcionais — tudo desligado por padrão (só TP/SL da estratégia)
const guard = reactive({
  dailyOn: false, daily_loss_pct: 5,
  maxOn: false, max_loss_pct: 10,
  check_balance: false,
  notionalOn: false, max_notional: 1000,
})

function buildGuardrails() {
  const g = {}
  if (guard.dailyOn && guard.daily_loss_pct > 0) g.daily_loss_pct = guard.daily_loss_pct
  if (guard.maxOn && guard.max_loss_pct > 0) g.max_loss_pct = guard.max_loss_pct
  if (guard.check_balance) g.check_balance = true
  if (guard.notionalOn && guard.max_notional > 0) g.max_notional = guard.max_notional
  return Object.keys(g).length ? g : null
}

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
  if (!store.accounts.length) await store.fetchAccounts()
  applyDefaults()
})

async function submit() {
  if (form.mode === 'real') {
    const ok = window.confirm(
      `Criar deployment com DINHEIRO REAL na conta "${form.account}"?\n\n` +
      `${form.symbol.toUpperCase()} ${form.interval} · capital $${form.initial_capital}`)
    if (!ok) return
  }
  await store.create({
    name: `${form.strategy_file} ${form.symbol} ${form.interval} (${form.mode})`,
    strategy_file: form.strategy_file,
    params: { ...form.params, initial_capital: form.initial_capital },
    symbol: form.symbol.trim().toUpperCase(),
    interval: form.interval,
    exchange: form.exchange,
    mode: form.mode,
    account: form.mode === 'real' ? form.account : null,
    guardrails: buildGuardrails(),
    initial_capital: form.initial_capital,
    backtest_ref: pending?.backtest_ref || null,
  })
}
</script>
