<template>
  <div class="rounded-xl border p-4" :class="borderClass">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500">
        Live vs Backtest
      </h3>
      <span class="text-[10px] px-2 py-0.5 rounded-md font-semibold uppercase" :class="badgeClass">
        {{ verdictLabel }}
      </span>
    </div>

    <div class="grid grid-cols-3 gap-3 text-center">
      <div>
        <div class="text-[10px] text-gray-500 uppercase">Trades</div>
        <div class="text-lg text-gray-200 font-semibold">{{ c.n_trades ?? 0 }}</div>
      </div>
      <div>
        <div class="text-[10px] text-gray-500 uppercase">WR realizada</div>
        <div class="text-lg font-semibold" :class="wrClass">
          {{ c.realized_wr != null ? c.realized_wr + '%' : '—' }}
        </div>
      </div>
      <div>
        <div class="text-[10px] text-gray-500 uppercase">WR esperada</div>
        <div class="text-lg text-gray-400 font-semibold">
          {{ c.expected_wr != null ? c.expected_wr + '%' : '—' }}
        </div>
      </div>
    </div>

    <p v-if="c.detail" class="mt-3 text-[11px] leading-snug" :class="detailClass">
      {{ c.detail }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  comparison: { type: Object, default: () => ({}) },
})

const c = computed(() => props.comparison || {})
const verdict = computed(() => c.value.verdict || 'insufficient')

const verdictLabel = computed(() => ({
  ok: 'compatível',
  warn: 'atenção',
  invalidated: 'INVALIDADA',
  insufficient: 'amostra insuf.',
}[verdict.value] || verdict.value))

const badgeClass = computed(() => ({
  ok: 'bg-accent-yellow/15 text-accent-yellow',
  warn: 'bg-orange-500/15 text-orange-400',
  invalidated: 'bg-red-500/20 text-red-400',
  insufficient: 'bg-surface-500 text-gray-400',
}[verdict.value]))

const borderClass = computed(() => ({
  ok: 'border-surface-500 bg-surface-700',
  warn: 'border-orange-500/40 bg-orange-500/5',
  invalidated: 'border-red-500/50 bg-red-500/5',
  insufficient: 'border-surface-500 bg-surface-700',
}[verdict.value]))

const wrClass = computed(() => {
  if (verdict.value === 'invalidated') return 'text-red-400'
  if (verdict.value === 'warn') return 'text-orange-400'
  return 'text-gray-200'
})

const detailClass = computed(() =>
  verdict.value === 'invalidated' ? 'text-red-400'
    : verdict.value === 'warn' ? 'text-orange-400' : 'text-gray-500')
</script>
