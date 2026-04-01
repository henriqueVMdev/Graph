<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <RegimeSidebar
      class="shrink-0 transition-all duration-300 overflow-hidden"
      :class="sidebarOpen ? 'w-72' : 'w-0'"
    />

    <!-- Toggle button -->
    <button
      @click="toggleSidebar"
      class="absolute top-1/2 -translate-y-1/2 z-20 w-4 h-10 flex items-center justify-center rounded-r-md bg-surface-700/60 hover:bg-surface-600/80 border-y border-r border-surface-500/50 text-gray-600 hover:text-gray-300 transition-all duration-300"
      :style="sidebarOpen ? 'left: calc(18rem - 1px)' : 'left: 0'"
      :title="sidebarOpen ? 'Recolher' : 'Expandir'"
    >
      <svg class="w-2.5 h-2.5 transition-transform duration-300" :class="sidebarOpen ? '' : 'rotate-180'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
      </svg>
    </button>

    <!-- Main content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">

      <!-- Error -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- Empty state -->
      <div v-if="!store.hasResults && !store.isRunning" class="flex flex-col items-center justify-center h-64 text-center">
        <p class="text-gray-400 text-sm">Configure os parâmetros e clique em "Detectar Regimes"</p>
        <p class="text-gray-600 text-xs mt-2">HMM classifica o mercado em estados (bull/bear/sideways) baseado em retornos e volatilidade</p>
      </div>

      <!-- Running spinner -->
      <div v-if="store.isRunning" class="flex flex-col items-center justify-center h-64">
        <div class="dollar-loader mb-3">$</div>
        <p class="text-gray-400 text-sm">Detectando regimes de mercado...</p>
      </div>

      <!-- Results -->
      <template v-if="store.hasResults && !store.isRunning">
        <!-- Header info -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="bg-surface-800 rounded-xl px-5 py-3 text-center min-w-28 border border-surface-600">
            <div class="text-xs text-gray-400 mb-0.5">Método</div>
            <div class="text-lg font-bold text-accent-yellow">{{ store.results.method.toUpperCase() }}</div>
          </div>
          <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
            <div class="text-xs text-gray-500 mb-0.5">Estados</div>
            <div class="text-sm font-semibold text-gray-200">{{ store.results.n_states }}</div>
          </div>
          <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
            <div class="text-xs text-gray-500 mb-0.5">Barras analisadas</div>
            <div class="text-sm font-semibold text-gray-200">{{ store.results.dates.length }}</div>
          </div>
          <div v-if="store.symbolLabel" class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
            <div class="text-xs text-gray-500 mb-0.5">Ativo</div>
            <div class="text-sm font-semibold text-gray-200">{{ store.symbolLabel }}</div>
          </div>
        </div>

        <!-- Charts section -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">
            <span class="text-accent-yellow">◆</span> Regime Detection
          </h2>
          <RegimeCharts />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRegimeStore } from '@/stores/regime.js'
import RegimeSidebar from '@/components/regime/RegimeSidebar.vue'
import RegimeCharts from '@/components/regime/RegimeCharts.vue'

const store = useRegimeStore()
const sidebarOpen = ref(true)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}
</script>
