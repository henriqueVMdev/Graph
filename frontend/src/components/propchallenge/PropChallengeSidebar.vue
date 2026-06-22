<template>
  <aside class="bg-surface-800 border-r border-surface-500 flex flex-col h-full overflow-y-auto">
    <div class="p-4 space-y-5">

      <!-- Estrategia -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Estrategia</p>
        <div v-if="store.strategies.length === 0" class="text-xs text-gray-500 py-2">
          Nenhuma estrategia encontrada
        </div>
        <template v-else>
          <select
            :value="store.selectedStrategy?.file"
            @change="onStrategyChange($event.target.value)"
            class="form-select w-full text-xs mb-2"
          >
            <option
              v-for="s in store.strategies"
              :key="s.file"
              :value="s.file"
              :disabled="!!s.error"
            >{{ s.name }}</option>
          </select>
          <p v-if="store.selectedStrategy?.description" class="text-xs text-gray-500 leading-relaxed">
            {{ store.selectedStrategy.description }}
          </p>
        </template>
      </div>

      <!-- Dados -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Ativo</p>

        <label class="text-xs text-gray-400 block mb-1">Categoria</label>
        <select v-model="selectedCategory" @change="onCategoryChange" class="form-select w-full mb-2 text-xs">
          <option value="">Selecione a categoria</option>
          <option v-for="cat in Object.keys(store.assets)" :key="cat" :value="cat">{{ cat }}</option>
        </select>

        <label class="text-xs text-gray-400 block mb-1">Ativo</label>
        <select
          v-model="selectedKey"
          @change="onAssetChange"
          :disabled="!selectedCategory"
          class="form-select w-full mb-2 text-xs"
          :class="!selectedCategory ? 'opacity-40 cursor-not-allowed' : ''"
        >
          <option value="">Selecione o ativo</option>
          <option
            v-for="(ticker, label) in (store.assets[selectedCategory] || {})"
            :key="ticker"
            :value="`${label}|||${ticker}`"
          >{{ label }}</option>
        </select>

        <label class="text-xs text-gray-400 block mb-1">Timeframe</label>
        <select v-model="store.interval" class="form-select w-full text-xs">
          <option v-for="tf in timeframes" :key="tf" :value="tf">{{ tf }}</option>
        </select>
      </div>

      <!-- Conta Prop -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Conta Prop</p>

        <label class="text-xs text-gray-400 block mb-1">Tamanho da Conta (USD)</label>
        <div class="grid grid-cols-3 gap-1.5 mb-3">
          <button
            v-for="size in accountSizes"
            :key="size"
            @click="store.accountSize = size"
            class="py-1.5 text-xs rounded-lg font-medium transition-colors"
            :class="store.accountSize === size
              ? 'bg-accent-yellow text-black font-bold'
              : 'bg-surface-600 text-gray-400 hover:bg-surface-500'"
          >{{ formatK(size) }}</button>
        </div>

        <label class="text-xs text-gray-400 block mb-1">Simulacoes Monte Carlo</label>
        <select v-model.number="store.numSims" class="form-select w-full text-xs">
          <option :value="500">500</option>
          <option :value="1000">1.000</option>
          <option :value="2000">2.000</option>
          <option :value="5000">5.000</option>
        </select>
      </div>

      <!-- Custos da corretora (fees + funding) -->
      <div class="sidebar-section">
        <div class="flex items-center justify-between mb-2">
          <p class="sidebar-section-title mb-0">Custos da Corretora</p>
          <button
            @click="store.costConfig.apply_costs = !store.costConfig.apply_costs"
            class="relative inline-flex h-4 w-8 items-center rounded-full transition-colors"
            :class="store.costConfig.apply_costs ? 'bg-accent-yellow' : 'bg-surface-500'"
          >
            <span
              class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
              :class="store.costConfig.apply_costs ? 'translate-x-4' : 'translate-x-0.5'"
            />
          </button>
        </div>

        <template v-if="store.costConfig.apply_costs">
          <label class="text-xs text-gray-400 block mb-1">Exchange (fees + funding)</label>
          <select v-model="store.costConfig.cost_exchange" class="form-select w-full text-xs mb-2">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
          </select>

          <label class="text-xs text-gray-400 block mb-1">Cenário</label>
          <select v-model="store.costConfig.cost_scenario" class="form-select w-full text-xs mb-2">
            <option value="realista">Realista</option>
            <option value="pessimista">Pessimista (funding 1.5x + slippage)</option>
          </select>

          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              :checked="store.costConfig.use_funding"
              @change="store.costConfig.use_funding = $event.target.checked"
              class="w-3.5 h-3.5 accent-accent-yellow"
            />
            <span class="text-xs text-gray-300">Incluir funding</span>
          </label>
        </template>
      </div>

      <!-- Regras -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Regras do Desafio</p>
        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 bg-surface-700 rounded-lg border border-surface-500">
            <span class="text-gray-400">Fase 1 - Meta</span>
            <span class="text-green-400 font-bold">+10%</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-surface-700 rounded-lg border border-surface-500">
            <span class="text-gray-400">Fase 2 - Meta</span>
            <span class="text-green-400 font-bold">+5%</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-surface-700 rounded-lg border border-surface-500">
            <span class="text-gray-400">Perda Max Total</span>
            <span class="text-red-400 font-bold">-10%</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-surface-700 rounded-lg border border-surface-500">
            <span class="text-gray-400">Perda Max Diaria</span>
            <span class="text-red-400 font-bold">-5%</span>
          </div>
        </div>
      </div>

      <!-- Parametros da estrategia -->
      <template v-if="store.selectedStrategy && !store.selectedStrategy.error">
        <div
          v-for="section in store.selectedStrategy.schema"
          :key="section.title"
          class="sidebar-section"
        >
          <p class="sidebar-section-title">{{ section.title }}</p>
          <div
            v-for="field in section.fields"
            :key="field.key"
            v-show="field.key !== 'initial_capital' && (!field.show_if || store.params[field.show_if])"
            class="mb-2"
          >
            <template v-if="field.type === 'checkbox'">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="store.params[field.key]"
                  @change="store.params[field.key] = $event.target.checked"
                  class="w-3.5 h-3.5 accent-accent-yellow"
                />
                <span class="text-xs text-gray-300">{{ field.label }}</span>
              </label>
            </template>
            <template v-else-if="field.type === 'select'">
              <label class="text-xs text-gray-400 block mb-1">{{ field.label }}</label>
              <select
                :value="store.params[field.key]"
                @change="store.params[field.key] = $event.target.value"
                class="form-select w-full text-xs"
              >
                <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </template>
            <template v-else-if="field.type === 'number'">
              <label class="text-xs text-gray-400 block mb-1">{{ field.label }}</label>
              <NumInput
                :model-value="store.params[field.key]"
                @change="store.params[field.key] = $event"
                :min="field.min ?? -Infinity"
                :max="field.max ?? Infinity"
                :step="field.step ?? 1"
              />
            </template>
          </div>
        </div>
      </template>

      <!-- Botao Simular -->
      <button
        @click="store.runSimulation()"
        :disabled="store.isRunning || !store.selectedStrategy || !store.selectedSymbol"
        class="btn-primary w-full py-2.5 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {{ store.isRunning ? 'Simulando...' : 'Simular Desafio' }}
      </button>

      <!-- ── Forward Testing (Walk-Forward Analysis) ──────────────── -->
      <div class="sidebar-section border-t border-surface-600 pt-4">
        <p class="sidebar-section-title">Forward Testing (WFA)</p>
        <p class="text-[11px] text-gray-500 mb-3 leading-relaxed">
          Valida a estrategia em dados nao vistos: otimiza in-sample e mede o desempenho out-of-sample.
        </p>

        <label class="text-xs text-gray-400 block mb-1">
          Janelas WFA
          <span class="text-accent-yellow font-semibold ml-1">{{ store.wfaConfig.n_windows }}</span>
        </label>
        <input
          type="range"
          v-model.number="store.wfaConfig.n_windows"
          min="5" max="20" step="1"
          class="w-full h-1.5 accent-yellow-400 mb-3"
        />

        <label class="text-xs text-gray-400 block mb-1">
          % In-Sample
          <span class="text-accent-yellow font-semibold ml-1">{{ Math.round(store.wfaConfig.is_pct * 100) }}%</span>
        </label>
        <input
          type="range"
          v-model.number="store.wfaConfig.is_pct"
          min="0.50" max="0.80" step="0.05"
          class="w-full h-1.5 accent-yellow-400 mb-3"
        />

        <!-- Otimizar IS toggle -->
        <div class="flex items-center justify-between mb-3">
          <label class="text-xs text-gray-400">Otimizar IS</label>
          <button
            @click="store.wfaConfig.optimize_is_samples = store.wfaConfig.optimize_is_samples > 0 ? 0 : 40"
            class="relative inline-flex h-4 w-8 items-center rounded-full transition-colors"
            :class="store.wfaConfig.optimize_is_samples > 0 ? 'bg-accent-yellow' : 'bg-surface-500'"
          >
            <span
              class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
              :class="store.wfaConfig.optimize_is_samples > 0 ? 'translate-x-4' : 'translate-x-0.5'"
            />
          </button>
        </div>

        <template v-if="store.wfaConfig.optimize_is_samples > 0">
          <label class="text-xs text-gray-400 block mb-1">
            Amostras IS
            <span class="text-accent-yellow font-semibold ml-1">{{ store.wfaConfig.optimize_is_samples }}</span>
          </label>
          <input
            type="range"
            v-model.number="store.wfaConfig.optimize_is_samples"
            min="20" max="100" step="10"
            class="w-full h-1.5 accent-yellow-400 mb-3"
          />
        </template>

        <!-- Custos reais da corretora no forward test -->
        <div class="flex items-center justify-between mb-3">
          <label class="text-xs text-gray-400">Custos da corretora</label>
          <button
            @click="store.wfaConfig.apply_costs = !store.wfaConfig.apply_costs"
            class="relative inline-flex h-4 w-8 items-center rounded-full transition-colors"
            :class="store.wfaConfig.apply_costs ? 'bg-accent-yellow' : 'bg-surface-500'"
          >
            <span
              class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
              :class="store.wfaConfig.apply_costs ? 'translate-x-4' : 'translate-x-0.5'"
            />
          </button>
        </div>

        <template v-if="store.wfaConfig.apply_costs">
          <label class="text-xs text-gray-500 block mb-1">Exchange (fees + funding)</label>
          <select v-model="store.wfaConfig.cost_exchange" class="form-select w-full text-xs mb-2">
            <option value="binance">Binance</option>
            <option value="bybit">Bybit</option>
            <option value="okx">OKX</option>
          </select>

          <label class="text-xs text-gray-500 block mb-1">Cenário</label>
          <select v-model="store.wfaConfig.cost_scenario" class="form-select w-full text-xs mb-2">
            <option value="realista">Realista</option>
            <option value="pessimista">Pessimista (funding 1.5x + slippage)</option>
          </select>

          <label class="flex items-center gap-2 cursor-pointer mb-3">
            <input
              type="checkbox"
              :checked="store.wfaConfig.use_funding"
              @change="store.wfaConfig.use_funding = $event.target.checked"
              class="w-3.5 h-3.5 accent-accent-yellow"
            />
            <span class="text-xs text-gray-300">Incluir funding</span>
          </label>
        </template>

        <button
          @click="store.runWfa()"
          :disabled="store.wfaLoading || !store.selectedSymbol"
          class="btn-secondary w-full py-2 text-xs font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span v-if="store.wfaLoading" class="dollar-loader-sm">$</span>
          {{ store.wfaLoading ? 'Calculando...' : 'Executar Forward Test' }}
        </button>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { usePropChallengeStore } from '@/stores/propChallenge.js'
import NumInput from '@/components/NumInput.vue'

const store = usePropChallengeStore()
const selectedCategory = ref('')
const selectedKey = ref('')
const timeframes = ['15m', '30m', '1h', '2h', '4h', '1d', '1wk', '1mo']
const accountSizes = [5000, 10000, 25000, 50000, 100000, 200000]

function formatK(n) {
  if (n >= 1000) return `$${n / 1000}k`
  return `$${n}`
}

function onStrategyChange(file) {
  const strat = store.strategies.find(s => s.file === file)
  if (strat) store.selectStrategy(strat)
}

function onCategoryChange() {
  selectedKey.value = ''
  store.selectedAssetLabel = ''
  store.selectedSymbol = ''
}

function onAssetChange() {
  if (!selectedKey.value) return
  const [label, ticker] = selectedKey.value.split('|||')
  store.selectedAssetLabel = label
  store.selectedSymbol = ticker
}
</script>
