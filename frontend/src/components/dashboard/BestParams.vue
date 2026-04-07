<template>
  <div>
    <h2 class="text-sm font-semibold text-gray-200 mb-1"><span class="text-accent-yellow">◆</span>
      Melhores Parâmetros (Top {{ store.filters.top_n }})
    </h2>
    <p class="text-xs text-gray-500 mb-4">Baseado nos parâmetros com melhor Score para orientar futuros backtests.</p>

    <div v-if="!bestParams || (!hasCategorical && !hasNumeric)" class="text-gray-500 text-sm text-center py-6">
      Sem dados suficientes para análise
    </div>

    <template v-else>
      <!-- Categóricos -->
      <div v-if="hasCategorical">
        <p class="sidebar-section-title mb-3">Parâmetros Categóricos — Frequência</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
          <div
            v-for="(data, key) in bestParams.categorical"
            :key="key"
            class="card p-3"
          >
            <p class="text-xs text-gray-400 mb-2">{{ data.label }}</p>
            <div class="space-y-1.5">
              <div
                v-for="(count, val) in sortedCounts(data.counts)"
                :key="val"
                class="flex items-center gap-2"
              >
                <div class="flex-1 min-w-0 h-2.5 bg-surface-600 rounded-sm overflow-hidden">
                  <div
                    class="h-full bg-accent-yellow rounded-sm transition-all"
                    :style="{ width: barWidth(count, data.counts) }"
                  ></div>
                </div>
                <span class="text-xs text-gray-300 shrink-0 max-w-[5rem] truncate text-right">{{ val }}</span>
                <span class="text-xs text-gray-500 shrink-0 w-5 text-right tabular-nums">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Numéricos -->
      <div v-if="hasNumeric">
        <p class="sidebar-section-title mb-3">Parâmetros Numéricos — Distribuição</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
          <div
            v-for="(data, key) in bestParams.numeric"
            :key="key"
            class="card p-3"
          >
            <p class="text-xs text-gray-400 mb-1">{{ data.label }}</p>
            <p class="text-sm font-mono text-gray-200 font-semibold">
              {{ fmtNum(data.median) }}
              <span class="text-xs text-gray-500 font-normal ml-1">mediana</span>
            </p>
            <p class="text-xs text-gray-500 mt-0.5">
              Q25: {{ fmtNum(data.q25) }} — Q75: {{ fmtNum(data.q75) }}
            </p>
            <!-- Mini histogram bars -->
            <div class="flex items-end gap-0.5 mt-2 h-8">
              <div
                v-for="(h, i) in histBuckets(data.values, 8)"
                :key="i"
                class="bg-accent-yellow/40 hover:bg-accent-yellow/70 rounded-sm transition-colors flex-1"
                :style="{ height: h + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary table -->
      <div v-if="bestParams.summary_table?.length">
        <div class="flex items-center justify-between mb-2">
          <p class="sidebar-section-title">Faixas Recomendadas</p>
          <button
            @click="sendToOptimizer()"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/30 hover:bg-green-500/20 transition"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
            Enviar para Otimizador
          </button>
        </div>
        <div class="overflow-x-auto rounded-lg border border-surface-500">
          <table class="w-full text-xs">
            <thead>
              <tr class="bg-surface-600 text-gray-400 text-left">
                <th class="px-3 py-2 font-medium">Parâmetro</th>
                <th class="px-3 py-2 font-medium">Melhor Valor</th>
                <th class="px-3 py-2 font-medium">Frequência no Top</th>
                <th class="px-3 py-2 font-medium">Faixa Sugerida</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in bestParams.summary_table"
                :key="i"
                class="border-b border-surface-500 last:border-0"
              >
                <td class="px-3 py-2 text-gray-300 font-medium">{{ row.Parametro }}</td>
                <td class="px-3 py-2 text-gray-200 font-mono">{{ row['Melhor Valor'] }}</td>
                <td class="px-3 py-2 text-accent-yellow">{{ row['Frequencia no Top'] }}</td>
                <td class="px-3 py-2 text-gray-400">{{ row['Faixa Sugerida'] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard.js'
import { useOptimizerStore } from '@/stores/optimizer.js'

const store = useDashboardStore()
const optimizerStore = useOptimizerStore()
const router = useRouter()
const bestParams = computed(() => store.bestParams)

async function sendToOptimizer() {
  const ok = await optimizerStore.loadRangesFromDashboard(bestParams.value.summary_table)
  if (ok) {
    router.push('/optimizer')
  }
}
const hasCategorical = computed(() => bestParams.value && Object.keys(bestParams.value.categorical || {}).length > 0)
const hasNumeric = computed(() => bestParams.value && Object.keys(bestParams.value.numeric || {}).length > 0)

function sortedCounts(counts) {
  return Object.fromEntries(
    Object.entries(counts).sort(([, a], [, b]) => b - a)
  )
}

function barWidth(count, counts) {
  const max = Math.max(...Object.values(counts))
  const pct = max > 0 ? Math.round((count / max) * 100) : 0
  return `${Math.max(pct, 4)}%`
}

function fmtNum(v) {
  if (v == null) return '-'
  return Number(v).toFixed(2)
}

function histBuckets(values, n = 8) {
  if (!values || values.length === 0) return Array(n).fill(0)
  const clean = values.filter(v => v != null)
  if (clean.length === 0) return Array(n).fill(0)
  const min = Math.min(...clean)
  const max = Math.max(...clean)
  if (min === max) return Array(n).fill(50)
  const size = (max - min) / n
  const buckets = Array(n).fill(0)
  for (const v of clean) {
    const i = Math.min(Math.floor((v - min) / size), n - 1)
    buckets[i]++
  }
  const maxB = Math.max(...buckets)
  return buckets.map(b => maxB > 0 ? Math.max(Math.round((b / maxB) * 100), 5) : 5)
}
</script>
