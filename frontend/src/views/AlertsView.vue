<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <h1 class="text-base font-semibold text-gray-100">Alertas de Preço, Funding e Sinais</h1>
    <p class="text-[10px] text-gray-600 -mt-3">além dos alertas manuais, o vigia automático monitora o universo da Central de Inteligência a cada 15 min: mudanças de sinal (ex.: NEUTRO → COMPRA) e divergências novas aparecem em Disparados</p>

    <!-- criar -->
    <div class="card p-4">
      <h2 class="text-sm font-semibold text-gray-200 mb-3">
        <span class="text-accent-yellow">◆</span> Novo alerta
      </h2>
      <form @submit.prevent="create" class="flex flex-wrap items-end gap-3">
        <label class="text-xs text-gray-500 block">
          Mercado
          <select v-model="form.market" class="form-select !py-1.5 text-xs mt-1 block">
            <option value="crypto">Cripto</option>
            <option value="tradfi">Tradicional</option>
          </select>
        </label>
        <label class="text-xs text-gray-500 block">
          Símbolo
          <input v-model="form.symbol" :placeholder="form.market === 'crypto' ? 'BTC' : 'AAPL, OURO...'" required
                 class="form-input !py-1.5 text-xs w-28 uppercase mt-1 block" />
        </label>
        <label class="text-xs text-gray-500 block">
          Condição
          <select v-model="form.kind" class="form-select !py-1.5 text-xs mt-1 block">
            <option value="price_above">Preço acima de</option>
            <option value="price_below">Preço abaixo de</option>
            <option v-if="form.market === 'crypto'" value="funding_above">Funding acima de</option>
            <option v-if="form.market === 'crypto'" value="funding_below">Funding abaixo de</option>
            <option value="signal_score_above">Score multifator acima de</option>
            <option value="signal_score_below">Score multifator abaixo de</option>
          </select>
        </label>
        <label class="text-xs text-gray-500 block">
          Nível {{ form.kind.startsWith('funding') ? '(fração, ex.: 0.0005)' : '($)' }}
          <input v-model.number="form.level" type="number" step="any" required
                 class="form-input !py-1.5 text-xs w-32 mt-1 block" />
        </label>
        <label class="text-xs text-gray-500 block flex-1 min-w-40">
          Nota (opcional)
          <input v-model="form.note" class="form-input !py-1.5 text-xs w-full mt-1 block" />
        </label>
        <button type="submit" class="btn-primary !py-1.5 text-xs">Criar alerta</button>
      </form>
      <p v-if="error" class="text-xs text-red-400 mt-2">{{ error }}</p>
    </div>

    <!-- ativos -->
    <div class="card p-4">
      <h2 class="text-sm font-semibold text-gray-200 mb-3">
        <span class="text-accent-yellow">◆</span> Ativos ({{ active.length }})
      </h2>
      <table v-if="active.length" class="w-full text-xs font-mono">
        <tbody>
          <tr v-for="a in active" :key="a.id" class="border-b border-surface-600/50">
            <td class="py-1.5 font-bold text-gray-100">{{ a.symbol }}
              <span v-if="a.market === 'tradfi'" class="ml-1 text-[9px] font-mono px-1 py-0.5
                    rounded bg-blue-900/40 text-blue-300 border border-blue-800/50">TRAD</span></td>
            <td class="py-1.5 text-gray-400">{{ terminal.kindLabel(a.kind) }} {{ a.level }}</td>
            <td class="py-1.5 text-gray-600">{{ a.note }}</td>
            <td class="py-1.5 text-gray-600">{{ tsFmt(a.created_at) }}</td>
            <td class="py-1.5 text-right">
              <button @click="terminal.removeAlert(a.id)"
                      class="text-gray-600 hover:text-red-400">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="text-xs text-gray-600">nenhum alerta ativo — checagem a cada 30s no servidor</p>
    </div>

    <!-- disparados -->
    <div class="card p-4">
      <h2 class="text-sm font-semibold text-gray-200 mb-3">
        <span class="text-accent-yellow">◆</span> Disparados ({{ triggered.length }})
      </h2>
      <table v-if="triggered.length" class="w-full text-xs font-mono">
        <tbody>
          <tr v-for="a in triggered" :key="a.id" class="border-b border-surface-600/50">
            <td class="py-1.5 font-bold text-accent-yellow">{{ a.symbol }}</td>
            <td class="py-1.5 text-gray-400">{{ terminal.kindLabel(a.kind) }} {{ a.level }}</td>
            <td class="py-1.5 text-gray-300">{{ a.trigger_value != null ? 'disparou em ' + a.trigger_value : a.note }}</td>
            <td class="py-1.5 text-gray-600">{{ tsFmt(a.triggered_at) }}</td>
            <td class="py-1.5 text-right">
              <button @click="terminal.removeAlert(a.id)"
                      class="text-gray-600 hover:text-red-400">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="text-xs text-gray-600">nenhum disparo ainda</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTerminalStore } from '@/stores/terminal.js'

const terminal = useTerminalStore()
const route = useRoute()
const error = ref(null)

const form = reactive({ symbol: '', kind: 'price_above', level: null, note: '', market: 'crypto' })

// tradfi não tem funding — reseta a condição se trocar de mercado
watch(() => form.market, (m) => {
  if (m === 'tradfi' && form.kind.startsWith('funding')) form.kind = 'price_above'
})

const active = computed(() => terminal.alerts.filter((a) => a.active))
const triggered = computed(() =>
  [...terminal.alerts.filter((a) => a.triggered_at)]
    .sort((a, b) => b.triggered_at - a.triggered_at))

async function create() {
  error.value = null
  try {
    const res = await terminal.addAlert({ ...form, symbol: form.symbol.toUpperCase() })
    if (res.error) { error.value = res.error; return }
    form.level = null
    form.note = ''
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
}

function tsFmt(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  terminal.fetchAlerts()
  terminal.markAlertsSeen()
  // pré-preenche vindo do Monitor ("⏰" na linha)
  if (route.query.symbol) form.symbol = String(route.query.symbol).toUpperCase()
  if (route.query.price) form.level = Number(route.query.price)
  if (route.query.market) form.market = String(route.query.market)
})
</script>
