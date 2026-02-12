import { Card, Button, Input, Select, Table, Tag, Space, message, Modal, Form, Tabs, Progress, Statistic, Row, Col } from 'antd'
import { PlayCircleOutlined, StopOutlined, ReloadOutlined, ApiOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

function Crawler() {
  const [platforms, setPlatforms] = useState([])
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [crawlLoading, setCrawlLoading] = useState(false)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('url')
  const [stats, setStats] = useState({})

  useEffect(() => {
    fetchPlatforms()
    fetchJobs()
    fetchStats()
  }, [])

  const fetchPlatforms = async () => {
    try {
      const response = await api.get('/crawler/platforms')
      setPlatforms(response.data.data || [])
    } catch (error) {
      console.error('Failed to fetch platforms:', error)
    }
  }

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const response = await api.get('/crawler/jobs')
      setJobs(response.data.data.data || [])
    } catch (error) {
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/crawler/stats')
      setStats(response.data.data || {})
    } catch (error) {
    }
  }

  const handleCrawlByUrl = async (values) => {
    setCrawlLoading(true)
    try {
      const response = await api.post('/crawler/url', { url: values.url })
      if (response.data.success) {
        message.success('爬取成功')
        fetchJobs()
        fetchStats()
      } else {
        message.error(response.data.error || '爬取失败')
      }
    } catch (error) {
      message.error(error.response?.data?.error || '爬取失败')
    } finally {
      setCrawlLoading(false)
    }
  }

  const handleCrawlByPlatform = async (values) => {
    setCrawlLoading(true)
    try {
      const response = await api.post('/crawler/start', values)
      if (response.data.success) {
        message.success('爬取任务已启动')
        fetchJobs()
        fetchStats()
      } else {
        message.error(response.data.error || '启动失败')
      }
    } catch (error) {
      message.error(error.response?.data?.error || '启动失败')
    } finally {
      setCrawlLoading(false)
    }
  }

  const handleCancelJob = async (jobId) => {
    try {
      await api.put(`/crawler/jobs/${jobId}/cancel`)
      message.success('任务已取消')
      fetchJobs()
    } catch (error) {
      message.error('取消失败')
    }
  }

  const jobColumns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 180,
      ellipsis: true
    },
    {
      title: '平台',
      dataIndex: 'platform_id',
      key: 'platform_id',
      width: 100,
      render: (id) => {
        const platforms = { 1: { name: '小红书', color: 'red' }, 2: { name: 'B站', color: 'blue' }, 5: { name: '抖音', color: 'green' } }
        const p = platforms[id] || { name: '未知', color: 'default' }
        return <Tag color={p.color}>{p.name}</Tag>
      }
    },
    {
      title: '类型',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 100
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colors = { pending: 'default', running: 'processing', completed: 'success', failed: 'error', cancelled: 'warning' }
        const labels = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败', cancelled: '已取消' }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
      }
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress, record) => (
        <Progress percent={progress || 0} size="small" status={record.status === 'failed' ? 'exception' : 'active'} />
      )
    },
    {
      title: '爬取数量',
      dataIndex: 'total_crawled',
      key: 'total_crawled',
      width: 100,
      render: (v) => v || 0
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        record.status === 'running' || record.status === 'pending' ? (
          <Button type="link" size="small" danger onClick={() => handleCancelJob(record.id)}>
            取消
          </Button>
        ) : null
      )
    }
  ]

  const tabItems = [
    {
      key: 'url',
      label: 'URL爬取',
      children: (
        <Form form={form} onFinish={handleCrawlByUrl} layout="vertical">
          <Form.Item
            name="url"
            label="内容URL"
            rules={[{ required: true, message: '请输入URL' }]}
          >
            <TextArea
              rows={3}
              placeholder="输入B站、抖音、小红书内容URL，支持短链接"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={crawlLoading} icon={<PlayCircleOutlined />}>
              开始爬取
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      key: 'platform',
      label: '平台爬取',
      children: (
        <Form form={form} onFinish={handleCrawlByPlatform} layout="vertical">
          <Form.Item name="platform" label="平台" rules={[{ required: true }]}>
            <Select placeholder="选择平台">
              {platforms.filter(p => p.enabled).map(p => (
                <Option key={p.code} value={p.code}>{p.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select placeholder="选择类型">
              <Option value="video">视频</Option>
              <Option value="user">用户</Option>
              <Option value="search">搜索</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target" label="目标ID">
            <Input placeholder="视频ID、用户ID等" />
          </Form.Item>
          <Form.Item name="keyword" label="关键词">
            <Input placeholder="搜索关键词" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={crawlLoading} icon={<PlayCircleOutlined />}>
              开始爬取
            </Button>
          </Form.Item>
        </Form>
      )
    }
  ]

  return (
    <div>
      <div className="page-header">
        <h2>爬虫任务</h2>
        <p>启动和管理爬虫任务</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="总任务数" value={stats.total || 0} prefix={<ApiOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="已完成" value={stats.completed || 0} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="失败" value={stats.failed || 0} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      <Card title="新建任务" style={{ marginTop: 16 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      <Card 
        title="任务列表" 
        style={{ marginTop: 16 }}
        extra={<Button icon={<ReloadOutlined />} onClick={fetchJobs}>刷新</Button>}
      >
        <Table
          columns={jobColumns}
          dataSource={jobs}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default Crawler
