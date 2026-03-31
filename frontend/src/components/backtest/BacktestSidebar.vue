<template>
  <aside class="bg-surface-800 border-r border-surface-500 flex flex-col h-full overflow-y-auto">
    <div class="p-4 space-y-5">

      <!-- ── Estratégia ──────────────────────────────────────────────── -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Estratégia</p>

        <div v-if="store.strategies.length === 0" class="text-xs text-gray-500 py-2">
          Nenhuma estratégia encontrada em strategies/
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
            >
              {{ s.name }}{{ s.error ? ' ⚠' : '' }}
            </option>
          </select>

          <p v-if="store.selectedStrategy?.description" class="text-xs text-gray-500 leading-relaxed">
            {{ store.selectedStrategy.description }}
          </p>

          <p v-if="store.selectedStrategy?.error" class="text-xs text-accent-red-light mt-1">
            Erro: {{ store.selectedStrategy.error }}
          </p>
        </template>
      </div>

      <!-- ── Dados ───────────────────────────────────────────────────── -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Dados</p>

        <!-- Fonte de dados toggle -->
        <div class="flex gap-2 mb-3">
          <button
            class="flex-1 py-1.5 text-xs rounded-lg font-medium transition-colors"
            :class="store.dataSource === 'asset' ? 'bg-accent-yellow text-black font-bold' : 'bg-surface-500 text-gray-400'"
            @click="store.dataSource = 'asset'"
          >Lista de Ativos</button>
          <button
            class="flex-1 py-1.5 text-xs rounded-lg font-medium transition-colors"
            :class="store.dataSource === 'csv' ? 'bg-accent-yellow text-black font-bold' : 'bg-surface-500 text-gray-400'"
            @click="store.dataSource = 'csv'"
          >CSV</button>
        </div>

        <!-- Asset selector -->
        <template v-if="store.dataSource === 'asset'">
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
        </template>

        <!-- CSV upload -->
        <template v-else>
          <label class="text-xs text-gray-400 block mb-1">CSV de Preços (Date, Open, High, Low, Close)</label>
          <input
            type="file"
            accept=".csv"
            @change="onCsvUpload"
            class="block w-full text-xs text-gray-400
                   file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0
                   file:text-xs file:font-medium file:bg-surface-500 file:text-gray-200
                   hover:file:bg-surface-400 cursor-pointer"
          />
        </template>
      </div>

      <!-- ── Parâmetros dinâmicos ────────────────────────────────────── -->
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
            v-show="!field.show_if || store.params[field.show_if]"
            class="mb-2"
          >
            <!-- Checkbox -->
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

            <!-- Select -->
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

            <!-- Number -->
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

      <!-- ── Ciclo Sazonal ───────────────────────────────────────────── -->
      <div class="sidebar-section">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            :checked="store.params.cycle_filter"
            @change="store.params.cycle_filter = $event.target.checked"
            class="w-3.5 h-3.5 accent-accent-yellow"
          />
          <span class="sidebar-section-title mb-0">Ciclo Sazonal</span>
        </label>

        <template v-if="store.params.cycle_filter">
          <div class="mt-3 space-y-2">
            <div>
              <p class="text-[10px] text-green-400 font-semibold mb-1">LONG</p>
              <div class="grid grid-cols-6 gap-1">
                <button
                  v-for="m in months"
                  :key="'L' + m.n"
                  @click="toggleMonth('cycle_long_months', m.n)"
                  class="py-1 text-[10px] rounded font-medium transition-colors"
                  :class="isMonthActive('cycle_long_months', m.n)
                    ? 'bg-green-500/30 text-green-300 border border-green-500/50'
                    : 'bg-surface-600 text-gray-500 border border-surface-500'"
                >{{ m.label }}</button>
              </div>
            </div>
            <div>
              <p class="text-[10px] text-red-400 font-semibold mb-1">SHORT</p>
              <div class="grid grid-cols-6 gap-1">
                <button
                  v-for="m in months"
                  :key="'S' + m.n"
                  @click="toggleMonth('cycle_short_months', m.n)"
                  class="py-1 text-[10px] rounded font-medium transition-colors"
                  :class="isMonthActive('cycle_short_months', m.n)
                    ? 'bg-red-500/30 text-red-300 border border-red-500/50'
                    : 'bg-surface-600 text-gray-500 border border-surface-500'"
                >{{ m.label }}</button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ── Walk-Forward Analysis ─────────────────────────────────── -->
      <div class="border-t border-surface-600 pt-3 mt-1">
        <p class="text-xs font-semibold text-gray-300 mb-3">Walk-Forward Analysis</p>

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

        <button
          @click="store.runWfa()"
          :disabled="store.wfaLoading || !store.results"
          class="btn-secondary w-full py-2 text-xs font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span v-if="store.wfaLoading" class="dollar-loader-sm">$</span>
          <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          {{ store.wfaLoading ? 'Calculando...' : 'Executar WFA' }}
        </button>
      </div>

      <!-- ── Botão Run ───────────────────────────────────────────────── -->
      <button
        @click="store.runBacktest()"
        :disabled="store.isRunning || !store.selectedStrategy"
        class="btn-primary w-full py-2.5 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <span v-if="store.isRunning" class="dollar-loader-sm">$</span>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ store.isRunning ? 'Executando...' : 'Executar Backtest' }}
      </button>

    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { useBacktestStore } from '@/stores/backtest.js'
import NumInput from '@/components/NumInput.vue'

const store = useBacktestStore()
const selectedCategory = ref('')
const selectedKey = ref('')
const timeframes = ['15m', '30m', '1h', '2h', '4h', '1d', '1wk', '1mo']

const months = [
  { n: 1, label: 'Jan' }, { n: 2, label: 'Fev' }, { n: 3, label: 'Mar' },
  { n: 4, label: 'Abr' }, { n: 5, label: 'Mai' }, { n: 6, label: 'Jun' },
  { n: 7, label: 'Jul' }, { n: 8, label: 'Ago' }, { n: 9, label: 'Set' },
  { n: 10, label: 'Out' }, { n: 11, label: 'Nov' }, { n: 12, label: 'Dez' },
]

function isMonthActive(key, month) {
  return (store.params[key] || []).includes(month)
}

function toggleMonth(key, month) {
  const arr = [...(store.params[key] || [])]
  const idx = arr.indexOf(month)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(month)
  store.params[key] = arr
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

function onCsvUpload(e) {
  const file = e.target.files?.[0]
  if (file) store.csvFile = file
}

function parseNum(val, field) {
  const n = parseFloat(val)
  if (isNaN(n)) return field.default ?? 0
  // Se step é inteiro ou não tem decimais, retorna inteiro
  if (!field.step || Number.isInteger(field.step)) return Math.round(n)
  return n
}
</script>
