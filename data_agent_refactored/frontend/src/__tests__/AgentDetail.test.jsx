import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import AgentDetail from '../pages/AgentDetail'
import { agentService, datasourceService, knowledgeService } from '../services'

vi.mock('../services', () => ({
  agentService: {
    getById: vi.fn(),
    getBusinessKnowledge: vi.fn(),
    createBusinessKnowledge: vi.fn(),
    initAgentSchema: vi.fn(),
  },
  datasourceService: {
    getAll: vi.fn(),
    getAgentDatasources: vi.fn(),
    linkAgent: vi.fn(),
    activateAgentDatasource: vi.fn(),
    getTables: vi.fn(),
  },
  knowledgeService: {
    getSemanticModels: vi.fn(),
    getAgentKnowledge: vi.fn(),
    getPresetQuestions: vi.fn(),
  },
}))

describe('AgentDetail', () => {
  beforeEach(() => {
    agentService.getById.mockResolvedValue({
      data: { data: { id: 1, name: 'Sales Agent', description: 'demo', status: 'draft' } },
    })
    agentService.getBusinessKnowledge.mockResolvedValue({ data: { data: [] } })
    agentService.initAgentSchema.mockResolvedValue({ data: { data: ['orders'] } })
    datasourceService.getAll.mockResolvedValue({
      data: { data: [{ id: 11, name: 'Sales DB', status: 'active' }] },
    })
    datasourceService.getAgentDatasources.mockResolvedValue({
      data: { data: [{ id: 21, agent_id: 1, datasource_id: 11, is_active: 1 }] },
    })
    datasourceService.getTables.mockResolvedValue({ data: { data: ['orders', 'customers'] } })
    knowledgeService.getSemanticModels.mockResolvedValue({ data: { data: [] } })
    knowledgeService.getAgentKnowledge.mockResolvedValue({ data: { data: [] } })
    knowledgeService.getPresetQuestions.mockResolvedValue({ data: { data: [] } })
  })

  it('initializes selected datasource tables for schema recall', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByText('数据源'))
    expect(await screen.findByText('Sales DB')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /初始化 Schema/ }))
    expect(datasourceService.getTables).toHaveBeenCalledWith(11)

    await user.click(await screen.findByRole('checkbox', { name: 'orders' }))
    await user.click(screen.getByRole('button', { name: /^初始化$/ }))

    await waitFor(() => expect(agentService.initAgentSchema).toHaveBeenCalledWith('1', ['orders']))
  })
})
