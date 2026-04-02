import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

// ─── Dashboard API ──────────────────────────────────────────────────────────

export function getFiles() {
  return api.get('/files')
}

export function loadCsvByName(filename, filters = {}) {
  return api.post('/load', { filename, filters })
}

export function loadCsvUpload(file, filters = {}) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('filters', JSON.stringify(filters))
  return api.post('/load', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function filterData(rows, filters) {
  return api.post('/filter', { rows, filters })
}

export function getStrategy(rank, rows) {
  return api.post('/strategy', { rank, rows })
}

export function filterChart(rows, chartType, chartFilters) {
  return api.post('/filter-chart', { rows, chart_type: chartType, chart_filters: chartFilters })
}

// ─── Backtest API ────────────────────────────────────────────────────────────

export function getAssets() {
  return api.get('/backtest/assets')
}

export function getStrategies() {
  return api.get('/backtest/strategies')
}

export function runBacktestAsset(symbol, symbolLabel, interval, config, strategyFile = 'depaula') {
  return api.post('/backtest/run', {
    data_source: 'asset',
    symbol,
    symbol_label: symbolLabel,
    interval,
    config,
    strategy_file: strategyFile,
  })
}

export function runBacktestCsv(file, config, strategyFile = 'depaula') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('config', JSON.stringify(config))
  formData.append('strategy_file', strategyFile)
  return api.post('/backtest/run', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getCorrelation(tickers) {
  return api.post('/backtest/correlation', { tickers })
}

export function runMonteCarlo(equityCurve, numSims, horizon, seed) {
  return api.post('/backtest/montecarlo', {
    equity_curve: equityCurve,
    num_sims: numSims,
    horizon,
    seed,
  })
}

export function runValidation(payload) {
  return api.post('/backtest/validate', payload, { timeout: 180000 })
}

export function runWfa(payload) {
  return api.post('/backtest/wfa', payload, { timeout: 180000 })
}

// Optimizer API
export function getOptimizerGrids(strategyFile = 'depaula') {
  return api.get('/optimizer/grids', { params: { strategy: strategyFile } })
}

export function getOptimizerCount(grid, capital, strategyFile = 'depaula') {
  return api.post('/optimizer/count', { grid, capital, strategy_file: strategyFile })
}

export function stopOptimizer() {
  return api.post('/optimizer/stop')
}

export function getOptimizerProgress() {
  return api.get('/optimizer/progress')
}

export function startOptimizer(payload) {
  return api.post('/optimizer/run', payload)
}

export function startOptimizerCsv(file, grid, capital, minTrades, rankBy, topN, strategyFile = 'depaula', cycleLongMonths = null, cycleShortMonths = null, config = null) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('grid', JSON.stringify(grid))
  formData.append('capital', capital)
  formData.append('min_trades', minTrades)
  formData.append('rank_by', rankBy)
  formData.append('top_n', topN)
  formData.append('strategy_file', strategyFile)
  if (cycleLongMonths) formData.append('cycle_long_months', JSON.stringify(cycleLongMonths))
  if (cycleShortMonths) formData.append('cycle_short_months', JSON.stringify(cycleShortMonths))
  if (config) formData.append('config', JSON.stringify(config))
  return api.post('/optimizer/run-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getOptimizerResult() {
  return api.get('/optimizer/result')
}

// Prop Challenge API
export function runPropChallenge(payload) {
  return api.post('/prop-challenge/simulate', payload, { timeout: 300000 })
}

export default api
