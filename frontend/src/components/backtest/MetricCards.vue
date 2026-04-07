<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-12 gap-2">
    <div v-for="m in metricList" :key="m.key" class="metric-card">
      <span class="metric-label">
        {{ m.label }}
        <span class="metric-help" :title="m.description">?</span>
      </span>
      <span class="metric-value" :class="m.colorClass">{{ m.display }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  metrics: { type: Object, required: true }
})

const METRIC_DESCRIPTIONS = {
  final_equity: 'Capital final apos todos os trades. Indica o valor acumulado da carteira ao fim do backtest.',
  total_return: 'Retorno percentual total da estrategia no periodo. Calculado como (capital final - capital inicial) / capital inicial.',
  max_dd: 'Maximum Drawdown: maior queda percentual do pico ao vale da curva de equity. Mede o pior cenario de perda consecutiva.',
  total_trades: 'Numero total de operacoes (compra e venda) realizadas no periodo do backtest.',
  win_rate: 'Percentual de trades lucrativos sobre o total de trades. Win Rate = trades positivos / total de trades.',
  profit_factor: 'Razao entre lucro bruto e prejuizo bruto. Profit Factor = soma dos ganhos / soma das perdas. Acima de 1.5 e considerado bom.',
  sharpe: 'Sharpe Ratio: retorno ajustado ao risco. Mede o excesso de retorno por unidade de volatilidade total. Acima de 1.0 e aceitavel, acima de 2.0 e excelente.',
  sortino: 'Sortino Ratio: similar ao Sharpe, mas penaliza apenas a volatilidade negativa (downside). Mais relevante para estrategias assimetricas.',
  calmar: 'Calmar Ratio: retorno anualizado dividido pelo max drawdown. Mede eficiencia do retorno em relacao ao pior cenario de perda.',
  omega: 'Omega Ratio: razao entre ganhos e perdas ponderados por probabilidade acima/abaixo de um limiar. Acima de 1.0 indica ganhos superiores as perdas.',
  sterling: 'Sterling Ratio: retorno anualizado dividido pela media dos maiores drawdowns. Variacao mais estavel do Calmar.',
  burke: 'Burke Ratio: retorno anualizado dividido pela raiz da soma dos quadrados dos drawdowns. Penaliza drawdowns frequentes e profundos.',
}

const metricList = computed(() => {
  const m = props.metrics
  return [
    {
      key: 'final_equity',
      label: 'Capital',
      description: METRIC_DESCRIPTIONS.final_equity,
      display: '$' + fmtMoney(m.final_equity),
      colorClass: 'text-gray-100',
    },
    {
      key: 'total_return',
      label: 'Retorno',
      description: METRIC_DESCRIPTIONS.total_return,
      display: fmtPct(m.total_return),
      colorClass: (m.total_return ?? 0) >= 0 ? 'text-accent-green-light' : 'text-accent-red-light',
    },
    {
      key: 'max_dd',
      label: 'Max DD',
      description: METRIC_DESCRIPTIONS.max_dd,
      display: fmtPct(m.max_dd),
      colorClass: 'text-accent-red-light',
    },
    {
      key: 'total_trades',
      label: 'Trades',
      description: METRIC_DESCRIPTIONS.total_trades,
      display: m.total_trades ?? '-',
      colorClass: 'text-gray-100',
    },
    {
      key: 'win_rate',
      label: 'Win Rate',
      description: METRIC_DESCRIPTIONS.win_rate,
      display: fmtPct(m.win_rate, 1),
      colorClass: (m.win_rate ?? 0) >= 50 ? 'text-accent-green-light' : 'text-accent-red-light',
    },
    {
      key: 'profit_factor',
      label: 'Profit F.',
      description: METRIC_DESCRIPTIONS.profit_factor,
      display: m.profit_factor != null ? Number(m.profit_factor).toFixed(2) : '\u221E',
      colorClass: m.profit_factor == null ? 'text-gray-400' : m.profit_factor >= 1.5 ? 'text-accent-green-light' : m.profit_factor >= 1 ? 'text-accent-yellow' : 'text-accent-red-light',
    },
    {
      key: 'sharpe',
      label: 'Sharpe',
      description: METRIC_DESCRIPTIONS.sharpe,
      display: m.sharpe != null ? Number(m.sharpe).toFixed(2) : '-',
      colorClass: (m.sharpe ?? 0) >= 1.5 ? 'text-accent-green-light' : (m.sharpe ?? 0) >= 1 ? 'text-accent-yellow' : 'text-gray-100',
    },
    {
      key: 'sortino',
      label: 'Sortino',
      description: METRIC_DESCRIPTIONS.sortino,
      display: m.sortino != null ? Number(m.sortino).toFixed(2) : '-',
      colorClass: (m.sortino ?? 0) >= 1 ? 'text-accent-green-light' : 'text-gray-100',
    },
    {
      key: 'calmar',
      label: 'Calmar',
      description: METRIC_DESCRIPTIONS.calmar,
      display: m.calmar != null ? Number(m.calmar).toFixed(2) : '-',
      colorClass: (m.calmar ?? 0) >= 3 ? 'text-accent-green-light' : (m.calmar ?? 0) >= 1 ? 'text-accent-yellow' : 'text-gray-100',
    },
    {
      key: 'omega',
      label: 'Omega',
      description: METRIC_DESCRIPTIONS.omega,
      display: m.omega != null ? Number(m.omega).toFixed(2) : '\u221E',
      colorClass: m.omega == null ? 'text-gray-400' : m.omega >= 1.5 ? 'text-accent-green-light' : m.omega >= 1 ? 'text-accent-yellow' : 'text-accent-red-light',
    },
    {
      key: 'sterling',
      label: 'Sterling',
      description: METRIC_DESCRIPTIONS.sterling,
      display: m.sterling != null ? Number(m.sterling).toFixed(2) : '-',
      colorClass: (m.sterling ?? 0) >= 3 ? 'text-accent-green-light' : (m.sterling ?? 0) >= 1 ? 'text-accent-yellow' : 'text-gray-100',
    },
    {
      key: 'burke',
      label: 'Burke',
      description: METRIC_DESCRIPTIONS.burke,
      display: m.burke != null ? Number(m.burke).toFixed(2) : '-',
      colorClass: (m.burke ?? 0) >= 1 ? 'text-accent-green-light' : 'text-gray-100',
    },
  ]
})

function fmtPct(v, dec = 2) {
  if (v == null) return '-'
  const n = Number(v)
  return (n >= 0 ? '+' : '') + n.toFixed(dec) + '%'
}

function fmtMoney(v) {
  if (v == null) return '-'
  return Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.metric-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 13px;
  height: 13px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(156, 163, 175, 0.6);
  border: 1px solid rgba(156, 163, 175, 0.3);
  border-radius: 50%;
  cursor: help;
  margin-left: 3px;
  vertical-align: middle;
  line-height: 1;
  position: relative;
}

.metric-help:hover {
  color: rgba(250, 204, 21, 0.9);
  border-color: rgba(250, 204, 21, 0.5);
}
</style>
