import { Table, Card, Button, Input, Select, Tag, Space, Modal, message, Pagination } from 'antd'
import { SearchOutlined, EyeOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

function Contents() {
  const [contents, setContents] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 })
  const [filters, setFilters] = useState({ platformId: undefined, search: '' })
  const [selectedContent, setSelectedContent] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)

  useEffect(() => {
    fetchContents()
  }, [pagination.page, filters])

  const fetchContents = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.page,
        limit: pagination.limit,
        ...filters
      }
      const response = await api.get('/contents', { params })
      setContents(response.data.data.data || [])
      setPagination(prev => ({
        ...prev,
        total: response.data.data.pagination?.total || 0
      }))
    } catch (error) {
      message.error('获取内容列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, search: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handlePlatformChange = (value) => {
    setFilters(prev => ({ ...prev, platformId: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleViewDetail = (record) => {
    setSelectedContent(record)
    setDetailVisible(true)
  }

  const handleDelete = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条内容吗？',
      onOk: async () => {
        try {
          await api.delete(`/contents/${id}`)
          message.success('删除成功')
          fetchContents()
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: 250,
      render: (text) => text || '无标题'
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
      title: '作者',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 120,
      ellipsis: true
    },
    {
      title: '浏览',
      dataIndex: 'view_count',
      key: 'view_count',
      width: 80,
      render: (v) => v?.toLocaleString() || 0
    },
    {
      title: '点赞',
      dataIndex: 'like_count',
      key: 'like_count',
      width: 80,
      render: (v) => v?.toLocaleString() || 0
    },
    {
      title: '评论',
      dataIndex: 'comment_count',
      key: 'comment_count',
      width: 80,
      render: (v) => v?.toLocaleString() || 0
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      key: 'published_at',
      width: 120,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
            查看
          </Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div className="page-header">
        <h2>内容管理</h2>
        <p>管理已采集的内容数据</p>
      </div>

      <Card>
        <div className="action-bar">
          <Space>
            <Select
              style={{ width: 120 }}
              placeholder="选择平台"
              allowClear
              onChange={handlePlatformChange}
            >
              <Option value={1}>小红书</Option>
              <Option value={2}>B站</Option>
              <Option value={5}>抖音</Option>
            </Select>
            <Search
              placeholder="搜索标题或内容"
              allowClear
              style={{ width: 250 }}
              onSearch={handleSearch}
            />
          </Space>
          <Button icon={<ReloadOutlined />} onClick={fetchContents}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={contents}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.page,
            pageSize: pagination.limit,
            total: pagination.total,
            onChange: (page) => setPagination(prev => ({ ...prev, page }))
          }}
        />
      </Card>

      <Modal
        title="内容详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={700}
      >
        {selectedContent && (
          <div>
            <p><strong>标题：</strong>{selectedContent.title}</p>
            <p><strong>作者：</strong>{selectedContent.author_name}</p>
            <p><strong>内容：</strong></p>
            <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
              {selectedContent.content || '无内容'}
            </div>
            <p style={{ marginTop: 16 }}><strong>数据统计：</strong></p>
            <Space size="large">
              <span>浏览: {selectedContent.view_count?.toLocaleString() || 0}</span>
              <span>点赞: {selectedContent.like_count?.toLocaleString() || 0}</span>
              <span>评论: {selectedContent.comment_count?.toLocaleString() || 0}</span>
              <span>分享: {selectedContent.share_count?.toLocaleString() || 0}</span>
            </Space>
            {selectedContent.url && (
              <p style={{ marginTop: 16 }}>
                <strong>原文链接：</strong>
                <a href={selectedContent.url} target="_blank" rel="noopener noreferrer">
                  {selectedContent.url}
                </a>
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Contents
