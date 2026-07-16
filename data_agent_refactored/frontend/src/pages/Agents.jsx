import { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, MessageOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { agentService } from '../services'

const { Option } = Select
const { TextArea } = Input

function Agents() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingAgent, setEditingAgent] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const res = await agentService.getAll()
      setAgents(res.data.data || [])
    } catch (error) {
      message.error('获取智能体列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingAgent(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await agentService.delete(id)
      message.success('删除成功')
      fetchAgents()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values) => {
    try {
      if (editingAgent) {
        await agentService.update(editingAgent.id, values)
        message.success('更新成功')
      } else {
        await agentService.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchAgents()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      draft: 'default',
      published: 'green',
      offline: 'red',
    }
    return colors[status] || 'default'
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<MessageOutlined />}
            onClick={() => navigate(`/chat/${record.id}`)}
          >
            聊天
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/agents/${record.id}`)}
          >
            配置
          </Button>
          <Popconfirm
            title="确定要删除这个智能体吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>智能体管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          创建智能体
        </Button>
      </div>
      <Card>
        <Table columns={columns} dataSource={agents} rowKey="id" loading={loading} />
      </Card>

      <Modal
        title={editingAgent ? '编辑智能体' : '创建智能体'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="请输入智能体名称" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={4} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item label="状态" name="status" initialValue="draft">
            <Select>
              <Option value="draft">草稿</Option>
              <Option value="published">已发布</Option>
              <Option value="offline">已下线</Option>
            </Select>
          </Form.Item>
          <Form.Item label="分类" name="category">
            <Input placeholder="请输入分类" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确定
              </Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Agents
