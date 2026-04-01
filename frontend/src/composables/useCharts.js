/**
 * useCharts — helpers para renderizar/atualizar gráficos Plotly com dark theme.
 */

const DARK_LAYOUT = {
  template: 'plotly_dark',
  paper_bgcolor: '#000000',
  plot_bgcolor: '#080808',
  font: { color: '#d0d0d0', family: 'Inter, system-ui, sans-serif' },
  xaxis: { gridcolor: '#1e1e1e', linecolor: '#2a2a2a', zerolinecolor: '#2a2a2a' },
  yaxis: { gridcolor: '#1e1e1e', linecolor: '#2a2a2a', zerolinecolor: '#2a2a2a' },
  legend: { bgcolor: 'rgba(0,0,0,0.85)', bordercolor: '#2a2a2a', borderwidth: 1 },
  hoverlabel: { bgcolor: '#0f0f0f', bordercolor: '#f5c518', font: { color: '#e0e0e0' } },
  margin: { t: 40, r: 20, b: 50, l: 60 },
}

/**
 * Aplica dark theme em um objeto Plotly JSON.
 * Modifica in-place e retorna o objeto.
 */
export function applyDarkTheme(plotlyJson) {
  if (!plotlyJson) return plotlyJson
  const orig = plotlyJson.layout || {}
  plotlyJson.layout = {
    ...orig,
    ...DARK_LAYOUT,
    xaxis: { ...orig.xaxis, ...DARK_LAYOUT.xaxis },
    yaxis: { ...orig.yaxis, ...DARK_LAYOUT.yaxis },
    margin: { ...(orig.margin || {}), ...DARK_LAYOUT.margin },
  }
  return plotlyJson
}

/**
 * Inicializa um gráfico Plotly em um elemento DOM.
 * @param {HTMLElement} el
 * @param {object} plotlyJson - { data, layout, config? }
 * @param {object} extraLayout - layout adicional (ex: height)
 */
export async function initChart(el, plotlyJson, extraLayout = {}) {
  if (!el || !plotlyJson) return
  const Plotly = await importPlotly()
  const json = applyDarkTheme(JSON.parse(JSON.stringify(plotlyJson)))
  const layout = { ...json.layout, ...extraLayout, autosize: true }
  await Plotly.newPlot(el, json.data || [], layout, {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
    displaylogo: false,
  })
}

/**
 * Atualiza um gráfico existente (preserva zoom/pan).
 */
export async function updateChart(el, plotlyJson, extraLayout = {}) {
  if (!el || !plotlyJson) return
  const Plotly = await importPlotly()
  const json = applyDarkTheme(JSON.parse(JSON.stringify(plotlyJson)))
  const layout = { ...json.layout, ...extraLayout, autosize: true }
  await Plotly.react(el, json.data || [], layout, {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
    displaylogo: false,
  })
}

/**
 * Remove um gráfico do DOM.
 */
export async function purgeChart(el) {
  if (!el) return
  const Plotly = await importPlotly()
  Plotly.purge(el)
}

/**
 * Registra handler de clique em ponto do scatter.
 * @param {HTMLElement} el
 * @param {function} cb - callback({ rank, pointIndex })
 */
export function onPointClick(el, cb) {
  if (!el) return
  el.on('plotly_click', (data) => {
    if (!data?.points?.length) return
    const pt = data.points[0]
    const rank = pt.customdata?.[0] ?? pt.pointIndex
    cb({ rank, pointIndex: pt.pointIndex })
  })
}

let _Plotly = null
async function importPlotly() {
  if (_Plotly) return _Plotly
  const mod = await import('plotly.js-dist-min')
  _Plotly = mod.default
  return _Plotly
}
