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
          <label class="text-xs text-gray-400 block mb-1">Ativo</label>
          <select v-model="selectedKey" @change="onAssetChange" class="form-select w-full mb-2 text-xs">
            <option value="">-- selecione --</option>
            <optgroup v-for="(items, cat) in store.assets" :key="cat" :label="cat">
              <option v-for="(ticker, label) in items" :key="ticker" :value="`${label}|||${ticker}`">
                {{ label }}
              </option>
            </optgroup>
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

      <!-- ── Botão Run ───────────────────────────────────────────────── -->
      <button
        @click="store.runBacktest()"
        :disabled="store.isRunning || !store.selectedStrategy"
        class="btn-primary w-full py-2.5 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <svg v-if="store.isRunning" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
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
const selectedKey = ref('')
const timeframes = ['1d', '1h', '4h', '1wk', '1mo']

function onStrategyChange(file) {
  const strat = store.strategies.find(s => s.file === file)
  if (strat) store.selectStrategy(strat)
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
