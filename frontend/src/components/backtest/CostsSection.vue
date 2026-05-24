<template>
  <div class="space-y-4">
    <!-- Controles -->
    <div class="flex flex-wrap items-end gap-3">
      <div>
        <label class="text-xs text-gray-400 block mb-1">Símbolo CCXT (swap)</label>
        <input
          v-model="store.costsConfig.symbol"
          :placeholder="store.inferCcxtSymbol()"
          class="form-input text-xs w-40 bg-surface-700 border border-surface-500 rounded-lg px-2 py-1.5 text-gray-200"
        />
      </div>

      <div>
        <label class="text-xs text-gray-400 block mb-1">Exchanges</label>
        <div class="flex gap-1.5">
          <button
            v-for="ex in allExchanges" :key="ex"
            @click="toggleExchange(ex)"
            class="px-2 py-1 text-xs rounded-md border transition-colors capitalize"
            :class="store.costsConfig.exchanges.includes(ex)
              ? 'bg-accent-yellow text-black border-accent-yellow font-semibold'
              : 'bg-surface-600 text-gray-400 border-surface-500 hover:border-gray-400'"
          >{{ ex }}</button>
        </div>
      </div>

      <div>
        <label class="text-xs text-gray-400 block mb-1">Cenários</label>
        <div class="flex gap-1.5">
          <button
            v-for="sc in allScenarios" :key="sc"
            @click="toggleScenario(sc)"
            class="px-2 py-1 text-xs rounded-md border transition-colors capitalize"
            :class="store.costsConfig.scenarios.includes(sc)
              ? 'bg-accent-yellow text-black border-accent-yellow font-semibold'
              : 'bg-surface-600 text-gray-400 border-surface-500 hover:border-gray-400'"
          >{{ sc }}</button>
        </div>
      </div>

      <label class="flex items-center gap-2 cursor-pointer pb-1.5">
        <input type="checkbox" v-model="store.costsConfig.use_funding" class="w-3.5 h-3.5 accent-accent-yellow" />
        <span class="text-xs text-gray-300">Baixar funding (CCXT)</span>
      </label>

      <button
        @click="store.runCosts()"
        :disabled="store.costsLoading || !hasTrades"
        class="btn-primary px-4 py-1.5 text-xs font-semibold disabled:opacity-50"
      >
        {{ store.costsLoading ? 'Calculando...' : 'Calcular custos' }}
      </button>
    </div>

    <p v-if="!hasTrades" class="text-xs text-gray-500">
      Rode um backtest com sizing (alavancagem/quantidade) definido para custear os trades.
    </p>

    <div v-if="store.costsError" class="card p-3 border-accent-red text-accent-red-light text-xs">
      {{ store.costsError }}
    </div>

    <div v-for="w in store.costsWarnings" :key="w" class="text-xs text-amber-400">⚠ {{ w }}</div>

    <!-- Tabela bruto vs líquido -->
    <div v-if="store.costsResult && store.costsResult.length" class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="text-gray-400 border-b border-surface-500">
            <th class="text-left py-2 px-2">Exchange</th>
            <th class="text-left py-2 px-2">Cenário</th>
            <th class="text-right py-2 px-2">PnL Bruto</th>
            <th class="text-right py-2 px-2">PnL Líquido</th>
            <th class="text-right py-2 px-2">Fees</th>
            <th class="text-right py-2 px-2">Funding</th>
            <th class="text-right py-2 px-2">Sharpe Bruto</th>
            <th class="text-right py-2 px-2">Sharpe Líq.</th>
            <th class="text-right py-2 px-2">Δ Sharpe</th>
            <th class="text-center py-2 px-2">Sobrevive?</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(r, i) in store.costsResult" :key="i"
            class="border-b border-surface-700 hover:bg-surface-700/40"
          >
            <td class="py-2 px-2 text-gray-200 capitalize">{{ r.Exchange }}</td>
            <td class="py-2 px-2 text-gray-400 capitalize">{{ r['Cenário'] }}</td>
            <td class="py-2 px-2 text-right" :class="num(r['PnL Bruto']) >= 0 ? 'text-green-400' : 'text-red-400'">{{ money(r['PnL Bruto']) }}</td>
            <td class="py-2 px-2 text-right font-semibold" :class="num(r['PnL Líquido']) >= 0 ? 'text-green-400' : 'text-red-400'">{{ money(r['PnL Líquido']) }}</td>
            <td class="py-2 px-2 text-right text-red-400">−{{ money(Math.abs(num(r.Fees))) }}</td>
            <td class="py-2 px-2 text-right" :class="num(r.Funding) >= 0 ? 'text-green-400' : 'text-red-400'">{{ money(r.Funding) }}</td>
            <td class="py-2 px-2 text-right text-gray-300">{{ fmt2(r['Sharpe Bruto']) }}</td>
            <td class="py-2 px-2 text-right text-gray-200">{{ fmt2(r['Sharpe Líquido']) }}</td>
            <td class="py-2 px-2 text-right" :class="num(r['Δ Sharpe']) >= 0 ? 'text-green-400' : 'text-red-400'">{{ fmt2(r['Δ Sharpe']) }}</td>
            <td class="py-2 px-2 text-center">
              <span :class="r['Sobrevive?'] ? 'text-green-400' : 'text-red-400 font-semibold'">
                {{ r['Sobrevive?'] ? 'Sim' : 'Não' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="text-[11px] text-gray-500 mt-2">
        Sobrevive = PnL líquido &gt; 0 e Sharpe líquido &gt; 0. Default taker nas duas pontas;
        o cenário pessimista usa funding × 1,5 + slippage. Custos sobre o notional alavancado.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'

const store = useBacktestStore()
const allExchanges = ['binance', 'bybit', 'okx']
const allScenarios = ['realista', 'pessimista']

const hasTrades = computed(() => (store.results?.trades || []).length > 0)

function toggleExchange(ex) {
  const arr = store.costsConfig.exchanges
  const i = arr.indexOf(ex)
  if (i >= 0) { if (arr.length > 1) arr.splice(i, 1) } else arr.push(ex)
}
function toggleScenario(sc) {
  const arr = store.costsConfig.scenarios
  const i = arr.indexOf(sc)
  if (i >= 0) { if (arr.length > 1) arr.splice(i, 1) } else arr.push(sc)
}

const num = (v) => (v == null ? 0 : Number(v))
const money = (v) => v == null ? '—' : `$${num(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const fmt2 = (v) => v == null ? '—' : num(v).toFixed(2)
</script>
