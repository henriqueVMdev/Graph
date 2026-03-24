<template>
  <aside class="bg-surface-800 border-r border-surface-500 flex flex-col h-full overflow-y-auto">
    <div class="p-4 space-y-5">
      <!-- Header -->
      <div>
        <h2 class="sidebar-section-title">Dados</h2>

        <!-- Upload CSV -->
        <label class="block mb-2">
          <span class="text-xs text-gray-400 mb-1 block">Upload CSV</span>
          <input
            type="file"
            accept=".csv"
            @change="onFileUpload"
            class="block w-full text-xs text-gray-400
                   file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0
                   file:text-xs file:font-medium file:bg-surface-500 file:text-gray-200
                   hover:file:bg-surface-400 cursor-pointer"
          />
        </label>

        <!-- Ou selecionar arquivo existente -->
        <div v-if="store.files.length > 0">
          <span class="text-xs text-gray-500 block mb-1">Ou selecionar arquivo:</span>
          <select v-model="selectedFile" @change="onSelectFile" class="form-select w-full">
            <option value="">-- selecione --</option>
            <option v-for="f in store.files" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>

        <!-- Asset indicator -->
        <div v-if="store.asset" class="mt-2 text-xs text-gray-400">
          <span class="text-gray-500">Ativo:</span>
          <span class="ml-1 font-semibold text-gray-200">{{ store.asset }}</span>
        </div>
      </div>

      <!-- Filters section -->
      <div v-if="store.hasData">
        <h2 class="sidebar-section-title">Filtros</h2>

        <!-- Min Trades -->
        <div class="mb-3">
          <label class="text-xs text-gray-400 block mb-1">Min Trades</label>
          <NumInput
            :model-value="localFilters.min_trades"
            @change="updateFilter('min_trades', $event)"
            :min="0"
            :step="1"
          />
        </div>

        <!-- Min Sharpe -->
        <div class="mb-3">
          <label class="text-xs text-gray-400 block mb-1">Min Sharpe</label>
          <NumInput
            :model-value="localFilters.min_sharpe"
            @change="updateFilter('min_sharpe', $event)"
            :step="0.1"
          />
        </div>

        <!-- Retorno range -->
        <div class="mb-3">
          <label class="text-xs text-gray-400 block mb-1">
            Retorno (%):
            <span class="font-mono text-gray-300">
              {{ fmt(localFilters.return_min) }} → {{ fmt(localFilters.return_max) }}
            </span>
          </label>
          <div class="flex gap-2">
            <NumInput
              :model-value="localFilters.return_min"
              @change="updateFilter('return_min', $event)"
              :step="1"
            />
            <NumInput
              :model-value="localFilters.return_max"
              @change="updateFilter('return_max', $event)"
              :step="1"
            />
          </div>
        </div>

        <!-- Top-N -->
        <div class="mb-3">
          <label class="text-xs text-gray-400 block mb-1">
            Top-N: <span class="font-mono text-gray-300">{{ localFilters.top_n }}</span>
          </label>
          <input
            type="range"
            :value="localFilters.top_n"
            @input="updateFilter('top_n', +$event.target.value)"
            min="5" max="100" step="5"
            class="w-full accent-accent-yellow"
          />
        </div>

        <!-- Count badge -->
        <div class="text-xs text-gray-500 mt-2">
          <span class="text-gray-400 font-semibold">{{ store.filteredCount }}</span>
          parâmetros filtrados
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'
import NumInput from '@/components/NumInput.vue'

const store = useDashboardStore()
const selectedFile = ref('')

// Cópia local dos filtros para evitar update a cada keystroke
const localFilters = computed(() => store.filters)

function fmt(val) {
  if (val === null || val === undefined) return '-'
  return Number(val).toFixed(1)
}

async function onFileUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  selectedFile.value = ''
  await store.loadCsv(file)
}

async function onSelectFile() {
  if (!selectedFile.value) return
  await store.loadCsv(selectedFile.value)
}

function updateFilter(key, value) {
  store.applyFilters({ [key]: value })
}
</script>
