<template>
  <div v-if="s" class="space-y-4">
    <!-- Header + ações -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base text-gray-100 font-semibold">{{ dep.name }}</h2>
        <p class="text-xs text-gray-500">
          {{ dep.strategy_file }} · {{ dep.symbol }} {{ dep.interval }} ·
          {{ dep.exchange }} · {{ dep.mode }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="dep.status !== 'running'"
          @click="store.start(dep.id)"
          class="btn-primary"
        >Iniciar</button>
        <button v-else @click="askStop" class="btn-secondary">Parar</button>
        <button
          v-if="dep.status !== 'running'"
          @click="askDelete"
          class="btn-danger"
        >Excluir</button>
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-4 gap-3">
      <div class="kpi">
        <div class="kpi-label">Equity</div>
        <div class="kpi-value">$ {{ fmt(dep.equity) }}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Retorno</div>
        <div class="kpi-value" :class="ret >= 0 ? 'text-accent-yellow' : 'text-red-400'">
          {{ ret >= 0 ? '+' : '' }}{{ ret.toFixed(2) }}%
        </div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Trades</div>
        <div class="kpi-value">{{ s.trades?.length ?? 0 }}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Último candle</div>
        <div class="kpi-value text-xs">{{ tsFmt(dep.last_candle_ts) }}</div>
      </div>
    </div>

    <!-- Posição aberta / ordem pendente -->
    <div class="grid grid-cols-2 gap-3">
      <div class="rounded-xl border border-surface-500 bg-surface-700 p-3">
        <div class="text-[10px] text-gray-500 uppercase mb-1.5">Posição aberta</div>
        <template v-if="s.position">
          <div class="text-sm" :class="s.position.side === 1 ? 'text-accent-yellow' : 'text-red-400'">
            {{ s.position.side === 1 ? 'LONG' : 'SHORT' }} @ {{ fmt(s.position.entry_price) }}
          </div>
          <div class="text-[11px] text-gray-500 mt-1">
            TP {{ fmt(s.position.tp_price) }} · SL {{ fmt(s.position.sl_price) }} ·
            {{ s.position.bars_held }}/{{ s.position.max_bars }} barras
          </div>
        </template>
        <div v-else class="text-xs text-gray-600">flat</div>
      </div>
      <div class="rounded-xl border border-surface-500 bg-surface-700 p-3">
        <div class="text-[10px] text-gray-500 uppercase mb-1.5">Ordem pendente</div>
        <template v-if="s.working_order">
          <div class="text-sm text-gray-300">
            Limite {{ s.working_order.side === 1 ? 'compra' : 'venda' }}
            @ {{ fmt(s.working_order.price) }}
          </div>
          <div class="text-[11px] text-gray-500 mt-1">válida por 1 candle</div>
        </template>
        <div v-else class="text-xs text-gray-600">nenhuma</div>
      </div>
    </div>

    <!-- Parâmetros da estratégia automatizada -->
    <div class="rounded-xl border border-surface-500 bg-surface-700 p-3">
      <div class="text-[10px] text-gray-500 uppercase mb-2">
        Parâmetros da estratégia · {{ dep.strategy_file }}
      </div>
      <div v-if="paramList.length" class="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-0.5">
        <div
          v-for="p in paramList"
          :key="p.key"
          class="flex justify-between gap-2 text-[11px] border-b border-surface-600/40 py-1"
        >
          <span class="text-gray-500 truncate" :title="p.key">{{ p.label }}</span>
          <span class="text-gray-300 font-medium shrink-0">{{ p.value }}</span>
        </div>
      </div>
      <div v-else class="text-xs text-gray-600">defaults da estratégia</div>
    </div>

    <!-- Monitor de invalidação -->
    <LiveVsBacktestPanel :comparison="s.comparison" />

    <!-- Equity -->
    <div class="rounded-xl border border-surface-500 bg-surface-700 p-3 h-72">
      <AutomationEquityChart
        :curve="s.equity_curve"
        :initial-capital="dep.initial_capital"
      />
    </div>

    <!-- Trades -->
    <div class="rounded-xl border border-surface-500 bg-surface-700 p-3">
      <div class="text-[10px] text-gray-500 uppercase mb-2">Trades fechados</div>
      <table v-if="s.trades?.length" class="w-full text-xs">
        <thead>
          <tr class="text-gray-600 text-left">
            <th class="pb-1.5 font-medium">Lado</th>
            <th class="pb-1.5 font-medium">Entrada</th>
            <th class="pb-1.5 font-medium">Saída</th>
            <th class="pb-1.5 font-medium">Motivo</th>
            <th class="pb-1.5 font-medium text-right">PnL %</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in s.trades" :key="t.id" class="border-t border-surface-600">
            <td class="py-1.5" :class="t.side === 1 ? 'text-accent-yellow' : 'text-red-400'">
              {{ t.side === 1 ? 'L' : 'S' }}
            </td>
            <td class="py-1.5 text-gray-400">{{ fmt(t.entry_price) }}</td>
            <td class="py-1.5 text-gray-400">{{ fmt(t.exit_price) }}</td>
            <td class="py-1.5 text-gray-500">{{ t.exit_reason }}</td>
            <td class="py-1.5 text-right font-medium"
                :class="t.pnl_pct >= 0 ? 'text-accent-yellow' : 'text-red-400'">
              {{ t.pnl_pct >= 0 ? '+' : '' }}{{ t.pnl_pct?.toFixed(3) }}%
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="text-xs text-gray-600">nenhum trade fechado ainda</div>
    </div>

    <!-- Eventos -->
    <div class="rounded-xl border border-surface-500 bg-surface-700 p-3">
      <div class="text-[10px] text-gray-500 uppercase mb-2">Eventos</div>
      <div class="space-y-1 max-h-52 overflow-y-auto">
        <div v-for="ev in s.events" :key="ev.id" class="flex gap-2 text-[11px]">
          <span class="text-gray-600 shrink-0">{{ tsFmt(ev.ts) }}</span>
          <span :class="ev.level === 'error' ? 'text-red-400' : 'text-gray-400'">
            {{ ev.message }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="flex items-center justify-center h-full text-sm text-gray-600">
    Selecione um deployment
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAutomationStore } from '@/stores/automation.js'
import AutomationEquityChart from './AutomationEquityChart.vue'
import LiveVsBacktestPanel from './LiveVsBacktestPanel.vue'

const store = useAutomationStore()
const s = computed(() => store.status)
const dep = computed(() => s.value?.deployment || {})
const ret = computed(() =>
  dep.value.initial_capital
    ? (dep.value.equity / dep.value.initial_capital - 1) * 100 : 0)

// Parâmetros do deployment com labels do schema da estratégia.
// Só as chaves do schema: o objeto salvo carrega sobras de outras
// estratégias (o form acumula defaults), que a estratégia ignora.
const paramList = computed(() => {
  const params = dep.value.params || {}
  const schema = store.strategies.find(x => x.file === dep.value.strategy_file)?.schema || []
  const labels = {}
  const order = []
  for (const sec of schema) {
    for (const f of (sec.fields || [])) { labels[f.key] = f.label; order.push(f.key) }
  }
  const keys = order.length
    ? order.filter(k => k in params)
    : Object.keys(params)                       // schema ainda não carregado
  return keys.map(k => ({ key: k, label: labels[k] || k, value: fmtParam(params[k]) }))
})

function fmtParam(v) {
  if (typeof v === 'boolean') return v ? 'sim' : 'não'
  if (Array.isArray(v)) return v.length > 8 ? `${v.length} itens` : v.join(', ')
  if (typeof v === 'number') {
    return Number.isInteger(v) ? String(v) : v.toLocaleString('pt-BR', { maximumFractionDigits: 4 })
  }
  return v == null || v === '' ? '—' : String(v)
}

function fmt(v) {
  return v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}
function tsFmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function askStop() {
  if (s.value?.position) {
    const close = window.confirm(
      'Há posição aberta.\n\nOK = parar e FECHAR a posição a mercado\nCancelar = parar e MANTER a posição (congela até religar)')
    store.stop(dep.value.id, close)
  } else {
    store.stop(dep.value.id, false)
  }
}

function askDelete() {
  if (window.confirm(`Excluir "${dep.value.name}" e todo o histórico?`)) {
    store.remove(dep.value.id)
  }
}
</script>

<style scoped>
.kpi {
  @apply rounded-xl border border-surface-500 bg-surface-700 p-3;
}
.kpi-label {
  @apply text-[10px] text-gray-500 uppercase;
}
.kpi-value {
  @apply text-base text-gray-200 font-semibold mt-0.5;
}
.btn-primary {
  @apply px-3 py-1.5 rounded-lg text-xs font-semibold bg-accent-yellow/15 text-accent-yellow
         hover:bg-accent-yellow/25 transition-colors;
}
.btn-secondary {
  @apply px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-500 text-gray-300
         hover:bg-surface-400 transition-colors;
}
.btn-danger {
  @apply px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-500/10 text-red-400
         hover:bg-red-500/20 transition-colors;
}
</style>
