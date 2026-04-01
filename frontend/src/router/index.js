import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import BacktestView from '@/views/BacktestView.vue'
import OptimizerView from '@/views/OptimizerView.vue'
import PropChallengeView from '@/views/PropChallengeView.vue'
import RegimeView from '@/views/RegimeView.vue'

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
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
