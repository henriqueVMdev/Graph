<template>
  <div class="space-y-2">
    <div
      v-for="d in store.deployments"
      :key="d.id"
      @click="store.select(d.id)"
      class="p-3 rounded-xl border cursor-pointer transition-colors"
      :class="store.selectedId === d.id
        ? 'border-accent-yellow/50 bg-accent-yellow/5'
        : 'border-surface-500 bg-surface-700 hover:border-surface-300'"
    >
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-200 font-medium truncate">{{ d.name }}</span>
        <span
          class="text-[11px] px-1.5 py-0.5 rounded-md font-semibold uppercase"
          :class="badgeClass(d)"
        >{{ d.status }}</span>
      </div>
      <div class="flex items-center justify-between mt-1.5 text-xs text-gray-400">
        <span class="flex items-center gap-1.5">
          {{ d.symbol }} · {{ d.interval }} ·
          <span v-if="d.mode === 'real'"
                class="text-[11px] px-1.5 py-px rounded bg-accent-red/15 text-accent-red-light font-semibold">
            REAL · {{ d.account }}
          </span>
          <template v-else>{{ d.mode }}</template>
        </span>
        <span :class="(d.return_pct ?? 0) >= 0 ? 'text-accent-yellow' : 'text-accent-red-light'">
          {{ d.return_pct != null ? (d.return_pct >= 0 ? '+' : '') + d.return_pct + '%' : '—' }}
        </span>
      </div>
      <div v-if="d.open_position" class="mt-1 flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-accent-yellow animate-pulse" />
        <span class="text-[11px] text-accent-yellow/80">posição aberta</span>
      </div>
      <div v-if="d.error" class="mt-1 text-[11px] text-accent-red-light truncate">{{ d.error }}</div>
    </div>

    <div v-if="!store.deployments.length" class="text-xs text-gray-500 text-center py-6">
      Nenhum deployment. Crie um aqui ou envie uma estratégia validada
      pelo Backtesting / Prop Challenge.
    </div>
  </div>
</template>

<script setup>
import { useAutomationStore } from '@/stores/automation.js'

const store = useAutomationStore()

function badgeClass(d) {
  if (d.status === 'running') return 'bg-accent-yellow/15 text-accent-yellow'
  if (d.status === 'error') return 'bg-accent-red/15 text-accent-red-light'
  if (d.status === 'stopped') return 'bg-surface-500 text-gray-400'
  return 'bg-surface-500 text-gray-400'
}
</script>
