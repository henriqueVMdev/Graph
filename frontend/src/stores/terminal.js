import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getWatch, getSpark, getScreener, getDes,
  getAlerts, createAlert, deleteAlert, getNews,
} from '@/api/client.js'

const WATCHLIST_KEY = 'graph.watchlist'
const SEEN_KEY = 'graph.alerts.seen'

export const useTerminalStore = defineStore('terminal', () => {
  // ── Watchlist (persistida) ────────────────────────────────────────────
  const watchlist = ref(
    JSON.parse(localStorage.getItem(WATCHLIST_KEY) || 'null')
    || ['BTC', 'ETH', 'SOL', 'DOGE'],   // cesta do relatório como default
  )
  const watchRows = ref([])
  const watchError = ref(null)
  const sparks = ref({})                 // base -> closes[]
  let watchTimer = null

  function saveWatchlist() {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist.value))
  }

  function addToWatchlist(base) {
    const b = base.trim().toUpperCase()
    if (b && !watchlist.value.includes(b)) {
      watchlist.value.push(b)
      saveWatchlist()
      fetchWatch()
    }
  }

  function removeFromWatchlist(base) {
    watchlist.value = watchlist.value.filter((s) => s !== base)
    saveWatchlist()
    watchRows.value = watchRows.value.filter((r) => r.base !== base)
  }

  async function fetchWatch() {
    if (!watchlist.value.length) { watchRows.value = []; return }
    try {
      const { data } = await getWatch(watchlist.value)
      if (data.rows) { watchRows.value = data.rows; watchError.value = null }
    } catch (e) {
      watchError.value = e.response?.data?.error || e.message
    }
  }

  async function fetchSpark(base) {
    if (sparks.value[base]) return
    try {
      const { data } = await getSpark(base)
      sparks.value = { ...sparks.value, [base]: data.closes || [] }
    } catch { /* sparkline é decorativa */ }
  }

  function startWatchPolling() {
    stopWatchPolling()
    fetchWatch()
    watchlist.value.forEach(fetchSpark)
    watchTimer = setInterval(fetchWatch, 5000)
  }

  function stopWatchPolling() {
    if (watchTimer) { clearInterval(watchTimer); watchTimer = null }
  }

  // ── Screener ──────────────────────────────────────────────────────────
  const screenerRows = ref([])
  const screenerLoading = ref(false)
  const screenerError = ref(null)
  let screenerTimer = null

  async function fetchScreener(top = 50) {
    screenerLoading.value = screenerRows.value.length === 0
    try {
      const { data } = await getScreener(top)
      if (data.rows) { screenerRows.value = data.rows; screenerError.value = null }
    } catch (e) {
      screenerError.value = e.response?.data?.error || e.message
    } finally {
      screenerLoading.value = false
    }
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

  async function fetchDes(base) {
    desLoading.value = true
    desError.value = null
    try {
      const { data } = await getDes(base)
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
  let newsTimer = null

  async function fetchNews() {
    newsLoading.value = newsItems.value.length === 0
    try {
      const { data } = await getNews()
      newsItems.value = data.items || []
      newsFailed.value = data.failed_sources || []
    } catch { /* proximo ciclo */ } finally {
      newsLoading.value = false
    }
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
    screenerRows, screenerLoading, screenerError,
    fetchScreener, startScreenerPolling, stopScreenerPolling,
    desData, desLoading, desError, fetchDes,
    alerts, toasts, unseenTriggered, kindLabel,
    fetchAlerts, addAlert, removeAlert, startAlertsPolling, markAlertsSeen, pushToast,
    newsItems, newsFailed, newsLoading, startNewsPolling, stopNewsPolling,
  }
})
