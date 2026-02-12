import { Row, Col, Card, Statistic, Table, Tag, Space, Button, Progress } from 'antd'
import {
  FileTextOutlined,
  ApiOutlined,
  BarChartOutlined,
  CloudUploadOutlined,
  RiseOutlined,
  EyeOutlined,
  LikeOutlined,
  CommentOutlined
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'

function Dashboard() {
  const [stats, setStats] = useState({
    totalContents: 0,
    totalCrawlerJobs: 0,
    totalPublishTasks: 0,
    totalViews: 0,
    totalLikes: 0,
    totalComments: 0
  })
  const [recentContents, setRecentContents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [contentsRes, crawlerRes] = await Promise.all([
        api.get('/contents', { params: { limit: 5 } }),
        api.get('/crawler/stats')
      ])

      const contents = contentsRes.data.data.data || []
      setRecentContents(contents)

      const totalViews = contents.reduce((sum, c) => sum + (c.view_count || 0), 0)
      const totalLikes = contents.reduce((sum, c) => sum + (c.like_count || 0), 0)
      const totalComments = contents.reduce((sum, c) => sum + (c.comment_count || 0), 0)

      setStats({
        totalContents: contentsRes.data.data.pagination?.total || contents.length,
        totalCrawlerJobs: crawlerRes.data.data?.total || 0,
        totalPublishTasks: 0,
        totalViews,
        totalLikes,
        totalComments
      })
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  const contentColumns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: 200
    },
    {
      title: '平台',
      dataIndex: 'platform_id',
      key: 'platform_id',
      render: (id) => {
        const platforms = { 1: '小红书', 2: 'B站', 5: '抖音' }
        return <Tag color="blue">{platforms[id] || '未知'}</Tag>
      }
    },
    {
      title: '浏览',
      dataIndex: 'view_count',
      key: 'view_count',
      render: (v) => v?.toLocaleString() || 0
    },
    {
      title: '点赞',
      dataIndex: 'like_count',
      key: 'like_count',
      render: (v) => v?.toLocaleString() || 0
    },
    {
      title: '评论',
      dataIndex: 'comment_count',
      key: 'comment_count',
      render: (v) => v?.toLocaleString() || 0
    }
  ]

  return (
    <div>
      <div className="page-header">
        <h2>仪表板</h2>
        <p>欢迎来到社交内容创作平台</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="内容总数"
              value={stats.totalContents}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="爬虫任务"
              value={stats.totalCrawlerJobs}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="总浏览量"
              value={stats.totalViews}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="总点赞数"
              value={stats.totalLikes}
              prefix={<LikeOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="最近内容" extra={<a href="/contents">查看全部</a>}>
            <Table
              columns={contentColumns}
              dataSource={recentContents}
              rowKey="id"
              loading={loading}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="快捷操作">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Button type="primary" icon={<ApiOutlined />} block href="/crawler">
                启动爬虫任务
              </Button>
              <Button icon={<FileTextOutlined />} block href="/contents">
                内容管理
              </Button>
              <Button icon={<BarChartOutlined />} block href="/analysis">
                内容分析
              </Button>
              <Button icon={<CloudUploadOutlined />} block href="/publish">
                发布管理
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
