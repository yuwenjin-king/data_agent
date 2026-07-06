import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout,
  List,
  Input,
  Button,
  Card,
  Space,
  Avatar,
  Spin,
  Empty,
  Tag,
  Divider,
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ArrowLeftOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { chatService, agentService } from '../services'
import { useAppStore } from '../store/appStore'

const { Sider, Content } = Layout
const { TextArea } = Input

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

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      const res = await chatService.sendMessage({
        agent_id: parseInt(agentId),
        session_id: currentSession.id,
        message: inputMessage,
        stream: false,
      })

      const assistantMessage = {
        id: Date.now() + 1,
        session_id: currentSession.id,
        role: 'assistant',
        content: res.data.data?.content || '收到您的消息，正在处理中...',
        message_type: 'text',
        create_time: new Date().toISOString(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        session_id: currentSession.id,
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        message_type: 'error',
        create_time: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
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
    code({ node, inline, className, children, ...props }) {
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
              <div style={{ width: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
            <Empty
              description="开始一段对话吧"
              style={{ marginTop: 100 }}
            />
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
