<template>
  <aside class="bg-surface-800 border-r border-surface-500 flex flex-col h-full overflow-y-auto">
    <div class="p-4 space-y-5">

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
            <option v-for="tf in timeframes" :key="tf.value" :value="tf.value">{{ tf.label }}</option>
          </select>
        </template>

        <!-- CSV upload -->
        <template v-else>
          <label class="block">
            <span class="text-xs text-gray-400 mb-1 block">Upload CSV (OHLCV)</span>
            <input
              type="file"
              accept=".csv"
              @change="onCsvFile"
              class="block w-full text-xs text-gray-400
                     file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0
                     file:text-xs file:font-medium file:bg-surface-500 file:text-gray-200
                     hover:file:bg-surface-400 cursor-pointer"
            />
          </label>
          <p class="text-[10px] text-gray-600 mt-1">CSV deve ter colunas: Date, Open, High, Low, Close, Volume</p>
        </template>
      </div>

      <!-- ── Configuração ────────────────────────────────────────────── -->
      <div class="sidebar-section">
        <p class="sidebar-section-title">Configuração</p>

        <label class="text-xs text-gray-400 block mb-1">Método</label>
        <select v-model="store.method" class="form-select w-full text-xs mb-3">
          <option value="hmm">HMM (sklearn + Viterbi)</option>
          <option value="markov_switching">Markov Switching (statsmodels)</option>
          <option value="changepoint">Change-Point Detection</option>
        </select>

        <template v-if="store.method !== 'changepoint'">
          <label class="text-xs text-gray-400 block mb-1">
            Nº de Estados
            <span class="text-gray-600">(0 = auto via BIC)</span>
          </label>
          <select v-model.number="store.nStates" class="form-select w-full text-xs mb-3">
            <option :value="0">Automático (BIC)</option>
            <option :value="2">2 (Bull / Bear)</option>
            <option :value="3">3 (Bull / Bear / Sideways)</option>
            <option :value="4">4 estados</option>
            <option :value="5">5 estados</option>
          </select>
        </template>

        <label class="text-xs text-gray-400 block mb-1">Features</label>
        <div class="space-y-1 mb-3">
          <label v-for="f in featureOptions" :key="f.value" class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
            <input type="checkbox" :value="f.value" v-model="store.features" class="accent-accent-yellow" />
            {{ f.label }}
          </label>
        </div>

        <label class="text-xs text-gray-400 block mb-1">
          Janela Volatilidade: <span class="font-mono text-gray-300">{{ store.volWindow }}</span>
        </label>
        <input
          type="range"
          v-model.number="store.volWindow"
          min="5" max="60" step="5"
          class="w-full accent-accent-yellow"
        />
      </div>

      <!-- ── Executar ────────────────────────────────────────────────── -->
      <button
        @click="onRun"
        :disabled="store.isRunning || !canRun"
        class="w-full py-2.5 rounded-lg text-sm font-bold transition-colors"
        :class="store.isRunning || !canRun
          ? 'bg-surface-600 text-gray-500 cursor-not-allowed'
          : 'bg-accent-yellow text-black hover:bg-yellow-400'"
      >
        <template v-if="store.isRunning">
          <span class="dollar-loader-sm mr-1">$</span> Detectando...
        </template>
        <template v-else>Detectar Regimes</template>
      </button>

    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRegimeStore } from '@/stores/regime.js'

const store = useRegimeStore()
const selectedCategory = ref('')
const selectedKey = ref('')
const csvFile = ref(null)

const timeframes = [
  { value: '15m', label: '15 min' },
  { value: '30m', label: '30 min' },
  { value: '1h', label: '1 hora' },
  { value: '2h', label: '2 horas' },
  { value: '4h', label: '4 horas' },
  { value: '1d', label: 'Diário' },
  { value: '1wk', label: 'Semanal' },
]

const featureOptions = [
  { value: 'log_return', label: 'Log Return' },
  { value: 'volatility', label: 'Volatilidade Realizada' },
  { value: 'volume', label: 'Volume (log)' },
]

const canRun = computed(() => {
  if (store.dataSource === 'csv') return csvFile.value != null
  return store.symbol !== ''
})

function onCategoryChange() {
  selectedKey.value = ''
  store.symbol = ''
  store.symbolLabel = ''
}

function onAssetChange() {
  if (!selectedKey.value) return
  const [label, ticker] = selectedKey.value.split('|||')
  store.symbolLabel = label
  store.symbol = ticker
}

function onCsvFile(e) {
  csvFile.value = e.target.files?.[0] || null
}

function onRun() {
  store.run(store.dataSource === 'csv' ? csvFile.value : null)
}

onMounted(() => {
  store.fetchAssets()
})
</script>
