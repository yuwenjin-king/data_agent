import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import Chat from '../pages/Chat'
import { agentService, chatService } from '../services'

vi.mock('../services', () => ({
  agentService: {
    getById: vi.fn(),
  },
  chatService: {
    getSessions: vi.fn(),
    getMessages: vi.fn(),
    createSession: vi.fn(),
    streamMessage: vi.fn(),
  },
}))

describe('Chat', () => {
  beforeEach(() => {
    agentService.getById.mockResolvedValue({
      data: { data: { id: 1, name: 'Sales Agent', description: 'demo' } },
    })
    chatService.getSessions.mockResolvedValue({
      data: { data: [{ id: 'session-1', title: '销售分析', agent_id: 1 }] },
    })
    chatService.getMessages.mockResolvedValue({
      data: {
        data: [
          {
            id: 100,
            session_id: 'session-1',
            role: 'assistant',
            content: '分析完成',
            create_time: new Date().toISOString(),
            metadata: {
              plan: { execution_plan: [{ step: 1, tool_to_use: 'sql_generate' }] },
              sql_query: 'select sum(amount) from orders',
              execution_result: { rows: [{ total: 100 }] },
              error: 'sample error',
            },
          },
        ],
      },
    })
  })

  it('renders workflow artifacts from persisted assistant metadata', async () => {
    render(
      <MemoryRouter initialEntries={['/chat/1']}>
        <Routes>
          <Route path="/chat/:agentId" element={<Chat />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('分析完成')).toBeInTheDocument()
    expect(screen.getByText('执行计划')).toBeInTheDocument()
    expect(screen.getByText('SQL')).toBeInTheDocument()
    expect(screen.getByText('执行结果')).toBeInTheDocument()
    expect(screen.getByText('错误')).toBeInTheDocument()
    expect(screen.getByText(/select sum\(amount\)/)).toBeInTheDocument()
    expect(screen.getByText(/sample error/)).toBeInTheDocument()
  })
})
