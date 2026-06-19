// Shared lazy Plotly loader — keeps the heavy plotly.js bundle out of the
// initial app chunk so the dashboard shell loads fast. All chart components
// should import Plotly through getPlotly() instead of a static import.

let _Plotly = null

export async function getPlotly() {
  if (_Plotly) return _Plotly
  _Plotly = (await import('plotly.js-dist-min')).default
  return _Plotly
}
