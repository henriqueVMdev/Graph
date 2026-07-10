<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">FA · Análise da Empresa</h1>
      <span class="text-[10px] text-gray-600 font-mono">demonstrações · analistas · donos · dividendos (yahoo)</span>
      <div class="flex-1" />
      <form @submit.prevent="load" class="flex gap-2">
        <input v-model="symbolInput" placeholder="ex.: AAPL, PETR4.SA"
               class="form-input !py-1.5 text-xs w-36 uppercase" />
        <button type="submit" class="btn-secondary !py-1.5 text-xs">Analisar</button>
      </form>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <div v-if="loading" class="flex flex-col items-center py-16">
      <div class="dollar-loader mb-3">$</div>
      <p class="text-gray-400 text-sm">Montando análise de {{ symbolInput.toUpperCase() }} (~10s na primeira vez)...</p>
    </div>

    <template v-else-if="d">
      <!-- header -->
      <div class="card p-5 flex flex-wrap items-end gap-6">
        <div>
          <div class="text-xs text-gray-500 font-mono">
            {{ d.yf_symbol }} · {{ d.exchange_name }} · {{ d.sector }} / {{ d.industry }}
          </div>
          <div class="text-lg text-gray-200 mt-0.5">{{ d.name }}</div>
          <div class="text-3xl font-bold font-mono text-gray-100">
            {{ fmt(d.last) }}
            <span class="text-sm text-gray-500">{{ d.currency }}</span>
            <span class="text-base ml-2" :class="pctClass(d.pct24h)">{{ fmtPct(d.pct24h) }}</span>
          </div>
        </div>
        <div class="flex-1" />
        <div class="text-right">
          <div class="text-[10px] text-gray-500 uppercase">Market cap</div>
          <div class="text-xl font-bold font-mono text-gray-200">{{ fmtVol(d.mcap) }}</div>
          <button @click="toDes" class="btn-secondary !py-1 text-[11px] mt-1">📋 DES</button>
          <button @click="toOmon" class="btn-secondary !py-1 text-[11px] mt-1 ml-1">OMON</button>
        </div>
      </div>

      <!-- tabs -->
      <div class="flex rounded-lg overflow-hidden border border-surface-500 w-fit">
        <button v-for="t in TABS" :key="t.key" @click="tab = t.key"
                class="px-3 py-1 text-[11px] font-mono transition-colors"
                :class="tab === t.key ? 'bg-accent-yellow text-black font-bold' : 'text-gray-400 hover:text-gray-200'">
          {{ t.label }}
        </button>
      </div>

      <!-- ══ RESUMO ══ -->
      <template v-if="tab === 'resumo'">
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
          <div v-for="m in multiplesCards" :key="m.label" class="metric-card">
            <span class="metric-label">{{ m.label }}</span>
            <span class="metric-value text-gray-200">{{ m.value }}</span>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- preço-alvo -->
          <div class="card p-4">
            <h2 class="text-sm font-semibold text-gray-200 mb-3">
              <span class="text-accent-yellow">◆</span> Preço-alvo dos analistas
            </h2>
            <template v-if="pt && pt.mean != null">
              <div class="relative h-8 rounded bg-surface-600/60 mb-2">
                <div class="absolute inset-y-0 rounded bg-surface-500/60"
                     :style="targetRange"></div>
                <div class="absolute top-0 bottom-0 w-0.5 bg-gray-200" :style="targetPos(pt.current)"
                     title="atual"></div>
                <div class="absolute top-0 bottom-0 w-0.5 bg-accent-yellow" :style="targetPos(pt.mean)"
                     title="alvo médio"></div>
              </div>
              <div class="flex justify-between text-xs font-mono text-gray-400">
                <span>min {{ fmt(pt.low) }}</span>
                <span class="text-gray-200">atual {{ fmt(pt.current) }}</span>
                <span class="text-accent-yellow font-bold">
                  alvo {{ fmt(pt.mean) }} ({{ upside }})</span>
                <span>máx {{ fmt(pt.high) }}</span>
              </div>
            </template>
            <p v-else class="text-xs text-gray-600">sem cobertura de analistas</p>
          </div>

          <!-- recomendações -->
          <div class="card p-4">
            <h2 class="text-sm font-semibold text-gray-200 mb-3">
              <span class="text-accent-yellow">◆</span> Recomendações ({{ recTotal }} analistas)
            </h2>
            <template v-if="recTotal">
              <div class="flex h-5 rounded overflow-hidden font-mono text-[10px] text-black">
                <div v-for="b in recBars" :key="b.label" :style="{ width: b.pct + '%' }"
                     :class="b.cls" class="flex items-center justify-center overflow-hidden"
                     :title="`${b.label}: ${b.n}`">{{ b.pct >= 12 ? b.n : '' }}</div>
              </div>
              <div class="flex flex-wrap gap-3 mt-2 text-[10px] font-mono text-gray-500">
                <span v-for="b in recBars" :key="b.label" class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-sm inline-block" :class="b.cls"></span>{{ b.label }} {{ b.n }}
                </span>
              </div>
            </template>
            <p v-else class="text-xs text-gray-600">sem recomendações</p>
          </div>
        </div>

        <!-- pares -->
        <div class="card overflow-x-auto" v-if="d.peers?.length">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Comparação com pares — {{ d.sector }}
          </div>
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="text-left px-3 py-2">Ativo</th>
                <th class="text-left px-3 py-2">Empresa</th>
                <th class="px-3 py-2">Mkt cap</th>
                <th class="px-3 py-2">P/E</th>
                <th class="px-3 py-2">P/E proj</th>
                <th class="px-3 py-2">P/B</th>
                <th class="px-3 py-2">DY</th>
                <th class="px-3 py-2">52s %</th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b border-surface-500 bg-surface-600/40 font-bold">
                <td class="px-3 py-1.5 text-accent-yellow">{{ d.yf_symbol }}</td>
                <td class="px-3 py-1.5 text-gray-200">{{ d.name?.slice(0, 28) }}</td>
                <td class="px-3 py-1.5 text-right">{{ fmtVol(d.mcap) }}</td>
                <td class="px-3 py-1.5 text-right">{{ n1(d.multiples?.pe) }}</td>
                <td class="px-3 py-1.5 text-right">{{ n1(d.multiples?.forward_pe) }}</td>
                <td class="px-3 py-1.5 text-right">{{ n1(d.multiples?.pb) }}</td>
                <td class="px-3 py-1.5 text-right">{{ d.multiples?.div_yield != null ? d.multiples.div_yield.toFixed(2) + '%' : '—' }}</td>
                <td class="px-3 py-1.5 text-right">—</td>
              </tr>
              <tr v-for="p in d.peers" :key="p.symbol" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5">
                  <button @click="loadSymbol(p.symbol)" class="text-gray-100 hover:text-accent-yellow font-bold">
                    {{ p.symbol }}</button>
                </td>
                <td class="px-3 py-1.5 text-gray-400">{{ p.name }}</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(p.mcap) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-300">{{ n1(p.pe) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-300">{{ n1(p.forward_pe) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-300">{{ n1(p.pb) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-300">{{ p.div_yield != null ? p.div_yield.toFixed(2) + '%' : '—' }}</td>
                <td class="px-3 py-1.5 text-right" :class="pctClass(p.chg_52w)">{{ fmtPct(p.chg_52w) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="d.summary" class="card p-4 text-[11px] text-gray-500 leading-relaxed">{{ d.summary }}…</p>
      </template>

      <!-- ══ DEMONSTRAÇÕES ══ -->
      <template v-else-if="tab === 'dre'">
        <StmtTable title="DRE — anual" :stmt="d.statements?.income_a" :labels="INCOME_LABELS" />
        <StmtTable title="DRE — trimestral" :stmt="d.statements?.income_q" :labels="INCOME_LABELS" />
        <StmtTable title="Balanço — anual" :stmt="d.statements?.balance_a" :labels="BALANCE_LABELS" />
        <StmtTable title="Fluxo de caixa — anual" :stmt="d.statements?.cashflow_a" :labels="CASHFLOW_LABELS" />
      </template>

      <!-- ══ RESULTADOS ══ -->
      <template v-else-if="tab === 'resultados'">
        <div class="card p-4" v-if="d.calendar?.next_earnings">
          <h2 class="text-sm font-semibold text-gray-200 mb-2">
            <span class="text-accent-yellow">◆</span> Próximo balanço: {{ d.calendar.next_earnings }}
          </h2>
          <div class="flex flex-wrap gap-6 text-xs font-mono text-gray-400">
            <span>EPS estimado <b class="text-gray-200">{{ d.calendar.eps_est ?? '—' }}</b>
              ({{ d.calendar.eps_low }} – {{ d.calendar.eps_high }})</span>
            <span>Receita estimada <b class="text-gray-200">{{ fmtVol(d.calendar.revenue_est) }}</b></span>
          </div>
        </div>
        <div class="card overflow-x-auto">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Histórico: estimado vs reportado
          </div>
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                <th class="text-left px-3 py-2">Data</th>
                <th class="px-3 py-2">EPS estimado</th>
                <th class="px-3 py-2">EPS reportado</th>
                <th class="px-3 py-2">Surpresa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in d.earnings_history || []" :key="e.date" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5 text-gray-300">{{ e.date }}</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ e.eps_est ?? '—' }}</td>
                <td class="px-3 py-1.5 text-right text-gray-200 font-bold">{{ e.eps_real ?? '—' }}</td>
                <td class="px-3 py-1.5 text-right" :class="pctClass(e.surprise_pct)">
                  {{ e.surprise_pct != null ? fmtPct(e.surprise_pct) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ══ DONOS & INSIDERS ══ -->
      <template v-else-if="tab === 'donos'">
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2" v-if="d.ownership">
          <div class="metric-card"><span class="metric-label">Insiders</span>
            <span class="metric-value text-gray-200">{{ pctOf(d.ownership.insiders_pct) }}</span></div>
          <div class="metric-card"><span class="metric-label">Institucionais</span>
            <span class="metric-value text-gray-200">{{ pctOf(d.ownership.institutions_pct) }}</span></div>
          <div class="metric-card"><span class="metric-label">Nº instituições</span>
            <span class="metric-value text-gray-200">{{ d.ownership.institutions_count?.toLocaleString('pt-BR') ?? '—' }}</span></div>
        </div>

        <div class="card overflow-x-auto" v-if="d.top_holders?.length">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Maiores acionistas institucionais
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="h in d.top_holders" :key="h.holder" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5 text-gray-200">{{ h.holder }}</td>
                <td class="px-3 py-1.5 text-right text-gray-300">{{ pctOf(h.pct) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(h.shares) }} ações</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(h.value) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-600">{{ h.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card overflow-x-auto" v-if="d.insiders?.length">
          <div class="px-3 pt-2 text-sm font-semibold text-gray-200">
            <span class="text-accent-yellow">◆</span> Insider transactions (últimas)
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="(t, i) in d.insiders" :key="i" class="border-b border-surface-600/40">
                <td class="px-3 py-1.5 text-gray-200 max-w-40 truncate">{{ t.insider }}</td>
                <td class="px-3 py-1.5 text-gray-500 max-w-32 truncate">{{ t.position }}</td>
                <td class="px-3 py-1.5"
                    :class="isSale(t.text) ? 'text-red-400' : 'text-green-400'">{{ t.text || '—' }}</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ fmtVol(t.shares) }}</td>
                <td class="px-3 py-1.5 text-right text-gray-400">{{ t.value ? fmtVol(t.value) : '—' }}</td>
                <td class="px-3 py-1.5 text-right text-gray-600">{{ t.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card p-4 space-y-3" v-if="d.smart_money">
          <div>
            <div class="text-sm font-semibold text-gray-200"><span class="text-accent-yellow">◆</span> Insiders & Smart Money · múltiplos mercados</div>
            <div class="text-[10px] text-gray-600">Filings regulatórios são separados de proxies de posicionamento em cripto e commodities.</div>
          </div>
          <div v-if="d.smart_money.errors?.length" class="text-[10px] text-amber-400">{{ d.smart_money.errors.join(' · ') }}</div>
          <div v-for="feed in d.smart_money.feeds || []" :key="feed.source" class="rounded-lg bg-surface-600/30 p-3">
            <div class="flex justify-between gap-2 mb-2">
              <div>
                <div class="text-xs font-semibold text-gray-200">{{ feed.source }}</div>
                <div v-if="feed.note" class="text-[9px] text-amber-400/80">{{ feed.note }}</div>
              </div>
              <a :href="feed.url" target="_blank" rel="noopener" class="text-[10px] text-accent-yellow hover:underline">fonte oficial ↗</a>
            </div>
            <div v-if="feed.latest" class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
              <div v-if="feed.latest.net != null"><span class="text-gray-500">Net especuladores</span><div :class="feed.latest.net >= 0 ? 'text-green-400' : 'text-red-400'">{{ fmtVol(feed.latest.net) }}</div></div>
              <div v-if="feed.latest.net_percentile_2y != null"><span class="text-gray-500">Percentil 2 anos</span><div class="text-gray-200">{{ feed.latest.net_percentile_2y }}%</div></div>
              <div v-if="feed.latest.ratio != null"><span class="text-gray-500">Long/Short top traders</span><div class="text-gray-200">{{ feed.latest.ratio.toFixed(2) }}</div></div>
              <div v-if="feed.latest.long_pct != null"><span class="text-gray-500">Long / Short</span><div><span class="text-green-400">{{ feed.latest.long_pct.toFixed(1) }}%</span> / <span class="text-red-400">{{ feed.latest.short_pct.toFixed(1) }}%</span></div></div>
              <div v-if="feed.latest.date"><span class="text-gray-500">Referência</span><div class="text-gray-300">{{ feed.latest.date }}</div></div>
            </div>
            <table v-if="feed.filings?.length" class="w-full text-[11px] font-mono">
              <tbody><tr v-for="f in feed.filings" :key="f.url" class="border-t border-surface-500/40">
                <td class="py-1 text-accent-yellow">Form {{ f.form }}</td><td class="text-gray-500">{{ f.date }}</td>
                <td class="text-gray-300">{{ f.description || 'Insider ownership filing' }}</td>
                <td class="text-right"><a :href="f.url" target="_blank" rel="noopener" class="text-gray-400 hover:text-accent-yellow">abrir ↗</a></td>
              </tr></tbody>
            </table>
            <div v-if="feed.famous_wallets?.length" class="mt-3 overflow-x-auto">
              <div class="text-[10px] text-gray-500 uppercase mb-1">Carteiras BTC públicas conhecidas</div>
              <table class="w-full text-[10px] font-mono">
                <thead><tr class="text-gray-600 border-b border-surface-500">
                  <th class="py-1 text-left">Rótulo</th><th class="text-left">Endereço</th>
                  <th class="text-right">Saldo BTC</th><th class="text-right">Recebido</th>
                  <th class="text-right">Txs</th><th class="text-right">Última atividade</th>
                </tr></thead>
                <tbody><tr v-for="w in feed.famous_wallets" :key="w.address" class="border-b border-surface-600/40">
                  <td class="py-1.5"><div class="text-gray-200">{{ w.label }}</div><div class="text-[8px]" :class="w.confidence === 'verified' ? 'text-green-500' : 'text-amber-500'">{{ w.entity }} · {{ w.confidence }}</div></td>
                  <td><a :href="w.explorer_url" target="_blank" rel="noopener" class="text-accent-yellow hover:underline">{{ shortAddress(w.address) }} ↗</a></td>
                  <td class="text-right text-gray-200">{{ w.balance_btc != null ? w.balance_btc.toLocaleString('pt-BR', { maximumFractionDigits: 8 }) : '—' }}</td>
                  <td class="text-right text-gray-400">{{ w.received_btc != null ? w.received_btc.toLocaleString('pt-BR', { maximumFractionDigits: 2 }) : '—' }}</td>
                  <td class="text-right text-gray-400">{{ w.tx_count?.toLocaleString('pt-BR') ?? '—' }}</td>
                  <td class="text-right text-gray-500">{{ fmtDateTs(w.last_activity_ts) }}</td>
                </tr></tbody>
              </table>
              <div class="text-[9px] text-amber-400/70 mt-1">Rótulos de custodiantes podem mudar; confirme sempre no explorer e na prova de reservas da entidade.</div>
            </div>
          </div>
          <details class="text-[10px]">
            <summary class="cursor-pointer text-gray-400">Diretório de fontes por mercado ({{ d.smart_money.sources?.length || 0 }})</summary>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-1 mt-2">
              <a v-for="s in d.smart_money.sources || []" :key="s.market + s.source" :href="s.url" target="_blank" rel="noopener"
                 class="rounded bg-surface-600/30 p-2 text-gray-400 hover:text-accent-yellow">
                <span class="text-gray-600">{{ s.market }} · </span>{{ s.source }} ↗
              </a>
            </div>
          </details>
        </div>
      </template>

      <!-- ══ DIVIDENDOS ══ -->
      <template v-else-if="tab === 'dividendos'">
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div class="metric-card"><span class="metric-label">Dividend yield</span>
            <span class="metric-value text-gray-200">
              {{ d.multiples?.div_yield != null ? d.multiples.div_yield.toFixed(2) + '%' : '—' }}</span></div>
          <div class="metric-card"><span class="metric-label">Payout</span>
            <span class="metric-value text-gray-200">{{ pctOf(d.multiples?.payout) }}</span></div>
          <div class="metric-card"><span class="metric-label">Ex-dividendo</span>
            <span class="metric-value text-gray-200 !text-sm">{{ d.calendar?.ex_dividend ?? '—' }}</span></div>
          <div class="metric-card"><span class="metric-label">Pagamento</span>
            <span class="metric-value text-gray-200 !text-sm">{{ d.calendar?.dividend_date ?? '—' }}</span></div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="card p-4" v-if="d.dividends?.by_year?.length">
            <h2 class="text-sm font-semibold text-gray-200 mb-2">
              <span class="text-accent-yellow">◆</span> Dividendo por ação — por ano
            </h2>
            <table class="w-full text-xs font-mono">
              <tbody>
                <tr v-for="y in d.dividends.by_year" :key="y.year" class="border-b border-surface-600/40">
                  <td class="px-2 py-1 text-gray-300">{{ y.year }}</td>
                  <td class="px-2 py-1 text-right text-gray-200">{{ y.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="card p-4" v-if="buybacks.length">
            <h2 class="text-sm font-semibold text-gray-200 mb-2">
              <span class="text-accent-yellow">◆</span> Recompras e dividendos pagos (fluxo de caixa)
            </h2>
            <table class="w-full text-xs font-mono">
              <thead>
                <tr class="text-[10px] text-gray-500 uppercase text-right border-b border-surface-500">
                  <th class="text-left px-2 py-1">Ano fiscal</th>
                  <th class="px-2 py-1">Recompras</th>
                  <th class="px-2 py-1">Dividendos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in buybacks" :key="b.period" class="border-b border-surface-600/40">
                  <td class="px-2 py-1 text-gray-300">{{ b.period }}</td>
                  <td class="px-2 py-1 text-right text-gray-200">{{ b.rec != null ? fmtVol(Math.abs(b.rec)) : '—' }}</td>
                  <td class="px-2 py-1 text-right text-gray-200">{{ b.div != null ? fmtVol(Math.abs(b.div)) : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card p-4" v-if="d.dividends?.recent?.length">
          <h2 class="text-sm font-semibold text-gray-200 mb-2">
            <span class="text-accent-yellow">◆</span> Últimos pagamentos
          </h2>
          <div class="flex flex-wrap gap-2 font-mono text-[11px]">
            <span v-for="p in d.dividends.recent" :key="p.date"
                  class="px-2 py-0.5 rounded bg-surface-600/50 text-gray-300">
              {{ p.date }} · {{ p.amount }}</span>
          </div>
        </div>
      </template>
    </template>

    <div v-else class="text-center text-gray-600 text-sm py-16">
      Informe um ticker — ou command line: <span class="font-mono text-accent-yellow">AAPL FA</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getEa } from '@/api/client.js'

const route = useRoute()
const router = useRouter()
const symbolInput = ref('')
const d = ref(null)
const loading = ref(false)
const error = ref(null)
const tab = ref('resumo')

const TABS = [
  { key: 'resumo', label: 'RESUMO' },
  { key: 'dre', label: 'DEMONSTRAÇÕES' },
  { key: 'resultados', label: 'RESULTADOS' },
  { key: 'donos', label: 'DONOS & INSIDERS' },
  { key: 'dividendos', label: 'DIVIDENDOS' },
]

const INCOME_LABELS = {
  receita: 'Receita', lucro_bruto: 'Lucro bruto', ebitda: 'EBITDA',
  lucro_operacional: 'Lucro operacional', lucro_liquido: 'Lucro líquido',
  eps: 'EPS básico', margem_bruta: 'Margem bruta %',
  margem_ebitda: 'Margem EBITDA %', margem_liquida: 'Margem líquida %',
}
const BALANCE_LABELS = {
  ativos: 'Ativos totais', divida_total: 'Dívida total',
  caixa: 'Caixa e equivalentes', patrimonio: 'Patrimônio líquido',
}
const CASHFLOW_LABELS = {
  fco: 'Caixa operacional', capex: 'Capex', fcl: 'Fluxo de caixa livre',
  recompras: 'Recompra de ações', dividendos_pagos: 'Dividendos pagos',
}

const pt = computed(() => d.value?.price_targets)
const upside = computed(() => {
  if (!pt.value?.mean || !pt.value?.current) return ''
  const u = (pt.value.mean / pt.value.current - 1) * 100
  return (u >= 0 ? '+' : '') + u.toFixed(1) + '%'
})
const targetRange = computed(() => {
  if (!pt.value) return {}
  const { low, high } = pt.value
  const span = spanOf()
  return { left: pos(low, span) + '%', width: (pos(high, span) - pos(low, span)) + '%' }
})
function spanOf() {
  const vals = [pt.value.low, pt.value.high, pt.value.current, pt.value.mean].filter((v) => v != null)
  const min = Math.min(...vals) * 0.97
  const max = Math.max(...vals) * 1.03
  return { min, max }
}
function pos(v, span) {
  return ((v - span.min) / (span.max - span.min)) * 100
}
function targetPos(v) {
  if (v == null || !pt.value) return {}
  return { left: pos(v, spanOf()) + '%' }
}

const recTotal = computed(() => {
  const r = d.value?.recommendations
  return r ? r.strong_buy + r.buy + r.hold + r.sell + r.strong_sell : 0
})
const recBars = computed(() => {
  const r = d.value?.recommendations
  if (!r || !recTotal.value) return []
  const mk = (label, n, cls) => ({ label, n, cls, pct: n / recTotal.value * 100 })
  return [
    mk('Compra forte', r.strong_buy, 'bg-green-500'),
    mk('Compra', r.buy, 'bg-green-700'),
    mk('Manter', r.hold, 'bg-gray-500'),
    mk('Venda', r.sell, 'bg-red-700'),
    mk('Venda forte', r.strong_sell, 'bg-red-500'),
  ].filter((b) => b.n > 0)
})

const multiplesCards = computed(() => {
  const m = d.value?.multiples || {}
  const x1 = (v) => (v != null ? v.toFixed(1) : '—')
  return [
    { label: 'P/L', value: x1(m.pe) },
    { label: 'P/L projetado', value: x1(m.forward_pe) },
    { label: 'EV/EBITDA', value: x1(m.ev_ebitda) },
    { label: 'P/VPA', value: x1(m.pb) },
    { label: 'P/S', value: x1(m.ps) },
    { label: 'PEG', value: m.peg != null ? m.peg.toFixed(2) : '—' },
    { label: 'Div. yield', value: m.div_yield != null ? m.div_yield.toFixed(2) + '%' : '—' },
    { label: 'Payout', value: pctOf(m.payout) },
    { label: 'ROE', value: pctOf(m.roe) },
    { label: 'Beta', value: m.beta != null ? m.beta.toFixed(2) : '—' },
  ]
})

const buybacks = computed(() => {
  const cf = d.value?.statements?.cashflow_a
  if (!cf) return []
  return (cf.periods || []).map((p, i) => ({
    period: p,
    rec: cf.data?.recompras?.[i],
    div: cf.data?.dividendos_pagos?.[i],
  })).filter((b) => b.rec != null || b.div != null)
})

// tabela de demonstração reutilizável
const StmtTable = (props) => {
  const s = props.stmt
  if (!s || !Object.keys(s.data || {}).length) return null
  const rows = Object.entries(props.labels)
    .filter(([k]) => s.data[k])
    .map(([k, label]) => h('tr', { class: 'border-b border-surface-600/40' }, [
      h('td', { class: 'px-3 py-1.5 text-gray-400 text-left whitespace-nowrap' }, label),
      ...s.data[k].map((v) => h('td', { class: 'px-3 py-1.5 text-right text-gray-200' },
        label.includes('%') ? (v != null ? v.toFixed(1) + '%' : '—')
        : label === 'EPS básico' ? (v != null ? v.toFixed(2) : '—')
        : fmtVol(v))),
    ]))
  return h('div', { class: 'card overflow-x-auto' }, [
    h('div', { class: 'px-3 pt-2 text-sm font-semibold text-gray-200' }, [
      h('span', { class: 'text-accent-yellow' }, '◆ '), props.title]),
    h('table', { class: 'w-full text-xs font-mono' }, [
      h('thead', h('tr', { class: 'text-[10px] text-gray-500 uppercase text-right border-b border-surface-500' }, [
        h('th', { class: 'px-3 py-2 text-left' }, ''),
        ...s.periods.map((p) => h('th', { class: 'px-3 py-2' }, p)),
      ])),
      h('tbody', rows),
    ]),
  ])
}
StmtTable.props = { title: String, stmt: Object, labels: Object }

async function load() {
  const s = symbolInput.value.trim().toUpperCase()
  if (!s) return
  loading.value = true
  error.value = null
  try {
    const { data } = await getEa(s)
    if (data.error) { error.value = data.error; d.value = null; return }
    d.value = data
  } catch (e) {
    error.value = e.response?.data?.error || e.message
    d.value = null
  } finally {
    loading.value = false
  }
}

function loadSymbol(sym) {
  symbolInput.value = sym
  tab.value = 'resumo'
  load()
}

function toDes() {
  router.push({ path: '/des', query: { symbol: d.value.yf_symbol, market: 'tradfi' } })
}
function toOmon() {
  router.push({ path: '/omon', query: { symbol: d.value.yf_symbol } })
}

function isSale(text) {
  return /sale|sold/i.test(text || '')
}
function shortAddress(v) {
  return v ? v.slice(0, 7) + '…' + v.slice(-6) : '—'
}
function fmtDateTs(v) {
  return v ? new Date(v).toLocaleDateString('pt-BR') : '—'
}
function pctOf(v) {
  if (v == null) return '—'
  return (v <= 1.5 ? v * 100 : v).toFixed(1) + '%'
}
function pctClass(v) {
  return (v ?? 0) >= 0 ? 'text-accent-yellow' : 'text-red-400'
}
function n1(v) {
  return v != null ? v.toFixed(1) : '—'
}
function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}
function fmtPct(v) {
  return v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}
function fmtVol(v) {
  if (v == null) return '—'
  const a = Math.abs(v)
  if (a >= 1e12) return (v / 1e12).toFixed(2) + 'T'
  if (a >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (a >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  return Math.round(v).toLocaleString('pt-BR')
}

onMounted(() => {
  const q = String(route.query.symbol || '').trim()
  if (q) { symbolInput.value = q.toUpperCase(); load() }
})
</script>
