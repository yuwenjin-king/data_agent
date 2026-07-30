import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import AgentDetail from '../pages/AgentDetail'
import { agentService, datasourceService, knowledgeService } from '../services'

const routerFuture = { v7_startTransition: true, v7_relativeSplatPath: true }

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
    createSemanticModel: vi.fn(),
    enableSemanticModel: vi.fn(),
    disableSemanticModel: vi.fn(),
    getAgentKnowledge: vi.fn(),
    createAgentKnowledgeMultipart: vi.fn(),
    setAgentKnowledgeRecall: vi.fn(),
    retryAgentKnowledgeEmbedding: vi.fn(),
    getPresetQuestions: vi.fn(),
    createPresetQuestion: vi.fn(),
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
    knowledgeService.getSemanticModels.mockResolvedValue({
      data: {
        data: [
          {
            id: 31,
            table_name: 'orders',
            column_name: 'amount',
            business_name: '订单金额',
            data_type: 'decimal',
            status: 1,
          },
        ],
      },
    })
    knowledgeService.createSemanticModel.mockResolvedValue({ data: { data: {} } })
    knowledgeService.disableSemanticModel.mockResolvedValue({ data: { data: {} } })
    knowledgeService.getAgentKnowledge.mockResolvedValue({
      data: {
        data: [
          {
            id: 41,
            title: '口径说明',
            type: 'QA',
            source_filename: null,
            embedding_status: 'COMPLETED',
            is_recall: 1,
          },
          {
            id: 42,
            title: '失败知识',
            type: 'DOCUMENT',
            source_filename: 'bad.txt',
            embedding_status: 'FAILED',
            error_msg: 'No indexable content',
            is_recall: 1,
          },
        ],
      },
    })
    knowledgeService.setAgentKnowledgeRecall.mockResolvedValue({ data: { data: {} } })
    knowledgeService.retryAgentKnowledgeEmbedding.mockResolvedValue({ data: { data: {} } })
    knowledgeService.getPresetQuestions.mockResolvedValue({ data: { data: [] } })
    knowledgeService.createPresetQuestion.mockResolvedValue({ data: { data: {} } })
  })

  it('initializes selected datasource tables for schema recall', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']} future={routerFuture}>
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

  it('creates semantic models from the semantic tab', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']} future={routerFuture}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByText('语义模型'))
    await user.click(screen.getByRole('button', { name: /添加语义模型/ }))
    await user.type(screen.getByPlaceholderText('orders'), 'payments')
    await user.type(screen.getByPlaceholderText('amount'), 'pay_amount')
    await user.type(screen.getByPlaceholderText('订单金额'), '支付金额')
    await user.type(screen.getByPlaceholderText('decimal'), 'decimal')
    await user.click(screen.getByRole('button', { name: /确\s*定/ }))

    await waitFor(() =>
      expect(knowledgeService.createSemanticModel).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_id: 1,
          table_name: 'payments',
          column_name: 'pay_amount',
          business_name: '支付金额',
        }),
      ),
    )
  })

  it('toggles agent knowledge recall', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']} future={routerFuture}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByText('文件知识'))
    expect(await screen.findByText('口径说明')).toBeInTheDocument()
    await user.click(screen.getAllByRole('button', { name: /关闭召回/ })[0])

    expect(knowledgeService.setAgentKnowledgeRecall).toHaveBeenCalledWith(41, 0)
  })

  it('retries failed agent knowledge indexing', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']} future={routerFuture}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByText('文件知识'))
    expect(await screen.findByText('失败知识')).toBeInTheDocument()
    expect(screen.getByText('失败')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /重试/ }))

    expect(knowledgeService.retryAgentKnowledgeEmbedding).toHaveBeenCalledWith(42)
  })

  it('creates preset questions', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/agents/1']} future={routerFuture}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByText('预设问题'))
    await user.click(screen.getByRole('button', { name: /添加预设问题/ }))
    await user.type(screen.getByLabelText('问题'), '本月销售额是多少')
    await user.click(screen.getByRole('button', { name: /确\s*定/ }))

    await waitFor(() =>
      expect(knowledgeService.createPresetQuestion).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_id: 1,
          question: '本月销售额是多少',
          is_active: 1,
        }),
      ),
    )
  })
})
