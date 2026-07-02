<template>
  <div class="flex h-[calc(100vh-3.5rem)]">
    <!-- Sidebar: lista + form -->
    <aside class="w-80 shrink-0 border-r border-surface-500 bg-surface-800 overflow-y-auto p-4 space-y-4">
      <div class="flex items-center justify-between">
        <h1 class="text-sm font-semibold text-gray-200">Automação</h1>
        <button
          @click="store.showForm = !store.showForm"
          class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-accent-yellow/15 text-accent-yellow hover:bg-accent-yellow/25 transition-colors"
        >{{ store.showForm ? 'fechar' : '+ novo' }}</button>
      </div>

      <!-- Status do runner -->
      <div class="flex items-center gap-2 text-[11px]"
           :class="runnerOk ? 'text-gray-500' : 'text-red-400'">
        <span class="w-1.5 h-1.5 rounded-full"
              :class="runnerOk ? 'bg-accent-yellow animate-pulse' : 'bg-red-500'" />
        <span v-if="runnerOk">
          runner ativo · {{ store.runnerStatus?.active_count ?? 0 }} rodando
          <template v-if="store.runnerStatus?.clock_skew_ms != null">
            · skew {{ store.runnerStatus.clock_skew_ms }}ms
          </template>
        </span>
        <span v-else>runner parado (inicia com o 1º deployment)</span>
      </div>

      <NewDeploymentForm v-if="store.showForm" />
      <DeploymentList />
    </aside>

    <!-- Detalhe -->
    <main class="flex-1 overflow-y-auto p-5">
      <DeploymentDetail />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useAutomationStore } from '@/stores/automation.js'
import DeploymentList from '@/components/automation/DeploymentList.vue'
import DeploymentDetail from '@/components/automation/DeploymentDetail.vue'
import NewDeploymentForm from '@/components/automation/NewDeploymentForm.vue'

const store = useAutomationStore()
const runnerOk = computed(() => store.runnerStatus?.alive)

onMounted(() => {
  store.fetchStrategies()
  store.startPolling()
  // veio de "Enviar para Automação"? abre o form pré-preenchido
  if (store.pendingDeployment) store.showForm = true
})
onUnmounted(() => store.stopPolling())
</script>
