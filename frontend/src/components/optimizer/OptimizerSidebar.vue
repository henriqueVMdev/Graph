<template>
  <aside class="h-full bg-surface-800 border-r border-surface-500 overflow-y-auto p-4 space-y-4 text-sm">
    <!-- Estrategia -->
    <section>
      <h3 class="sidebar-title">Estrategia</h3>
      <div v-if="store.strategies.length === 0" class="text-xs text-gray-500 py-2">
        Nenhuma estrategia encontrada em strategies/
      </div>
      <template v-else>
        <select
          :value="store.selectedStrategy?.file"
          @change="onStrategyChange($event.target.value)"
          class="input-field mb-2"
        >
          <option
            v-for="s in store.strategies"
            :key="s.file"
            :value="s.file"
            :disabled="!!s.error"
          >{{ s.name }}</option>
        </select>
        <p v-if="store.selectedStrategy?.description" class="text-xs text-gray-500 leading-relaxed mb-2">
          {{ store.selectedStrategy.description }}
        </p>
      </template>
    </section>

    <!-- Fonte de dados -->
    <section>
      <h3 class="sidebar-title">Dados</h3>
      <div class="flex gap-2 mb-3">
        <button
          class="flex-1 btn-sm"
          :class="store.dataSource === 'asset' ? 'btn-active' : 'btn-inactive'"
          @click="store.dataSource = 'asset'"
        >Ativo</button>
        <button
          class="flex-1 btn-sm"
          :class="store.dataSource === 'csv' ? 'btn-active' : 'btn-inactive'"
          @click="store.dataSource = 'csv'"
        >CSV</button>
      </div>

      <template v-if="store.dataSource === 'asset'">
        <label class="label">Categoria</label>
        <select v-model="store.selectedCategory" class="input-field mb-2">
          <option v-for="cat in Object.keys(store.assets)" :key="cat" :value="cat">{{ cat }}</option>
        </select>

        <label class="label">Ativo</label>
        <select v-model="selectedAssetKey" class="input-field mb-2">
          <option value="">Selecione...</option>
          <option v-for="(ticker, name) in categoryAssets" :key="ticker" :value="name">{{ name }}</option>
        </select>

        <label class="label">Timeframe</label>
        <select v-model="store.interval" class="input-field mb-2">
          <option v-for="tf in ['1d', '1h', '4h', '1wk', '1mo']" :key="tf" :value="tf">{{ tf }}</option>
        </select>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="label">Inicio</label>
            <input type="date" v-model="store.startDate" class="input-field" />
          </div>
          <div>
            <label class="label">Fim</label>
            <input type="date" v-model="store.endDate" class="input-field" />
          </div>
        </div>
      </template>

      <template v-else>
        <label class="label">Upload CSV</label>
        <input type="file" accept=".csv" @change="onFileChange" class="input-field text-xs" />
      </template>
    </section>

    <!-- Grid -->
    <section>
      <h3 class="sidebar-title">Grid de Parametros</h3>
      <label class="label">Modo</label>
      <select v-model="store.gridMode" class="input-field mb-2" @change="store.useCustomGrid = false">
        <option v-for="mode in gridModes" :key="mode" :value="mode">{{ mode }}</option>
      </select>

      <label class="flex items-center gap-2 text-gray-400 mb-2 cursor-pointer">
        <input type="checkbox" v-model="store.useCustomGrid" class="accent-accent-yellow" />
        Personalizar grid
      </label>

      <template v-if="store.useCustomGrid && schemaFields.length > 0">
        <div v-for="field in schemaFields" :key="field.key" class="mb-3">
          <label class="label">{{ field.label }}</label>

          <!-- select: toggle buttons for each option -->
          <div v-if="field.type === 'select'" class="flex flex-wrap gap-1">
            <button
              v-for="opt in field.options" :key="opt"
              class="tag text-xs"
              :class="(store.customGrid[field.key] || []).includes(opt) ? 'tag-active' : 'tag-inactive'"
              @click="toggleArrayItem(field.key, opt)"
            >{{ opt }}</button>
          </div>

          <!-- checkbox: ON/OFF toggles -->
          <div v-else-if="field.type === 'checkbox'" class="flex gap-1">
            <button
              v-for="v in [true, false]" :key="String(v)"
              class="tag"
              :class="(store.customGrid[field.key] || []).includes(v) ? 'tag-active' : 'tag-inactive'"
              @click="toggleArrayItem(field.key, v)"
            >{{ v ? 'ON' : 'OFF' }}</button>
          </div>

          <!-- number: min/max/step range -->
          <div v-else-if="field.type === 'number'" class="space-y-1">
            <div class="grid grid-cols-3 gap-1">
              <input type="number" v-model.number="ranges[field.key].min" class="input-field" placeholder="min" />
              <input type="number" v-model.number="ranges[field.key].max" class="input-field" placeholder="max" />
              <input type="number" v-model.number="ranges[field.key].step" class="input-field" placeholder="step" />
            </div>
            <div class="text-xs text-gray-600">
              {{ (store.customGrid[field.key] || []).length }} valores
            </div>
          </div>
        </div>
      </template>

      <div v-else-if="store.useCustomGrid && schemaFields.length === 0" class="text-xs text-gray-500">
        Estrategia sem schema de parametros
      </div>
    </section>

    <!-- Backtest config -->
    <section>
      <h3 class="sidebar-title">Configuracao</h3>
      <label class="label">Capital Inicial</label>
      <input type="number" v-model.number="store.capital" class="input-field mb-2" />

      <label class="label">Min Trades</label>
      <input type="number" v-model.number="store.minTrades" class="input-field mb-2" />

      <label class="label">Rankear por</label>
      <select v-model="store.rankBy" class="input-field mb-2">
        <option v-for="r in ['Score','Retorno (%)','Sharpe','Profit Factor','Win Rate (%)']" :key="r" :value="r">{{ r }}</option>
      </select>

      <label class="label">Top-N</label>
      <input type="number" v-model.number="store.topN" min="5" max="200" class="input-field mb-2" />
    </section>

    <!-- Combo count + run -->
    <section>
      <div class="flex items-center justify-between text-gray-400 mb-2">
        <span>Combinacoes:</span>
        <span class="font-bold text-gray-200">{{ store.comboCount.toLocaleString() }}</span>
      </div>
      <div v-if="store.comboCount > 50000" class="text-accent-red-light text-xs mb-2">
        Muitas combinacoes! Pode demorar bastante.
      </div>
      <button
        @click="store.run()"
        :disabled="store.isRunning || store.comboCount === 0"
        class="w-full py-2.5 rounded-lg font-semibold text-sm transition-all duration-200"
        :class="store.isRunning ? 'bg-surface-600 text-gray-500 cursor-wait' : 'bg-accent-yellow text-surface-900 hover:bg-accent-yellow/90'"
      >
        {{ store.isRunning ? 'Otimizando...' : 'Rodar Otimizacao' }}
      </button>
    </section>
  </aside>
</template>

<script setup>
import { ref, computed, watch, reactive, onMounted } from 'vue'
import { useOptimizerStore } from '@/stores/optimizer.js'

const store = useOptimizerStore()

// Grid modes disponiveis
const gridModes = computed(() => {
  const modes = Object.keys(store.availableGrids)
  return modes.length > 0 ? modes : ['rapido', 'completo', 'custom']
})

// Schema fields da estrategia selecionada (flat list)
const schemaFields = computed(() => {
  const schema = store.selectedStrategy?.schema || []
  const fields = []
  for (const section of schema) {
    for (const field of (section.fields || [])) {
      fields.push(field)
    }
  }
  return fields
})

// Ranges para campos numericos (min/max/step)
const ranges = reactive({})

watch(schemaFields, (fields) => {
  for (const field of fields) {
    if (field.type === 'number' && !ranges[field.key]) {
      const def = field.default ?? 0
      ranges[field.key] = {
        min: def,
        max: def,
        step: field.step || 1,
      }
    }
  }
}, { immediate: true })

// Quando ranges mudam, atualiza o customGrid com os valores gerados
watch(ranges, () => {
  for (const field of schemaFields.value) {
    if (field.type !== 'number') continue
    const r = ranges[field.key]
    if (!r) continue
    const arr = []
    const step = Math.max(r.step || 1, 0.001)
    for (let v = r.min; v <= r.max + step * 0.01; v += step) {
      arr.push(Math.round(v * 1000) / 1000)
    }
    if (arr.length === 0) arr.push(r.min)
    store.customGrid[field.key] = arr
  }
}, { deep: true })

// Strategy change
function onStrategyChange(file) {
  const strat = store.strategies.find(s => s.file === file)
  if (strat) store.selectStrategy(strat)
}

// Selected asset
const selectedAssetKey = ref('')
const categoryAssets = computed(() => store.assets[store.selectedCategory] || {})

watch(selectedAssetKey, (name) => {
  const ticker = categoryAssets.value[name]
  if (ticker) {
    store.selectedAssetLabel = name
    store.selectedSymbol = ticker
  }
})

// File change
function onFileChange(e) {
  store.csvFile = e.target.files[0] || null
}

// Toggle array item helper
function toggleArrayItem(key, item) {
  if (!store.customGrid[key]) store.customGrid[key] = []
  const arr = store.customGrid[key]
  const idx = arr.indexOf(item)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(item)
}

// Update combo count when grid changes
let countTimer = null
watch(() => store.activeGrid, () => {
  clearTimeout(countTimer)
  countTimer = setTimeout(() => store.updateComboCount(), 300)
}, { deep: true })

onMounted(() => {
  store.updateComboCount()
})
</script>

<style scoped>
.sidebar-title {
  @apply text-xs font-bold text-gray-400 uppercase tracking-wider mb-2;
}
.label {
  @apply block text-xs text-gray-500 mb-1;
}
.input-field {
  @apply w-full bg-surface-700 border border-surface-500 rounded-md px-2.5 py-1.5 text-sm text-gray-200 outline-none focus:border-accent-yellow/50 transition;
}
.btn-sm {
  @apply px-3 py-1.5 rounded-md text-xs font-medium transition;
}
.btn-active {
  @apply bg-accent-yellow/15 text-accent-yellow border border-accent-yellow/30;
}
.btn-inactive {
  @apply bg-surface-700 text-gray-500 border border-surface-500 hover:text-gray-300;
}
.tag {
  @apply px-2 py-1 rounded text-xs font-medium transition cursor-pointer;
}
.tag-active {
  @apply bg-accent-yellow/15 text-accent-yellow border border-accent-yellow/30;
}
.tag-inactive {
  @apply bg-surface-700 text-gray-500 border border-surface-500 hover:text-gray-300;
}
</style>
