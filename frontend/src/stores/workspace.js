import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Seleção de trabalho compartilhada entre as páginas: ativo, timeframe,
 * fonte dos candles e estratégia+parâmetros. Cada store de página expõe
 * esses valores sob os nomes que seus componentes já usam (via computed
 * get/set), então escolher BTC 15m Bybit no Backtest deixa tudo
 * pré-selecionado no Prop Challenge, Regimes, Otimizador e Gráfico.
 */
export const useWorkspaceStore = defineStore('workspace', () => {
  const symbol = ref('')          // ticker (ex.: 'BTC-USD')
  const symbolLabel = ref('')     // rótulo humano (ex.: 'Bitcoin (BTC)')
  const interval = ref('1d')
  const exchange = ref('')        // '' = yfinance; senão exchange CCXT

  // Estratégia + params compartilhados (Backtest / Prop Challenge / Gráfico)
  const selectedStrategy = ref(null)
  const params = ref({})

  /** Localiza categoria+label de um ticker na lista de assets do backend
   *  (p/ pré-selecionar os dropdowns das sidebars). */
  function findAsset(assets, ticker) {
    if (!ticker) return null
    for (const [category, items] of Object.entries(assets || {})) {
      for (const [label, t] of Object.entries(items || {})) {
        if (t === ticker) return { category, label, ticker: t }
      }
    }
    return null
  }

  return { symbol, symbolLabel, interval, exchange, selectedStrategy, params, findAsset }
})
