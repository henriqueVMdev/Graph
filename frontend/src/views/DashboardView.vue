<template>
  <WorkspaceShell width="16rem">
    <template #sidebar>
      <DashSidebar />
    </template>

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
        <p class="text-gray-400 text-sm">Faca upload de um CSV ou selecione um arquivo na sidebar</p>
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
</WorkspaceShell>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.js'
import DashSidebar from '@/components/dashboard/DashSidebar.vue'
import SummaryMetrics from '@/components/dashboard/SummaryMetrics.vue'
import ScatterTabs from '@/components/dashboard/ScatterTabs.vue'
import StrategyTable from '@/components/dashboard/StrategyTable.vue'
import StrategyDetail from '@/components/dashboard/StrategyDetail.vue'
import BestParams from '@/components/dashboard/BestParams.vue'
import WorkspaceShell from '@/components/layout/WorkspaceShell.vue'

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
