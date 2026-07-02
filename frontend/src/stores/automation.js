import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getDeployments, createDeployment, startDeployment, stopDeployment,
  deleteDeployment, getDeploymentStatus, getRunnerStatus, getStrategies,
} from '@/api/client.js'

export const useAutomationStore = defineStore('automation', () => {
  const deployments = ref([])
  const strategies = ref([])
  const selectedId = ref(null)
  const status = ref(null)          // detalhe do deployment selecionado
  const runnerStatus = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Config validada vinda de outra view ("Enviar para Automação")
  const pendingDeployment = ref(null)
  const showForm = ref(false)

  let pollTimer = null

  async function fetchStrategies() {
    try {
      const { data } = await getStrategies()
      strategies.value = (data.strategies || []).filter((s) => !s.error)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  async function fetchDeployments() {
    try {
      const { data } = await getDeployments()
      deployments.value = data.deployments || []
      error.value = null
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  async function fetchStatus() {
    if (!selectedId.value) return
    try {
      const { data } = await getDeploymentStatus(selectedId.value)
      status.value = data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  async function fetchRunner() {
    try {
      const { data } = await getRunnerStatus()
      runnerStatus.value = data
    } catch {
      runnerStatus.value = null
    }
  }

  function select(id) {
    selectedId.value = id
    status.value = null
    fetchStatus()
  }

  async function create(payload) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await createDeployment(payload)
      await fetchDeployments()
      select(data.id)
      showForm.value = false
      pendingDeployment.value = null
      return data.id
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function start(id) {
    try {
      await startDeployment(id)
      await Promise.all([fetchDeployments(), fetchStatus(), fetchRunner()])
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  async function stop(id, closePosition = false) {
    try {
      await stopDeployment(id, closePosition)
      await Promise.all([fetchDeployments(), fetchStatus()])
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  async function remove(id) {
    try {
      await deleteDeployment(id)
      if (selectedId.value === id) {
        selectedId.value = null
        status.value = null
      }
      await fetchDeployments()
    } catch (e) {
      error.value = e.response?.data?.error || e.message
    }
  }

  function startPolling() {
    stopPolling()
    fetchDeployments()
    fetchRunner()
    fetchStatus()
    pollTimer = setInterval(() => {
      fetchDeployments()
      fetchRunner()
      if (selectedId.value) fetchStatus()
    }, 3000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    deployments, strategies, selectedId, status, runnerStatus,
    isLoading, error, pendingDeployment, showForm,
    fetchStrategies, fetchDeployments, fetchStatus, select,
    create, start, stop, remove, startPolling, stopPolling,
  }
})
