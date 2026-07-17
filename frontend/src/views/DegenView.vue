<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">

    <!-- Header / controls -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-lg font-bold text-gray-100">
        <span class="text-accent-yellow">◆</span> Degenerado
      </h1>

      <!-- Chain tabs -->
      <div class="flex items-center gap-1 bg-surface-800 rounded-lg p-1 border border-surface-600">
        <button
          v-for="(label, id) in store.chains"
          :key="id"
          @click="store.setChain(id)"
          class="px-3 py-1 text-xs rounded-md transition-all font-medium"
          :class="store.chain === id
            ? 'bg-accent-yellow/15 text-accent-yellow'
            : 'text-gray-500 hover:text-gray-200'"
        >
          {{ label }}
        </button>
      </div>

      <!-- Kind toggle -->
      <div class="flex items-center gap-1 bg-surface-800 rounded-lg p-1 border border-surface-600">
        <button
          @click="store.setKind('trending')"
          class="px-3 py-1 text-xs rounded-md transition-all font-medium"
          :class="store.kind === 'trending' ? 'bg-accent-yellow/15 text-accent-yellow' : 'text-gray-500 hover:text-gray-200'"
        >
          🔥 Trending
        </button>
        <button
          @click="store.setKind('new')"
          class="px-3 py-1 text-xs rounded-md transition-all font-medium"
          :class="store.kind === 'new' ? 'bg-accent-yellow/15 text-accent-yellow' : 'text-gray-500 hover:text-gray-200'"
        >
          ✨ Novos
        </button>
      </div>

      <div class="flex-1" />

      <!-- Refresh info -->
      <div class="flex items-center gap-3 text-xs text-gray-500">
        <span v-if="store.updatedAt">Atualizado {{ formatTime(store.updatedAt) }}</span>
        <button
          @click="store.toggleAutoRefresh()"
          class="px-2 py-1 rounded-md border border-surface-600 transition-all"
          :class="store.autoRefresh ? 'text-accent-yellow border-accent-yellow/40' : 'text-gray-500'"
          title="Auto-refresh a cada 60s"
        >
          {{ store.autoRefresh ? 'Auto 60s ●' : 'Auto off' }}
        </button>
        <button
          @click="store.fetchTokens()"
          class="px-2 py-1 rounded-md border border-surface-600 text-gray-400 hover:text-gray-200 transition-all"
        >
          ⟳ Atualizar
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="store.error" class="card p-3 border-accent-red text-accent-red-light text-sm">
      {{ store.error }}
    </div>

    <!-- Loading -->
    <div v-if="store.loading && !store.hasTokens" class="flex flex-col items-center justify-center h-64">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Buscando memecoins on-chain...</p>
    </div>

    <!-- Table -->
    <div v-if="store.hasTokens" class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-xs text-gray-500 border-b border-surface-600">
            <th class="text-left px-4 py-2.5 font-medium">#</th>
            <th class="text-left px-4 py-2.5 font-medium">Token</th>
            <th class="text-right px-4 py-2.5 font-medium">Preço</th>
            <th class="text-right px-4 py-2.5 font-medium">5m</th>
            <th class="text-right px-4 py-2.5 font-medium">1h</th>
            <th class="text-right px-4 py-2.5 font-medium">6h</th>
            <th class="text-right px-4 py-2.5 font-medium">24h</th>
            <th class="text-right px-4 py-2.5 font-medium">Vol 24h</th>
            <th class="text-right px-4 py-2.5 font-medium">Liquidez</th>
            <th class="text-right px-4 py-2.5 font-medium">FDV</th>
            <th class="text-right px-4 py-2.5 font-medium">Txns 24h</th>
            <th class="text-right px-4 py-2.5 font-medium">Idade</th>
            <th class="px-2 py-2.5"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(t, i) in store.tokens"
            :key="t.pool_address"
            class="border-b border-surface-700/50 hover:bg-surface-700/30 transition-colors cursor-pointer"
            :class="{ 'bg-accent-yellow/5': store.hypeToken?.pool_address === t.pool_address }"
            @click="store.fetchHype(t)"
          >
            <td class="px-4 py-2.5 text-gray-600">{{ i + 1 }}</td>
            <td class="px-4 py-2.5">
              <div class="flex items-center gap-2">
                <img v-if="t.image_url && t.image_url !== 'missing.png'" :src="t.image_url" class="w-5 h-5 rounded-full" @error="$event.target.style.display='none'" />
                <span class="font-semibold text-gray-100">{{ t.symbol }}</span>
                <span class="text-xs text-gray-500 truncate max-w-36">{{ t.name }}</span>
              </div>
            </td>
            <td class="px-4 py-2.5 text-right font-mono text-gray-200">{{ formatPrice(t.price_usd) }}</td>
            <td class="px-4 py-2.5 text-right font-mono" :class="pctClass(t.change_m5)">{{ formatPct(t.change_m5) }}</td>
            <td class="px-4 py-2.5 text-right font-mono" :class="pctClass(t.change_h1)">{{ formatPct(t.change_h1) }}</td>
            <td class="px-4 py-2.5 text-right font-mono" :class="pctClass(t.change_h6)">{{ formatPct(t.change_h6) }}</td>
            <td class="px-4 py-2.5 text-right font-mono" :class="pctClass(t.change_h24)">{{ formatPct(t.change_h24) }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-gray-300">{{ formatUsd(t.volume_h24) }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-gray-400">{{ formatUsd(t.liquidity_usd) }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-gray-400">{{ formatUsd(t.fdv_usd) }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-xs">
              <span class="text-accent-green">{{ t.buys_h24 ?? '—' }}</span>
              <span class="text-gray-600"> / </span>
              <span class="text-accent-red-light">{{ t.sells_h24 ?? '—' }}</span>
            </td>
            <td class="px-4 py-2.5 text-right text-xs text-gray-500">{{ formatAge(t.created_at) }}</td>
            <td class="px-2 py-2.5 text-right">
              <button
                @click.stop="openDex(t)"
                class="text-gray-600 hover:text-accent-yellow transition-colors"
                title="Abrir no DexScreener"
              >↗</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty -->
    <div v-if="!store.loading && !store.hasTokens && !store.error" class="flex flex-col items-center justify-center h-64 text-center">
      <p class="text-gray-400 text-sm">Nenhum token encontrado nessa chain</p>
    </div>

    <!-- Hype Radar panel -->
    <Teleport to="body">
      <div
        v-if="store.hypeToken"
        class="fixed inset-0 z-40 bg-black/40"
        @click="store.closeHype()"
      />
      <div
        v-if="store.hypeToken"
        class="fixed top-0 right-0 z-50 h-full w-full max-w-md bg-surface-800 border-l border-surface-500 shadow-2xl overflow-y-auto p-5 space-y-4"
      >
        <!-- Panel header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <img v-if="store.hypeToken.image_url && store.hypeToken.image_url !== 'missing.png'" :src="store.hypeToken.image_url" class="w-6 h-6 rounded-full" />
            <h2 class="text-base font-bold text-gray-100">{{ store.hypeToken.symbol }}</h2>
            <span class="text-xs text-gray-500">{{ store.hypeToken.name }}</span>
          </div>
          <button @click="store.closeHype()" class="text-gray-500 hover:text-gray-200 text-lg leading-none">✕</button>
        </div>

        <!-- Loading -->
        <div v-if="store.hypeLoading" class="flex flex-col items-center justify-center h-40">
          <div class="dollar-loader mb-3">$</div>
          <p class="text-gray-400 text-sm">Medindo o hype...</p>
        </div>

        <div v-if="store.hypeError" class="card p-3 border-accent-red text-accent-red-light text-sm">
          {{ store.hypeError }}
        </div>

        <template v-if="store.hype && !store.hypeLoading">
          <!-- Score -->
          <div class="bg-surface-900 rounded-xl p-4 text-center border border-surface-600">
            <div class="text-4xl font-bold" :class="scoreClass(store.hype.score)">{{ store.hype.score }}</div>
            <div class="text-sm font-semibold mt-1" :class="scoreClass(store.hype.score)">{{ store.hype.label }}</div>
            <div class="text-xs text-gray-600 mt-1">Hype score 0–100</div>
          </div>

          <!-- Breakdown -->
          <div class="space-y-2">
            <div v-for="(v, k) in store.hype.breakdown" :key="k">
              <div class="flex justify-between text-xs mb-0.5">
                <span class="text-gray-400">{{ breakdownLabel(k) }}</span>
                <span class="text-gray-300 font-mono">{{ v }}/25</span>
              </div>
              <div class="h-1.5 bg-surface-900 rounded-full overflow-hidden">
                <div class="h-full bg-accent-yellow rounded-full transition-all" :style="{ width: (v / 25 * 100) + '%' }" />
              </div>
            </div>
          </div>

          <!-- Socials -->
          <div v-if="store.hype.socials.length || store.hype.websites.length" class="flex flex-wrap gap-2">
            <a
              v-for="s in store.hype.socials" :key="s.url" :href="s.url" target="_blank"
              class="px-2 py-1 text-xs rounded-md border border-surface-600 text-gray-400 hover:text-accent-yellow transition-colors"
            >{{ s.type || s.label }}</a>
            <a
              v-for="w in store.hype.websites" :key="w.url" :href="w.url" target="_blank"
              class="px-2 py-1 text-xs rounded-md border border-surface-600 text-gray-400 hover:text-accent-yellow transition-colors"
            >{{ w.label || 'site' }}</a>
            <span v-if="store.hype.boosts" class="px-2 py-1 text-xs rounded-md bg-accent-yellow/10 text-accent-yellow">⚡ {{ store.hype.boosts }} boosts</span>
          </div>

          <!-- Tweets -->
          <div>
            <h3 class="text-sm font-semibold text-gray-200 mb-2">
              <span class="text-accent-yellow">◆</span> Social
              <span class="text-xs text-gray-600 font-normal ml-1">({{ twitterSourceLabel }})</span>
            </h3>
            <div v-if="store.hype.tweets.length" class="space-y-2">
              <div v-for="(tw, i) in store.hype.tweets" :key="i" class="bg-surface-900 rounded-lg p-3 border border-surface-700">
                <div class="flex justify-between text-xs text-gray-500 mb-1">
                  <a v-if="tw.url" :href="tw.url" target="_blank" class="font-medium text-gray-400 hover:text-accent-yellow">@{{ tw.user || '?' }}</a>
                  <span v-else class="font-medium text-gray-400">@{{ tw.user || '?' }}</span>
                  <span>{{ tw.created_at }}</span>
                </div>
                <p class="text-xs text-gray-300 leading-relaxed">{{ tw.text }}</p>
                <div class="flex gap-3 mt-1.5 text-xs text-gray-600">
                  <span>♥ {{ tw.likes ?? 0 }}</span>
                  <span>⟳ {{ tw.retweets ?? 0 }}</span>
                  <span v-if="tw.views">👁 {{ tw.views }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-gray-600 leading-relaxed">
              Nenhum post encontrado sobre esse token (nem no Bluesky).
              Isso por si só já é sinal: sem conversa social = hype só on-chain.
            </p>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useDegenStore } from '@/stores/degen.js'

const store = useDegenStore()

onMounted(() => {
  store.fetchChains()
  store.fetchTokens()
  store.startAutoRefresh()
})

onUnmounted(() => store.stopAutoRefresh())

const twitterSourceLabel = computed(() => {
  const s = store.hype?.twitter_source
  if (s === 'twitterapi.io') return 'busca real via twitterapi.io'
  if (s === 'nitter') return 'via Nitter'
  if (s === 'bluesky') return 'via Bluesky'
  return 'indisponível'
})

function scoreClass(score) {
  if (score >= 75) return 'text-accent-green'
  if (score >= 55) return 'text-accent-yellow'
  if (score >= 35) return 'text-orange-400'
  return 'text-accent-red-light'
}

function breakdownLabel(k) {
  return {
    pressao_compradora: 'Pressão compradora (buys vs sells)',
    turnover: 'Turnover (vol 24h / liquidez)',
    aceleracao: 'Aceleração (6h vs 24h)',
    social: 'Sinal social (X / TG / boosts)',
  }[k] || k
}

function openDex(t) {
  const chainSlug = store.chain === 'eth' ? 'ethereum' : store.chain
  window.open(`https://dexscreener.com/${chainSlug}/${t.pool_address}`, '_blank')
}

function formatPrice(v) {
  if (v == null) return '—'
  if (v >= 1) return `$${v.toLocaleString('en-US', { maximumFractionDigits: 4 })}`
  if (v >= 0.0001) return `$${v.toFixed(6)}`
  return `$${v.toExponential(2)}`
}

function formatPct(v) {
  if (v == null) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

function pctClass(v) {
  if (v == null) return 'text-gray-600'
  return v >= 0 ? 'text-accent-green' : 'text-accent-red-light'
}

function formatUsd(v) {
  if (v == null) return '—'
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`
  return `$${v.toFixed(0)}`
}

function formatAge(iso) {
  if (!iso) return '—'
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 60) return `${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

function formatTime(d) {
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>
