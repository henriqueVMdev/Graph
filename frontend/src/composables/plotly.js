// Shared lazy Plotly loader — keeps the heavy plotly.js bundle out of the
// initial app chunk so the dashboard shell loads fast. All chart components
// should import Plotly through getPlotly() instead of a static import.
//
// O pacote plotly.js-dist-min trazia os ~40 tipos de trace da biblioteca
// (3d, mapbox, sankey, parcoords, sunburst...) em 4.67 MB. O app usa seis.
// Aqui o core e carregado e so esses seis sao registrados.
//
// Ao adicionar um grafico com trace novo, registre o modulo dele nesta lista
// ou o Plotly ignora o trace silenciosamente e o grafico sai vazio.

let _Plotly = null
let _carregando = null

async function montar() {
  const [core, scatter, bar, heatmap, histogram, candlestick, scatterpolar] = await Promise.all([
    import('plotly.js/lib/core'),
    import('plotly.js/lib/scatter'),
    import('plotly.js/lib/bar'),
    import('plotly.js/lib/heatmap'),
    import('plotly.js/lib/histogram'),
    import('plotly.js/lib/candlestick'),
    import('plotly.js/lib/scatterpolar'),
  ])

  const Plotly = core.default
  Plotly.register([
    scatter.default, bar.default, heatmap.default,
    histogram.default, candlestick.default, scatterpolar.default,
  ])
  return Plotly
}

export async function getPlotly() {
  if (_Plotly) return _Plotly
  // Sem isso, dois graficos montando ao mesmo tempo disparam dois carregamentos
  // e dois register() do mesmo modulo.
  if (!_carregando) _carregando = montar().then((p) => { _Plotly = p; return p })
  return _carregando
}
