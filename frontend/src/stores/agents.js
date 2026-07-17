import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client.js'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref([])
  const skills = ref([])
  const proposals = ref([])
  const toolCatalog = ref({})
  const hasKey = ref(false)
  const selected = ref(null)      // agente ativo no runner
  const events = ref([])          // stream da conversa atual
  const history = ref([])         // messages para continuação
  const running = ref(false)
  const error = ref(null)

  async function fetchAgents() {
    const { data } = await api.get('/agents')
    agents.value = data.agents
    skills.value = data.skills
    proposals.value = data.proposals
    toolCatalog.value = data.tools
    hasKey.value = data.has_key
  }

  async function saveSkill(skill) {
    if (skill.id) await api.put(`/agents/skills/${skill.id}`, skill)
    else await api.post('/agents/skills', skill)
    await fetchAgents()
  }

  async function removeSkill(id) {
    await api.delete(`/agents/skills/${id}`)
    await fetchAgents()
  }

  async function reviewProposal(id, action) {
    await api.post(`/agents/proposals/${id}/${action}`)
    await fetchAgents()
  }

  async function saveAgent(agent) {
    const { data } = agent.id
      ? await api.put(`/agents/${agent.id}`, agent)
      : await api.post('/agents', agent)
    await fetchAgents()
    return data
  }

  async function removeAgent(id) {
    await api.delete(`/agents/${id}`)
    if (selected.value?.id === id) select(null)
    await fetchAgents()
  }

  function select(agent) {
    selected.value = agent
    events.value = []
    history.value = []
    error.value = null
  }

  async function run(prompt) {
    if (!selected.value || running.value) return
    running.value = true
    error.value = null
    events.value.push({ type: 'user', content: prompt })

    try {
      const resp = await fetch(`/api/agents/${selected.value.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, messages: history.value }),
      })
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        let idx
        while ((idx = buf.indexOf('\n\n')) >= 0) {
          const chunk = buf.slice(0, idx)
          buf = buf.slice(idx + 2)
          const evMatch = chunk.match(/^event: (.+)$/m)
          const dataMatch = chunk.match(/^data: (.+)$/m)
          if (!evMatch || !dataMatch) continue
          const type = evMatch[1]
          const data = JSON.parse(dataMatch[1])
          if (type === 'done') {
            history.value = data.messages
          } else if (type === 'error') {
            error.value = data.error
          } else {
            events.value.push({ type, ...data })
          }
        }
      }
    } catch (e) {
      error.value = e.message
    } finally {
      running.value = false
    }
  }

  return {
    agents, skills, proposals, toolCatalog, hasKey,
    selected, events, history, running, error,
    fetchAgents, saveAgent, removeAgent, select, run,
    saveSkill, removeSkill, reviewProposal,
  }
})
