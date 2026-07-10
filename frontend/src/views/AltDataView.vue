<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h1 class="text-base font-semibold text-gray-100">ALTD · Dados Alternativos & Inteligência</h1>
      <span class="text-[10px] text-gray-600 font-mono">
        GSCPI NY Fed · TSA · NOAA ENSO · met.no · filings SEC · funding Bybit — fontes gratuitas, proxies rotulados
      </span>
    </div>

    <div class="flex gap-1 flex-wrap">
      <button v-for="t in TABS" :key="t.key" @click="setTab(t.key)"
              class="px-3 py-1.5 text-xs rounded-lg border transition-colors"
              :class="tab === t.key
                ? 'bg-accent-yellow/10 border-accent-yellow/40 text-accent-yellow font-semibold'
                : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
        {{ t.label }}
      </button>
      <div class="flex-1" />
      <span v-if="loading" class="text-xs text-accent-yellow/80 self-center font-mono">carregando…</span>
    </div>

    <div v-if="error" class="card p-3 text-xs text-red-400">{{ error }}</div>

    <!-- ══ PAINEL — indicadores proprietários ══ -->
    <template v-if="tab === 'painel' && ind">
      <p class="text-[10px] text-gray-600">{{ ind.note }}</p>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div v-for="i in ind.indicators" :key="i.id" class="card p-4 space-y-3">
          <div class="flex items-start justify-between">
            <div class="text-xs font-semibold text-gray-200">{{ i.name }}</div>
            <span v-if="!i.error" class="text-[10px] font-bold px-2 py-0.5 rounded font-mono"
                  :class="readingClass(i.reading)">{{ i.reading }}</span>
          </div>
          <div v-if="i.error" class="text-xs text-red-400">{{ i.error }}</div>
          <template v-else>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl font-bold font-mono"
                    :class="i.value > 0 ? 'text-green-400' : i.value < 0 ? 'text-red-400' : 'text-gray-200'">
                {{ i.value > 0 ? '+' : '' }}{{ i.value }}</span>
              <span class="text-xs text-gray-500 font-mono">{{ i.unit }}</span>
            </div>
            <!-- barra de posição na faixa -->
            <div class="relative h-2 rounded-full bg-gradient-to-r from-red-900/60 via-surface-600 to-green-900/60">
              <div class="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-accent-yellow border-2 border-black"
                   :style="{ left: gaugePos(i) }" />
            </div>
            <table class="w-full text-[11px] font-mono">
              <tbody>
                <tr v-for="c in i.components" :key="c.name" class="border-t border-surface-600/30">
                  <td class="py-1 text-gray-500">{{ c.name }}</td>
                  <td class="py-1 text-right"
                      :class="c.z > 0 ? 'text-green-400' : c.z < 0 ? 'text-red-400' : 'text-gray-400'">
                    {{ c.z > 0 ? '+' : '' }}{{ c.z }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="i.history" :ref="(el) => setIndRef(el, i.id)" class="h-32" />
            <p class="text-[10px] text-gray-600 leading-relaxed">{{ i.method }}</p>
          </template>
        </div>
      </div>
    </template>

    <!-- ══ SUPPLY CHAIN ══ -->
    <template v-if="tab === 'supply' && sc">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="card p-4 lg:col-span-2">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="text-xs font-semibold text-gray-200">GSCPI — Pressão Global de Supply Chain</span>
            <span class="text-2xl font-bold font-mono"
                  :class="sc.gscpi.last > 0.5 ? 'text-red-400' : sc.gscpi.last < -0.5 ? 'text-green-400' : 'text-gray-200'">
              {{ sc.gscpi.last }}</span>
            <span class="text-xs text-gray-500 font-mono" v-if="sc.gscpi.yoy_delta != null">
              {{ sc.gscpi.yoy_delta > 0 ? '+' : '' }}{{ sc.gscpi.yoy_delta }} vs 1 ano</span>
          </div>
          <div ref="gscpiChart" class="h-72" />
          <p class="text-[10px] text-gray-600 mt-2">{{ sc.gscpi.source }} · z-score: 0 = média histórica, +1 = 1 desvio acima</p>
        </div>
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Proxies de frete & logística</div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="p in sc.proxies" :key="p.symbol" class="border-t border-surface-600/30">
                <td class="py-1.5 text-gray-300">{{ p.label }}</td>
                <td class="text-right text-gray-200">{{ fmt(p.last) }}</td>
                <td class="text-right w-16" :class="pctClass(p.pct24h)">{{ fmtPct(p.pct24h) }}</td>
              </tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600 mt-3 leading-relaxed">{{ sc.note }}</p>
        </div>
      </div>
    </template>

    <!-- ══ TRÁFEGO ══ -->
    <template v-if="tab === 'trafego' && tsa">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Passageiros ({{ tsa.last_date }})</div>
          <div class="text-lg font-bold font-mono text-gray-100">{{ fmtInt(tsa.last) }}</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Média 7 dias</div>
          <div class="text-lg font-bold font-mono text-accent-yellow">{{ fmtInt(tsa.avg7_last) }}</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Tendência vs mês anterior</div>
          <div class="text-lg font-bold font-mono" :class="pctClass(tsa.mom_pct)">{{ fmtPct(tsa.mom_pct) }}</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Dias na série</div>
          <div class="text-lg font-bold font-mono text-gray-300">{{ tsa.ts.length }}</div>
        </div>
      </div>
      <div class="card p-4">
        <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Passageiros/dia em checkpoints TSA (EUA)</div>
        <div ref="tsaChart" class="h-72" />
        <p class="text-[10px] text-gray-600 mt-2">{{ tsa.source }} · leitura p/ aéreas (AAL, DAL, UAL, LUV), hotéis e querosene de aviação</p>
      </div>
    </template>

    <!-- ══ CLIMA ══ -->
    <template v-if="tab === 'clima' && cli">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">ENSO — El Niño / La Niña</div>
          <div class="flex items-baseline gap-3">
            <span class="text-2xl font-bold font-mono"
                  :class="cli.enso.status === 'El Niño' ? 'text-red-400'
                    : cli.enso.status === 'La Niña' ? 'text-blue-400' : 'text-gray-200'">
              {{ cli.enso.status }}</span>
            <span class="text-xs text-gray-500 font-mono">anomalia {{ cli.enso.anom > 0 ? '+' : '' }}{{ cli.enso.anom }}°C · {{ cli.enso.season }}</span>
          </div>
          <p class="text-xs text-gray-400 mt-2 leading-relaxed">{{ cli.enso.impact }}</p>
          <table class="w-full text-[11px] font-mono mt-3">
            <tbody>
              <tr v-for="r in [...cli.enso.recent].reverse()" :key="r.season + r.year" class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">{{ r.season }} {{ r.year }}</td>
                <td class="text-right" :class="r.anom >= 0.5 ? 'text-red-400' : r.anom <= -0.5 ? 'text-blue-400' : 'text-gray-400'">
                  {{ r.anom > 0 ? '+' : '' }}{{ r.anom }}°C</td>
              </tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600 mt-2">{{ cli.enso.source }}</p>
        </div>
        <div class="card p-4 lg:col-span-2">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Regiões produtoras (7 dias, met.no)</div>
          <div v-if="!cli.regions?.rows?.length" class="text-xs text-gray-600 py-6 text-center">clima indisponível no momento</div>
          <table v-else class="w-full text-xs font-mono">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-left">
                <th class="py-1.5">Região</th><th>Culturas</th>
                <th class="text-right">Chuva 7d</th><th class="text-right">T máx</th><th class="text-right">Alerta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in cli.regions.rows" :key="r.region" :title="r.impact"
                  class="border-t border-surface-600/30">
                <td class="py-1.5 text-gray-200">{{ r.region }}</td>
                <td class="text-gray-500">{{ r.crops }}</td>
                <td class="text-right text-gray-300">{{ r.precip_7d_mm }} mm</td>
                <td class="text-right text-gray-300">{{ r.tmax_7d }}°C</td>
                <td class="text-right">
                  <span v-for="f in r.flags || []" :key="f"
                        class="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/50 text-amber-300 ml-1">{{ f }}</span>
                  <span v-if="!(r.flags || []).length" class="text-gray-600">—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600 mt-2">{{ cli.regions?.source }}</p>
        </div>
      </div>
    </template>

    <!-- ══ SETORES ══ -->
    <template v-if="tab === 'setores'">
      <div class="flex items-center gap-2">
        <button v-for="(lbl, k) in sectorList" :key="k" @click="loadSector(k)"
                class="px-3 py-1.5 text-xs rounded-lg border transition-colors"
                :class="sectorKey === k
                  ? 'bg-accent-yellow/10 border-accent-yellow/40 text-accent-yellow font-semibold'
                  : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
          {{ lbl }}
        </button>
      </div>
      <div v-if="sec" class="space-y-3">
        <div class="card p-3 text-xs text-gray-400">💡 {{ sec.insight }}</div>
        <div class="card p-3 overflow-x-auto">
          <table class="w-full text-xs font-mono whitespace-nowrap">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-left">
                <th class="py-1.5 pr-3">Empresa</th>
                <th class="pr-3 text-right">Estoque</th>
                <th class="pr-3 text-right">Dias de estoque</th>
                <th class="pr-3 text-right">Δ dias vs 1 ano</th>
                <th class="pr-3 text-right">Margem bruta</th>
                <th class="pr-3 text-right">Receita YoY</th>
                <th class="pr-3">Trajetória (5 tri)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in sec.rows" :key="r.symbol" class="border-t border-surface-600/30">
                <td class="py-2 pr-3 text-gray-200">{{ r.symbol }}
                  <span v-if="r.suspect" class="text-amber-400 text-[10px]" title="valores implausíveis — possível erro na fonte (Yahoo)">⚠ verificar</span></td>
                <td class="pr-3 text-right text-gray-400">{{ fmtB(r.inventory) }}</td>
                <td class="pr-3 text-right text-gray-200">{{ r.days_inventory != null ? r.days_inventory + 'd' : '—' }}</td>
                <td class="pr-3 text-right" :class="(r.days_delta_yoy || 0) > 5 ? 'text-red-400' : (r.days_delta_yoy || 0) < -5 ? 'text-green-400' : 'text-gray-400'">
                  {{ r.days_delta_yoy != null ? (r.days_delta_yoy > 0 ? '+' : '') + r.days_delta_yoy + 'd' : '—' }}</td>
                <td class="pr-3 text-right text-gray-300">{{ r.gross_margin_pct != null ? r.gross_margin_pct + '%' : '—' }}</td>
                <td class="pr-3 text-right" :class="pctClass(r.rev_yoy_pct)">{{ fmtPct(r.rev_yoy_pct) }}</td>
                <td class="pr-3 text-gray-500">
                  {{ (r.days_hist || []).map((h) => h.days).join(' → ') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="text-[10px] text-gray-600">{{ sec.source }}</p>
      </div>
    </template>

    <!-- ══ CRIPTO MICRO ══ -->
    <template v-if="tab === 'cripto' && cm">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Perps monitorados</div>
          <div class="text-lg font-bold font-mono text-gray-100">{{ cm.n_perps }}</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">% funding positivo</div>
          <div class="text-lg font-bold font-mono"
               :class="cm.pct_positive > 75 ? 'text-red-400' : cm.pct_positive < 40 ? 'text-green-400' : 'text-gray-200'">
            {{ cm.pct_positive }}%</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Funding médio (8h)</div>
          <div class="text-lg font-bold font-mono text-gray-200">{{ cm.mean_funding_pct }}%</div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">OI dos majors</div>
          <div class="text-lg font-bold font-mono text-accent-yellow">{{ fmtB(totalOi) }}</div>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="card p-3 lg:col-span-2 overflow-x-auto">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Open interest & funding — majors (Bybit)</div>
          <table class="w-full text-xs font-mono whitespace-nowrap">
            <thead>
              <tr class="text-[10px] text-gray-500 uppercase text-left">
                <th class="py-1.5 pr-3">Ativo</th><th class="pr-3 text-right">Preço</th>
                <th class="pr-3 text-right">24h</th><th class="pr-3 text-right">OI (US$)</th>
                <th class="pr-3 text-right">Funding 8h</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in cm.majors" :key="m.symbol" class="border-t border-surface-600/30">
                <td class="py-1.5 pr-3 text-gray-200">{{ m.symbol }}</td>
                <td class="pr-3 text-right text-gray-300">{{ fmt(m.last) }}</td>
                <td class="pr-3 text-right" :class="pctClass(m.pct24h)">{{ fmtPct(m.pct24h) }}</td>
                <td class="pr-3 text-right text-gray-200">{{ fmtB(m.oi_usd) }}</td>
                <td class="pr-3 text-right"
                    :class="(m.funding_pct || 0) > 0.02 ? 'text-red-400' : (m.funding_pct || 0) < 0 ? 'text-green-400' : 'text-gray-400'">
                  {{ m.funding_pct != null ? m.funding_pct.toFixed(4) + '%' : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="space-y-4">
          <div class="card p-3">
            <div class="text-[10px] text-green-400 uppercase font-semibold mb-2">Funding mais NEGATIVO (shorts pagando)</div>
            <table class="w-full text-xs font-mono">
              <tbody>
                <tr v-for="e in cm.extremes.negative" :key="e.symbol" class="border-t border-surface-600/30">
                  <td class="py-1 text-gray-300">{{ e.symbol }}</td>
                  <td class="text-right text-green-400">{{ e.funding_pct }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="card p-3">
            <div class="text-[10px] text-red-400 uppercase font-semibold mb-2">Funding mais POSITIVO (longs pagando)</div>
            <table class="w-full text-xs font-mono">
              <tbody>
                <tr v-for="e in cm.extremes.positive" :key="e.symbol" class="border-t border-surface-600/30">
                  <td class="py-1 text-gray-300">{{ e.symbol }}</td>
                  <td class="text-right text-red-400">{{ e.funding_pct }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <p class="text-[10px] text-gray-600">{{ cm.note }}</p>
    </template>

    <!-- ══ ON-CHAIN ══ -->
    <template v-if="tab === 'onchain' && oc">
      <div v-if="(oc.errors || []).length" class="card p-3 text-xs text-amber-400">
        fontes indisponíveis agora: {{ oc.errors.join(' · ') }}
      </div>

      <!-- por moeda -->
      <div class="card p-4 space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <div class="text-[10px] text-gray-500 uppercase font-semibold">Por moeda</div>
          <form @submit.prevent="loadCoin()" class="flex gap-2">
            <input v-model="coinSym" placeholder="ex.: ETH, SOL, DOGE"
                   class="form-input !py-1.5 text-xs w-36 uppercase" />
            <button type="submit" class="btn-secondary !py-1.5 text-xs" :disabled="coinLoading">
              {{ coinLoading ? 'Puxando…' : 'Puxar' }}</button>
          </form>
          <button v-for="s in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'SUI']" :key="s"
                  @click="loadCoin(s)"
                  class="px-2 py-1 text-[10px] rounded border font-mono transition-colors"
                  :class="ocCoin?.symbol === s
                    ? 'bg-accent-yellow/10 border-accent-yellow/40 text-accent-yellow'
                    : 'bg-surface-700 border-surface-500 text-gray-500 hover:text-gray-300'">
            {{ s }}
          </button>
          <span v-if="coinError" class="text-xs text-red-400">{{ coinError }}</span>
        </div>

        <template v-if="ocCoin && ocCoin.profile">
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div class="rounded-lg bg-surface-600/40 p-3">
              <div class="text-[10px] text-gray-500 uppercase">{{ ocCoin.profile.name }} · #{{ ocCoin.profile.rank }}</div>
              <div class="text-base font-bold font-mono text-gray-100">${{ fmt(ocCoin.profile.price) }}</div>
              <div class="text-[10px] font-mono">
                <span :class="pctClass(ocCoin.profile.chg_7d_pct)">7d {{ fmtPct(ocCoin.profile.chg_7d_pct) }}</span>
                <span class="ml-1.5" :class="pctClass(ocCoin.profile.chg_30d_pct)">30d {{ fmtPct(ocCoin.profile.chg_30d_pct) }}</span>
              </div>
            </div>
            <div class="rounded-lg bg-surface-600/40 p-3">
              <div class="text-[10px] text-gray-500 uppercase">Mcap / Volume 24h</div>
              <div class="text-base font-bold font-mono text-gray-100">{{ fmtB(ocCoin.profile.mcap) }}</div>
              <div class="text-[10px] text-gray-500 font-mono">{{ fmtB(ocCoin.profile.volume_24h) }} vol</div>
            </div>
            <div class="rounded-lg bg-surface-600/40 p-3">
              <div class="text-[10px] text-gray-500 uppercase">Distância do ATH</div>
              <div class="text-base font-bold font-mono text-red-400">
                {{ ocCoin.profile.ath?.change_pct?.toFixed(1) }}%</div>
              <div class="text-[10px] text-gray-500 font-mono">
                ${{ fmt(ocCoin.profile.ath?.price) }} · {{ ocCoin.profile.ath?.date }}</div>
            </div>
            <div class="rounded-lg bg-surface-600/40 p-3">
              <div class="text-[10px] text-gray-500 uppercase">Supply circulante</div>
              <div class="text-base font-bold font-mono text-gray-100">{{ fmtSupply(ocCoin.profile.supply?.circulating) }}</div>
              <div class="text-[10px] text-gray-500 font-mono">
                {{ ocCoin.profile.supply?.pct_emitted != null
                  ? ocCoin.profile.supply.pct_emitted.toFixed(1) + '% do máx ' + fmtSupply(ocCoin.profile.supply.max)
                  : 'sem supply máximo' }}</div>
            </div>
            <div class="rounded-lg bg-surface-600/40 p-3">
              <div class="text-[10px] text-gray-500 uppercase">Perp Bybit</div>
              <div class="text-base font-bold font-mono"
                   :class="(ocCoin.deriv?.funding_pct || 0) > 0.02 ? 'text-red-400' : (ocCoin.deriv?.funding_pct || 0) < 0 ? 'text-green-400' : 'text-gray-200'">
                {{ ocCoin.deriv?.funding_pct != null ? ocCoin.deriv.funding_pct.toFixed(4) + '%' : '—' }}</div>
              <div class="text-[10px] text-gray-500 font-mono">OI {{ fmtB(ocCoin.deriv?.oi_usd) }}</div>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <div v-if="ocCoin.tvl" class="lg:col-span-2 rounded-lg bg-surface-600/20 p-3">
              <div class="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                TVL da chain {{ ocCoin.tvl.chain }} — 1 ano
                <span class="ml-2 font-mono" :class="pctClass(ocCoin.tvl.chg_30d_pct)">
                  {{ fmtB(ocCoin.tvl.last) }} · 30d {{ fmtPct(ocCoin.tvl.chg_30d_pct) }}</span>
              </div>
              <div ref="coinTvlChart" class="h-48" />
            </div>
            <div class="space-y-2">
              <div v-if="ocCoin.network" class="rounded-lg bg-surface-600/20 p-3">
                <div class="text-[10px] text-gray-500 uppercase font-semibold mb-1">Rede (Blockchair)</div>
                <table class="w-full text-[11px] font-mono">
                  <tbody>
                    <tr><td class="py-0.5 text-gray-500">Txs 24h</td>
                      <td class="text-right text-gray-200">{{ fmtInt(ocCoin.network.txs_24h) }}</td></tr>
                    <tr><td class="py-0.5 text-gray-500">Fee média 24h</td>
                      <td class="text-right text-gray-200">${{ ocCoin.network.avg_fee_usd_24h?.toFixed(3) }}</td></tr>
                    <tr v-if="ocCoin.network.mempool_txs != null"><td class="py-0.5 text-gray-500">Mempool</td>
                      <td class="text-right text-gray-200">{{ fmtInt(ocCoin.network.mempool_txs) }}</td></tr>
                    <tr v-if="ocCoin.network.hodling_addresses"><td class="py-0.5 text-gray-500">Endereços c/ saldo</td>
                      <td class="text-right text-gray-200">{{ fmtInt(ocCoin.network.hodling_addresses) }}</td></tr>
                  </tbody>
                </table>
              </div>
              <div class="rounded-lg bg-surface-600/20 p-3">
                <div class="text-[10px] text-gray-500 uppercase font-semibold mb-1">Dev & comunidade (CoinGecko)</div>
                <table class="w-full text-[11px] font-mono">
                  <tbody>
                    <tr><td class="py-0.5 text-gray-500">Commits 4 semanas</td>
                      <td class="text-right" :class="(ocCoin.profile.dev?.commits_4w || 0) === 0 ? 'text-red-400' : 'text-gray-200'">
                        {{ ocCoin.profile.dev?.commits_4w ?? '—' }}</td></tr>
                    <tr><td class="py-0.5 text-gray-500">GitHub stars</td>
                      <td class="text-right text-gray-200">{{ fmtInt(ocCoin.profile.dev?.stars) }}</td></tr>
                    <tr><td class="py-0.5 text-gray-500">Twitter</td>
                      <td class="text-right text-gray-200">{{ fmtInt(ocCoin.profile.community?.twitter) }}</td></tr>
                    <tr><td class="py-0.5 text-gray-500">Sentimento (votos up)</td>
                      <td class="text-right text-gray-200">{{ ocCoin.profile.sentiment_up_pct?.toFixed(0) }}%</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <p v-if="(ocCoin.errors || []).length" class="text-[10px] text-amber-400/80">
            fontes parciais: {{ ocCoin.errors.join(' · ') }}</p>
        </template>
      </div>

      <!-- métricas BTC avançadas -->
      <div class="card p-4 space-y-4" v-if="oc.btc_metrics">
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="text-[10px] text-accent-yellow uppercase font-semibold">BTC · On-chain avançado</div>
            <div class="text-[10px] text-gray-600">Cada valor identifica sua fonte; métricas proprietárias não são estimadas.</div>
          </div>
          <div class="text-right font-mono">
            <div class="text-[9px] text-gray-500 uppercase">Open Interest agregado</div>
            <div class="text-sm text-gray-100">{{ fmtB(oc.btc_metrics.open_interest?.total_usd) }}</div>
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="m in advancedMetricCards" :key="m.id" class="rounded-lg bg-surface-600/30 p-3">
            <div class="text-[9px] text-gray-500 uppercase leading-tight">{{ m.label }}</div>
            <div class="text-base font-bold font-mono text-gray-100">{{ m.value }}</div>
            <div class="text-[9px] text-gray-600">{{ m.source }}</div>
          </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <div class="text-[10px] text-gray-500 uppercase mb-1">Pi Cycle Top · BTC, 111DMA e 2×350DMA</div>
            <div ref="piCycleChart" class="h-64" />
          </div>
          <div>
            <div class="text-[10px] text-gray-500 uppercase mb-1">Realized Price · STH vs LTH</div>
            <div ref="holderPriceChart" class="h-64" />
          </div>
        </div>
        <div v-if="oc.btc_metrics.sth_sopr_mvrv_indicator">
          <div class="flex flex-wrap justify-between gap-2 mb-1">
            <div class="text-[10px] text-gray-500 uppercase">STH MVRV & 2× STH SOPR · break-even = 1</div>
            <div class="text-[10px] font-mono text-gray-400">
              MVRV {{ oc.btc_metrics.sth_sopr_mvrv_indicator.latest?.sth_mvrv?.toFixed(3) }} ·
              SOPR {{ oc.btc_metrics.sth_sopr_mvrv_indicator.latest?.sth_sopr?.toFixed(3) }}
            </div>
          </div>
          <div ref="sthSoprMvrvChart" class="h-72" />
          <div class="text-[9px] text-gray-600">{{ oc.btc_metrics.sth_sopr_mvrv_indicator.formula }}</div>
        </div>
        <details v-if="oc.btc_metrics.unavailable?.length" class="text-[10px] text-amber-400/80">
          <summary class="cursor-pointer">{{ oc.btc_metrics.unavailable.length }} métricas aguardando provedor/credencial</summary>
          <div v-for="u in oc.btc_metrics.unavailable" :key="u.id" class="mt-1">
            {{ u.label }} — {{ u.reason }}
          </div>
        </details>
      </div>

      <!-- cards de topo -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Fear & Greed</div>
          <div class="text-lg font-bold font-mono" :class="fngClass(oc.sentiment?.fear_greed?.value)">
            {{ oc.sentiment?.fear_greed?.value ?? '—' }}
            <span class="text-[10px] font-normal">{{ oc.sentiment?.fear_greed?.label }}</span>
          </div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Mcap cripto global</div>
          <div class="text-lg font-bold font-mono text-gray-100">{{ fmtB(oc.sentiment?.global?.mcap_usd) }}
            <span class="text-[10px]" :class="pctClass(oc.sentiment?.global?.mcap_change_24h_pct)">
              {{ fmtPct(oc.sentiment?.global?.mcap_change_24h_pct) }}</span></div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Dominância BTC / ETH</div>
          <div class="text-lg font-bold font-mono text-accent-yellow">
            {{ oc.sentiment?.global?.btc_dominance?.toFixed(1) }}%
            <span class="text-gray-500 text-sm">/ {{ oc.sentiment?.global?.eth_dominance?.toFixed(1) }}%</span></div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">Stablecoins (supply)</div>
          <div class="text-lg font-bold font-mono text-gray-100">{{ fmtB(oc.defi?.stablecoins?.total) }}
            <span class="text-[10px]" :class="pctClass(oc.defi?.stablecoins?.delta_30d_pct)">
              {{ fmtPct(oc.defi?.stablecoins?.delta_30d_pct) }} 30d</span></div>
        </div>
        <div class="card p-3">
          <div class="text-[10px] text-gray-500 uppercase">TVL DeFi total</div>
          <div class="text-lg font-bold font-mono text-gray-100">{{ fmtB(oc.defi?.tvl_total) }}</div>
        </div>
      </div>

      <!-- gráficos -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Fear & Greed — 90 dias</div>
          <div ref="fngChart" class="h-56" />
        </div>
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Hashrate BTC — 180 dias (EH/s)</div>
          <div ref="hashChart" class="h-56" />
        </div>
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Endereços ativos BTC — 180 dias</div>
          <div ref="addrChart" class="h-56" />
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- rede BTC -->
        <div class="card p-4 space-y-3">
          <div class="text-[10px] text-gray-500 uppercase font-semibold">Rede Bitcoin agora</div>
          <div class="grid grid-cols-4 gap-2 text-center">
            <div v-for="(v, k) in {rápida: oc.btc?.fees_satvb?.fastestFee, '30min': oc.btc?.fees_satvb?.halfHourFee, '1h': oc.btc?.fees_satvb?.hourFee, eco: oc.btc?.fees_satvb?.economyFee}"
                 :key="k" class="rounded-lg bg-surface-600/40 p-2">
              <div class="text-[9px] text-gray-500 uppercase">{{ k }}</div>
              <div class="text-sm font-bold font-mono text-gray-200">{{ v ?? '—' }}</div>
              <div class="text-[8px] text-gray-600">sat/vB</div>
            </div>
          </div>
          <table class="w-full text-[11px] font-mono">
            <tbody>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">Ajuste de dificuldade</td>
                <td class="text-right" :class="pctClass(oc.btc?.difficulty?.change_pct)">
                  {{ fmtPct(oc.btc?.difficulty?.change_pct) }} est.</td></tr>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">Progresso do período</td>
                <td class="text-right text-gray-300">{{ oc.btc?.difficulty?.progress_pct?.toFixed(1) }}% · faltam {{ oc.btc?.difficulty?.remaining_blocks }} blocos</td></tr>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">Mempool</td>
                <td class="text-right text-gray-300">{{ fmtInt(oc.btc?.snapshot?.mempool_txs) }} txs</td></tr>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">Fee média 24h</td>
                <td class="text-right text-gray-300">${{ oc.btc?.snapshot?.avg_fee_usd_24h?.toFixed(2) }}</td></tr>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">BTC em circulação</td>
                <td class="text-right text-gray-300">{{ fmtInt(oc.btc?.snapshot?.circulation_btc) }} / 21M</td></tr>
              <tr class="border-t border-surface-600/30">
                <td class="py-1 text-gray-500">Altura do bloco</td>
                <td class="text-right text-gray-300">{{ fmtInt(oc.btc?.snapshot?.blocks) }}</td></tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600">mempool.space · blockchair · blockchain.info</p>
        </div>

        <!-- TVL por chain -->
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">TVL DeFi por chain</div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="c in oc.defi?.chains || []" :key="c.name" class="border-t border-surface-600/30">
                <td class="py-1.5 text-gray-300">{{ c.name }}
                  <span class="text-gray-600 text-[10px]">{{ c.symbol }}</span></td>
                <td class="text-right text-gray-200">{{ fmtB(c.tvl) }}</td>
                <td class="text-right text-gray-500 w-14">
                  {{ oc.defi.tvl_total ? (c.tvl / oc.defi.tvl_total * 100).toFixed(1) + '%' : '' }}</td>
              </tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600 mt-2">DeFiLlama</p>
        </div>

        <!-- stablecoins -->
        <div class="card p-4">
          <div class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Stablecoins — supply & fluxo 30d</div>
          <table class="w-full text-xs font-mono">
            <tbody>
              <tr v-for="s in oc.defi?.stablecoins?.top || []" :key="s.symbol" class="border-t border-surface-600/30">
                <td class="py-1.5 text-gray-300">{{ s.symbol }}</td>
                <td class="text-right text-gray-200">{{ fmtB(s.circulating) }}</td>
                <td class="text-right w-20" :class="pctClass(s.delta_30d_pct)">{{ fmtPct(s.delta_30d_pct) }}</td>
              </tr>
            </tbody>
          </table>
          <p class="text-[10px] text-gray-600 mt-2 leading-relaxed">{{ oc.defi?.stablecoins?.note }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import {
  getAltIndicators, getAltSupplyChain, getAltTraffic, getAltClimate,
  getAltSectors, getAltCryptoMicro, getAltOnchain, getAltOnchainCoin,
} from '@/api/client.js'

const TABS = [
  { key: 'painel', label: 'PAINEL' },
  { key: 'supply', label: 'SUPPLY CHAIN' },
  { key: 'trafego', label: 'TRÁFEGO AÉREO' },
  { key: 'clima', label: 'CLIMA & ENSO' },
  { key: 'setores', label: 'SETORES' },
  { key: 'cripto', label: 'CRIPTO MICRO' },
  { key: 'onchain', label: 'ON-CHAIN' },
]
const tab = ref('painel')
const loading = ref(false)
const error = ref(null)
let Plotly = null

const ind = ref(null)
const sc = ref(null)
const tsa = ref(null)
const cli = ref(null)
const sec = ref(null)
const sectorKey = ref('varejo')
const cm = ref(null)
const oc = ref(null)
const ocCoin = ref(null)
const coinSym = ref('')
const coinLoading = ref(false)
const coinError = ref(null)
const coinTvlChart = ref(null)

const gscpiChart = ref(null)
const tsaChart = ref(null)
const fngChart = ref(null)
const hashChart = ref(null)
const addrChart = ref(null)
const piCycleChart = ref(null)
const holderPriceChart = ref(null)
const sthSoprMvrvChart = ref(null)
const indRefs = {}

const sectorList = computed(() => sec.value?.sectors
  || { varejo: 'Varejo (EUA)', semis: 'Semicondutores', autos: 'Automóveis', energia: 'Energia (integradas)' })
const totalOi = computed(() =>
  (cm.value?.majors || []).reduce((s, m) => s + (m.oi_usd || 0), 0))
const advancedMetricCards = computed(() => {
  const series = oc.value?.btc_metrics?.series || {}
  const defs = [
    ['exchange_whale_ratio', 'Exchange Whale Ratio'],
    ['estimated_leverage_ratio', 'Estimated Leverage Ratio'],
    ['nupl', 'NUPL'],
    ['retail_demand_30d', 'Retail Demand · Δ30D'],
    ['sth_realized_price', 'STH Realized Price'],
    ['lth_realized_price', 'LTH Realized Price'],
    ['whale_realized_price', 'Whales Realized Price'],
    ['whale_last_active', 'Whale Last Active'],
  ]
  return defs.map(([id, label]) => {
    const s = series[id]
    const v = s?.values?.at(-1)
    const money = id.includes('price')
    return { id, label, value: v == null ? '—' : money ? '$' + fmt(v) : Number(v).toFixed(3), source: s?.source || 'não configurado' }
  })
})

function setIndRef(el, id) {
  if (el) indRefs[id] = el
}

const LAYOUT = (h) => ({
  template: 'plotly_dark', paper_bgcolor: '#000', plot_bgcolor: '#080808',
  font: { color: '#d0d0d0', size: 10 }, height: h,
  margin: { t: 8, r: 10, b: 30, l: 45 },
  xaxis: { type: 'date', gridcolor: '#1e1e1e' },
  yaxis: { gridcolor: '#1e1e1e' },
  showlegend: false,
})
const CFG = { responsive: true, displaylogo: false, displayModeBar: false }

async function plotly() {
  if (!Plotly) Plotly = (await import('plotly.js-dist-min')).default
  return Plotly
}

function gaugePos(i) {
  const [lo, hi] = i.range || [-2.5, 2.5]
  const p = Math.max(0, Math.min(1, (i.value - lo) / (hi - lo)))
  return `calc(${(p * 100).toFixed(1)}% - 6px)`
}
function readingClass(r) {
  if (['RISK-ON', 'FOLGA'].includes(r)) return 'bg-green-900/50 text-green-300'
  if (['RISK-OFF', 'PRESSÃO ALTA', 'PRESSÃO INFLACIONÁRIA'].includes(r)) return 'bg-red-900/50 text-red-300'
  return 'bg-surface-600 text-gray-300'
}

async function setTab(k) {
  tab.value = k
  error.value = null
  try {
    loading.value = true
    if (k === 'painel' && !ind.value) {
      ind.value = (await getAltIndicators()).data
      await drawIndicators()
    } else if (k === 'supply' && !sc.value) {
      sc.value = (await getAltSupplyChain()).data
      await drawGscpi()
    } else if (k === 'trafego' && !tsa.value) {
      tsa.value = (await getAltTraffic()).data
      await drawTsa()
    } else if (k === 'clima' && !cli.value) {
      cli.value = (await getAltClimate()).data
    } else if (k === 'setores' && !sec.value) {
      await loadSector(sectorKey.value)
    } else if (k === 'cripto' && !cm.value) {
      cm.value = (await getAltCryptoMicro()).data
    } else if (k === 'onchain' && !oc.value) {
      oc.value = (await getAltOnchain()).data
      await drawOnchain()
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function loadSector(k) {
  sectorKey.value = k
  loading.value = true
  error.value = null
  try {
    sec.value = (await getAltSectors(k)).data
  } catch (e) {
    error.value = e.response?.data?.error || e.message
  } finally {
    loading.value = false
  }
}

async function drawIndicators() {
  const P = await plotly()
  await nextTick()
  for (const i of ind.value?.indicators || []) {
    const el = indRefs[i.id]
    if (!el || !i.history) continue
    P.newPlot(el, [{
      type: 'scatter', mode: 'lines',
      x: i.history.ts.map((t) => new Date(t)), y: i.history.values,
      line: { color: '#f5c518', width: 1.5 },
      fill: 'tozeroy', fillcolor: 'rgba(245,197,24,0.08)',
    }], LAYOUT(128), CFG)
  }
}

async function drawGscpi() {
  const P = await plotly()
  await nextTick()
  if (!gscpiChart.value || !sc.value) return
  const g = sc.value.gscpi
  P.newPlot(gscpiChart.value, [{
    type: 'scatter', mode: 'lines',
    x: g.ts.map((t) => new Date(t + '-01')), y: g.values,
    line: { color: '#f5c518', width: 1.5 },
  }], {
    ...LAYOUT(288),
    shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 0, y1: 0,
               line: { color: '#555', width: 1, dash: 'dot' } }],
  }, CFG)
}

async function drawTsa() {
  const P = await plotly()
  await nextTick()
  if (!tsaChart.value || !tsa.value) return
  const x = tsa.value.ts.map((t) => new Date(t))
  P.newPlot(tsaChart.value, [
    { type: 'scatter', mode: 'lines', x, y: tsa.value.passengers,
      name: 'diário', line: { color: '#4dabf7', width: 1 }, opacity: 0.5 },
    { type: 'scatter', mode: 'lines', x, y: tsa.value.avg7,
      name: 'média 7d', line: { color: '#f5c518', width: 2 } },
  ], { ...LAYOUT(288), showlegend: true, legend: { orientation: 'h', y: 1.1 } }, CFG)
}

async function drawOnchain() {
  const P = await plotly()
  await nextTick()
  const fg = oc.value?.sentiment?.fear_greed?.series
  if (fngChart.value && fg) {
    P.newPlot(fngChart.value, [{
      type: 'scatter', mode: 'lines',
      x: fg.ts.map((t) => new Date(t)), y: fg.values,
      line: { color: '#f5c518', width: 1.5 },
      fill: 'tozeroy', fillcolor: 'rgba(245,197,24,0.08)',
    }], {
      ...LAYOUT(224),
      yaxis: { gridcolor: '#1e1e1e', range: [0, 100] },
      shapes: [
        { type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 25, y1: 25,
          line: { color: '#7f1d1d', width: 1, dash: 'dot' } },
        { type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 75, y1: 75,
          line: { color: '#14532d', width: 1, dash: 'dot' } },
      ],
    }, CFG)
  }
  const hr = oc.value?.btc?.hashrate
  if (hashChart.value && hr) {
    P.newPlot(hashChart.value, [{
      type: 'scatter', mode: 'lines',
      x: hr.ts.map((t) => new Date(t)),
      y: hr.values.map((v) => (v != null ? v / 1e6 : null)),   // TH/s → EH/s
      line: { color: '#4dabf7', width: 1.5 },
    }], LAYOUT(224), CFG)
  }
  const ad = oc.value?.btc?.addresses
  if (addrChart.value && ad) {
    P.newPlot(addrChart.value, [{
      type: 'scatter', mode: 'lines',
      x: ad.ts.map((t) => new Date(t)), y: ad.values,
      line: { color: '#69db7c', width: 1.5 },
    }], LAYOUT(224), CFG)
  }
  const pi = oc.value?.btc_metrics?.pi_cycle
  if (piCycleChart.value && pi) {
    const x = pi.ts.map((t) => new Date(t))
    P.newPlot(piCycleChart.value, [
      { type: 'scatter', mode: 'lines', x, y: pi.price, name: 'BTC', line: { color: '#888', width: 1 } },
      { type: 'scatter', mode: 'lines', x, y: pi.dma111, name: '111DMA', line: { color: '#f5c518', width: 1.5 } },
      { type: 'scatter', mode: 'lines', x, y: pi.dma350x2, name: '2×350DMA', line: { color: '#ef4444', width: 1.5 } },
    ], { ...LAYOUT(256), showlegend: true, legend: { orientation: 'h', y: 1.12 }, yaxis: { type: 'log', gridcolor: '#1e1e1e' } }, CFG)
  }
  const sth = oc.value?.btc_metrics?.series?.sth_realized_price
  const lth = oc.value?.btc_metrics?.series?.lth_realized_price
  if (holderPriceChart.value && (sth || lth)) {
    const traces = []
    if (sth) traces.push({ type: 'scatter', mode: 'lines', x: sth.ts.map((t) => new Date(t)), y: sth.values, name: 'STH', line: { color: '#f5c518', width: 1.5 } })
    if (lth) traces.push({ type: 'scatter', mode: 'lines', x: lth.ts.map((t) => new Date(t)), y: lth.values, name: 'LTH', line: { color: '#4dabf7', width: 1.5 } })
    P.newPlot(holderPriceChart.value, traces, { ...LAYOUT(256), showlegend: true, legend: { orientation: 'h', y: 1.12 } }, CFG)
  }
  const sm = oc.value?.btc_metrics?.sth_sopr_mvrv_indicator
  if (sthSoprMvrvChart.value && sm) {
    const x = sm.ts.map((t) => new Date(t))
    P.newPlot(sthSoprMvrvChart.value, [
      { type: 'scatter', mode: 'lines', x, y: sm.mvrv_positive, name: 'MVRV-STH (+)', line: { color: '#38d996', width: 1.3 } },
      { type: 'scatter', mode: 'lines', x, y: sm.mvrv_negative, name: 'MVRV-STH (−)', line: { color: '#f74870', width: 1.3 } },
      { type: 'scatter', mode: 'lines', x, y: sm.sopr2_positive, name: '2× STH-SOPR (+)', line: { color: '#4dabf7', width: 1.1 } },
      { type: 'scatter', mode: 'lines', x, y: sm.sopr2_negative, name: '2× STH-SOPR (−)', line: { color: '#f59f00', width: 1.1 } },
    ], {
      ...LAYOUT(288), showlegend: true, legend: { orientation: 'h', y: 1.1 },
      shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 1, y1: 1,
        line: { color: '#aaa', width: 1, dash: 'dot' } }],
    }, CFG)
  }
}

async function loadCoin(sym) {
  const s = (sym || coinSym.value).trim().toUpperCase()
  if (!s) return
  coinSym.value = s
  coinLoading.value = true
  coinError.value = null
  try {
    ocCoin.value = (await getAltOnchainCoin(s)).data
    const P = await plotly()
    await nextTick()
    const t = ocCoin.value?.tvl
    if (coinTvlChart.value && t) {
      P.newPlot(coinTvlChart.value, [{
        type: 'scatter', mode: 'lines',
        x: t.ts.map((x) => new Date(x)), y: t.values,
        line: { color: '#f5c518', width: 1.5 },
        fill: 'tozeroy', fillcolor: 'rgba(245,197,24,0.06)',
      }], LAYOUT(192), CFG)
    }
  } catch (e) {
    coinError.value = e.response?.data?.error || e.message
    ocCoin.value = null
  } finally {
    coinLoading.value = false
  }
}

function fmtSupply(v) {
  if (v == null) return '—'
  if (v >= 1e12) return (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M'
  return Math.round(v).toLocaleString('pt-BR')
}

function fngClass(v) {
  if (v == null) return 'text-gray-300'
  if (v <= 25) return 'text-red-400'
  if (v >= 75) return 'text-green-400'
  return 'text-gray-200'
}

function fmt(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: Math.abs(v) < 1 ? 6 : 2 })
}
function fmtInt(v) {
  return v != null ? Number(v).toLocaleString('pt-BR') : '—'
}
function fmtPct(v) {
  if (v == null) return '—'
  return (v > 0 ? '+' : '') + Number(v).toFixed(1) + '%'
}
function pctClass(v) {
  if (v == null) return 'text-gray-500'
  return v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400'
}
function fmtB(v) {
  if (v == null) return '—'
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B'
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M'
  return '$' + Math.round(v).toLocaleString('pt-BR')
}

onMounted(() => setTab('painel'))
</script>
