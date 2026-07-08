<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <!-- header -->
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">TRD · Execução de Ordens (OMS/EMS)</h1>
      <span class="text-[10px] text-gray-600 font-mono">
        paper: fills simulados (tradfi atrasado ~15min) · bybit: ordens reais via API
      </span>
      <div class="flex-1" />
      <select v-model="account" @change="onAccountChange" class="form-select !py-1.5 text-xs">
        <option v-for="a in accounts" :key="a.id" :value="a.id" :disabled="!a.configured">
          {{ a.label }}{{ a.configured ? '' : ' (sem chaves)' }}
        </option>
      </select>
      <span class="text-[10px] font-bold px-2 py-1 rounded font-mono"
            :class="accountKind === 'real' ? 'bg-red-900/60 text-red-300'
              : accountKind === 'demo' ? 'bg-blue-900/60 text-blue-300'
              : 'bg-surface-600 text-gray-400'">
        {{ accountKind === 'real' ? 'DINHEIRO REAL' : accountKind === 'demo' ? 'DEMO' : 'PAPER' }}
      </span>
      <button v-if="account === 'paper'" @click="resetPaper"
              class="btn-secondary !py-1.5 text-xs" title="Zera ordens, posições e caixa da conta paper">
        Resetar paper
      </button>
    </div>

    <!-- resumo da conta -->
    <div v-if="blot" class="grid grid-cols-2 md:grid-cols-5 gap-3">
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase">Caixa</div>
        <div class="text-lg font-bold font-mono text-gray-100">{{ fmtUsd(blot.cash) }}</div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase">Equity</div>
        <div class="text-lg font-bold font-mono text-accent-yellow">{{ fmtUsd(blot.summary?.equity) }}</div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase">PnL realizado</div>
        <div class="text-lg font-bold font-mono" :class="pnlClass(blot.summary?.realized)">
          {{ fmtUsd(blot.summary?.realized) }}</div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase">PnL aberto</div>
        <div class="text-lg font-bold font-mono" :class="pnlClass(blot.summary?.unrealized)">
          {{ fmtUsd(blot.summary?.unrealized) }}</div>
      </div>
      <div class="card p-3">
        <div class="text-[10px] text-gray-500 uppercase">Fees pagas</div>
        <div class="text-lg font-bold font-mono text-gray-300">{{ fmtUsd(blot.summary?.fees) }}</div>
      </div>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <!-- ══ Ticket + pré-trade ══ -->
      <div class="space-y-4">
        <div class="card p-4 space-y-3">
          <div class="text-[10px] text-gray-500 uppercase font-semibold">Nova ordem</div>

          <div class="grid grid-cols-2 gap-2">
            <select v-model="ticket.market" class="form-select !py-1.5 text-xs">
              <option value="crypto">Cripto (perps)</option>
              <option value="tradfi">Ações / ETFs / FX / Futuros</option>
            </select>
            <input v-model="ticket.symbol" class="form-input !py-1.5 text-xs uppercase"
                   :placeholder="ticket.market === 'crypto' ? 'ex.: BTC' : 'ex.: AAPL · TLT · EURUSD · CLZ26.NYM'" />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <button @click="ticket.side = 'buy'"
                    class="py-2 rounded-lg text-xs font-bold border transition-colors"
                    :class="ticket.side === 'buy'
                      ? 'bg-green-900/50 border-green-600 text-green-300'
                      : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
              COMPRA
            </button>
            <button @click="ticket.side = 'sell'"
                    class="py-2 rounded-lg text-xs font-bold border transition-colors"
                    :class="ticket.side === 'sell'
                      ? 'bg-red-900/50 border-red-600 text-red-300'
                      : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
              VENDA
            </button>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <select v-model="ticket.type" class="form-select !py-1.5 text-xs">
              <option value="market">Mercado</option>
              <option value="limit">Limite</option>
            </select>
            <input v-model="ticket.qty" type="number" step="any" min="0"
                   placeholder="qtd" class="form-input !py-1.5 text-xs" />
            <input v-model="ticket.limit_price" type="number" step="any" min="0"
                   placeholder="preço limite" :disabled="ticket.type !== 'limit'"
                   class="form-input !py-1.5 text-xs disabled:opacity-40" />
          </div>

          <label v-if="accountKind === 'real'"
                 class="flex items-center gap-2 text-xs text-red-300 bg-red-900/20 border border-red-800/50 rounded-lg p-2">
            <input type="checkbox" v-model="ticket.confirm" class="accent-red-500" />
            Confirmo o envio de ordem com <b>dinheiro real</b>
          </label>

          <div class="grid grid-cols-2 gap-2">
            <button @click="runPreTrade" :disabled="busy" class="btn-secondary !py-2 text-xs">
              {{ busy === 'pre' ? 'Analisando…' : 'Pré-trade' }}
            </button>
            <button @click="sendOrder" :disabled="busy || (accountKind === 'real' && !ticket.confirm)"
                    class="!py-2 text-xs font-bold rounded-lg border transition-colors disabled:opacity-40"
                    :class="ticket.side === 'buy'
                      ? 'bg-green-800/60 border-green-600 text-green-200 hover:bg-green-800'
                      : 'bg-red-800/60 border-red-600 text-red-200 hover:bg-red-800'">
              {{ busy === 'send' ? 'Enviando…' : `Enviar ${ticket.side === 'buy' ? 'COMPRA' : 'VENDA'}` }}
            </button>
          </div>
        </div>

        <!-- pré-trade analytics -->
        <div v-if="pre" class="card p-4 space-y-2">
          <div class="flex items-center gap-2">
            <div class="text-[10px] text-gray-500 uppercase font-semibold">Pré-trade · {{ pre.resolved }}</div>
            <span v-if="pre.delayed" class="text-[9px] px-1.5 py-0.5 rounded bg-amber-900/50 text-amber-300 font-mono">
              atrasado ~15min</span>
          </div>
          <div class="grid grid-cols-3 gap-2 font-mono text-xs">
            <div><span class="text-gray-600">bid</span> <span class="text-green-400">{{ fmt(pre.bid) }}</span></div>
            <div><span class="text-gray-600">mid</span> <span class="text-gray-200">{{ fmt(pre.mid) }}</span></div>
            <div><span class="text-gray-600">ask</span> <span class="text-red-400">{{ fmt(pre.ask) }}</span></div>
          </div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="[k, v] in preRows" :key="k" class="border-b border-surface-600/30">
                <td class="py-1 text-gray-500">{{ k }}</td>
                <td class="py-1 text-right text-gray-200">{{ v }}</td>
              </tr>
            </tbody>
          </table>
          <div v-for="(w, i) in pre.warnings" :key="i"
               class="text-[10px] text-amber-400/90 flex gap-1.5">
            <span>⚠</span><span>{{ w }}</span>
          </div>
        </div>
      </div>

      <!-- ══ Blotter ══ -->
      <div class="xl:col-span-2 space-y-3">
        <div class="flex gap-1">
          <button v-for="t in TABS" :key="t" @click="tab = t"
                  class="px-3 py-1.5 text-xs rounded-lg border transition-colors"
                  :class="tab === t
                    ? 'bg-accent-yellow/10 border-accent-yellow/40 text-accent-yellow font-semibold'
                    : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
            {{ t }}
          </button>
          <div class="flex-1" />
          <span class="text-[10px] text-gray-600 font-mono self-center">atualiza a cada 5s</span>
        </div>

        <!-- ORDENS -->
        <div v-if="tab === 'ORDENS'" class="card p-3 overflow-x-auto">
          <table class="w-full text-xs font-mono whitespace-nowrap">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-left">
                <th class="py-1.5 pr-3">Hora</th><th class="pr-3">Ativo</th><th class="pr-3">Lado</th>
                <th class="pr-3">Tipo</th><th class="pr-3 text-right">Qtd</th>
                <th class="pr-3 text-right">Limite</th><th class="pr-3 text-right">Preço médio</th>
                <th class="pr-3">Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="o in blot?.orders || []" :key="o.id" class="border-t border-surface-600/30">
                <td class="py-1.5 pr-3 text-gray-500">{{ tsFmt(o.ts) }}</td>
                <td class="pr-3 text-gray-200">{{ o.symbol }}<span class="text-gray-600 text-[10px]"> {{ o.market === 'crypto' ? '· cripto' : '· tradfi' }}</span></td>
                <td class="pr-3" :class="o.side === 'buy' ? 'text-green-400' : 'text-red-400'">
                  {{ o.side === 'buy' ? 'COMPRA' : 'VENDA' }}</td>
                <td class="pr-3 text-gray-400">{{ o.type === 'market' ? 'mercado' : 'limite' }}</td>
                <td class="pr-3 text-right text-gray-300">{{ fmtQty(o.qty) }}<span v-if="o.status === 'partial'" class="text-gray-600"> ({{ fmtQty(o.filled_qty) }})</span></td>
                <td class="pr-3 text-right text-gray-400">{{ o.limit_price != null ? fmt(o.limit_price) : '—' }}</td>
                <td class="pr-3 text-right text-gray-200">{{ o.avg_price != null ? fmt(o.avg_price) : '—' }}</td>
                <td class="pr-3"><span class="px-1.5 py-0.5 rounded text-[10px]" :class="statusClass(o.status)">{{ statusLabel(o.status) }}</span></td>
                <td class="text-right">
                  <button v-if="['working', 'partial'].includes(o.status)" @click="cancel(o.id)"
                          class="text-[10px] text-red-400 hover:text-red-300 underline">cancelar</button>
                </td>
              </tr>
              <tr v-if="!(blot?.orders || []).length">
                <td colspan="9" class="py-6 text-center text-gray-600">sem ordens nesta conta</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- POSIÇÕES -->
        <div v-if="tab === 'POSIÇÕES'" class="space-y-3">
          <div class="card p-3 overflow-x-auto">
            <table class="w-full text-xs font-mono whitespace-nowrap">
              <thead>
                <tr class="text-[10px] text-gray-500 uppercase text-left">
                  <th class="py-1.5 pr-3">Ativo</th><th class="pr-3 text-right">Qtd</th>
                  <th class="pr-3 text-right">Preço médio</th><th class="pr-3 text-right">Mark</th>
                  <th class="pr-3 text-right">Notional</th><th class="pr-3 text-right">PnL aberto</th>
                  <th class="pr-3 text-right">PnL realizado</th><th class="pr-3 text-right">Fees</th><th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in blot?.positions || []" :key="p.symbol + p.market" class="border-t border-surface-600/30">
                  <td class="py-1.5 pr-3 text-gray-200">{{ p.symbol }}
                    <span class="text-gray-600 text-[10px]">{{ p.market === 'crypto' ? '· cripto' : '· tradfi' }}</span>
                    <span v-if="p.delayed" class="text-amber-500/80 text-[9px]"> ~15min</span></td>
                  <td class="pr-3 text-right" :class="p.qty > 0 ? 'text-green-400' : p.qty < 0 ? 'text-red-400' : 'text-gray-500'">{{ fmtQty(p.qty) }}</td>
                  <td class="pr-3 text-right text-gray-300">{{ fmt(p.avg_price) }}</td>
                  <td class="pr-3 text-right text-gray-300">{{ fmt(p.mark) }}</td>
                  <td class="pr-3 text-right text-gray-400">{{ fmtUsd(p.notional) }}</td>
                  <td class="pr-3 text-right" :class="pnlClass(p.unrealized)">{{ fmtUsd(p.unrealized) }}</td>
                  <td class="pr-3 text-right" :class="pnlClass(p.realized)">{{ fmtUsd(p.realized) }}</td>
                  <td class="pr-3 text-right text-gray-500">{{ fmtUsd(p.fees) }}</td>
                  <td class="text-right">
                    <button v-if="Math.abs(p.qty) > 1e-12" @click="flatten(p)"
                            class="text-[10px] text-amber-400 hover:text-amber-300 underline">zerar</button>
                  </td>
                </tr>
                <tr v-if="!(blot?.positions || []).length">
                  <td colspan="9" class="py-6 text-center text-gray-600">sem posições</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="(blot?.exchange_positions || []).length" class="card p-3">
            <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Posições na exchange (Bybit, ao vivo)</div>
            <table class="w-full text-xs font-mono">
              <tbody>
                <tr v-for="(p, i) in blot.exchange_positions" :key="i" class="border-t border-surface-600/30">
                  <td v-if="p.error" colspan="6" class="py-1.5 text-red-400">{{ p.error }}</td>
                  <template v-else>
                    <td class="py-1.5 pr-3 text-gray-200">{{ p.symbol }}</td>
                    <td class="pr-3" :class="p.side === 'long' ? 'text-green-400' : 'text-red-400'">{{ p.side }}</td>
                    <td class="pr-3 text-right text-gray-300">{{ fmtQty(p.qty) }}</td>
                    <td class="pr-3 text-right text-gray-400">entrada {{ fmt(p.entry) }}</td>
                    <td class="pr-3 text-right text-gray-400">mark {{ fmt(p.mark) }}</td>
                    <td class="pr-3 text-right" :class="pnlClass(p.unrealized)">{{ fmtUsd(p.unrealized) }}</td>
                  </template>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- EXECUÇÕES -->
        <div v-if="tab === 'EXECUÇÕES'" class="card p-3 overflow-x-auto">
          <table class="w-full text-xs font-mono whitespace-nowrap">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-left">
                <th class="py-1.5 pr-3">Hora</th><th class="pr-3">Ativo</th><th class="pr-3">Lado</th>
                <th class="pr-3 text-right">Qtd</th><th class="pr-3 text-right">Preço</th>
                <th class="pr-3 text-right">Mid chegada</th><th class="pr-3 text-right">Slippage</th>
                <th class="pr-3 text-right">Fee</th><th class="pr-3 text-right">Latência</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in blot?.fills || []" :key="f.id" class="border-t border-surface-600/30">
                <td class="py-1.5 pr-3 text-gray-500">{{ tsFmt(f.ts) }}</td>
                <td class="pr-3 text-gray-200">{{ f.symbol }}</td>
                <td class="pr-3" :class="f.side === 'buy' ? 'text-green-400' : 'text-red-400'">
                  {{ f.side === 'buy' ? 'COMPRA' : 'VENDA' }}</td>
                <td class="pr-3 text-right text-gray-300">{{ fmtQty(f.qty) }}</td>
                <td class="pr-3 text-right text-gray-200">{{ fmt(f.price) }}</td>
                <td class="pr-3 text-right text-gray-500">{{ fmt(f.arrival_mid) }}</td>
                <td class="pr-3 text-right" :class="(f.slippage_bps || 0) > 5 ? 'text-red-400' : 'text-gray-300'">
                  {{ f.slippage_bps != null ? f.slippage_bps.toFixed(2) + ' bps' : '—' }}</td>
                <td class="pr-3 text-right text-gray-500">{{ fmtUsd(f.fee) }}</td>
                <td class="pr-3 text-right text-gray-600">{{ f.latency_ms }} ms</td>
              </tr>
              <tr v-if="!(blot?.fills || []).length">
                <td colspan="9" class="py-6 text-center text-gray-600">sem execuções</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- PÓS-TRADE (TCA) -->
        <div v-if="tab === 'PÓS-TRADE'" class="space-y-3">
          <div v-if="!tcaD || !tcaD.n_fills" class="card p-6 text-center text-gray-600 text-sm">
            sem execuções para analisar
          </div>
          <template v-else>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase">Execuções / Notional</div>
                <div class="text-base font-bold font-mono text-gray-100">
                  {{ tcaD.n_fills }} · {{ fmtUsd(tcaD.notional) }}</div>
              </div>
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase">Slippage média / mediana</div>
                <div class="text-base font-bold font-mono text-gray-100">
                  {{ bps(tcaD.avg_slippage_bps) }} · {{ bps(tcaD.median_slippage_bps) }}</div>
              </div>
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase">Implementation shortfall</div>
                <div class="text-base font-bold font-mono" :class="pnlClass(-(tcaD.implementation_shortfall_usd || 0))">
                  {{ fmtUsd(tcaD.implementation_shortfall_usd) }} ({{ bps(tcaD.shortfall_bps) }})</div>
              </div>
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase">Fees / Latência média</div>
                <div class="text-base font-bold font-mono text-gray-100">
                  {{ fmtUsd(tcaD.fees) }} · {{ Math.round(tcaD.avg_latency_ms || 0) }} ms</div>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Por mercado</div>
                <table class="w-full text-xs font-mono">
                  <tbody>
                    <tr v-for="g in tcaD.by_market" :key="g.key" class="border-t border-surface-600/30">
                      <td class="py-1.5 text-gray-300">{{ g.key === 'crypto' ? 'Cripto' : 'Tradicional' }}</td>
                      <td class="text-right text-gray-500">{{ g.n }} fills</td>
                      <td class="text-right text-gray-400">{{ fmtUsd(g.notional) }}</td>
                      <td class="text-right text-gray-200">{{ bps(g.avg_slippage_bps) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="card p-3">
                <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Por tipo de ordem</div>
                <table class="w-full text-xs font-mono">
                  <tbody>
                    <tr v-for="g in tcaD.by_type" :key="g.key" class="border-t border-surface-600/30">
                      <td class="py-1.5 text-gray-300">{{ g.key === 'market' ? 'Mercado' : g.key === 'limit' ? 'Limite' : g.key }}</td>
                      <td class="text-right text-gray-500">{{ g.n }} fills</td>
                      <td class="text-right text-gray-400">{{ fmtUsd(g.notional) }}</td>
                      <td class="text-right text-gray-200">{{ bps(g.avg_slippage_bps) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="card p-3 overflow-x-auto">
              <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Piores execuções (slippage)</div>
              <table class="w-full text-xs font-mono whitespace-nowrap">
                <tbody>
                  <tr v-for="f in tcaD.worst_fills" :key="f.id" class="border-t border-surface-600/30">
                    <td class="py-1.5 pr-3 text-gray-500">{{ tsFmt(f.ts) }}</td>
                    <td class="pr-3 text-gray-200">{{ f.symbol }}</td>
                    <td class="pr-3" :class="f.side === 'buy' ? 'text-green-400' : 'text-red-400'">
                      {{ f.side === 'buy' ? 'COMPRA' : 'VENDA' }}</td>
                    <td class="pr-3 text-right text-gray-300">{{ fmtQty(f.qty) }} @ {{ fmt(f.price) }}</td>
                    <td class="pr-3 text-right text-red-400">{{ bps(f.slippage_bps) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-if="tcaD.note" class="text-[10px] text-amber-400/80">⚠ {{ tcaD.note }}</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import { useRoute } from 'vue-router'
import {
  getOmsAccounts, postPreTrade, submitOmsOrder, cancelOmsOrder,
  getOmsBlotter, getOmsTca, resetOmsPaper,
} from '@/api/client.js'

const route = useRoute()
const TABS = ['ORDENS', 'POSIÇÕES', 'EXECUÇÕES', 'PÓS-TRADE']

const accounts = ref([])
const account = ref('paper')
const tab = ref('ORDENS')
const blot = ref(null)
const tcaD = ref(null)
const pre = ref(null)
const busy = ref(null)
const error = ref(null)
let timer = null

const ticket = reactive({
  market: 'crypto', symbol: '', side: 'buy', type: 'market',
  qty: '', limit_price: '', confirm: false,
})

const accountKind = computed(
  () => accounts.value.find((a) => a.id === account.value)?.kind || 'paper')

const preRows = computed(() => {
  if (!pre.value) return []
  const p = pre.value
  return [
    ['Notional', fmtUsd(p.notional)],
    ['Spread', bps(p.spread_bps)],
    ['Slippage estimada', bps(p.slippage_est_bps)],
    ['Fee estimada', `${fmtUsd(p.fee_est)} (${bps(p.fee_rate_bps)})`],
    ['Custo total estimado', `${fmtUsd(p.cost_total_usd)} (${bps(p.cost_total_bps)})`],
    ['% do volume diário', p.pct_adv != null ? (p.pct_adv * 100).toFixed(3) + '%' : '—'],
    ['Vol diária', p.daily_vol_pct != null ? p.daily_vol_pct.toFixed(2) + '%' : '—'],
    ['VaR 1d (95%)', fmtUsd(p.var_1d_95)],
  ]
})

function payload() {
  return {
    account: account.value,
    symbol: ticket.symbol.trim().toUpperCase(),
    market: ticket.market,
    side: ticket.side,
    type: ticket.type,
    qty: Number(ticket.qty),
    limit_price: ticket.type === 'limit' ? Number(ticket.limit_price) : undefined,
    confirm: ticket.confirm || undefined,
  }
}

async function runPreTrade() {
  error.value = null
  busy.value = 'pre'
  try {
    const { data } = await postPreTrade(payload())
    pre.value = data
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    busy.value = null
  }
}

async function sendOrder() {
  error.value = null
  busy.value = 'send'
  try {
    const { data } = await submitOmsOrder(payload())
    if (data.status === 'rejected') error.value = `Ordem rejeitada: ${data.note || ''}`
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    busy.value = null
  }
}

async function cancel(id) {
  try {
    await cancelOmsOrder(id)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
}

async function flatten(p) {
  // zera a posição com ordem a mercado no lado oposto
  error.value = null
  try {
    await submitOmsOrder({
      account: account.value, symbol: p.symbol, market: p.market,
      side: p.qty > 0 ? 'sell' : 'buy', type: 'market', qty: Math.abs(p.qty),
      confirm: accountKind.value === 'real' ? ticket.confirm : undefined,
    })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
}

async function resetPaper() {
  if (!window.confirm('Zerar TODAS as ordens, posições e caixa da conta paper?')) return
  await resetOmsPaper()
  pre.value = null
  await refresh()
}

async function refresh() {
  try {
    const { data } = await getOmsBlotter(account.value)
    blot.value = data
    if (tab.value === 'PÓS-TRADE') {
      const { data: t } = await getOmsTca(account.value)
      tcaD.value = t
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
}

function onAccountChange() {
  blot.value = null
  tcaD.value = null
  refresh()
}

function statusLabel(s) {
  return { working: 'ABERTA', partial: 'PARCIAL', filled: 'EXECUTADA',
           cancelled: 'CANCELADA', rejected: 'REJEITADA' }[s] || s
}
function statusClass(s) {
  return { working: 'bg-blue-900/50 text-blue-300',
           partial: 'bg-amber-900/50 text-amber-300',
           filled: 'bg-green-900/50 text-green-300',
           cancelled: 'bg-surface-600 text-gray-400',
           rejected: 'bg-red-900/50 text-red-300' }[s] || 'bg-surface-600 text-gray-400'
}
function pnlClass(v) {
  if (v == null || Math.abs(v) < 1e-9) return 'text-gray-300'
  return v > 0 ? 'text-green-400' : 'text-red-400'
}
function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: Math.abs(v) < 1 ? 6 : 2 })
}
function fmtQty(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 6 })
}
function fmtUsd(v) {
  if (v == null) return '—'
  return '$' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
}
function bps(v) {
  return v != null ? Number(v).toFixed(1) + ' bps' : '—'
}
function tsFmt(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('pt-BR', { hour12: false })
}

onMounted(async () => {
  try {
    const { data } = await getOmsAccounts()
    accounts.value = data.accounts || []
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  }
  const q = String(route.query.symbol || '').trim()
  if (q) {
    ticket.symbol = q.toUpperCase()
    if (String(route.query.market || '') === 'tradfi') ticket.market = 'tradfi'
  }
  await refresh()
  timer = setInterval(refresh, 5000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>
