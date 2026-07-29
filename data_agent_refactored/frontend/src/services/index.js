import api from './api'

export const authService = {
  status: () => api.get('/auth/status'),
  login: (username, password) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
}

export const agentService = {
  getAll: (params) => api.get('/agents', { params }),
  getById: (id) => api.get(`/agents/${id}`),
  create: (data) => api.post('/agents', data),
  update: (id, data) => api.put(`/agents/${id}`, data),
  delete: (id) => api.delete(`/agents/${id}`),
  getBusinessKnowledge: (agentId) => api.get(`/agents/${agentId}/business-knowledge`),
  createBusinessKnowledge: (agentId, data) =>
    api.post(`/agents/${agentId}/business-knowledge`, { ...data, agent_id: agentId }),
}

export const datasourceService = {
  getAll: () => api.get('/datasources'),
  getById: (id) => api.get(`/datasources/${id}`),
  create: (data) => api.post('/datasources', data),
  update: (id, data) => api.put(`/datasources/${id}`, data),
  delete: (id) => api.delete(`/datasources/${id}`),
  testConnection: (id) => api.post(`/datasources/${id}/test`),
  activate: (id) => api.post(`/datasources/${id}/activate`),
  deactivate: (id) => api.post(`/datasources/${id}/deactivate`),
  getTables: (id) => api.get(`/datasources/${id}/tables`),
  getColumns: (id, tableName) =>
    api.get(`/datasources/${id}/tables/${encodeURIComponent(tableName)}/columns`),
  linkAgent: (data) => api.post('/datasources/agent-datasources', data),
  activateAgentDatasource: (linkId) => api.post(`/datasources/agent-datasources/${linkId}/activate`),
  getAgentDatasources: (agentId) => api.get(`/datasources/agent-datasources/agent/${agentId}`),
  getLogicalRelations: (datasourceId) =>
    api.get(`/datasources/logical-relations/datasource/${datasourceId}`),
  createLogicalRelation: (data) => api.post('/datasources/logical-relations', data),
}

export const knowledgeService = {
  getSemanticModels: (agentId) => api.get(`/knowledge/semantic-models/agent/${agentId}`),
  createSemanticModel: (data) => api.post('/knowledge/semantic-models', data),
  getAgentKnowledge: (agentId) => api.get(`/knowledge/agent-knowledge/agent/${agentId}`),
  createAgentKnowledge: (data) => api.post('/knowledge/agent-knowledge', data),
  getPresetQuestions: (agentId) => api.get(`/knowledge/preset-questions/agent/${agentId}`),
  createPresetQuestion: (data) => api.post('/knowledge/preset-questions', data),
}

export const chatService = {
  getSessions: (agentId) => api.get(`/chat/sessions/agent/${agentId}`),
  getSession: (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  createSession: (data) => api.post('/chat/sessions', data),
  updateSession: (sessionId, data) => api.put(`/chat/sessions/${sessionId}`, data),
  getMessages: (sessionId) => api.get(`/chat/messages/session/${sessionId}`),
  sendMessage: (data) => api.post('/chat/completions', data),
  streamMessage: async (data, onEvent) => {
    const token = localStorage.getItem('data_agent_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers,
      body: JSON.stringify({ ...data, stream: true }),
    })

    if (!response.ok || !response.body) {
      if (response.status === 401) {
        localStorage.removeItem('data_agent_token')
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      throw new Error(`Stream request failed: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const lines = part.split('\n')
        let event = 'message'
        let data = {}
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            event = line.slice('event: '.length)
          } else if (line.startsWith('data: ')) {
            const payload = line.slice('data: '.length)
            try {
              data = JSON.parse(payload)
            } catch {
              data = { raw: payload }
            }
          }
        }
        onEvent?.({ event, data })
      }
    }

    return response
  },
}

export const configService = {
  getPromptConfigs: (params) => api.get('/chat/prompt-configs', { params }),
  createPromptConfig: (data) => api.post('/chat/prompt-configs', data),
  getModelConfigs: (modelType) =>
    api.get('/chat/model-configs', { params: { model_type: modelType } }),
  createModelConfig: (data) => api.post('/chat/model-configs', data),
  updateModelConfig: (id, data) => api.put(`/chat/model-configs/${id}`, data),
  activateModelConfig: (id) => api.post(`/chat/model-configs/${id}/activate`),
  deactivateModelConfig: (id) => api.post(`/chat/model-configs/${id}/deactivate`),
}
