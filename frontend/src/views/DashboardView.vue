<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Sidebar -->
    <DashSidebar
      class="shrink-0 transition-all duration-300 overflow-hidden"
      :class="sidebarOpen ? 'w-64' : 'w-0'"
    />

    <!-- Toggle button -->
    <button
      @click="toggleSidebar"
      class="absolute top-1/2 -translate-y-1/2 z-20 w-4 h-10 flex items-center justify-center rounded-r-md bg-surface-700/60 hover:bg-surface-600/80 border-y border-r border-surface-500/50 text-gray-600 hover:text-gray-300 transition-all duration-300"
      :style="sidebarOpen ? 'left: calc(16rem - 1px)' : 'left: 0'"
      :title="sidebarOpen ? 'Recolher' : 'Expandir'"
    >
      <svg class="w-2.5 h-2.5 transition-transform duration-300" :class="sidebarOpen ? '' : 'rotate-180'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
      </svg>
    </button>

    <!-- Main content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Error alert -->
      <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm flex items-center gap-2">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        {{ store.error }}
      </div>

      <!-- No data placeholder -->
      <div v-if="!store.hasData && !store.loading" class="flex flex-col items-center justify-center h-64 text-center">
        <svg class="w-12 h-12 text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0120 9.414V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-400 text-sm">Faça upload de um CSV ou selecione um arquivo na sidebar</p>
      </div>

      <!-- Data loaded -->
      <template v-if="store.hasData">
        <!-- Summary metrics -->
        <SummaryMetrics />

        <!-- Scatter charts tabs -->
        <div class="card p-4">
          <ScatterTabs />
        </div>

        <!-- Strategy table -->
        <div class="card p-4">
          <h2 class="text-sm font-semibold text-gray-200 mb-3">Top <span class="text-accent-yellow">{{ store.filters.top_n }}</span> Parâmetros</h2>
          <StrategyTable />
        </div>

        <!-- Strategy detail panel -->
        <Transition name="slide-fade">
          <div v-if="store.selectedDetail" class="card p-4">
            <StrategyDetail />
          </div>
        </Transition>

        <!-- Best params -->
        <div class="card p-4">
          <BestParams />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const sidebarOpen = ref(true)
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
  setTimeout(() => window.dispatchEvent(new Event('resize')), 310)
}
import { useDashboardStore } from '@/stores/dashboard.js'
import DashSidebar from '@/components/dashboard/DashSidebar.vue'
import SummaryMetrics from '@/components/dashboard/SummaryMetrics.vue'
import ScatterTabs from '@/components/dashboard/ScatterTabs.vue'
import StrategyTable from '@/components/dashboard/StrategyTable.vue'
import StrategyDetail from '@/components/dashboard/StrategyDetail.vue'
import BestParams from '@/components/dashboard/BestParams.vue'

const store = useDashboardStore()

onMounted(() => {
  store.loadFileList()
})
</script>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
