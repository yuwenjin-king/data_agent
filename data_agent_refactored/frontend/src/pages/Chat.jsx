import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout, List, Input, Button, Card, Space, Avatar, Spin, Empty, Divider, Tag } from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ArrowLeftOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import 'highlight.js/styles/github.css'
import { chatService, agentService } from '../services'

const { Sider, Content } = Layout
const { TextArea } = Input

const formatJson = (value) => {
  if (value === undefined || value === null) return ''
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}

const normalizeWorkflowEvents = (metadata = {}) => {
  const events = Array.isArray(metadata.workflow_events) ? [...metadata.workflow_events] : []
  const sqlValues = metadata.sql_query
    ? Array.isArray(metadata.sql_query)
      ? metadata.sql_query
      : [metadata.sql_query]
    : []
  const resultValues = metadata.execution_result
    ? Array.isArray(metadata.execution_result)
      ? metadata.execution_result
      : [metadata.execution_result]
    : []

  if (metadata.plan && !events.some((item) => item.type === 'plan')) {
    events.unshift({ type: 'plan', payload: metadata.plan })
  }
  sqlValues.forEach((sql) => {
    if (!events.some((item) => item.type === 'sql' && item.payload === sql)) {
      events.push({ type: 'sql', payload: sql })
    }
  })
  resultValues.forEach((result) => {
    if (!events.some((item) => item.type === 'sql_result' && item.payload === result)) {
      events.push({ type: 'sql_result', payload: result })
    }
  })
  if (metadata.error && !events.some((item) => item.type === 'error')) {
    events.push({ type: 'error', payload: metadata.error })
  }
  return events
}

const workflowEventTitle = {
  plan: '执行计划',
  sql: 'SQL',
  sql_result: '执行结果',
  error: '错误',
}

function WorkflowEvents({ metadata }) {
  const events = normalizeWorkflowEvents(metadata)
  if (!events.length) return null

  return (
    <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 12 }}>
      {events.map((item, index) => (
        <div
          key={`${item.type}-${index}`}
          style={{
            border: '1px solid #e5e7eb',
            borderRadius: 6,
            padding: 10,
            background: item.type === 'error' ? '#fff2f0' : '#fafafa',
          }}
        >
          <Tag color={item.type === 'error' ? 'red' : item.type === 'sql' ? 'blue' : 'default'}>
            {workflowEventTitle[item.type] || item.type}
          </Tag>
          <pre
            style={{
              margin: '8px 0 0',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: 12,
            }}
          >
            {formatJson(item.payload)}
          </pre>
        </div>
      ))}
    </Space>
  )
}

function Chat() {
  const { agentId } = useParams()
  const navigate = useNavigate()
  const [agent, setAgent] = useState(null)
  const [sessions, setSessions] = useState([])
  const [currentSession, setCurrentSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (agentId) {
      fetchAgent()
      fetchSessions()
    }
    // Fetch on agent (route param) change only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchAgent = async () => {
    try {
      const res = await agentService.getById(agentId)
      setAgent(res.data.data)
    } catch (error) {
      console.error('Failed to fetch agent:', error)
    }
  }

  const fetchSessions = async () => {
    try {
      setSessionsLoading(true)
      const res = await chatService.getSessions(agentId)
      const sessionList = res.data.data || []
      setSessions(sessionList)
      if (sessionList.length > 0 && !currentSession) {
        selectSession(sessionList[0])
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    } finally {
      setSessionsLoading(false)
    }
  }

  const selectSession = async (session) => {
    try {
      setCurrentSession(session)
      const res = await chatService.getMessages(session.id)
      setMessages(res.data.data || [])
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const createNewSession = async () => {
    try {
      const res = await chatService.createSession({
        agent_id: parseInt(agentId),
        title: '新对话',
      })
      const newSession = res.data.data
      setSessions([newSession, ...sessions])
      setCurrentSession(newSession)
      setMessages([])
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const updateAssistantMessage = (updater) => {
    setMessages((prev) =>
      prev.map((msg, idx) =>
        idx === prev.length - 1 && msg.role === 'assistant' ? updater(msg) : msg,
      ),
    )
  }

  const appendWorkflowEvent = (type, payload) => {
    updateAssistantMessage((msg) => {
      const metadata = msg.metadata || {}
      const workflowEvents = Array.isArray(metadata.workflow_events)
        ? metadata.workflow_events
        : []
      return {
        ...msg,
        metadata: {
          ...metadata,
          workflow_events: [...workflowEvents, { type, payload }],
        },
      }
    })
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !currentSession) return

    const userMessage = {
      id: Date.now(),
      session_id: currentSession.id,
      role: 'user',
      content: inputMessage,
      message_type: 'text',
      create_time: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    const assistantMessage = {
      id: Date.now() + 1,
      session_id: currentSession.id,
      role: 'assistant',
      content: '',
      message_type: 'text',
      create_time: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      let sessionId = currentSession.id
      await chatService.streamMessage(
        {
          agent_id: parseInt(agentId),
          session_id: sessionId,
          message: inputMessage,
        },
        (event) => {
          if (event.event === 'session' && event.data.session_id) {
            sessionId = event.data.session_id
            if (sessionId !== currentSession.id) {
              setCurrentSession((prev) => ({ ...prev, id: sessionId }))
            }
          }
          if (event.event === 'message' && typeof event.data.text === 'string') {
            updateAssistantMessage((msg) => ({ ...msg, content: event.data.text }))
          }
          if (event.event === 'plan' && event.data.plan) {
            appendWorkflowEvent('plan', event.data.plan)
          }
          if (event.event === 'sql' && event.data.sql) {
            appendWorkflowEvent('sql', event.data.sql)
          }
          if (event.event === 'sql_result' && event.data.result) {
            appendWorkflowEvent('sql_result', event.data.result)
          }
          if (event.event === 'error') {
            appendWorkflowEvent('error', event.data.message || event.data)
          }
        },
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      updateAssistantMessage((msg) => ({ ...msg, content: '抱歉，发生了错误，请稍后重试。' }))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const components = {
    code({ inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      return !inline && match ? (
        <pre className={className} {...props}>
          <code className={className}>{children}</code>
        </pre>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      )
    },
  }

  return (
    <Layout style={{ height: '100%' }}>
      <Sider width={280} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/agents')} block>
              返回智能体列表
            </Button>
            <Divider style={{ margin: '8px 0' }} />
            <Button type="primary" icon={<PlusOutlined />} onClick={createNewSession} block>
              新建对话
            </Button>
          </Space>
        </div>
        <div style={{ padding: '0 16px' }}>
          <h4>对话历史</h4>
        </div>
        <List
          loading={sessionsLoading}
          dataSource={sessions}
          renderItem={(session) => (
            <List.Item
              style={{
                cursor: 'pointer',
                background: currentSession?.id === session.id ? '#e6f7ff' : 'transparent',
                padding: '8px 16px',
              }}
              onClick={() => selectSession(session)}
            >
              <div
                style={{
                  width: '100%',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {session.title}
              </div>
            </List.Item>
          )}
        />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Space>
            <Avatar icon={<RobotOutlined />} />
            <div>
              <h3 style={{ margin: 0 }}>{agent?.name}</h3>
              <span style={{ color: '#999', fontSize: 12 }}>{agent?.description}</span>
            </div>
          </Space>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {messages.length === 0 ? (
            <Empty description="开始一段对话吧" style={{ marginTop: 100 }} />
          ) : (
            <div style={{ maxWidth: 900, margin: '0 auto' }}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    marginBottom: 24,
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  {msg.role === 'assistant' && (
                    <Avatar icon={<RobotOutlined />} style={{ marginRight: 12 }} />
                  )}
                  <Card
                    size="small"
                    style={{
                      maxWidth: '70%',
                      background: msg.role === 'user' ? '#e6f7ff' : '#fff',
                    }}
                  >
                    <ReactMarkdown components={components}>{msg.content}</ReactMarkdown>
                    {msg.role === 'assistant' && <WorkflowEvents metadata={msg.metadata} />}
                    <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                      {new Date(msg.create_time).toLocaleTimeString()}
                    </div>
                  </Card>
                  {msg.role === 'user' && (
                    <Avatar icon={<UserOutlined />} style={{ marginLeft: 12 }} />
                  )}
                </div>
              ))}
              {loading && (
                <div style={{ display: 'flex', marginBottom: 24 }}>
                  <Avatar icon={<RobotOutlined />} style={{ marginRight: 12 }} />
                  <Spin />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
          <Space.Compact style={{ width: '100%', maxWidth: 900, margin: '0 auto' }}>
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题..."
              autoSize={{ minRows: 1, maxRows: 6 }}
              style={{ flex: 1 }}
              disabled={!currentSession}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!currentSession || !inputMessage.trim()}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Content>
    </Layout>
  )
}

export default Chat
