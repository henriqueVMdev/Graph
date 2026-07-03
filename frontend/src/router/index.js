import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import BacktestView from '@/views/BacktestView.vue'
import OptimizerView from '@/views/OptimizerView.vue'
import PropChallengeView from '@/views/PropChallengeView.vue'
import RegimeView from '@/views/RegimeView.vue'
import JournalView from '@/views/JournalView.vue'
import ChartView from '@/views/ChartView.vue'
import AutomationView from '@/views/AutomationView.vue'

const routes = [
  {
    path: '/',
    redirect: '/optimizer',
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
  },
  {
    path: '/backtest',
    name: 'backtest',
    component: BacktestView,
  },
  {
    path: '/grafico',
    name: 'grafico',
    component: ChartView,
  },
  {
    path: '/optimizer',
    name: 'optimizer',
    component: OptimizerView,
  },
  {
    path: '/prop-challenge',
    name: 'prop-challenge',
    component: PropChallengeView,
  },
  {
    path: '/regime',
    name: 'regime',
    component: RegimeView,
  },
  {
    path: '/journal',
    name: 'journal',
    component: JournalView,
  },
  {
    path: '/automation',
    name: 'automation',
    component: AutomationView,
  },
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
  { path: '/des', name: 'des', component: () => import('@/views/DesView.vue') },
  { path: '/alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue') },
  { path: '/news', name: 'news', component: () => import('@/views/NewsView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
