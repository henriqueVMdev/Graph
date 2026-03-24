<template>
  <nav class="h-14 bg-surface-800 border-b border-surface-500 flex items-center px-5 gap-6 shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-2.5">
      <div class="w-7 h-7 bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg flex items-center justify-center">
        <svg class="w-4 h-4 text-accent-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4v16" />
        </svg>
      </div>
      <span class="font-bold text-sm tracking-wider text-white">BACK<span class="text-accent-yellow">TEST</span></span>
    </div>

    <!-- Divider -->
    <div class="w-px h-5 bg-surface-500" />

    <!-- Nav links -->
    <div class="flex items-center gap-1">
      <RouterLink
        to="/dashboard"
        class="nav-link"
        :class="{ active: route.path === '/dashboard' }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        Dashboard
      </RouterLink>
      <RouterLink
        to="/backtest"
        class="nav-link"
        :class="{ active: route.path === '/backtest' }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Backtesting Live
      </RouterLink>
      <RouterLink
        to="/optimizer"
        class="nav-link"
        :class="{ active: route.path === '/optimizer' }"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Otimizador
      </RouterLink>
    </div>

    <!-- Spacer -->
    <div class="flex-1" />

    <!-- Status indicator -->
    <div v-if="dashStore.loading || btStore.isRunning || optStore.isRunning" class="flex items-center gap-2 text-xs text-accent-yellow/80">
      <span class="dollar-loader-sm">$</span>
      {{ optStore.isRunning ? 'Otimizando...' : btStore.isRunning ? 'Executando backtest...' : 'Carregando...' }}
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

const route = useRoute()
const dashStore = useDashboardStore()
const btStore = useBacktestStore()
const optStore = useOptimizerStore()
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
