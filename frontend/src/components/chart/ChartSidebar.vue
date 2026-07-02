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
        </template>
      </div>

      <!-- ── Dados ───────────────────────────────────────────────────── -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Dados</p>

        <label class="text-xs text-gray-400 block mb-1">Corretora (candles)</label>
        <select v-model="store.exchange" class="form-select w-full mb-2 text-xs">
          <option value="bybit">Bybit</option>
          <option value="hyperliquid">Hyperliquid</option>
          <option value="binance">Binance</option>
          <option value="okx">OKX</option>
        </select>

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

      <!-- ── Parâmetros dinâmicos (schema da estratégia) ─────────────── -->
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

      <!-- ── Botão Carregar ──────────────────────────────────────────── -->
      <button
        @click="store.fetchChart()"
        :disabled="store.loading || !store.selectedSymbol"
        class="btn-primary w-full py-2.5 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <span v-if="store.loading" class="dollar-loader-sm">$</span>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 13h4l3 8 4-16 3 8h4" />
        </svg>
        {{ store.loading ? 'Carregando...' : 'Carregar gráfico' }}
      </button>

    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useChartStore } from '@/stores/chart.js'
import { useWorkspaceStore } from '@/stores/workspace.js'
import NumInput from '@/components/NumInput.vue'

const store = useChartStore()
const selectedCategory = ref('')
const selectedKey = ref('')
const timeframes = ['15m', '30m', '1h', '2h', '4h', '1d', '1wk', '1mo']

// Pré-seleciona os dropdowns com o ativo escolhido em outra página
const ws = useWorkspaceStore()
watch(() => store.assets, (a) => {
  if (selectedKey.value || !store.selectedSymbol) return
  const hit = ws.findAsset(a, store.selectedSymbol)
  if (hit) {
    selectedCategory.value = hit.category
    selectedKey.value = `${hit.label}|||${hit.ticker}`
  }
}, { immediate: true })

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
