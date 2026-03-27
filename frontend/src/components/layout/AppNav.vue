<template>
  <nav class="h-14 bg-surface-800 border-b border-surface-500 flex items-center px-5 gap-6 shrink-0">

    <!-- Nav links -->
    <div class="flex items-center gap-1">
      <RouterLink
        to="/dashboard"
        class="nav-link"
        :class="{ active: route.path === '/dashboard' }"
      >
        Parametros
      </RouterLink>
      <RouterLink
        to="/backtest"
        class="nav-link"
        :class="{ active: route.path === '/backtest' }"
      >
        Backtesting
      </RouterLink>
      <RouterLink
        to="/optimizer"
        class="nav-link"
        :class="{ active: route.path === '/optimizer' }"
      >
        Otimizador
      </RouterLink>
      <RouterLink
        to="/prop-challenge"
        class="nav-link"
        :class="{ active: route.path === '/prop-challenge' }"
      >
        Prop Challenge
      </RouterLink>
    </div>

    <!-- Spacer -->
    <div class="flex-1" />

    <!-- Status indicator -->
    <div v-if="dashStore.loading || btStore.isRunning || optStore.isRunning || propStore.isRunning" class="flex items-center gap-2 text-xs text-accent-yellow/80">
      <span class="dollar-loader-sm">$</span>
      {{ propStore.isRunning ? 'Simulando prop...' : optStore.isRunning ? 'Otimizando...' : btStore.isRunning ? 'Executando backtest...' : 'Carregando...' }}
    </div>

    <!-- Live dot -->
    <div v-if="btStore.isRunning" class="flex items-center gap-1.5">
      <span class="w-2 h-2 rounded-full bg-accent-yellow animate-pulse" />
      <span class="text-xs text-accent-yellow/70 font-medium tracking-wide">LIVE</span>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard.js'
import { useBacktestStore } from '@/stores/backtest.js'
import { useOptimizerStore } from '@/stores/optimizer.js'
import { usePropChallengeStore } from '@/stores/propChallenge.js'

const route = useRoute()
const dashStore = useDashboardStore()
const btStore = useBacktestStore()
const optStore = useOptimizerStore()
const propStore = usePropChallengeStore()
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 rounded-lg
         hover:text-gray-200 hover:bg-surface-600 transition-all duration-150 font-medium;
}
.nav-link.active {
  @apply text-accent-yellow bg-accent-yellow/10;
}
</style>
