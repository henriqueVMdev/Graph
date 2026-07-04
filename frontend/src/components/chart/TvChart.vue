<template>
  <div class="relative w-full h-full">
    <div ref="el" class="w-full h-full"></div>
    <div
      ref="legend"
      class="absolute top-2 left-3 text-xs font-mono leading-tight pointer-events-none z-10 text-gray-300"
    ></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useChartStore } from '@/stores/chart.js'

const store = useChartStore()
const el = ref(null)
const legend = ref(null)

const COLORS = {
  up: '#26a69a', down: '#ef5350',
  ma: '#f5c518', maSlow: '#42a5f5',
  upper: 'rgba(66,165,245,0.85)', lower: 'rgba(171,71,188,0.85)',
  stop: '#ef5350', target: '#26a69a',
}

let LW = null
let chart = null
let candleSeries = null
let volumeSeries = null
let maSeries = null
let maSlowSeries = null
let upperSeries = null   // p/ mm9: EMA50 · p/ bandas: banda superior
let lowerSeries = null   // p/ mm9: EMA200 · p/ bandas: banda inferior
let zones = null   // primitive: caixas de risco/retorno por trade

// ── Helpers ──────────────────────────────────────────────────────────────
// Converte data (string UTC tz-naive) ou epoch ms para UTCTimestamp (segundos).
function toSec(d) {
  if (typeof d === 'number') return Math.floor(d / 1000)
  let s = String(d)
  if (!/[zZ]|[+-]\d\d:?\d\d$/.test(s)) s = s.replace(' ', 'T') + 'Z'
  return Math.floor(Date.parse(s) / 1000)
}

// Busca binária: tempo de candle mais próximo (arr ascendente).
function nearest(arr, t) {
  if (!arr.length) return t
  if (t <= arr[0]) return arr[0]
  if (t >= arr[arr.length - 1]) return arr[arr.length - 1]
  let lo = 0, hi = arr.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (arr[mid] === t) return arr[mid]
    if (arr[mid] < t) lo = mid + 1
    else hi = mid - 1
  }
  const a = arr[hi], b = arr[lo]
  return (t - a) <= (b - t) ? a : b
}

// Primitive: caixa de posição (entrada -> alvo em verde, entrada -> stop em vermelho),
// estilo "Long Position" do TradingView. Cada trade vira duas zonas preenchidas.
function makeZonesPrimitive() {
  let series = null
  let chartRef = null
  let requestUpdate = null
  let items = []   // { x1, x2 em time(seg); entry, stop, target; dir }

  const view = {
    zOrder: () => 'bottom',
    renderer() {
      return {
        draw(target) {
          if (!series || !chartRef) return
          const ts = chartRef.timeScale()
          target.useBitmapCoordinateSpace((scope) => {
            const ctx = scope.context
            const hr = scope.horizontalPixelRatio
            const vr = scope.verticalPixelRatio
            for (const it of items) {
              const x1 = ts.timeToCoordinate(it.x1)
              const x2 = ts.timeToCoordinate(it.x2)
              const yE = series.priceToCoordinate(it.entry)
              const yS = series.priceToCoordinate(it.stop)
              const yT = series.priceToCoordinate(it.target)
              if (x1 == null || x2 == null || yE == null || yS == null || yT == null) continue
              const X1 = Math.round(x1 * hr)
              const X2 = Math.round(x2 * hr)
              const w = Math.max(X2 - X1, 1)
              const Ye = yE * vr, Ys = yS * vr, Yt = yT * vr
              // zona de alvo (verde): entrada -> alvo
              ctx.fillStyle = 'rgba(38,166,154,0.16)'
              ctx.fillRect(X1, Math.min(Ye, Yt), w, Math.abs(Yt - Ye))
              // zona de stop (vermelha): entrada -> stop
              ctx.fillStyle = 'rgba(239,83,80,0.16)'
              ctx.fillRect(X1, Math.min(Ye, Ys), w, Math.abs(Ys - Ye))
              // bordas de alvo e stop + linha de entrada
              ctx.lineWidth = Math.max(vr, 1)
              ctx.setLineDash([])
              ctx.strokeStyle = 'rgba(38,166,154,0.9)'
              ctx.beginPath(); ctx.moveTo(X1, Yt); ctx.lineTo(X2, Yt); ctx.stroke()
              ctx.strokeStyle = 'rgba(239,83,80,0.9)'
              ctx.beginPath(); ctx.moveTo(X1, Ys); ctx.lineTo(X2, Ys); ctx.stroke()
              ctx.strokeStyle = 'rgba(220,220,220,0.85)'
              ctx.beginPath(); ctx.moveTo(X1, Ye); ctx.lineTo(X2, Ye); ctx.stroke()
            }
          })
        },
      }
    },
  }

  return {
    setItems(next) { items = next || [] },
    attached(p) { chartRef = p.chart; series = p.series; requestUpdate = p.requestUpdate },
    detached() { chartRef = null; series = null; requestUpdate = null },
    updateAllViews() {},
    paneViews() { return [view] },
    redraw() { if (requestUpdate) requestUpdate() },
  }
}

async function ensureChart() {
  if (!LW) LW = await import('lightweight-charts')
  if (chart || !el.value) return
  chart = LW.createChart(el.value, {
    autoSize: true,
    layout: { background: { color: '#080808' }, textColor: '#a0a0a0', fontFamily: 'Inter, system-ui, sans-serif' },
    grid: { vertLines: { color: '#161616' }, horzLines: { color: '#161616' } },
    crosshair: {
      mode: LW.CrosshairMode.Normal,
      vertLine: { color: '#555', width: 1, labelBackgroundColor: '#f5c518' },
      horzLine: { color: '#555', width: 1, labelBackgroundColor: '#f5c518' },
    },
    rightPriceScale: { borderColor: '#2a2a2a' },
    timeScale: { borderColor: '#2a2a2a', timeVisible: true, secondsVisible: false },
  })
  candleSeries = chart.addCandlestickSeries({
    upColor: COLORS.up, downColor: COLORS.down, borderVisible: false,
    wickUpColor: COLORS.up, wickDownColor: COLORS.down,
  })
  volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' })
  volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })

  const lineOpts = { lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }
  maSeries = chart.addLineSeries({ ...lineOpts, color: COLORS.ma })
  maSlowSeries = chart.addLineSeries({ ...lineOpts, color: COLORS.maSlow })
  upperSeries = chart.addLineSeries({ ...lineOpts, lineWidth: 1, color: COLORS.upper })
  lowerSeries = chart.addLineSeries({ ...lineOpts, lineWidth: 1, color: COLORS.lower })

  zones = makeZonesPrimitive()
  candleSeries.attachPrimitive(zones)

  chart.subscribeCrosshairMove(onCrosshair)
}

function render(fit) {
  if (!chart || !store.chartData) return
  const c = store.chartData.candles
  if (!c?.dates?.length) return
  const ov = store.overlays
  const times = c.dates.map(toSec)

  candleSeries.setData(times.map((t, i) => ({
    time: t, open: c.open[i], high: c.high[i], low: c.low[i], close: c.close[i],
  })))

  volumeSeries.setData(ov.volume && c.volume
    ? times.map((t, i) => ({
        time: t, value: c.volume[i] ?? 0,
        color: (c.close[i] >= c.open[i]) ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)',
      }))
    : [])

  const ind = store.chartData.indicators || {}
  const lineData = (arr) => {
    const out = []
    if (!arr) return out
    for (let i = 0; i < arr.length; i++) if (arr[i] != null) out.push({ time: times[i], value: arr[i] })
    return out
  }
  maSeries.setData(ov.indicators ? lineData(ind.ma) : [])
  maSlowSeries.setData(ov.indicators ? lineData(ind.ma_slow) : [])
  // linhas de tendência da estratégia (mm9: EMA50/EMA200; depaula: bandas)
  upperSeries.setData(ov.indicators ? lineData(ind.upper) : [])
  lowerSeries.setData(ov.indicators ? lineData(ind.lower) : [])

  renderTrades(times)

  if (fit) chart.timeScale().fitContent()
}

function renderTrades(times) {
  const trades = store.chartData.trades || []
  const ov = store.overlays
  const snap = (ms) => nearest(times, Math.floor(ms / 1000))

  // Marcadores de entrada/saída
  let markers = []
  if (ov.markers) {
    for (const tr of trades) {
      if (tr.entry_ts) {
        markers.push({
          time: snap(tr.entry_ts),
          position: tr.direction === 1 ? 'belowBar' : 'aboveBar',
          color: tr.direction === 1 ? COLORS.up : COLORS.down,
          shape: tr.direction === 1 ? 'arrowUp' : 'arrowDown',
          text: tr.direction === 1 ? 'L' : 'S',
        })
      }
      if (tr.exit_ts) {
        const win = (tr.pnl_pct ?? 0) >= 0
        markers.push({
          time: snap(tr.exit_ts), position: 'aboveBar',
          color: win ? 'rgba(38,166,154,0.9)' : 'rgba(239,83,80,0.9)', shape: 'circle',
          text: tr.pnl_pct != null ? `${tr.pnl_pct >= 0 ? '+' : ''}${tr.pnl_pct.toFixed(1)}%` : '',
        })
      }
    }
    markers.sort((a, b) => a.time - b.time)
  }
  candleSeries.setMarkers(markers)

  // Caixas de risco/retorno (entrada/stop/alvo) por trade
  if (!ov.stops) {
    if (zones) { zones.setItems([]); zones.redraw() }
    return
  }
  const zoneItems = []
  const withLevels = trades
    .filter(t => t.entry_ts && t.exit_ts && t.stop_price != null && t.target_price != null)
    .sort((a, b) => a.entry_ts - b.entry_ts)

  for (const tr of withLevels) {
    const eT = snap(tr.entry_ts), xT = snap(tr.exit_ts)
    if (xT <= eT) continue
    zoneItems.push({
      x1: eT, x2: xT,
      entry: tr.entry_price, stop: tr.stop_price, target: tr.target_price,
      dir: tr.direction,
    })
  }
  if (zones) { zones.setItems(zoneItems); zones.redraw() }
}

function onCrosshair(param) {
  if (!legend.value) return
  if (!param || !param.time || !param.seriesData) { legend.value.innerHTML = ''; return }
  const cd = param.seriesData.get(candleSeries)
  if (!cd) { legend.value.innerHTML = ''; return }
  const fmt = (v) => v != null ? Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 }) : '–'
  const up = cd.close >= cd.open
  const maV = param.seriesData.get(maSeries)?.value
  const maSV = param.seriesData.get(maSlowSeries)?.value
  const upV = param.seriesData.get(upperSeries)?.value
  const loV = param.seriesData.get(lowerSeries)?.value
  const lbl = store.chartData?.indicators?.labels || {}
  legend.value.innerHTML =
    `<span style="color:#777">O</span> ${fmt(cd.open)} ` +
    `<span style="color:#777">H</span> ${fmt(cd.high)} ` +
    `<span style="color:#777">L</span> ${fmt(cd.low)} ` +
    `<span style="color:#777">C</span> <span style="color:${up ? COLORS.up : COLORS.down}">${fmt(cd.close)}</span>` +
    (maV != null ? ` &nbsp;<span style="color:${COLORS.ma}">${lbl.ma || 'MA'} ${fmt(maV)}</span>` : '') +
    (maSV != null ? ` <span style="color:${COLORS.maSlow}">${lbl.ma_slow || 'MM'} ${fmt(maSV)}</span>` : '') +
    (upV != null ? ` <span style="color:${COLORS.upper}">${lbl.upper || 'Sup'} ${fmt(upV)}</span>` : '') +
    (loV != null ? ` <span style="color:${COLORS.lower}">${lbl.lower || 'Inf'} ${fmt(loV)}</span>` : '')
}

async function draw(fit) {
  await ensureChart()
  render(fit)
}

watch(() => store.chartData, () => draw(true))
watch(() => store.overlays, () => draw(false), { deep: true })

onMounted(() => { if (store.chartData) draw(true) })
onBeforeUnmount(() => { if (chart) { chart.remove(); chart = null } })
</script>
