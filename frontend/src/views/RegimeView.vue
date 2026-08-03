<template>
  <WorkspaceShell width="18rem">
    <template #sidebar>
      <RegimeSidebar />
    </template>

    <!-- Main content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">

      <!-- Error -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
        {{ store.error }}
      </div>

      <!-- Empty state -->
      <div v-if="!store.hasResults && !store.isRunning" class="flex flex-col items-center justify-center h-64 text-center">
        <p class="text-gray-400 text-sm">Configure os parâmetros e clique em "Detectar Regimes"</p>
        <p class="text-gray-500 text-xs mt-2">HMM classifica o mercado em estados (bull/bear/sideways) baseado em retornos e volatilidade</p>
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
            <div class="text-xs text-gray-400 mb-0.5">Estados</div>
            <div class="text-sm font-semibold text-gray-200">{{ store.results.n_states }}</div>
          </div>
          <div class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
            <div class="text-xs text-gray-400 mb-0.5">Barras analisadas</div>
            <div class="text-sm font-semibold text-gray-200">{{ store.results.dates.length }}</div>
          </div>
          <div v-if="store.symbolLabel" class="bg-surface-800 rounded-lg px-4 py-3 text-center flex-1 min-w-24 border border-surface-600">
            <div class="text-xs text-gray-400 mb-0.5">Ativo</div>
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
</WorkspaceShell>
</template>

<script setup>

import { useRegimeStore } from '@/stores/regime.js'
import RegimeSidebar from '@/components/regime/RegimeSidebar.vue'
import RegimeCharts from '@/components/regime/RegimeCharts.vue'
import WorkspaceShell from '@/components/layout/WorkspaceShell.vue'

const store = useRegimeStore()
</script>
