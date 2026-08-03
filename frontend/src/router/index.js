import { createRouter, createWebHistory } from 'vue-router'

// Toda rota e lazy. Estas nove eram import estatico e sozinhas respondiam por
// 513 kB no chunk inicial — quem cai em /optimizer baixava outras oito telas
// que nao pediu.
const routes = [
  {
    path: '/',
    redirect: '/optimizer',
  },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/backtest', name: 'backtest', component: () => import('@/views/BacktestView.vue') },
  { path: '/grafico', name: 'grafico', component: () => import('@/views/ChartView.vue') },
  { path: '/optimizer', name: 'optimizer', component: () => import('@/views/OptimizerView.vue') },
  { path: '/prop-challenge', name: 'prop-challenge', component: () => import('@/views/PropChallengeView.vue') },
  { path: '/regime', name: 'regime', component: () => import('@/views/RegimeView.vue') },
  { path: '/degenerado', name: 'degenerado', component: () => import('@/views/DegenView.vue') },
  { path: '/journal', name: 'journal', component: () => import('@/views/JournalView.vue') },
  { path: '/automation', name: 'automation', component: () => import('@/views/AutomationView.vue') },
  { path: '/agentes', name: 'agentes', component: () => import('@/views/AgentsView.vue') },
  { path: '/hft', name: 'hft', component: () => import('@/views/HftView.vue') },
  // ── Terminal (Bloomberg-like) — lazy-loaded ──
  { path: '/monitor', name: 'monitor', component: () => import('@/views/MonitorView.vue') },
  { path: '/screener', name: 'screener', component: () => import('@/views/ScreenerView.vue') },
  { path: '/eqs', name: 'eqs', component: () => import('@/views/EqsView.vue') },
  { path: '/rates', name: 'rates', component: () => import('@/views/RatesView.vue') },
  { path: '/omon', name: 'omon', component: () => import('@/views/OptionsView.vue') },
  { path: '/book', name: 'book', component: () => import('@/views/BookView.vue') },
  { path: '/ea', name: 'ea', component: () => import('@/views/EaView.vue') },
  { path: '/cdty', name: 'cdty', component: () => import('@/views/CdtyView.vue') },
  { path: '/osa', name: 'osa', component: () => import('@/views/StrategyView.vue') },
  { path: '/tech', name: 'tech', component: () => import('@/views/TechChartView.vue') },
  { path: '/trade', name: 'trade', component: () => import('@/views/TradeView.vue') },
  { path: '/alt', name: 'alt', component: () => import('@/views/AltDataView.vue') },
  { path: '/des', name: 'des', component: () => import('@/views/DesView.vue') },
  { path: '/alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue') },
  { path: '/news', name: 'news', component: () => import('@/views/NewsView.vue') },
  { path: '/seasonality', name: 'seasonality', component: () => import('@/views/SeasonalityView.vue') },
  { path: '/intelligence', name: 'intelligence', component: () => import('@/views/IntelligenceView.vue') },
  { path: '/calendar', name: 'calendar', component: () => import('@/views/MarketCalendarView.vue') },
  { path: '/portfolio-lab', name: 'portfolio-lab', component: () => import('@/views/PortfolioLabView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
