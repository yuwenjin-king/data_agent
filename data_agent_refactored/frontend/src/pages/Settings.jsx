import { useEffect, useState } from 'react'
import { Card, Tabs, Table, Button, Space, Form, Input, Select, Modal, message, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { configService, datasourceService } from '../services'

const { Option } = Select
const { TextArea } = Input

function Settings() {
  const [activeTab, setActiveTab] = useState('datasources')
  const [datasources, setDatasources] = useState([])
  const [modelConfigs, setModelConfigs] = useState([])
  const [promptConfigs, setPromptConfigs] = useState([])
  const [datasourceModalVisible, setDatasourceModalVisible] = useState(false)
  const [tablesModalVisible, setTablesModalVisible] = useState(false)
  const [selectedDatasource, setSelectedDatasource] = useState(null)
  const [datasourceTables, setDatasourceTables] = useState([])
  const [selectedTable, setSelectedTable] = useState(null)
  const [tableColumns, setTableColumns] = useState([])
  const [datasourceActionLoading, setDatasourceActionLoading] = useState(null)
  const [modelModalVisible, setModelModalVisible] = useState(false)
  const [modelActionLoading, setModelActionLoading] = useState(null)
  const [promptModalVisible, setPromptModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchDatasources()
    fetchModelConfigs()
    fetchPromptConfigs()
  }, [])

  const fetchDatasources = async () => {
    try {
      const res = await datasourceService.getAll()
      setDatasources(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch datasources:', error)
    }
  }

  const fetchModelConfigs = async () => {
    try {
      const res = await configService.getModelConfigs()
      setModelConfigs(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch model configs:', error)
    }
  }

  const fetchPromptConfigs = async () => {
    try {
      const res = await configService.getPromptConfigs()
      setPromptConfigs(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch prompt configs:', error)
    }
  }

  const handleCreateDatasource = async (values) => {
    try {
      await datasourceService.create(values)
      message.success('创建成功')
      setDatasourceModalVisible(false)
      fetchDatasources()
      form.resetFields()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleDatasourceAction = async (record, action) => {
    const actionKey = `${record.id}-${action}`
    try {
      setDatasourceActionLoading(actionKey)
      if (action === 'test') {
        const res = await datasourceService.testConnection(record.id)
        const result = res.data.data
        if (result?.success) {
          message.success(result.message || '连接测试成功')
        } else {
          message.error(result?.message || '连接测试失败')
        }
      } else if (action === 'activate') {
        await datasourceService.activate(record.id)
        message.success('已激活数据源')
      } else if (action === 'deactivate') {
        await datasourceService.deactivate(record.id)
        message.success('已停用数据源')
      }
      fetchDatasources()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setDatasourceActionLoading(null)
    }
  }

  const openTablesModal = async (record) => {
    try {
      setSelectedDatasource(record)
      setSelectedTable(null)
      setTableColumns([])
      setTablesModalVisible(true)
      const res = await datasourceService.getTables(record.id)
      setDatasourceTables(res.data.data || [])
    } catch (error) {
      message.error('读取表列表失败')
      setDatasourceTables([])
    }
  }

  const selectDatasourceTable = async (tableName) => {
    try {
      setSelectedTable(tableName)
      const res = await datasourceService.getColumns(selectedDatasource.id, tableName)
      setTableColumns(res.data.data || [])
    } catch (error) {
      message.error('读取字段列表失败')
      setTableColumns([])
    }
  }

  const handleCreateModelConfig = async (values) => {
    try {
      await configService.createModelConfig(values)
      message.success('创建成功')
      setModelModalVisible(false)
      fetchModelConfigs()
      form.resetFields()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleModelAction = async (record, active) => {
    try {
      setModelActionLoading(`${record.id}-${active ? 'activate' : 'deactivate'}`)
      if (active) {
        await configService.activateModelConfig(record.id)
        message.success('模型配置已激活')
      } else {
        await configService.deactivateModelConfig(record.id)
        message.success('模型配置已停用')
      }
      fetchModelConfigs()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setModelActionLoading(null)
    }
  }

  const handleCreatePromptConfig = async (values) => {
    try {
      await configService.createPromptConfig(values)
      message.success('创建成功')
      setPromptModalVisible(false)
      fetchPromptConfigs()
      form.resetFields()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const datasourceColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '主机', dataIndex: 'host', key: 'host' },
    { title: '端口', dataIndex: 'port', key: 'port' },
    { title: '数据库', dataIndex: 'database_name', key: 'database_name' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value) => (
        <Tag color={value === 'active' ? 'green' : 'default'}>
          {value === 'active' ? '已激活' : '未激活'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space wrap>
          <Button
            size="small"
            loading={datasourceActionLoading === `${record.id}-test`}
            onClick={() => handleDatasourceAction(record, 'test')}
          >
            测试连接
          </Button>
          <Button size="small" onClick={() => openTablesModal(record)}>
            表字段
          </Button>
          {record.status === 'active' ? (
            <Button
              size="small"
              loading={datasourceActionLoading === `${record.id}-deactivate`}
              onClick={() => handleDatasourceAction(record, 'deactivate')}
            >
              停用
            </Button>
          ) : (
            <Button
              size="small"
              type="primary"
              loading={datasourceActionLoading === `${record.id}-activate`}
              onClick={() => handleDatasourceAction(record, 'activate')}
            >
              激活
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const modelColumns = [
    { title: '提供商', dataIndex: 'provider', key: 'provider' },
    { title: '模型名称', dataIndex: 'model_name', key: 'model_name' },
    { title: '类型', dataIndex: 'model_type', key: 'model_type' },
    { title: 'Base URL', dataIndex: 'base_url', key: 'base_url', ellipsis: true },
    {
      title: '是否激活',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => (v ? '是' : '否'),
    },
    { title: 'API Key', dataIndex: 'api_key', key: 'api_key' },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) =>
        record.is_active ? (
          <Button
            size="small"
            loading={modelActionLoading === `${record.id}-deactivate`}
            onClick={() => handleModelAction(record, false)}
          >
            停用
          </Button>
        ) : (
          <Button
            size="small"
            type="primary"
            loading={modelActionLoading === `${record.id}-activate`}
            onClick={() => handleModelAction(record, true)}
          >
            激活
          </Button>
        ),
    },
  ]

  const promptColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'prompt_type', key: 'prompt_type' },
    { title: '是否启用', dataIndex: 'enabled', key: 'enabled', render: (v) => (v ? '是' : '否') },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ]

  const tabItems = [
    {
      key: 'datasources',
      label: '数据源管理',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setDatasourceModalVisible(true)}
            >
              添加数据源
            </Button>
          }
        >
          <Table columns={datasourceColumns} dataSource={datasources} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'models',
      label: '模型配置',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModelModalVisible(true)}
            >
              添加模型配置
            </Button>
          }
        >
          <Table columns={modelColumns} dataSource={modelConfigs} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'prompts',
      label: 'Prompt 配置',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setPromptModalVisible(true)}
            >
              添加 Prompt 配置
            </Button>
          }
        >
          <Table columns={promptColumns} dataSource={promptConfigs} rowKey="id" />
        </Card>
      ),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>系统设置</h1>
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      <Modal
        title="添加数据源"
        open={datasourceModalVisible}
        onCancel={() => setDatasourceModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateDatasource}>
          <Form.Item label="名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="类型" name="type" rules={[{ required: true }]}>
            <Select>
              <Option value="mysql">MySQL</Option>
              <Option value="postgresql">PostgreSQL</Option>
            </Select>
          </Form.Item>
          <Form.Item label="主机" name="host" rules={[{ required: true }]}>
            <Input placeholder="localhost" />
          </Form.Item>
          <Form.Item label="端口" name="port" rules={[{ required: true }]}>
            <Input type="number" placeholder="3306" />
          </Form.Item>
          <Form.Item label="数据库名" name="database_name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setDatasourceModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加模型配置"
        open={modelModalVisible}
        onCancel={() => setModelModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateModelConfig}>
          <Form.Item label="提供商" name="provider" rules={[{ required: true }]}>
            <Input placeholder="openai" />
          </Form.Item>
          <Form.Item label="Base URL" name="base_url" rules={[{ required: true }]}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item label="API Key" name="api_key" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item label="模型名称" name="model_name" rules={[{ required: true }]}>
            <Input placeholder="gpt-4" />
          </Form.Item>
          <Form.Item label="模型类型" name="model_type" initialValue="CHAT">
            <Select>
              <Option value="CHAT">Chat</Option>
              <Option value="EMBEDDING">Embedding</Option>
            </Select>
          </Form.Item>
          <Form.Item label="温度" name="temperature" initialValue={0.7}>
            <Input type="number" step={0.1} min={0} max={2} />
          </Form.Item>
          <Form.Item label="最大 Token" name="max_tokens" initialValue={2000}>
            <Input type="number" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setModelModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`${selectedDatasource?.name || ''} 表字段`}
        open={tablesModalVisible}
        onCancel={() => setTablesModalVisible(false)}
        footer={null}
        width={760}
      >
        <Space align="start" style={{ width: '100%' }}>
          <Table
            size="small"
            style={{ width: 320 }}
            columns={[{ title: '表名', dataIndex: 'name', key: 'name' }]}
            dataSource={datasourceTables.map((name) => ({ name }))}
            rowKey="name"
            pagination={false}
            onRow={(record) => ({
              onClick: () => selectDatasourceTable(record.name),
              style: {
                cursor: 'pointer',
                background: selectedTable === record.name ? '#e6f4ff' : undefined,
              },
            })}
          />
          <Table
            size="small"
            style={{ flex: 1, minWidth: 320 }}
            columns={[{ title: selectedTable ? `${selectedTable} 字段` : '字段', dataIndex: 'name' }]}
            dataSource={tableColumns.map((name) => ({ name }))}
            rowKey="name"
            pagination={false}
          />
        </Space>
      </Modal>

      <Modal
        title="添加 Prompt 配置"
        open={promptModalVisible}
        onCancel={() => setPromptModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreatePromptConfig}>
          <Form.Item label="名称" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Prompt 类型" name="prompt_type" rules={[{ required: true }]}>
            <Select>
              <Option value="report-generator">报告生成</Option>
              <Option value="planner">规划器</Option>
              <Option value="sql-generator">SQL 生成</Option>
            </Select>
          </Form.Item>
          <Form.Item label="系统 Prompt" name="system_prompt" rules={[{ required: true }]}>
            <TextArea rows={8} />
          </Form.Item>
          <Form.Item label="优先级" name="priority" initialValue={0}>
            <Input type="number" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setPromptModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Settings
