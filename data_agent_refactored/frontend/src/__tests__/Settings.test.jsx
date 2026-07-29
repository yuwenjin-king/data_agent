import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import Settings from '../pages/Settings'
import { configService, datasourceService } from '../services'

vi.mock('../services', () => ({
  datasourceService: {
    getAll: vi.fn(),
    testConnection: vi.fn(),
    activate: vi.fn(),
    deactivate: vi.fn(),
    getTables: vi.fn(),
    getColumns: vi.fn(),
  },
  configService: {
    getModelConfigs: vi.fn(),
    getPromptConfigs: vi.fn(),
    activateModelConfig: vi.fn(),
    deactivateModelConfig: vi.fn(),
  },
}))

describe('Settings', () => {
  beforeEach(() => {
    datasourceService.getAll.mockResolvedValue({
      data: {
        data: [
          {
            id: 1,
            name: 'Sales DB',
            type: 'mysql',
            host: 'localhost',
            port: 3306,
            database_name: 'sales',
            status: 'inactive',
          },
        ],
      },
    })
    datasourceService.testConnection.mockResolvedValue({
      data: { data: { success: true, message: 'ok' } },
    })
    datasourceService.activate.mockResolvedValue({ data: { data: {} } })
    datasourceService.deactivate.mockResolvedValue({ data: { data: {} } })
    datasourceService.getTables.mockResolvedValue({ data: { data: ['orders'] } })
    datasourceService.getColumns.mockResolvedValue({ data: { data: ['id', 'amount'] } })
    configService.getModelConfigs.mockResolvedValue({
      data: {
        data: [
          {
            id: 10,
            provider: 'openai',
            model_name: 'gpt-4o',
            model_type: 'CHAT',
            base_url: 'https://api.openai.com/v1',
            api_key: '****1234',
            is_active: false,
          },
        ],
      },
    })
    configService.getPromptConfigs.mockResolvedValue({ data: { data: [] } })
    configService.activateModelConfig.mockResolvedValue({ data: { data: {} } })
  })

  it('supports datasource test, activation, and table/column inspection', async () => {
    const user = userEvent.setup()
    render(<Settings />)

    expect(await screen.findByText('Sales DB')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /测试连接/ }))
    expect(datasourceService.testConnection).toHaveBeenCalledWith(1)

    await user.click(screen.getByRole('button', { name: /激\s*活/ }))
    expect(datasourceService.activate).toHaveBeenCalledWith(1)

    await user.click(screen.getByRole('button', { name: /表字段/ }))
    expect(datasourceService.getTables).toHaveBeenCalledWith(1)
    expect(await screen.findByText('orders')).toBeInTheDocument()

    await user.click(screen.getByText('orders'))
    expect(datasourceService.getColumns).toHaveBeenCalledWith(1, 'orders')
    await waitFor(() => expect(screen.getByText('amount')).toBeInTheDocument())
  })

  it('activates model configs from the model tab', async () => {
    const user = userEvent.setup()
    render(<Settings />)

    await user.click(await screen.findByText('模型配置'))
    expect(await screen.findByText('gpt-4o')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /激\s*活/ }))

    expect(configService.activateModelConfig).toHaveBeenCalledWith(10)
  })
})
