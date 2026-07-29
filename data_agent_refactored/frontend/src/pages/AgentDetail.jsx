import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Card,
  Tabs,
  Button,
  Space,
  Table,
  Form,
  Input,
  Select,
  Modal,
  message,
  Tag,
  Checkbox,
} from 'antd'
import { ArrowLeftOutlined, PlusOutlined } from '@ant-design/icons'
import { agentService, datasourceService, knowledgeService } from '../services'

const { Option } = Select
const { TextArea } = Input

function AgentDetail() {
  const { id } = useParams()
  const [agent, setAgent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('basic')

  const [businessKnowledge, setBusinessKnowledge] = useState([])
  const [semanticModels, setSemanticModels] = useState([])
  const [, setAgentKnowledge] = useState([])
  const [presetQuestions, setPresetQuestions] = useState([])
  const [agentDatasources, setAgentDatasources] = useState([])
  const [allDatasources, setAllDatasources] = useState([])

  const [knowledgeModalVisible, setKnowledgeModalVisible] = useState(false)
  const [datasourceModalVisible, setDatasourceModalVisible] = useState(false)
  const [schemaModalVisible, setSchemaModalVisible] = useState(false)
  const [schemaDatasource, setSchemaDatasource] = useState(null)
  const [availableTables, setAvailableTables] = useState([])
  const [schemaTables, setSchemaTables] = useState([])
  const [datasourceActionLoading, setDatasourceActionLoading] = useState(null)

  const [form] = Form.useForm()

  useEffect(() => {
    if (id) {
      fetchAgent()
      fetchAllDatasources()
      fetchRelatedData()
    }
    // Fetch on agent (route param) change only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const fetchAgent = async () => {
    try {
      setLoading(true)
      const res = await agentService.getById(id)
      setAgent(res.data.data)
    } catch (error) {
      message.error('获取智能体信息失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchAllDatasources = async () => {
    try {
      const res = await datasourceService.getAll()
      setAllDatasources(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch datasources:', error)
    }
  }

  const fetchRelatedData = async () => {
    try {
      const [bkRes, smRes, akRes, pqRes, adRes] = await Promise.all([
        agentService.getBusinessKnowledge(id),
        knowledgeService.getSemanticModels(id),
        knowledgeService.getAgentKnowledge(id),
        knowledgeService.getPresetQuestions(id),
        datasourceService.getAgentDatasources(id),
      ])
      setBusinessKnowledge(bkRes.data.data || [])
      setSemanticModels(smRes.data.data || [])
      setAgentKnowledge(akRes.data.data || [])
      setPresetQuestions(pqRes.data.data || [])
      setAgentDatasources(adRes.data.data || [])
    } catch (error) {
      console.error('Failed to fetch related data:', error)
    }
  }

  const handleAddKnowledge = async (values) => {
    try {
      await agentService.createBusinessKnowledge(id, values)
      message.success('添加成功')
      setKnowledgeModalVisible(false)
      fetchRelatedData()
      form.resetFields()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleLinkDatasource = async (values) => {
    try {
      await datasourceService.linkAgent({
        agent_id: parseInt(id),
        datasource_id: values.datasource_id,
        is_active: true,
      })
      message.success('关联成功')
      setDatasourceModalVisible(false)
      fetchRelatedData()
    } catch (error) {
      message.error('关联失败')
    }
  }

  const handleActivateDatasourceLink = async (record) => {
    try {
      setDatasourceActionLoading(`activate-${record.id}`)
      await datasourceService.activateAgentDatasource(record.id)
      message.success('已设为当前数据源')
      fetchRelatedData()
    } catch (error) {
      message.error('激活失败')
    } finally {
      setDatasourceActionLoading(null)
    }
  }

  const openSchemaModal = async (record) => {
    const datasource = allDatasources.find((item) => item.id === record.datasource_id)
    try {
      setSchemaDatasource(datasource || record)
      setSchemaTables([])
      setSchemaModalVisible(true)
      setDatasourceActionLoading(`tables-${record.id}`)
      const res = await datasourceService.getTables(record.datasource_id)
      setAvailableTables(res.data.data || [])
    } catch (error) {
      message.error('读取表列表失败')
      setAvailableTables([])
    } finally {
      setDatasourceActionLoading(null)
    }
  }

  const handleInitSchema = async () => {
    if (!schemaTables.length) {
      message.warning('请至少选择一张表')
      return
    }
    try {
      setDatasourceActionLoading('init-schema')
      await agentService.initAgentSchema(id, schemaTables)
      message.success('Schema 初始化完成')
      setSchemaModalVisible(false)
      setSchemaTables([])
    } catch (error) {
      message.error('Schema 初始化失败')
    } finally {
      setDatasourceActionLoading(null)
    }
  }

  const bkColumns = [
    { title: '业务名词', dataIndex: 'business_term', key: 'business_term' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '同义词', dataIndex: 'synonyms', key: 'synonyms' },
    {
      title: '是否召回',
      dataIndex: 'is_recall',
      key: 'is_recall',
      render: (v) => (v ? '是' : '否'),
    },
  ]

  const smColumns = [
    { title: '表名', dataIndex: 'table_name', key: 'table_name' },
    { title: '字段名', dataIndex: 'column_name', key: 'column_name' },
    { title: '业务名称', dataIndex: 'business_name', key: 'business_name' },
    { title: '数据类型', dataIndex: 'data_type', key: 'data_type' },
  ]

  const pqColumns = [
    { title: '问题', dataIndex: 'question', key: 'question' },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order' },
    {
      title: '是否启用',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => (v ? '是' : '否'),
    },
  ]

  const adColumns = [
    {
      title: '数据源',
      dataIndex: 'datasource_id',
      key: 'datasource_id',
      render: (id) => {
        const ds = allDatasources.find((d) => d.id === id)
        return ds?.name || id
      },
    },
    {
      title: '是否激活',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => <Tag color={v ? 'green' : 'default'}>{v ? '当前使用' : '未使用'}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space wrap>
          {record.is_active ? null : (
            <Button
              size="small"
              type="primary"
              loading={datasourceActionLoading === `activate-${record.id}`}
              onClick={() => handleActivateDatasourceLink(record)}
            >
              设为当前
            </Button>
          )}
          <Button
            size="small"
            loading={datasourceActionLoading === `tables-${record.id}`}
            onClick={() => openSchemaModal(record)}
          >
            初始化 Schema
          </Button>
        </Space>
      ),
    },
  ]

  const tabItems = [
    {
      key: 'basic',
      label: '基本信息',
      children: (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <strong>名称：</strong>
              {agent?.name}
            </div>
            <div>
              <strong>描述：</strong>
              {agent?.description}
            </div>
            <div>
              <strong>状态：</strong>
              {agent?.status}
            </div>
            <div>
              <strong>分类：</strong>
              {agent?.category}
            </div>
          </Space>
        </Card>
      ),
    },
    {
      key: 'datasources',
      label: '数据源',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setDatasourceModalVisible(true)}
            >
              关联数据源
            </Button>
          }
        >
          <Table columns={adColumns} dataSource={agentDatasources} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'business',
      label: '业务知识',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setKnowledgeModalVisible(true)}
            >
              添加业务知识
            </Button>
          }
        >
          <Table columns={bkColumns} dataSource={businessKnowledge} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'semantic',
      label: '语义模型',
      children: (
        <Card>
          <Table columns={smColumns} dataSource={semanticModels} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'preset',
      label: '预设问题',
      children: (
        <Card>
          <Table columns={pqColumns} dataSource={presetQuestions} rowKey="id" />
        </Card>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Link to="/agents">
          <Button icon={<ArrowLeftOutlined />}>返回</Button>
        </Link>
        <h1 style={{ margin: 0 }}>智能体配置 - {agent?.name}</h1>
      </Space>
      <Card loading={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      <Modal
        title="添加业务知识"
        open={knowledgeModalVisible}
        onCancel={() => setKnowledgeModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAddKnowledge}>
          <Form.Item label="业务名词" name="business_term" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item label="同义词" name="synonyms">
            <Input placeholder="多个同义词用逗号分隔" />
          </Form.Item>
          <Form.Item label="是否召回" name="is_recall" initialValue={1}>
            <Select>
              <Option value={1}>是</Option>
              <Option value={0}>否</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setKnowledgeModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="关联数据源"
        open={datasourceModalVisible}
        onCancel={() => setDatasourceModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleLinkDatasource}>
          <Form.Item label="数据源" name="datasource_id" rules={[{ required: true }]}>
            <Select>
              {allDatasources.map((ds) => (
                <Option key={ds.id} value={ds.id}>
                  {ds.name}
                </Option>
              ))}
            </Select>
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
        title={`初始化 Schema - ${schemaDatasource?.name || ''}`}
        open={schemaModalVisible}
        onCancel={() => setSchemaModalVisible(false)}
        onOk={handleInitSchema}
        confirmLoading={datasourceActionLoading === 'init-schema'}
        okText="初始化"
        cancelText="取消"
      >
        <Checkbox.Group
          value={schemaTables}
          onChange={setSchemaTables}
          options={availableTables.map((name) => ({ label: name, value: name }))}
        />
      </Modal>
    </div>
  )
}

export default AgentDetail
