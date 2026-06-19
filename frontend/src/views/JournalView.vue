<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto">
    <div class="max-w-7xl mx-auto p-5 space-y-5">

      <!-- Header -->
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-gray-100 tracking-tight">Diário de Operações</h1>
          <p class="text-sm text-gray-500 mt-0.5">Registre seus trades por estratégia e acompanhe o capital</p>
        </div>
        <!-- Capital inicial -->
        <div class="card px-4 py-2.5 flex items-end gap-3">
          <div>
            <label class="metric-label block mb-1">Capital inicial</label>
            <div class="flex items-center gap-1.5">
              <span class="text-gray-500 text-sm">$</span>
              <input
                v-model.number="capitalDraft"
                type="number"
                step="0.01"
                class="form-input w-32 font-mono"
                @keyup.enter="saveCapital"
              />
            </div>
          </div>
          <button class="btn-secondary" :disabled="store.saving" @click="saveCapital">Salvar</button>
        </div>
      </div>

      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- KPIs -->
      <div v-if="s" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        <div class="metric-card">
          <span class="metric-label">Capital atual</span>
          <span class="metric-value" :class="netClass(s.capital_atual - s.capital_inicial)">
            {{ money(s.capital_atual) }}
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Resultado líq.</span>
          <span class="metric-value" :class="netClass(s.net_pnl)">{{ moneySigned(s.net_pnl) }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">ROI</span>
          <span class="metric-value" :class="netClass(s.roi)">{{ pct(s.roi) }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Win rate</span>
          <span class="metric-value text-gray-100">{{ s.win_rate.toFixed(1) }}%</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Profit factor</span>
          <span class="metric-value text-gray-100">{{ s.profit_factor == null ? '∞' : s.profit_factor.toFixed(2) }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Trades</span>
          <span class="metric-value text-gray-100">
            {{ s.total_trades }}
            <span class="text-[10px] font-normal text-gray-500">
              ({{ s.wins }}W / {{ s.losses }}L)
            </span>
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Equity curve -->
        <div class="card p-4 lg:col-span-2">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-semibold text-gray-300">Curva de Capital</h2>
            <div class="flex gap-4 text-[11px] text-gray-500">
              <span>Ganho médio <b class="text-accent-yellow font-mono">{{ money(s?.avg_win) }}</b></span>
              <span>Perda média <b class="text-accent-red-light font-mono">{{ money(s?.avg_loss) }}</b></span>
            </div>
          </div>
          <JournalEquityChart
            v-if="s && store.trades.length"
            :curve="s.equity_curve"
            :capital-inicial="s.capital_inicial"
            class="h-72"
          />
          <div v-else class="h-72 flex items-center justify-center text-gray-600 text-sm">
            Nenhuma operação registrada ainda
          </div>
        </div>

        <!-- Por estratégia -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-300 mb-3">Por Estratégia</h2>
          <div v-if="s && s.by_strategy.length" class="space-y-2">
            <div
              v-for="b in s.by_strategy"
              :key="b.strategy"
              class="bg-surface-600 rounded-lg p-2.5 border border-surface-500"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-gray-200 truncate">{{ b.strategy }}</span>
                <span class="text-sm font-mono font-semibold" :class="netClass(b.net)">{{ moneySigned(b.net) }}</span>
              </div>
              <div class="flex items-center gap-3 text-[11px] text-gray-500">
                <span>{{ b.trades }} trades</span>
                <span class="text-accent-yellow/80">{{ b.win_rate.toFixed(0) }}% win</span>
                <span>PF {{ b.profit_factor == null ? '∞' : b.profit_factor.toFixed(2) }}</span>
              </div>
              <!-- win/loss bar -->
              <div class="mt-1.5 h-1.5 rounded-full overflow-hidden bg-surface-500 flex">
                <div class="bg-accent-yellow h-full" :style="{ width: winPct(b) + '%' }" />
                <div class="bg-accent-red h-full" :style="{ width: 100 - winPct(b) + '%' }" />
              </div>
            </div>
          </div>
          <div v-else class="text-gray-600 text-sm py-8 text-center">Sem dados</div>
        </div>
      </div>

      <!-- Novo trade -->
      <div class="card-accent p-4">
        <h2 class="text-sm font-semibold text-gray-300 mb-3">Registrar operação</h2>
        <form class="grid grid-cols-2 md:grid-cols-6 gap-3 items-end" @submit.prevent="submit">
          <div class="col-span-1">
            <label class="metric-label block mb-1">Data</label>
            <input v-model="form.date" type="date" class="form-input w-full" />
          </div>
          <div class="col-span-1">
            <label class="metric-label block mb-1">Estratégia</label>
            <input
              v-model="form.strategy"
              list="strategy-options"
              placeholder="Ex: depaula"
              class="form-input w-full"
            />
            <datalist id="strategy-options">
              <option v-for="opt in strategyNames" :key="opt" :value="opt" />
            </datalist>
          </div>
          <div class="col-span-1">
            <label class="metric-label block mb-1">Ativo</label>
            <input v-model="form.asset" placeholder="BTCUSDT" class="form-input w-full" />
          </div>
          <div class="col-span-1">
            <label class="metric-label block mb-1">Resultado</label>
            <div class="flex gap-1">
              <button
                type="button"
                class="flex-1 px-2 py-2 rounded-lg text-sm font-semibold transition-all"
                :class="form.result === 'gain'
                  ? 'bg-accent-yellow text-black'
                  : 'bg-surface-600 text-gray-400 border border-surface-400 hover:text-gray-200'"
                @click="form.result = 'gain'"
              >Gain</button>
              <button
                type="button"
                class="flex-1 px-2 py-2 rounded-lg text-sm font-semibold transition-all"
                :class="form.result === 'loss'
                  ? 'bg-accent-red text-white'
                  : 'bg-surface-600 text-gray-400 border border-surface-400 hover:text-gray-200'"
                @click="form.result = 'loss'"
              >Loss</button>
            </div>
          </div>
          <div class="col-span-1">
            <label class="metric-label block mb-1">Valor ($)</label>
            <input v-model.number="form.amount" type="number" step="0.01" min="0" placeholder="0.00" class="form-input w-full font-mono" />
          </div>
          <div class="col-span-1">
            <button type="submit" class="btn-primary w-full" :disabled="store.saving || !canSubmit">
              + Adicionar
            </button>
          </div>
          <div class="col-span-2 md:col-span-6">
            <input v-model="form.notes" placeholder="Notas (opcional)" class="form-input w-full" />
          </div>
        </form>
      </div>

      <!-- Tabela de trades -->
      <div class="card overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-surface-500">
          <h2 class="text-sm font-semibold text-gray-300">Histórico ({{ store.trades.length }})</h2>
        </div>
        <div v-if="store.trades.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-[11px] uppercase tracking-wide text-gray-500 border-b border-surface-500">
                <th class="px-4 py-2 font-medium">Data</th>
                <th class="px-4 py-2 font-medium">Estratégia</th>
                <th class="px-4 py-2 font-medium">Ativo</th>
                <th class="px-4 py-2 font-medium">Resultado</th>
                <th class="px-4 py-2 font-medium text-right">Valor</th>
                <th class="px-4 py-2 font-medium">Notas</th>
                <th class="px-4 py-2 font-medium text-right"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in store.trades" :key="t.id" class="border-b border-surface-500/60 hover:bg-surface-600/40">
                <td class="px-4 py-2 font-mono text-gray-400 whitespace-nowrap">{{ t.date || '—' }}</td>
                <td class="px-4 py-2 text-gray-200">{{ t.strategy }}</td>
                <td class="px-4 py-2 text-gray-400">{{ t.asset || '—' }}</td>
                <td class="px-4 py-2">
                  <span
                    class="px-2 py-0.5 rounded text-[11px] font-semibold"
                    :class="t.result === 'gain' ? 'bg-accent-yellow/15 text-accent-yellow' : 'bg-accent-red/15 text-accent-red-light'"
                  >{{ t.result === 'gain' ? 'GAIN' : 'LOSS' }}</span>
                </td>
                <td class="px-4 py-2 text-right font-mono" :class="t.result === 'gain' ? 'text-accent-yellow' : 'text-accent-red-light'">
                  {{ t.result === 'gain' ? '+' : '−' }}{{ money(t.amount) }}
                </td>
                <td class="px-4 py-2 text-gray-500 max-w-xs truncate">{{ t.notes || '—' }}</td>
                <td class="px-4 py-2 text-right">
                  <button
                    class="text-gray-600 hover:text-accent-red-light transition-colors"
                    title="Excluir"
                    @click="store.removeTrade(t.id)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-4 py-12 text-center text-gray-600 text-sm">
          Nenhuma operação registrada. Use o formulário acima para começar.
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useJournalStore } from '@/stores/journal.js'
import { getStrategies } from '@/api/client.js'
import JournalEquityChart from '@/components/journal/JournalEquityChart.vue'

const store = useJournalStore()
const s = computed(() => store.stats)

const capitalDraft = ref(0)
const strategyNames = ref([])

const form = reactive({
  date: new Date().toISOString().slice(0, 10),
  strategy: '',
  asset: '',
  result: 'gain',
  amount: null,
  notes: '',
})

const canSubmit = computed(() => form.amount != null && Number(form.amount) > 0)

function money(v) {
  if (v == null) return '$ 0,00'
  return '$ ' + Math.abs(Number(v)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function moneySigned(v) {
  const n = Number(v) || 0
  return (n >= 0 ? '+' : '−') + money(n).replace('$ ', '$ ')
}
function pct(v) {
  const n = Number(v) || 0
  return (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
}
function netClass(v) {
  return Number(v) >= 0 ? 'text-accent-yellow' : 'text-accent-red-light'
}
function winPct(b) {
  return b.trades ? (b.wins / b.trades) * 100 : 0
}

async function saveCapital() {
  await store.saveCapital(capitalDraft.value)
}

async function submit() {
  if (!canSubmit.value) return
  const ok = await store.addTrade({ ...form, amount: Number(form.amount) })
  if (ok) {
    form.amount = null
    form.notes = ''
  }
}

onMounted(async () => {
  await store.load()
  capitalDraft.value = store.capitalInicial
  try {
    const { data } = await getStrategies()
    strategyNames.value = (data.strategies || []).map((x) => x.name || x.file)
  } catch { /* lista opcional */ }
})
</script>
