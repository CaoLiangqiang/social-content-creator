import { Card, Button, Input, Select, Space, message, Row, Col, Statistic, Table, Tag, Modal, Form, DatePicker, Tabs } from 'antd'
import { CloudUploadOutlined, ScheduleOutlined, BarChartOutlined, ReloadOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select
const { RangePicker } = DatePicker

function Publish() {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState([])
  const [platforms, setPlatforms] = useState([])
  const [stats, setStats] = useState({})
  const [scheduleModal, setScheduleModal] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchTasks()
    fetchPlatforms()
    fetchStats()
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await api.get('/publish/tasks')
      setTasks(response.data.data.data || [])
    } catch (error) {
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchPlatforms = async () => {
    try {
      const response = await api.get('/publish/platforms')
      setPlatforms(response.data.data || [])
    } catch (error) {
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/publish/analytics/overview')
      setStats(response.data.data || {})
    } catch (error) {
    }
  }

  const handleSchedule = async (values) => {
    try {
      await api.post('/publish/schedule', {
        ...values,
        scheduledTime: values.scheduledTime.toISOString()
      })
      message.success('发布任务已创建')
      setScheduleModal(false)
      form.resetFields()
      fetchTasks()
    } catch (error) {
      message.error(error.response?.data?.error || '创建失败')
    }
  }

  const handleCancel = async (taskId) => {
    try {
      await api.put(`/publish/tasks/${taskId}/cancel`)
      message.success('任务已取消')
      fetchTasks()
    } catch (error) {
      message.error('取消失败')
    }
  }

  const handleRetry = async (taskId) => {
    try {
      await api.post(`/publish/tasks/${taskId}/retry`)
      message.success('任务已重新调度')
      fetchTasks()
    } catch (error) {
      message.error('重试失败')
    }
  }

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 180,
      ellipsis: true
    },
    {
      title: '内容',
      dataIndex: 'content_title',
      key: 'content_title',
      ellipsis: true,
      width: 200
    },
    {
      title: '平台',
      dataIndex: 'platform_name',
      key: 'platform_name',
      width: 100,
      render: (name) => <Tag color="blue">{name}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colors = { scheduled: 'default', processing: 'processing', completed: 'success', failed: 'error', cancelled: 'warning' }
        const labels = { scheduled: '已调度', processing: '发布中', completed: '已完成', failed: '失败', cancelled: '已取消' }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
      }
    },
    {
      title: '计划时间',
      dataIndex: 'scheduled_time',
      key: 'scheduled_time',
      width: 150,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.status === 'scheduled' && (
            <Button type="link" size="small" danger onClick={() => handleCancel(record.id)}>
              取消
            </Button>
          )}
          {record.status === 'failed' && (
            <Button type="link" size="small" onClick={() => handleRetry(record.id)}>
              重试
            </Button>
          )}
        </Space>
      )
    }
  ]

  return (
    <div>
      <div className="page-header">
        <h2>发布管理</h2>
        <p>管理和调度内容发布任务</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title="总发布数" value={stats.total_published || 0} prefix={<CloudUploadOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title="总浏览量" value={stats.total_views || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title="总点赞数" value={stats.total_likes || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title="平均互动率" value={stats.avg_engagement_rate || 0} suffix="%" />
          </Card>
        </Col>
      </Row>

      <Card 
        title="发布任务" 
        style={{ marginTop: 16 }}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchTasks}>刷新</Button>
            <Button type="primary" icon={<ScheduleOutlined />} onClick={() => setScheduleModal(true)}>
              新建任务
            </Button>
          </Space>
        }
      >
        <Table
          columns={taskColumns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="新建发布任务"
        open={scheduleModal}
        onCancel={() => setScheduleModal(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleSchedule} layout="vertical">
          <Form.Item name="contentId" label="内容ID" rules={[{ required: true }]}>
            <Input placeholder="输入内容ID" />
          </Form.Item>
          <Form.Item name="platformId" label="发布平台" rules={[{ required: true }]}>
            <Select placeholder="选择平台">
              {platforms.filter(p => p.enabled).map(p => (
                <Option key={p.id} value={p.id}>{p.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="scheduledTime" label="计划发布时间" rules={[{ required: true }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              创建任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Publish
