import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Spin, Alert } from 'antd'
import {
  RobotOutlined,
  DatabaseOutlined,
  MessageOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { agentService, datasourceService, chatService } from '../services'

function Dashboard() {
  const [stats, setStats] = useState({ agents: 0, datasources: 0, sessions: 0, messages: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const [agentsRes, datasourcesRes] = await Promise.all([
        agentService.getAll(),
        datasourceService.getAll(),
      ])
      setStats({
        agents: agentsRes.data.data?.length || 0,
        datasources: datasourcesRes.data.data?.length || 0,
        sessions: 0,
        messages: 0,
      })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }} />
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>仪表盘</h1>
      <Alert
        message="欢迎使用 Data Agent"
        description="这是一个企业级智能数据分析师平台，支持自然语言转SQL、Python深度分析、智能报告生成等功能。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="智能体数量"
              value={stats.agents}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据源数量"
              value={stats.datasources}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="会话数量"
              value={stats.sessions}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="消息数量"
              value={stats.messages}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
