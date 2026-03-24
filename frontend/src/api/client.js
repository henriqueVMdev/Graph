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

// Optimizer API
export function getOptimizerGrids(strategyFile = 'depaula') {
  return api.get('/optimizer/grids', { params: { strategy: strategyFile } })
}

export function getOptimizerCount(grid, capital, strategyFile = 'depaula') {
  return api.post('/optimizer/count', { grid, capital, strategy_file: strategyFile })
}

export function runOptimizer(payload) {
  return api.post('/optimizer/run', payload, { timeout: 600000 })
}

export function runOptimizerCsv(file, grid, capital, minTrades, rankBy, topN, strategyFile = 'depaula') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('grid', JSON.stringify(grid))
  formData.append('capital', capital)
  formData.append('min_trades', minTrades)
  formData.append('rank_by', rankBy)
  formData.append('top_n', topN)
  formData.append('strategy_file', strategyFile)
  return api.post('/optimizer/run-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
  })
}

export default api
