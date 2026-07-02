<template>
  <nav class="h-14 bg-surface-800/90 backdrop-blur border-b border-surface-500 flex items-center px-4 gap-4 shrink-0 sticky top-0 z-40">

    <!-- Marca -->
    <RouterLink to="/" class="flex items-center gap-2.5 pr-2 group">
      <div class="w-7 h-7 rounded-md bg-accent-yellow text-black font-extrabold text-sm
                  flex items-center justify-center shadow-yellow-glow-sm
                  group-hover:shadow-yellow-glow transition-shadow">G</div>
      <div class="leading-none hidden lg:block">
        <div class="text-[13px] font-bold tracking-wide text-gray-100">GRAPH</div>
        <div class="text-[9px] text-gray-600 uppercase tracking-[0.2em]">quant lab</div>
      </div>
    </RouterLink>

    <div class="w-px h-6 bg-surface-500 hidden md:block" />

    <!-- Nav links -->
    <div class="flex items-center gap-0.5 overflow-x-auto">
      <RouterLink
        v-for="item in NAV"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ active: route.path === item.to }"
      >
        <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 shrink-0" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round"
             stroke-linejoin="round" v-html="item.icon" />
        <span class="hidden xl:inline">{{ item.label }}</span>
      </RouterLink>
    </div>

    <div class="flex-1" />

    <!-- Status de execução -->
    <div v-if="busyLabel" class="flex items-center gap-2 text-xs text-accent-yellow/80 shrink-0">
      <span class="dollar-loader-sm">$</span>
      <span class="hidden md:inline">{{ busyLabel }}</span>
    </div>

    <!-- Relógio de sessão (UTC + Brasília) -->
    <div class="hidden md:flex items-center gap-3 font-mono text-[11px] leading-none shrink-0">
      <div class="text-right">
        <div class="text-gray-300">{{ clockUtc }} <span class="text-gray-600">UTC</span></div>
        <div class="text-gray-500">{{ clockBrt }} <span class="text-gray-700">BRT</span></div>
      </div>
      <!-- Janela de entrada 19h-00h BRT da estratégia validada -->
      <div class="flex items-center gap-1.5 px-2 py-1 rounded-md border"
           :class="inWindow
             ? 'border-accent-yellow/40 bg-accent-yellow/10 text-accent-yellow'
             : 'border-surface-500 bg-surface-700 text-gray-600'"
           title="Janela de entrada da estratégia validada: 19:00-00:00 Brasília">
        <span class="w-1.5 h-1.5 rounded-full"
              :class="inWindow ? 'bg-accent-yellow animate-pulse' : 'bg-gray-600'" />
        <span class="text-[10px] font-semibold tracking-wide">19-00h</span>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard.js'
import { useBacktestStore } from '@/stores/backtest.js'
import { useOptimizerStore } from '@/stores/optimizer.js'
import { usePropChallengeStore } from '@/stores/propChallenge.js'
import { useRegimeStore } from '@/stores/regime.js'

const route = useRoute()
const dashStore = useDashboardStore()
const btStore = useBacktestStore()
const optStore = useOptimizerStore()
const propStore = usePropChallengeStore()
const regimeStore = useRegimeStore()

// Ícones estilo feather (conteúdo interno do <svg>)
const NAV = [
  { to: '/dashboard', label: 'Parâmetros',
    icon: '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>' },
  { to: '/backtest', label: 'Backtesting',
    icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
  { to: '/grafico', label: 'Gráfico',
    icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { to: '/optimizer', label: 'Otimizador',
    icon: '<circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/>' },
  { to: '/prop-challenge', label: 'Prop Challenge',
    icon: '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>' },
  { to: '/regime', label: 'Regimes',
    icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  { to: '/journal', label: 'Diário',
    icon: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>' },
  { to: '/automation', label: 'Automação',
    icon: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>' },
]

const busyLabel = computed(() => {
  if (regimeStore.isRunning) return 'Detectando regimes...'
  if (propStore.isRunning) return 'Simulando prop...'
  if (optStore.isRunning) return 'Otimizando...'
  if (btStore.isRunning) return 'Executando backtest...'
  if (dashStore.loading) return 'Carregando...'
  return ''
})

// ── Relógio de sessão ──────────────────────────────────────────────
const clockUtc = ref('')
const clockBrt = ref('')
const inWindow = ref(false)
let clockTimer = null

function tick() {
  const now = new Date()
  const pad = (v) => String(v).padStart(2, '0')
  clockUtc.value = `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`
  const brtH = (now.getUTCHours() + 21) % 24 // UTC-3
  clockBrt.value = `${pad(brtH)}:${pad(now.getUTCMinutes())}`
  // Janela de entrada validada: 19:00-00:00 BRT = 22:00-03:00 UTC
  const h = now.getUTCHours()
  inWindow.value = h >= 22 || h < 3
}

onMounted(() => { tick(); clockTimer = setInterval(tick, 1000) })
onBeforeUnmount(() => clearInterval(clockTimer))
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-1.5 px-2.5 py-1.5 text-[13px] text-gray-500 rounded-lg
         hover:text-gray-200 hover:bg-surface-600 transition-all duration-150 font-medium
         whitespace-nowrap;
}
.nav-link.active {
  @apply text-accent-yellow bg-accent-yellow/10;
}
</style>
