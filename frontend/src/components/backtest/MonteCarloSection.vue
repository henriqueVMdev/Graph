<template>
  <div class="space-y-3">

    <!-- ── Top-level tabs ────────────────────────────────────────────────── -->
    <div class="flex gap-1 border-b border-surface-500 pb-2">
      <button
        v-for="(t, i) in topTabs" :key="i"
        class="tab-btn" :class="{ active: topTab === i }"
        @click="topTab = i"
      >{{ t }}</button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         TAB 0 — GBM Projeção (existing)
    ═══════════════════════════════════════════════════════════════════════ -->
    <div v-show="topTab === 0" class="space-y-3">
      <!-- Controls -->
      <div class="flex flex-wrap gap-2 items-center">

        <!-- Simulações GBM -->
        <div class="mc-dropdown-wrap">
          <button @click="openDd = openDd === 'gbmSims' ? null : 'gbmSims'" class="mc-dd-btn">
            Simulações: <span class="text-accent-yellow font-semibold">{{ gbmSims }}</span>
            <svg class="w-3 h-3 ml-1 transition-transform" :class="openDd==='gbmSims'?'rotate-180':''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
          <div v-if="openDd === 'gbmSims'" class="mc-dd-list">
            <button v-for="n in [2000, 4000, 6000, 8000, 10000]" :key="n" @click="gbmSims = n; openDd = null"
              class="mc-dd-item" :class="gbmSims === n ? 'text-accent-yellow font-semibold' : ''">{{ n }}</button>
          </div>
        </div>

        <!-- Horizonte -->
        <div class="mc-dropdown-wrap">
          <button @click="openDd = openDd === 'horizon' ? null : 'horizon'" class="mc-dd-btn">
            Horizonte: <span class="text-accent-yellow font-semibold">{{ horizonOptions.find(o=>o.val===horizon)?.label }}</span>
            <svg class="w-3 h-3 ml-1 transition-transform" :class="openDd==='horizon'?'rotate-180':''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
          <div v-if="openDd === 'horizon'" class="mc-dd-list">
            <button v-for="opt in horizonOptions" :key="opt.val" @click="horizon = opt.val; openDd = null"
              class="mc-dd-item" :class="horizon === opt.val ? 'text-accent-yellow font-semibold' : ''">{{ opt.label }}</button>
          </div>
        </div>

        <button @click="gbmSeed = Math.floor(Math.random()*1e6)" :disabled="gbmLoading"
          class="ml-auto px-3 py-1 text-xs rounded-md bg-surface-600 text-gray-400 hover:bg-surface-500 border border-surface-400 transition-colors disabled:opacity-40"
        >↺ Regenerar</button>
      </div>
      <div v-if="gbmLoading" class="flex items-center justify-center h-32 text-gray-500 text-sm gap-2">
        <span class="dollar-loader-sm">$</span>
        Calculando simulacoes...
      </div>
      <div v-else-if="gbmError" class="text-red-400 text-xs p-3 bg-red-400/10 rounded-lg">{{ gbmError }}</div>
      <div v-show="!gbmLoading && !gbmError" ref="gbmChart" style="min-height:520px;" class="w-full"></div>
      <div v-if="gbmData && !gbmLoading" class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div class="card p-3 text-center">
          <div class="text-xs text-gray-500 mb-0.5">Capital Mediano</div>
          <div class="text-sm font-semibold text-accent-yellow">{{ fmtMoney(gbmData.stats.median_final) }}</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-xs text-gray-500 mb-0.5">P10 · pessimista</div>
          <div class="text-sm font-semibold text-red-400">{{ fmtMoney(gbmData.stats.p10_final) }}</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-xs text-gray-500 mb-0.5">P90 · otimista</div>
          <div class="text-sm font-semibold text-green-400">{{ fmtMoney(gbmData.stats.p90_final) }}</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-xs text-gray-500 mb-0.5">Prob. de Lucro</div>
          <div class="text-sm font-semibold"
            :class="gbmData.stats.prob_profit >= 50 ? 'text-green-400' : 'text-red-400'"
          >{{ gbmData.stats.prob_profit?.toFixed(1) }}%</div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         TAB 1 — Validação MC (4 métodos)
    ═══════════════════════════════════════════════════════════════════════ -->
    <div v-show="topTab === 1" class="space-y-3">

      <!-- Run controls -->
      <div class="flex flex-wrap gap-2 items-center">

        <!-- Simulações MC -->
        <div class="mc-dropdown-wrap">
          <button @click="openDd = openDd === 'valSims' ? null : 'valSims'" class="mc-dd-btn">
            <span class="mc-info-wrap cursor-default">Simulações<div class="mc-tooltip" style="width:240px;">Número de cenários gerados por cada método Monte Carlo. Mais simulações = distribuição mais precisa e estável, porém mais lento. 500 é um bom equilíbrio entre velocidade e precisão.</div></span>:
            <span class="text-accent-yellow font-semibold">{{ valSims }}</span>
            <svg class="w-3 h-3 ml-1 transition-transform" :class="openDd==='valSims'?'rotate-180':''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
          <div v-if="openDd === 'valSims'" class="mc-dd-list">
            <button v-for="n in [2000, 4000, 6000, 8000, 10000]" :key="n" @click="valSims = n; openDd = null"
              class="mc-dd-item" :class="valSims === n ? 'text-accent-yellow font-semibold' : ''">{{ n }}</button>
          </div>
        </div>

        <!-- Permutações -->
        <div class="mc-dropdown-wrap">
          <button @click="openDd = openDd === 'valPerms' ? null : 'valPerms'" class="mc-dd-btn">
            <span class="mc-info-wrap cursor-default">Permutações<div class="mc-tooltip" style="width:260px;">Número de embaralhamentos usados no Permutation Test para calcular o p-value. Mais permutações = p-value mais preciso. 300 já é suficiente para a maioria dos casos; use 500 se quiser maior confiança estatística.</div></span>:
            <span class="text-accent-yellow font-semibold">{{ valPerms }}</span>
            <svg class="w-3 h-3 ml-1 transition-transform" :class="openDd==='valPerms'?'rotate-180':''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
          <div v-if="openDd === 'valPerms'" class="mc-dd-list">
            <button v-for="n in [100, 300, 500]" :key="n" @click="valPerms = n; openDd = null"
              class="mc-dd-item" :class="valPerms === n ? 'text-accent-yellow font-semibold' : ''">{{ n }}</button>
          </div>
        </div>

        <button @click="runValidation"
          :disabled="valLoading"
          class="ml-auto flex items-center gap-2 px-4 py-1.5 text-xs rounded-md font-semibold bg-accent-yellow text-black hover:bg-yellow-400 transition-colors disabled:opacity-40"
        >
          <svg v-if="valLoading" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          {{ valLoading ? 'Calculando...' : '▶ Executar Validação' }}
        </button>
      </div>

      <div v-if="valError" class="text-red-400 text-xs p-3 bg-red-400/10 rounded-lg">{{ valError }}</div>

      <!-- Placeholder before first run -->
      <div v-if="!valData && !valLoading" class="flex flex-col items-center justify-center text-center text-gray-500 text-sm" style="min-height:520px;">
        <svg class="w-10 h-10 mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        Clique em "Executar Validação" para rodar a análise completa
      </div>

      <!-- First-run loading indicator (no previous data) -->
      <div v-if="!valData && valLoading" class="flex flex-col items-center justify-center text-center" style="min-height:520px;">
        <div class="mc-dollar-loader">$</div>
        <div class="text-gray-500 text-xs mt-4">Calculando simulações...</div>
      </div>

      <!-- Results (kept visible during re-runs) -->
      <template v-if="valData">
        <!-- Method selector -->
        <div class="flex gap-1 border-b border-surface-600 pb-2">
          <button
            v-for="(m, i) in mcMethods" :key="m.key"
            class="tab-btn" :class="{ active: mcTab === i }"
            @click="mcTab = i; renderMcCharts()"
          >{{ m.label }}</button>
        </div>

        <!-- Sub-tabs: Equity / Drawdown / Sharpe -->
        <div class="flex gap-1 mb-2">
          <button v-for="(s, i) in subTabs" :key="i"
            class="px-3 py-1 text-xs rounded-md transition-colors"
            :class="subTab === i ? 'bg-surface-500 text-gray-100' : 'bg-surface-700 text-gray-500 hover:bg-surface-600'"
            @click="subTab = i; renderMcCharts()"
          >{{ s }}</button>
        </div>

        <!-- Chart areas -->
        <div class="relative">
          <div v-show="subTab === 0" ref="boomEl"  style="min-height:520px;" class="w-full"></div>
          <div v-show="subTab === 1" ref="ddEl"    style="min-height:460px;" class="w-full"></div>
          <div v-show="subTab === 2" ref="shEl"    style="min-height:460px;" class="w-full"></div>
          <!-- Loading overlay (shown while re-running) -->
          <div v-if="valLoading" class="mc-chart-overlay">
            <div class="mc-dollar-loader">$</div>
          </div>
        </div>

        <!-- Stats grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
          <template v-if="currentMc">
            <!-- Retorno Mediano -->
            <div class="card p-3 text-center group relative">
              <div class="text-xs text-gray-500 mb-0.5 flex items-center justify-center gap-1">
                Retorno Mediano
                <span class="mc-info-wrap"><span class="mc-info-icon">?</span><div class="mc-tooltip">Retorno percentual da equity curve na simulação mediana (P50). Metade das simulações ficou acima, metade abaixo desse valor.</div></span>
              </div>
              <div class="text-sm font-semibold"
                :class="currentMc.final_equity_pct.p50 >= 0 ? 'text-green-400' : 'text-red-400'"
              >{{ currentMc.final_equity_pct.p50?.toFixed(1) }}%</div>
            </div>
            <!-- DD P95 -->
            <div class="card p-3 text-center group relative">
              <div class="text-xs text-gray-500 mb-0.5 flex items-center justify-center gap-1">
                DD P95 · pior cenário
                <span class="mc-info-wrap"><span class="mc-info-icon">?</span><div class="mc-tooltip">Drawdown máximo no percentil 95 das simulações. Ou seja, em 95% dos cenários o drawdown não passou desse valor — representa o pior cenário plausível da estratégia.</div></span>
              </div>
              <div class="text-sm font-semibold text-red-400">{{ currentMc.max_drawdown.p95?.toFixed(1) }}%</div>
            </div>
            <!-- Rank Sharpe -->
            <div class="card p-3 text-center group relative">
              <div class="text-xs text-gray-500 mb-0.5 flex items-center justify-center gap-1">
                Rank Sharpe
                <span class="mc-info-wrap"><span class="mc-info-icon">?</span><div class="mc-tooltip">Posição percentual do Sharpe original em relação às simulações. Se está no 80º percentil, significa que o backtest real teve Sharpe melhor que 80% das simulações — quanto maior, mais robusta é a estratégia.</div></span>
              </div>
              <div class="text-sm font-semibold"
                :class="currentMc.backtest_rank_sharpe >= 50 ? 'text-green-400' : 'text-red-400'"
              >{{ currentMc.backtest_rank_sharpe?.toFixed(0) }}º percentil</div>
            </div>
            <!-- Prob. Ruína -->
            <div class="card p-3 text-center group relative">
              <div class="text-xs text-gray-500 mb-0.5 flex items-center justify-center gap-1">
                Prob. Ruína
                <span class="mc-info-wrap"><span class="mc-info-icon">?</span><div class="mc-tooltip">Percentual de simulações em que o capital final ficou abaixo de 50% do capital inicial. Indica a probabilidade da estratégia sofrer uma perda catastrófica — abaixo de 5% é considerado seguro.</div></span>
              </div>
              <div class="text-sm font-semibold"
                :class="currentMc.ruin_prob < 5 ? 'text-green-400' : 'text-red-400'"
              >{{ currentMc.ruin_prob?.toFixed(1) }}%</div>
            </div>
          </template>
        </div>

        <!-- Methods legend (collapsible) -->
        <div class="mt-4 rounded-xl border border-surface-600 bg-surface-800/50 overflow-hidden">
          <button
            @click="showMethodsLegend = !showMethodsLegend"
            class="w-full flex items-center justify-between px-4 py-3 text-xs font-semibold text-gray-400 hover:text-gray-300 hover:bg-surface-700/50 transition-colors uppercase tracking-widest"
          >
            <span>Sobre os Métodos de Simulação</span>
            <svg
              class="w-3.5 h-3.5 transition-transform duration-200"
              :class="showMethodsLegend ? 'rotate-180' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div v-show="showMethodsLegend" class="px-4 pb-4 grid sm:grid-cols-2 gap-3 border-t border-surface-600">
            <div class="flex gap-3 pt-3">
              <span class="mt-0.5 w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0"></span>
              <div>
                <div class="text-xs font-semibold text-gray-300">Reshuffle (sem reposição)</div>
                <div class="text-xs text-gray-500 leading-relaxed">Embaralha a ordem dos trades sem repetição. Preserva exatamente os mesmos resultados individuais de cada trade, mas testa se a ordem de entrada/saída importa. Ideal para verificar se os lucros dependem de timing específico.</div>
              </div>
            </div>
            <div class="flex gap-3 pt-3">
              <span class="mt-0.5 w-2 h-2 rounded-full bg-blue-400 flex-shrink-0"></span>
              <div>
                <div class="text-xs font-semibold text-gray-300">Bootstrap (com reposição)</div>
                <div class="text-xs text-gray-500 leading-relaxed">Reamostrado com reposição — cada simulação sorteia trades aleatoriamente, podendo repetir o mesmo trade. Simula variações plausíveis do histórico e expande o espaço de cenários possíveis.</div>
              </div>
            </div>
            <div class="flex gap-3 pt-3">
              <span class="mt-0.5 w-2 h-2 rounded-full bg-green-400 flex-shrink-0"></span>
              <div>
                <div class="text-xs font-semibold text-gray-300">Aleatorizado (ruído gaussiano)</div>
                <div class="text-xs text-gray-500 leading-relaxed">Adiciona ruído gaussiano ao PnL de cada trade, simulando variações de execução realistas como derrapagem, slippage e impacto de mercado. Útil para estressar a estratégia com pequenas perturbações.</div>
              </div>
            </div>
            <div class="flex gap-3 pt-3">
              <span class="mt-0.5 w-2 h-2 rounded-full bg-purple-400 flex-shrink-0"></span>
              <div>
                <div class="text-xs font-semibold text-gray-300">Alt. Retornos (equity curve)</div>
                <div class="text-xs text-gray-500 leading-relaxed">Embaralha os retornos diários da equity curve, destruindo a correlação temporal mas preservando a distribuição estatística dos retornos. Avalia a robustez da curva de capital como um todo, independente dos trades individuais.</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         TAB 2 — Permutation Test
    ═══════════════════════════════════════════════════════════════════════ -->
    <div v-show="topTab === 2" class="space-y-4" style="min-height:520px;">
      <div v-if="!valData && !valLoading" class="text-gray-500 text-sm text-center flex items-center justify-center" style="min-height:520px;">
        Execute a Validação MC (aba anterior) para ver o Permutation Test.
      </div>
      <template v-if="valData?.permutation_test">
        <!-- p-value banner -->
        <div class="rounded-xl p-4 border"
          :class="valData.permutation_test.approved
            ? 'border-green-500/40 bg-green-500/5'
            : 'border-red-500/40 bg-red-500/5'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xs text-gray-400 mb-1">Resultado do Permutation Test (Timothy Masters)</div>
              <div class="text-2xl font-bold"
                :class="valData.permutation_test.approved ? 'text-green-400' : 'text-red-400'"
              >{{ valData.permutation_test.conclusion }}</div>
              <div class="text-xs text-gray-400 mt-1">
                p-value = {{ valData.permutation_test.p_value?.toFixed(4) }}
                ({{ valData.permutation_test.approved ? 'p &lt; 0.05 → edge estatisticamente significante' : 'p ≥ 0.05 → sem evidência de edge' }})
              </div>
            </div>
            <div class="text-right">
              <div class="text-xs text-gray-500 mb-1">Sharpe Original</div>
              <div class="text-xl font-semibold text-accent-yellow">{{ valData.permutation_test.original_sharpe?.toFixed(4) }}</div>
              <div class="text-xs text-gray-500 mt-1">Mediana aleatória: {{ valData.permutation_test.median_random?.toFixed(4) }}</div>
            </div>
          </div>
        </div>

        <!-- Permutation chart -->
        <div ref="permEl" style="min-height:460px;" class="w-full"></div>

        <!-- Stats -->
        <div class="grid grid-cols-3 gap-3">
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-0.5">p-value</div>
            <div class="text-base font-semibold"
              :class="valData.permutation_test.p_value < 0.05 ? 'text-green-400' : 'text-red-400'"
            >{{ valData.permutation_test.p_value?.toFixed(4) }}</div>
          </div>
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-0.5">Rank Percentil</div>
            <div class="text-base font-semibold text-accent-yellow">{{ valData.permutation_test.backtest_rank?.toFixed(1) }}º</div>
          </div>
          <div class="card p-3 text-center">
            <div class="text-xs text-gray-500 mb-0.5">Permutações</div>
            <div class="text-base font-semibold text-gray-300">{{ valData.permutation_test.n_perms?.toLocaleString('pt-BR') }}</div>
          </div>
        </div>

        <!-- Explanation -->
        <div class="text-xs text-gray-500 bg-surface-700 rounded-lg p-3 leading-relaxed">
          <span class="text-gray-400 font-medium">Como funciona:</span>
          Os log-retornos da equity curve são embaralhados aleatoriamente <em>{{ valData.permutation_test.n_perms?.toLocaleString('pt-BR') }}</em> vezes,
          destruindo os padrões temporais mas preservando as propriedades estatísticas dos retornos.
          O Sharpe de cada série aleatória é comparado com o Sharpe original.
          Um p-value &lt; 0.05 indica que a estratégia tem edge genuíno, não explicado por aleatoriedade.
        </div>
      </template>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         TAB 3 — Relatório
    ═══════════════════════════════════════════════════════════════════════ -->
    <div v-show="topTab === 3" class="space-y-3" style="min-height:520px;">
      <div v-if="!valData" class="text-gray-500 text-sm text-center flex items-center justify-center" style="min-height:520px;">
        Execute a Validação MC (aba Validação) para gerar o relatório.
      </div>
      <template v-if="valData?.report">
        <div class="flex justify-end">
          <button @click="copyReport"
            class="px-3 py-1.5 text-xs rounded-md bg-surface-600 text-gray-400 hover:bg-surface-500 border border-surface-400 transition-colors flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
            {{ copied ? 'Copiado!' : 'Copiar' }}
          </button>
        </div>
        <pre class="text-xs text-gray-300 bg-surface-800 rounded-xl p-4 overflow-x-auto leading-relaxed font-mono border border-surface-600 whitespace-pre">{{ valData.report }}</pre>

        <!-- Verdict chips -->
        <div v-if="valData.permutation_test" class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div v-for="v in verdicts" :key="v.label"
            class="rounded-lg p-3 border text-center"
            :class="v.ok ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'"
          >
            <div class="text-base mb-0.5">{{ v.ok ? '✓' : '✗' }}</div>
            <div class="text-xs" :class="v.ok ? 'text-green-400' : 'text-red-400'">{{ v.label }}</div>
          </div>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { purgeChart } from '@/composables/useCharts.js'
import { runMonteCarlo, runValidation as apiRunValidation } from '@/api/client.js'
import { useBacktestStore } from '@/stores/backtest.js'

const props = defineProps({
  equityCurve: { type: Object, required: true },
})

const store = useBacktestStore()

// ── Top tabs ─────────────────────────────────────────────────────────────────
const topTabs = ['GBM · Projeção', 'Validação MC', 'Permutation Test', 'Relatório']
const topTab  = ref(0)

// ── GBM state (existing) ──────────────────────────────────────────────────────
const gbmChart  = ref(null)
const gbmSims   = ref(2000)
const horizon   = ref(252)
const gbmSeed   = ref(Math.floor(Math.random() * 1e6))
const gbmLoading = ref(false)
const gbmError  = ref(null)
const gbmData   = ref(null)

const horizonOptions = [
  { val: 252,  label: '1 ano'  },
  { val: 504,  label: '2 anos' },
  { val: 1008, label: '4 anos' },
  { val: 1260, label: '5 anos' },
]

function fmtMoney(v) {
  return '$' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

async function fetchGbm() {
  if (!props.equityCurve?.values?.length) return
  gbmLoading.value = true
  gbmError.value   = null
  try {
    const { data } = await runMonteCarlo(props.equityCurve, gbmSims.value, horizon.value, gbmSeed.value)
    gbmData.value = data
    await renderGbmChart(data)
  } catch (e) {
    gbmError.value = e.response?.data?.error || e.message
  } finally {
    gbmLoading.value = false
  }
}

async function renderGbmChart(d) {
  if (!gbmChart.value) return
  const Plotly = (await import('plotly.js-dist-min')).default
  const lastDate = d.proj_dates[0]
  const traces = []

  traces.push({
    type: 'scatter', mode: 'lines', name: 'Histórico',
    x: d.hist_dates, y: d.hist_values,
    line: { color: '#f5c518', width: 2 },
    hovertemplate: '<b>%{x}</b><br>Capital: $%{y:,.2f}<extra></extra>',
  })
  for (const path of d.sample_paths) {
    traces.push({
      type: 'scatter', mode: 'lines',
      x: d.proj_dates, y: path,
      line: { color: 'rgba(120,120,140,0.12)', width: 1 },
      showlegend: false, hoverinfo: 'skip',
    })
  }
  traces.push({ type: 'scatter', mode: 'lines', name: 'P10',
    x: d.proj_dates, y: d.p10, line: { color: 'rgba(248,113,113,0.7)', width: 1, dash: 'dot' },
    hovertemplate: 'P10: $%{y:,.0f}<extra></extra>' })
  traces.push({ type: 'scatter', mode: 'lines', name: 'Mediana (P50)',
    x: d.proj_dates, y: d.p50, line: { color: '#a78bfa', width: 2 },
    fill: 'tonexty', fillcolor: 'rgba(248,113,113,0.08)',
    hovertemplate: 'P50: $%{y:,.0f}<extra></extra>' })
  traces.push({ type: 'scatter', mode: 'lines', name: 'P90',
    x: d.proj_dates, y: d.p90, line: { color: 'rgba(34,197,94,0.7)', width: 1, dash: 'dot' },
    fill: 'tonexty', fillcolor: 'rgba(34,197,94,0.08)',
    hovertemplate: 'P90: $%{y:,.0f}<extra></extra>' })
  traces.push({ type: 'scatter', mode: 'lines', name: 'Regressão Linear',
    x: d.proj_dates, y: d.reg_line, line: { color: '#ffffff', width: 2, dash: 'dash' },
    hovertemplate: 'Regressão: $%{y:,.0f}<extra></extra>' })

  const layout = {
    template: 'plotly_dark', paper_bgcolor: '#000000', plot_bgcolor: '#080808',
    font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 },
    height: 520, autosize: true, margin: { t: 30, r: 20, b: 50, l: 75 },
    xaxis: { gridcolor: '#1e1e1e', linecolor: '#2a2a2a', tickfont: { color: '#707070' } },
    yaxis: { title: 'Capital ($)', gridcolor: '#1e1e1e', linecolor: '#2a2a2a',
      tickprefix: '$', tickfont: { color: '#707070' } },
    shapes: [{ type: 'line', xref: 'x', x0: lastDate, x1: lastDate,
      yref: 'paper', y0: 0, y1: 1, line: { color: '#f5c518', dash: 'dot', width: 1 } }],
    annotations: [{ xref: 'x', x: lastDate, yref: 'paper', y: 0.98,
      text: '◀ histórico · projeção ▶', showarrow: false,
      font: { size: 10, color: '#f5c518' }, xanchor: 'center',
      bgcolor: 'rgba(0,0,0,0.5)' }],
    hovermode: 'x unified',
    hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
    legend: { bgcolor: 'transparent', font: { size: 11, color: '#a0a0a0' }, orientation: 'h', x: 0, y: 1.08 },
  }
  await Plotly.react(gbmChart.value, traces, layout, { responsive: true, displaylogo: false })
  await nextTick()
  Plotly.Plots.resize(gbmChart.value)
}

// ── Validation state ──────────────────────────────────────────────────────────
const valSims    = ref(2000)
const valPerms   = ref(300)
const valLoading = ref(false)
const valError   = ref(null)
const valData    = ref(null)

// MC method selector
const mcMethods = [
  { key: 'reshuffle',        label: 'Reshuffle'      },
  { key: 'resample',         label: 'Bootstrap'      },
  { key: 'randomized',       label: 'Aleatorizado'   },
  { key: 'return_alteration', label: 'Alt. Retornos' },
]
const mcTab  = ref(0)
const subTabs = ['Equity Curves', 'Drawdowns', 'Sharpe']
const subTab  = ref(0)

const boomEl = ref(null)
const ddEl   = ref(null)
const shEl   = ref(null)
const permEl = ref(null)

const currentMc = computed(() => {
  if (!valData.value) return null
  const key = mcMethods[mcTab.value].key
  return valData.value[key]
})

const copied = ref(false)
const showMethodsLegend = ref(false)
const openDd = ref(null)
async function copyReport() {
  if (!valData.value?.report) return
  await navigator.clipboard.writeText(valData.value.report)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

const verdicts = computed(() => {
  if (!valData.value) return []
  const ref = valData.value.reshuffle || {}
  const pt  = valData.value.permutation_test || {}
  const dd  = ref.max_drawdown || {}
  const origDd = ref.original_dd || 0
  const ddRatio = origDd !== 0 ? Math.abs((dd.p95 || 0) / origDd) : 0
  return [
    { label: 'Sharpe rank ≥ P50',    ok: (ref.backtest_rank_sharpe || 0) >= 50 },
    { label: 'P95 DD < 2× original', ok: ddRatio < 2.0 },
    { label: 'Prob. Ruína < 5%',     ok: (ref.ruin_prob || 0) < 5.0 },
    { label: 'Perm. Test p < 0.05',  ok: pt.approved === true },
  ]
})

async function runValidation() {
  if (!store.results) return
  valLoading.value = true
  valError.value   = null
  try {
    const { data } = await apiRunValidation({
      trades:        store.results.trades || [],
      equity_curve:  store.results.equity_curve,
      metrics:       store.results.metrics,
      n_sims:        valSims.value,
      n_perms:       valPerms.value,
      seed:          42,
      strategy_label: store.selectedStrategy?.name || 'Estratégia',
      asset_label:   store.results.symbol || '-',
    })
    valData.value = data
    await nextTick()
    await renderMcCharts()
    await renderPermChart()
  } catch (e) {
    valError.value = e.response?.data?.error || e.message
  } finally {
    valLoading.value = false
  }
}

// ── Chart renderers ───────────────────────────────────────────────────────────

const BLUE  = '#378ADD'
const GREEN = '#1D9E75'
const RED   = '#E24B4A'
const GRAY  = '#888888'
const WHITE = '#d0d0d0'
const PANEL = { paper_bgcolor: '#000000', plot_bgcolor: '#080808' }
const FONT  = { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif', size: 12 }
const AXIS  = { gridcolor: '#1a1a1a', linecolor: '#252525', tickfont: { color: '#606060' } }

async function renderMcCharts() {
  if (!valData.value) return
  const mc = currentMc.value
  if (!mc) return
  const Plotly = (await import('plotly.js-dist-min')).default

  // Broom chart
  if (boomEl.value) {
    const x = mc.x_type === 'date' ? mc.x_labels : Array.from({ length: mc.p50.length }, (_, i) => i)
    const traces = []

    for (const path of mc.sample_paths) {
      traces.push({ type: 'scatter', mode: 'lines',
        x, y: path.slice(0, x.length),
        line: { color: 'rgba(136,136,136,0.10)', width: 0.8 },
        showlegend: false, hoverinfo: 'skip' })
    }
    traces.push({ type: 'scatter', mode: 'lines', name: 'P95',
      x, y: mc.p95.slice(0, x.length),
      line: { color: GREEN, width: 1.2, dash: 'dash' },
      hovertemplate: 'P95: $%{y:,.0f}<extra></extra>' })
    traces.push({ type: 'scatter', mode: 'lines', name: 'P50 mediana',
      x, y: mc.p50.slice(0, x.length),
      line: { color: WHITE, width: 1.5, dash: 'dot' },
      hovertemplate: 'P50: $%{y:,.0f}<extra></extra>' })
    traces.push({ type: 'scatter', mode: 'lines', name: 'P5',
      x, y: mc.p5.slice(0, x.length),
      line: { color: RED, width: 1.2, dash: 'dash' },
      hovertemplate: 'P5: $%{y:,.0f}<extra></extra>' })
    traces.push({ type: 'scatter', mode: 'lines', name: 'Backtest Original',
      x: Array.from({ length: mc.original_equity.length }, (_, i) => mc.x_type === 'date' ? mc.x_labels[i] ?? i : i),
      y: mc.original_equity,
      line: { color: BLUE, width: 2 },
      hovertemplate: 'Original: $%{y:,.0f}<extra></extra>' })

    const layout = {
      ...PANEL, font: FONT, height: 520, autosize: true,
      margin: { t: 20, r: 20, b: 50, l: 75 },
      xaxis: { ...AXIS, title: mc.x_type === 'date' ? 'Data' : 'Nº do Trade' },
      yaxis: { ...AXIS, title: 'Capital ($)', tickprefix: '$' },
      legend: { bgcolor: 'transparent', font: { size: 11, color: '#909090' }, orientation: 'h', x: 0, y: 1.06 },
      hovermode: 'x unified',
      hoverlabel: { bgcolor: '#111', bordercolor: '#555', font: { color: '#e0e0e0' } },
    }
    await Plotly.react(boomEl.value, traces, layout, { responsive: true, displaylogo: false })
  }

  // Drawdown histogram
  if (ddEl.value) {
    const origDd = mc.original_dd ?? 0
    const p95Dd  = mc.max_drawdown?.p95 ?? 0
    const traces = [
      { type: 'histogram', x: mc.max_drawdown_dist, name: 'Simulações',
        marker: { color: RED, opacity: 0.6 }, nbinsx: 60,
        hovertemplate: 'DD: %{x:.2f}%<br>Freq: %{y}<extra></extra>' },
    ]
    const layout = {
      ...PANEL, font: FONT, height: 460, autosize: true,
      margin: { t: 20, r: 20, b: 50, l: 60 },
      xaxis: { ...AXIS, title: 'Max Drawdown (%)' },
      yaxis: { ...AXIS, title: 'Frequência' },
      shapes: [
        { type: 'line', x0: origDd, x1: origDd, yref: 'paper', y0: 0, y1: 1,
          line: { color: BLUE, dash: 'dash', width: 2 } },
        { type: 'line', x0: p95Dd,  x1: p95Dd,  yref: 'paper', y0: 0, y1: 1,
          line: { color: RED, dash: 'dot', width: 1.5 } },
      ],
      annotations: [
        { xref: 'x', x: origDd, yref: 'paper', y: 0.95,
          text: `Original: ${origDd?.toFixed(1)}%`, showarrow: false,
          font: { size: 10, color: BLUE }, bgcolor: 'rgba(0,0,0,0.6)', xanchor: 'left' },
        { xref: 'x', x: p95Dd, yref: 'paper', y: 0.86,
          text: `P95: ${p95Dd?.toFixed(1)}%`, showarrow: false,
          font: { size: 10, color: RED }, bgcolor: 'rgba(0,0,0,0.6)', xanchor: 'left' },
      ],
      bargap: 0.05,
    }
    await Plotly.react(ddEl.value, traces, layout, { responsive: true, displaylogo: false })
  }

  // Sharpe histogram
  if (shEl.value) {
    const origSh = mc.original_sharpe ?? 0
    const rank   = mc.backtest_rank_sharpe ?? 0
    const traces = [
      { type: 'histogram', x: mc.sharpe_dist, name: 'Simulações',
        marker: { color: BLUE, opacity: 0.6 }, nbinsx: 60,
        hovertemplate: 'Sharpe: %{x:.4f}<br>Freq: %{y}<extra></extra>' },
    ]
    const layout = {
      ...PANEL, font: FONT, height: 460, autosize: true,
      margin: { t: 20, r: 20, b: 50, l: 60 },
      xaxis: { ...AXIS, title: 'Sharpe Ratio' },
      yaxis: { ...AXIS, title: 'Frequência' },
      shapes: [
        { type: 'line', x0: origSh, x1: origSh, yref: 'paper', y0: 0, y1: 1,
          line: { color: GREEN, dash: 'dash', width: 2 } },
      ],
      annotations: [
        { xref: 'x', x: origSh, yref: 'paper', y: 0.95,
          text: `Original: ${origSh?.toFixed(4)}<br>${rank?.toFixed(0)}º percentil`,
          showarrow: false, font: { size: 10, color: GREEN },
          bgcolor: 'rgba(0,0,0,0.6)', xanchor: 'left' },
      ],
      bargap: 0.05,
    }
    await Plotly.react(shEl.value, traces, layout, { responsive: true, displaylogo: false })
  }
}

async function renderPermChart() {
  if (!valData.value?.permutation_test || !permEl.value) return
  const Plotly = (await import('plotly.js-dist-min')).default
  const pt = valData.value.permutation_test
  const origS = pt.original_sharpe ?? 0
  const color = pt.approved ? GREEN : RED

  const traces = [
    { type: 'histogram', x: pt.sharpe_dist, name: 'Séries aleatórias',
      marker: { color: GRAY, opacity: 0.6 }, nbinsx: 50,
      hovertemplate: 'Sharpe: %{x:.4f}<br>Freq: %{y}<extra></extra>' },
  ]
  const layout = {
    ...PANEL, font: FONT, height: 460, autosize: true,
    margin: { t: 20, r: 20, b: 50, l: 60 },
    xaxis: { ...AXIS, title: 'Sharpe Ratio' },
    yaxis: { ...AXIS, title: 'Frequência' },
    shapes: [
      { type: 'line', x0: origS, x1: origS, yref: 'paper', y0: 0, y1: 1,
        line: { color: BLUE, dash: 'dash', width: 2 } },
    ],
    annotations: [
      { xref: 'x', x: origS, yref: 'paper', y: 0.96,
        text: `Estratégia: ${origS?.toFixed(4)}`, showarrow: false,
        font: { size: 10, color: BLUE }, bgcolor: 'rgba(0,0,0,0.6)', xanchor: 'left' },
      { xref: 'paper', x: 0.98, yref: 'paper', y: 0.96,
        text: `p = ${pt.p_value?.toFixed(4)}<br>${pt.conclusion}`,
        showarrow: false, font: { size: 12, color }, fontweight: 'bold',
        bgcolor: 'rgba(0,0,0,0.7)', bordercolor: color, borderpad: 6, xanchor: 'right' },
    ],
    bargap: 0.05,
  }
  await Plotly.react(permEl.value, traces, layout, { responsive: true, displaylogo: false })
}

// ── Tab switching ─────────────────────────────────────────────────────────────
watch(topTab, async (i) => {
  await nextTick()
  if (i === 0 && gbmData.value) await renderGbmChart(gbmData.value)
  if (i === 1 && valData.value) await renderMcCharts()
  if (i === 2 && valData.value) await renderPermChart()
})
watch(mcTab,  () => nextTick().then(renderMcCharts))
watch(subTab, () => nextTick().then(renderMcCharts))

onMounted(fetchGbm)
watch([gbmSims, horizon, () => props.equityCurve], fetchGbm, { deep: true })
watch(gbmSeed, fetchGbm)

onBeforeUnmount(() => {
  [gbmChart, boomEl, ddEl, shEl, permEl].forEach(r => purgeChart(r.value))
})
</script>

<style scoped>
/* Dropdown selector */
.mc-dropdown-wrap {
  position: relative;
  display: inline-flex;
  flex-direction: column;
}
.mc-dd-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  font-size: 11px;
  border-radius: 8px;
  background: #0a0a10;
  border: 1px solid #2a2a3a;
  color: #aaa;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  white-space: nowrap;
}
.mc-dd-btn:hover {
  border-color: #444;
  background: #111118;
  color: #ccc;
}
.mc-dd-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 100%;
  background: #07070e;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
  z-index: 40;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.mc-dd-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 7px 14px;
  font-size: 11px;
  color: #999;
  transition: background 0.1s, color 0.1s;
  cursor: pointer;
}
.mc-dd-item:hover {
  background: #0f0f1a;
  color: #e0e0e0;
}

/* Dollar-sign pulsing loader */
@keyframes mc-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(245, 197, 24, 0.8);  border-color: #f5c518; color: #f5c518; background: #000; }
  50%  { box-shadow: 0 0 24px 8px rgba(245, 197, 24, 0.25); border-color: #f5c518; color: #000;   background: #f5c518; }
  100% { box-shadow: 0 0 0 0 rgba(245, 197, 24, 0.8);  border-color: #f5c518; color: #f5c518; background: #000; }
}

.mc-dollar-loader {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  border: 2px solid #f5c518;
  background: #000;
  color: #f5c518;
  font-size: 2.4rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: mc-pulse 1.4s ease-in-out infinite;
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -1px;
}

/* Metric info icon + tooltip */
.mc-info-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.mc-info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 1px solid #555;
  color: #666;
  font-size: 8px;
  font-weight: 700;
  cursor: default;
  line-height: 1;
}

.mc-tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  width: 220px;
  background: #0d0d12;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 10px;
  color: #bbb;
  line-height: 1.5;
  text-align: left;
  z-index: 50;
  pointer-events: none;
  transition: opacity 0.15s;
  white-space: normal;
}

.mc-info-wrap:hover .mc-tooltip {
  visibility: visible;
  opacity: 1;
}

/* Overlay that sits on top of the chart area */
.mc-chart-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  z-index: 10;
}
</style>
