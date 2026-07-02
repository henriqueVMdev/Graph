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
  { path: '/des', name: 'des', component: () => import('@/views/DesView.vue') },
  { path: '/alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue') },
  { path: '/news', name: 'news', component: () => import('@/views/NewsView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
