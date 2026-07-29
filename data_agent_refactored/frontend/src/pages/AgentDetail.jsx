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
  Upload,
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
  const [agentKnowledge, setAgentKnowledge] = useState([])
  const [presetQuestions, setPresetQuestions] = useState([])
  const [agentDatasources, setAgentDatasources] = useState([])
  const [allDatasources, setAllDatasources] = useState([])

  const [knowledgeModalVisible, setKnowledgeModalVisible] = useState(false)
  const [semanticModalVisible, setSemanticModalVisible] = useState(false)
  const [agentKnowledgeModalVisible, setAgentKnowledgeModalVisible] = useState(false)
  const [presetModalVisible, setPresetModalVisible] = useState(false)
  const [datasourceModalVisible, setDatasourceModalVisible] = useState(false)
  const [schemaModalVisible, setSchemaModalVisible] = useState(false)
  const [schemaDatasource, setSchemaDatasource] = useState(null)
  const [availableTables, setAvailableTables] = useState([])
  const [schemaTables, setSchemaTables] = useState([])
  const [datasourceActionLoading, setDatasourceActionLoading] = useState(null)
  const [knowledgeActionLoading, setKnowledgeActionLoading] = useState(null)

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

  const handleAddSemanticModel = async (values) => {
    try {
      await knowledgeService.createSemanticModel({
        ...values,
        agent_id: parseInt(id),
      })
      message.success('语义模型已添加')
      setSemanticModalVisible(false)
      fetchRelatedData()
      form.resetFields()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleSemanticModelStatus = async (record, enabled) => {
    try {
      setKnowledgeActionLoading(`semantic-${record.id}`)
      if (enabled) {
        await knowledgeService.enableSemanticModel(record.id)
        message.success('语义模型已启用')
      } else {
        await knowledgeService.disableSemanticModel(record.id)
        message.success('语义模型已停用')
      }
      fetchRelatedData()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setKnowledgeActionLoading(null)
    }
  }

  const handleAddAgentKnowledge = async (values) => {
    try {
      const payload = new FormData()
      payload.append('agent_id', parseInt(id))
      payload.append('title', values.title)
      payload.append('type', values.type)
      payload.append('is_recall', values.is_recall ?? 1)
      payload.append('splitter_type', values.splitter_type || 'token')
      if (values.question) payload.append('question', values.question)
      if (values.content) payload.append('content', values.content)
      const uploadFile = values.file?.[0]?.originFileObj
      if (uploadFile) payload.append('file', uploadFile)
      await knowledgeService.createAgentKnowledgeMultipart(payload)
      message.success('知识已添加')
      setAgentKnowledgeModalVisible(false)
      fetchRelatedData()
      form.resetFields()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleAgentKnowledgeRecall = async (record, enabled) => {
    try {
      setKnowledgeActionLoading(`knowledge-${record.id}`)
      await knowledgeService.setAgentKnowledgeRecall(record.id, enabled ? 1 : 0)
      message.success(enabled ? '已开启召回' : '已关闭召回')
      fetchRelatedData()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setKnowledgeActionLoading(null)
    }
  }

  const handleAddPresetQuestion = async (values) => {
    try {
      await knowledgeService.createPresetQuestion({
        ...values,
        agent_id: parseInt(id),
        is_active: values.is_active ?? 1,
      })
      message.success('预设问题已添加')
      setPresetModalVisible(false)
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
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) =>
        record.status ? (
          <Button
            size="small"
            loading={knowledgeActionLoading === `semantic-${record.id}`}
            onClick={() => handleSemanticModelStatus(record, false)}
          >
            停用
          </Button>
        ) : (
          <Button
            size="small"
            type="primary"
            loading={knowledgeActionLoading === `semantic-${record.id}`}
            onClick={() => handleSemanticModelStatus(record, true)}
          >
            启用
          </Button>
        ),
    },
  ]

  const akColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '文件', dataIndex: 'source_filename', key: 'source_filename' },
    {
      title: '向量状态',
      dataIndex: 'embedding_status',
      key: 'embedding_status',
      render: (v) => v || '-',
    },
    {
      title: '是否召回',
      dataIndex: 'is_recall',
      key: 'is_recall',
      render: (v) => <Tag color={v ? 'green' : 'default'}>{v ? '召回' : '不召回'}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) =>
        record.is_recall ? (
          <Button
            size="small"
            loading={knowledgeActionLoading === `knowledge-${record.id}`}
            onClick={() => handleAgentKnowledgeRecall(record, false)}
          >
            关闭召回
          </Button>
        ) : (
          <Button
            size="small"
            type="primary"
            loading={knowledgeActionLoading === `knowledge-${record.id}`}
            onClick={() => handleAgentKnowledgeRecall(record, true)}
          >
            开启召回
          </Button>
        ),
    },
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
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setSemanticModalVisible(true)}
            >
              添加语义模型
            </Button>
          }
        >
          <Table columns={smColumns} dataSource={semanticModels} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'agent-knowledge',
      label: '文件知识',
      children: (
        <Card
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAgentKnowledgeModalVisible(true)}
            >
              添加知识
            </Button>
          }
        >
          <Table columns={akColumns} dataSource={agentKnowledge} rowKey="id" />
        </Card>
      ),
    },
    {
      key: 'preset',
      label: '预设问题',
      children: (
        <Card
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setPresetModalVisible(true)}>
              添加预设问题
            </Button>
          }
        >
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
        title="添加语义模型"
        open={semanticModalVisible}
        onCancel={() => setSemanticModalVisible(false)}
        footer={null}
        width={680}
      >
        <Form form={form} layout="vertical" onFinish={handleAddSemanticModel}>
          <Space style={{ width: '100%' }} align="start">
            <Form.Item label="表名" name="table_name" rules={[{ required: true }]}>
              <Input placeholder="orders" />
            </Form.Item>
            <Form.Item label="字段名" name="column_name" rules={[{ required: true }]}>
              <Input placeholder="amount" />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} align="start">
            <Form.Item label="业务名称" name="business_name" rules={[{ required: true }]}>
              <Input placeholder="订单金额" />
            </Form.Item>
            <Form.Item label="数据类型" name="data_type" rules={[{ required: true }]}>
              <Input placeholder="decimal" />
            </Form.Item>
          </Space>
          <Form.Item label="同义词" name="synonyms">
            <Input placeholder="销售额,GMV" />
          </Form.Item>
          <Form.Item label="业务描述" name="business_description">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setSemanticModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加知识"
        open={agentKnowledgeModalVisible}
        onCancel={() => setAgentKnowledgeModalVisible(false)}
        footer={null}
        width={680}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddAgentKnowledge}
          initialValues={{ type: 'QA', is_recall: 1, splitter_type: 'token' }}
        >
          <Form.Item label="标题" name="title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="类型" name="type" rules={[{ required: true }]}>
            <Select>
              <Option value="QA">问答</Option>
              <Option value="FAQ">FAQ</Option>
              <Option value="DOCUMENT">文档</Option>
            </Select>
          </Form.Item>
          <Form.Item label="问题" name="question">
            <Input />
          </Form.Item>
          <Form.Item label="内容" name="content">
            <TextArea rows={4} />
          </Form.Item>
          <Form.Item
            label="文档文件"
            name="file"
            valuePropName="fileList"
            getValueFromEvent={(event) => event?.fileList || []}
          >
            <Upload beforeUpload={() => false} maxCount={1}>
              <Button>选择文件</Button>
            </Upload>
          </Form.Item>
          <Form.Item label="是否召回" name="is_recall">
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
              <Button onClick={() => setAgentKnowledgeModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加预设问题"
        open={presetModalVisible}
        onCancel={() => setPresetModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAddPresetQuestion}>
          <Form.Item label="问题" name="question" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="排序" name="sort_order" initialValue={0}>
            <Input type="number" />
          </Form.Item>
          <Form.Item label="是否启用" name="is_active" initialValue={1}>
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
              <Button onClick={() => setPresetModalVisible(false)}>取消</Button>
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
