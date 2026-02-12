import { Card, Button, Input, Select, Space, message, Tabs, Form, Row, Col, Statistic, Tag } from 'antd'
import { RobotOutlined, ThunderboltOutlined, TagsOutlined, EditOutlined, SendOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'

const { TextArea } = Input
const { Option } = Select

function AI() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('generate')
  const [status, setStatus] = useState({})
  const [form] = Form.useForm()

  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await api.get('/ai/status')
      setStatus(response.data.data || {})
    } catch (error) {
    }
  }

  const handleGenerate = async (values) => {
    setLoading(true)
    try {
      const response = await api.post('/ai/generate/xiaohongshu', {
        topic: values.topic,
        style: values.style
      })
      setResult({ type: 'generate', data: response.data.data })
      message.success('内容生成成功')
    } catch (error) {
      message.error('生成失败')
    } finally {
      setLoading(false)
    }
  }

  const handleOptimizeTitle = async (values) => {
    setLoading(true)
    try {
      const response = await api.post('/ai/optimize/title', {
        title: values.title,
        platform: values.platform
      })
      setResult({ type: 'title', data: response.data.data })
      message.success('标题优化成功')
    } catch (error) {
      message.error('优化失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestTags = async (values) => {
    setLoading(true)
    try {
      const response = await api.post('/ai/suggest/tags', {
        content: values.content,
        platform: values.platform
      })
      setResult({ type: 'tags', data: response.data.data })
      message.success('标签推荐成功')
    } catch (error) {
      message.error('推荐失败')
    } finally {
      setLoading(false)
    }
  }

  const handleImprove = async (values) => {
    setLoading(true)
    try {
      const response = await api.post('/ai/improve/content', {
        content: values.content,
        improvements: values.improvements
      })
      setResult({ type: 'improve', data: response.data.data })
      message.success('内容优化成功')
    } catch (error) {
      message.error('优化失败')
    } finally {
      setLoading(false)
    }
  }

  const renderResult = () => {
    if (!result) return null

    const { type, data } = result

    switch (type) {
      case 'generate':
        return (
          <Card title="生成结果" style={{ marginTop: 16 }}>
            <p><strong>标题：</strong>{data.title}</p>
            <p><strong>内容：</strong></p>
            <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
              {data.content}
            </div>
            <p style={{ marginTop: 16 }}><strong>推荐标签：</strong></p>
            <Space wrap>
              {data.tags?.map((tag, i) => <Tag key={i} color="blue">{tag}</Tag>)}
            </Space>
          </Card>
        )

      case 'title':
        return (
          <Card title="优化标题" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {data.titles?.map((title, i) => (
                <div key={i} style={{ padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                  {title}
                </div>
              ))}
            </Space>
            {data.analysis && <p style={{ marginTop: 16 }}><strong>分析：</strong>{data.analysis}</p>}
          </Card>
        )

      case 'tags':
        return (
          <Card title="推荐标签" style={{ marginTop: 16 }}>
            <Space wrap>
              {data.tags?.map((tag, i) => (
                <Tag key={i} color="blue">{tag.tag} ({(tag.relevance * 100)?.toFixed(0)}%)</Tag>
              ))}
            </Space>
          </Card>
        )

      case 'improve':
        return (
          <Card title="优化结果" style={{ marginTop: 16 }}>
            <p><strong>原文：</strong></p>
            <div style={{ background: '#fffbe6', padding: 12, borderRadius: 4, marginBottom: 16 }}>
              {data.original}
            </div>
            <p><strong>优化后：</strong></p>
            <div style={{ background: '#f6ffed', padding: 12, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
              {data.improved}
            </div>
          </Card>
        )

      default:
        return null
    }
  }

  const tabItems = [
    {
      key: 'generate',
      label: '内容生成',
      icon: <RobotOutlined />,
      children: (
        <Form form={form} onFinish={handleGenerate} layout="vertical">
          <Form.Item name="topic" label="主题" rules={[{ required: true }]}>
            <Input placeholder="输入内容主题" />
          </Form.Item>
          <Form.Item name="style" label="风格">
            <Select placeholder="选择风格" defaultValue="干货分享">
              <Option value="干货分享">干货分享</Option>
              <Option value="生活记录">生活记录</Option>
              <Option value="种草推荐">种草推荐</Option>
              <Option value="教程攻略">教程攻略</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<SendOutlined />}>
              生成内容
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      key: 'title',
      label: '标题优化',
      icon: <ThunderboltOutlined />,
      children: (
        <Form form={form} onFinish={handleOptimizeTitle} layout="vertical">
          <Form.Item name="title" label="原标题" rules={[{ required: true }]}>
            <Input placeholder="输入需要优化的标题" />
          </Form.Item>
          <Form.Item name="platform" label="平台">
            <Select placeholder="选择平台" defaultValue="xiaohongshu">
              <Option value="xiaohongshu">小红书</Option>
              <Option value="bilibili">B站</Option>
              <Option value="weibo">微博</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<ThunderboltOutlined />}>
              优化标题
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      key: 'tags',
      label: '标签推荐',
      icon: <TagsOutlined />,
      children: (
        <Form form={form} onFinish={handleSuggestTags} layout="vertical">
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <TextArea rows={4} placeholder="输入内容文本" />
          </Form.Item>
          <Form.Item name="platform" label="平台">
            <Select placeholder="选择平台" defaultValue="xiaohongshu">
              <Option value="xiaohongshu">小红书</Option>
              <Option value="bilibili">B站</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<TagsOutlined />}>
              推荐标签
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      key: 'improve',
      label: '内容润色',
      icon: <EditOutlined />,
      children: (
        <Form form={form} onFinish={handleImprove} layout="vertical">
          <Form.Item name="content" label="原文内容" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="输入需要润色的内容" />
          </Form.Item>
          <Form.Item name="improvements" label="优化方向">
            <Select mode="multiple" placeholder="选择优化方向">
              <Option value="readability">提高可读性</Option>
              <Option value="engagement">增加互动引导</Option>
              <Option value="emoji">添加emoji</Option>
              <Option value="structure">优化结构</Option>
              <Option value="tone">调整语气</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<EditOutlined />}>
              润色内容
            </Button>
          </Form.Item>
        </Form>
      )
    }
  ]

  return (
    <div>
      <div className="page-header">
        <h2>AI助手</h2>
        <p>使用AI生成和优化内容</p>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>AI服务状态：</span>
          <Tag color={status.openaiConfigured ? 'green' : 'orange'}>
            {status.openaiConfigured ? 'OpenAI已配置' : 'Fallback模式'}
          </Tag>
          <span>模型：{status.model || 'gpt-4'}</span>
        </Space>
      </Card>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      {renderResult()}
    </div>
  )
}

export default AI
