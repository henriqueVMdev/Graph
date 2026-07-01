<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <ChartSidebar
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
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Toolbar -->
      <div class="h-12 shrink-0 border-b border-surface-600 bg-surface-800/60 flex items-center gap-4 px-4">
        <!-- Renderer toggle -->
        <div class="flex rounded-lg overflow-hidden border border-surface-500 text-xs">
          <button
            class="px-3 py-1.5 font-medium transition-colors"
            :class="store.renderer === 'tv' ? 'bg-accent-yellow text-black' : 'text-gray-400 hover:text-gray-200'"
            @click="store.renderer = 'tv'"
          >TradingView</button>
          <button
            class="px-3 py-1.5 font-medium transition-colors"
            :class="store.renderer === 'plotly' ? 'bg-accent-yellow text-black' : 'text-gray-400 hover:text-gray-200'"
            @click="store.renderer = 'plotly'"
          >Plotly</button>
        </div>

        <!-- Overlay toggles -->
        <div class="flex items-center gap-3">
          <label v-for="o in overlayDefs" :key="o.key" class="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" v-model="store.overlays[o.key]" class="w-3.5 h-3.5 accent-accent-yellow" />
            <span class="text-xs text-gray-400">{{ o.label }}</span>
          </label>
        </div>

        <div class="flex-1" />

        <!-- Asset label -->
        <span v-if="store.chartData" class="text-xs text-gray-300 font-medium">
          {{ store.chartData.symbol }} · {{ store.chartData.interval }}
        </span>
      </div>

      <!-- Chart area -->
      <div class="flex-1 relative overflow-hidden">
        <div v-if="store.loading" class="absolute inset-0 flex flex-col items-center justify-center">
          <div class="dollar-loader mb-3">$</div>
          <p class="text-gray-400 text-sm">Buscando candles e aplicando a estratégia...</p>
        </div>

        <div v-else-if="store.error" class="absolute inset-0 flex items-center justify-center p-6">
          <div class="text-sm text-red-400 bg-red-900/20 rounded-lg p-3 border border-red-800 max-w-lg">
            {{ store.error }}
          </div>
        </div>

        <ChartCanvas v-else-if="store.chartData" class="absolute inset-0" />

        <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
          <p class="text-gray-400 text-sm">Escolha o ativo, o timeframe e a estratégia, e clique em <span class="text-accent-yellow font-semibold">"Carregar gráfico"</span>.</p>
          <p class="text-gray-600 text-xs mt-2">Você verá candles, indicadores e os marcadores de trade da estratégia — com stop e alvo.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChartStore } from '@/stores/chart.js'
import ChartSidebar from '@/components/chart/ChartSidebar.vue'
import ChartCanvas from '@/components/chart/ChartCanvas.vue'

const store = useChartStore()

const overlayDefs = [
  { key: 'indicators', label: 'Indicadores' },
  { key: 'markers', label: 'Marcadores' },
  { key: 'stops', label: 'Stop/Alvo' },
  { key: 'volume', label: 'Volume' },
]

const sidebarOpen = ref(true)
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}

onMounted(async () => {
  await Promise.all([store.fetchAssets(), store.fetchStrategies()])
})
</script>
