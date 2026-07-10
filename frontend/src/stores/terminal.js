import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getWatch, getSpark, getScreener, getDes,
  getAlerts, createAlert, deleteAlert, getNews,
} from '@/api/client.js'

const WATCHLIST_KEY = 'graph.watchlist'
const SEEN_KEY = 'graph.alerts.seen'

export const useTerminalStore = defineStore('terminal', () => {
  // ── Watchlist (persistida; itens {s, m} — m: 'crypto' | 'tradfi') ─────
  function normalizeList(list) {
    if (!Array.isArray(list)) return null
    return list.map((x) => (typeof x === 'string' ? { s: x, m: 'crypto' } : x))
  }
  const watchlist = ref(
    normalizeList(JSON.parse(localStorage.getItem(WATCHLIST_KEY) || 'null'))
    || [{ s: 'BTC', m: 'crypto' }, { s: 'ETH', m: 'crypto' },
        { s: 'SOL', m: 'crypto' }, { s: 'DOGE', m: 'crypto' }],
  )
  const watchRows = ref([])
  const watchError = ref(null)
  const sparks = ref({})                 // `${m}:${base}` -> closes[]
  let watchTimer = null

  function saveWatchlist() {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist.value))
  }

  function addToWatchlist(base, market = 'crypto') {
    const b = base.trim().toUpperCase()
    if (b && !watchlist.value.some((w) => w.s === b && w.m === market)) {
      watchlist.value.push({ s: b, m: market })
      saveWatchlist()
      fetchWatch()
      fetchSpark(b, market)
    }
  }

  function removeFromWatchlist(base, market = 'crypto') {
    watchlist.value = watchlist.value.filter((w) => !(w.s === base && w.m === market))
    saveWatchlist()
    watchRows.value = watchRows.value.filter((r) => !(r.base === base && r.market === market))
  }

  async function fetchWatch() {
    if (!watchlist.value.length) { watchRows.value = []; return }
    try {
      const crypto = watchlist.value.filter((w) => w.m === 'crypto').map((w) => w.s)
      const tradfi = watchlist.value.filter((w) => w.m === 'tradfi').map((w) => w.s)
      const { data } = await getWatch(crypto, 'bybit', tradfi)
      if (data.rows) { watchRows.value = data.rows; watchError.value = null }
    } catch (e) {
      watchError.value = e.response?.data?.error || e.message
    }
  }

  async function fetchSpark(base, market = 'crypto') {
    const key = `${market}:${base}`
    if (sparks.value[key]) return
    try {
      const { data } = await getSpark(base, 'bybit', '15m', 96, market)
      sparks.value = { ...sparks.value, [key]: data.closes || [] }
    } catch { /* sparkline é decorativa */ }
  }

  function startWatchPolling() {
    stopWatchPolling()
    fetchWatch()
    watchlist.value.forEach((w) => fetchSpark(w.s, w.m))
    watchTimer = setInterval(fetchWatch, 5000)
  }

  function stopWatchPolling() {
    if (watchTimer) { clearInterval(watchTimer); watchTimer = null }
  }

  // ── Screener ──────────────────────────────────────────────────────────
  const screenerRows = ref([])
  const screenerLoading = ref(false)
  const screenerError = ref(null)
  const screenerMarket = ref('crypto')   // crypto|stocks|commodities|forex|indices
  let screenerTimer = null

  async function fetchScreener(top = 50) {
    screenerLoading.value = screenerRows.value.length === 0
    try {
      const { data } = await getScreener(top, 'bybit', screenerMarket.value)
      if (data.rows) { screenerRows.value = data.rows; screenerError.value = null }
    } catch (e) {
      screenerError.value = e.response?.data?.error || e.message
    } finally {
      screenerLoading.value = false
    }
  }

  function setScreenerMarket(m) {
    if (screenerMarket.value === m) return
    screenerMarket.value = m
    screenerRows.value = []
    fetchScreener()
  }

  function startScreenerPolling() {
    stopScreenerPolling()
    fetchScreener()
    screenerTimer = setInterval(fetchScreener, 60000)
  }

  function stopScreenerPolling() {
    if (screenerTimer) { clearInterval(screenerTimer); screenerTimer = null }
  }

  // ── DES ───────────────────────────────────────────────────────────────
  const desData = ref(null)
  const desLoading = ref(false)
  const desError = ref(null)

  async function fetchDes(base, market = 'auto') {
    desLoading.value = true
    desError.value = null
    try {
      const { data } = await getDes(base, 'bybit', market)
      desData.value = data.error ? null : data
      if (data.error) desError.value = data.error
    } catch (e) {
      desError.value = e.response?.data?.error || e.message
      desData.value = null
    } finally {
      desLoading.value = false
    }
  }

  // ── Alertas (badge global + toasts) ───────────────────────────────────
  const alerts = ref([])
  const toasts = ref([])                 // {id, title, body}
  let alertsTimer = null
  const seenTriggered = ref(new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')))

  const unseenTriggered = computed(() =>
    alerts.value.filter((a) => a.triggered_at && !seenTriggered.value.has(a.id)))

  async function fetchAlerts() {
    try {
      const { data } = await getAlerts()
      const prevTriggered = new Set(
        alerts.value.filter((a) => a.triggered_at).map((a) => a.id))
      alerts.value = data.alerts || []
      // recém-disparados nesta sessão -> toast
      for (const a of alerts.value) {
        if (a.triggered_at && !prevTriggered.has(a.id)
            && !seenTriggered.value.has(a.id) && alertsTimerHasRun) {
          pushToast(`Alerta ${a.symbol}`,
            `${kindLabel(a.kind)} ${a.level} — valor ${a.trigger_value}`)
        }
      }
      alertsTimerHasRun = true
    } catch { /* proximo ciclo */ }
  }

  let alertsTimerHasRun = false

  function markAlertsSeen() {
    for (const a of alerts.value) {
      if (a.triggered_at) seenTriggered.value.add(a.id)
    }
    localStorage.setItem(SEEN_KEY, JSON.stringify([...seenTriggered.value]))
  }

  async function addAlert(payload) {
    const { data } = await createAlert(payload)
    if (data.alert) alerts.value.push(data.alert)
    return data
  }

  async function removeAlert(id) {
    await deleteAlert(id)
    alerts.value = alerts.value.filter((a) => a.id !== id)
  }

  function startAlertsPolling() {
    if (alertsTimer) return
    fetchAlerts()
    alertsTimer = setInterval(fetchAlerts, 30000)
  }

  function kindLabel(kind) {
    return {
      price_above: 'preço acima de', price_below: 'preço abaixo de',
      funding_above: 'funding acima de', funding_below: 'funding abaixo de',
      signal_score_above: 'score multifator acima de', signal_score_below: 'score multifator abaixo de',
    }[kind] || kind
  }

  function pushToast(title, body) {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, title, body })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 8000)
  }

  // ── Notícias ──────────────────────────────────────────────────────────
  const newsItems = ref([])
  const newsFailed = ref([])
  const newsLoading = ref(false)
  const newsCat = ref('all')             // all | crypto | markets
  let newsTimer = null

  async function fetchNews() {
    newsLoading.value = newsItems.value.length === 0
    try {
      const { data } = await getNews(newsCat.value)
      newsItems.value = data.items || []
      newsFailed.value = data.failed_sources || []
    } catch { /* proximo ciclo */ } finally {
      newsLoading.value = false
    }
  }

  function setNewsCat(c) {
    if (newsCat.value === c) return
    newsCat.value = c
    newsItems.value = []
    fetchNews()
  }

  function startNewsPolling() {
    stopNewsPolling()
    fetchNews()
    newsTimer = setInterval(fetchNews, 300000)
  }

  function stopNewsPolling() {
    if (newsTimer) { clearInterval(newsTimer); newsTimer = null }
  }

  return {
    watchlist, watchRows, watchError, sparks,
    addToWatchlist, removeFromWatchlist, fetchWatch, fetchSpark,
    startWatchPolling, stopWatchPolling,
    screenerRows, screenerLoading, screenerError, screenerMarket,
    fetchScreener, setScreenerMarket, startScreenerPolling, stopScreenerPolling,
    desData, desLoading, desError, fetchDes,
    alerts, toasts, unseenTriggered, kindLabel,
    fetchAlerts, addAlert, removeAlert, startAlertsPolling, markAlertsSeen, pushToast,
    newsItems, newsFailed, newsLoading, newsCat, setNewsCat,
    startNewsPolling, stopNewsPolling,
  }
})
