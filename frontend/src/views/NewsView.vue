<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">Notícias Cripto</h1>
      <span class="text-[10px] text-gray-600 font-mono">RSS agregado · atualiza 5 min</span>
      <div class="flex-1" />
      <select v-model="sourceFilter" class="form-select !py-1 text-xs">
        <option value="">Todas as fontes</option>
        <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <div v-if="terminal.newsFailed.length" class="text-[11px] text-amber-300 bg-amber-900/20 rounded-lg p-2 border border-amber-800/50">
      ⚠ Fontes indisponíveis agora: {{ terminal.newsFailed.join(', ') }}
    </div>

    <div v-if="terminal.newsLoading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Buscando notícias...</p>
    </div>

    <div v-else class="card divide-y divide-surface-600/50">
      <a v-for="n in items" :key="n.link" :href="n.link" target="_blank" rel="noopener"
         class="flex items-baseline gap-3 px-4 py-2.5 hover:bg-surface-600/40 transition-colors group">
        <span class="text-[10px] font-mono w-16 shrink-0 text-gray-600">{{ rel(n.ts) }}</span>
        <span class="text-[10px] font-mono w-24 shrink-0 uppercase tracking-wide"
              :class="SOURCE_COLORS[n.source] || 'text-gray-500'">{{ n.source }}</span>
        <span class="text-sm text-gray-300 group-hover:text-gray-100 leading-snug">{{ n.title }}</span>
      </a>
      <div v-if="!items.length" class="text-center text-xs text-gray-600 py-10">
        nenhuma notícia carregada
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useTerminalStore } from '@/stores/terminal.js'

const terminal = useTerminalStore()
const sourceFilter = ref('')

const SOURCE_COLORS = {
  CoinDesk: 'text-accent-yellow/80',
  Cointelegraph: 'text-blue-400/80',
  Decrypt: 'text-purple-400/80',
  Livecoins: 'text-green-400/80',
}

const sources = computed(() =>
  [...new Set(terminal.newsItems.map((n) => n.source))])

const items = computed(() =>
  sourceFilter.value
    ? terminal.newsItems.filter((n) => n.source === sourceFilter.value)
    : terminal.newsItems)

function rel(ts) {
  if (!ts) return '—'
  const m = Math.max(0, Math.round((Date.now() - ts) / 60000))
  if (m < 60) return `${m}min`
  const h = Math.round(m / 60)
  if (h < 48) return `${h}h`
  return `${Math.round(h / 24)}d`
}

onMounted(() => terminal.startNewsPolling())
onBeforeUnmount(() => terminal.stopNewsPolling())
</script>
