import { Card, Button, Input, Select, Space, message, Row, Col, Statistic, Table, Tag } from 'antd'
import { LineChartOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import api from '../utils/api'

const { TextArea } = Input
const { Option } = Select

function Analysis() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [contentType, setContentType] = useState('sentiment')
  const [inputText, setInputText] = useState('')

  const handleAnalyze = async () => {
    if (!inputText.trim()) {
      message.warning('请输入要分析的内容')
      return
    }

    setLoading(true)
    try {
      const endpoints = {
        sentiment: '/analysis/sentiment',
        keywords: '/analysis/keywords',
        topics: '/analysis/topics',
        viral: '/analysis/viral'
      }

      const response = await api.post(endpoints[contentType], { content: inputText })
      setResult({
        type: contentType,
        data: response.data.data
      })
      message.success('分析完成')
    } catch (error) {
      message.error('分析失败')
    } finally {
      setLoading(false)
    }
  }

  const renderResult = () => {
    if (!result) return null

    const { type, data } = result

    switch (type) {
      case 'sentiment':
        return (
          <Card title="情感分析结果" style={{ marginTop: 16 }}>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic title="情感倾向" value={data.sentiment === 'positive' ? '正面' : data.sentiment === 'negative' ? '负面' : '中性'} />
              </Col>
              <Col span={8}>
                <Statistic title="情感分数" value={data.score?.toFixed(2)} />
              </Col>
              <Col span={8}>
                <Statistic title="置信度" value={(data.confidence * 100)?.toFixed(0)} suffix="%" />
              </Col>
            </Row>
          </Card>
        )

      case 'keywords':
        return (
          <Card title="关键词提取结果" style={{ marginTop: 16 }}>
            <Space wrap>
              {data.keywords?.map((kw, i) => (
                <Tag key={i} color="blue">{kw.word} ({kw.count})</Tag>
              ))}
            </Space>
          </Card>
        )

      case 'topics':
        return (
          <Card title="话题识别结果" style={{ marginTop: 16 }}>
            <Space wrap>
              {data.topics?.map((t, i) => (
                <Tag key={i} color="green">{t.topic} (相关度: {(t.score * 100)?.toFixed(0)}%)</Tag>
              ))}
            </Space>
          </Card>
        )

      case 'viral':
        return (
          <Card title="爆款预测结果" style={{ marginTop: 16 }}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic title="爆款潜力" value={(data.viralScore * 100)?.toFixed(0)} suffix="%" />
              </Col>
              <Col span={6}>
                <Statistic title="预期浏览" value={data.prediction?.expectedViews} />
              </Col>
              <Col span={6}>
                <Statistic title="预期点赞" value={data.prediction?.expectedLikes} />
              </Col>
              <Col span={6}>
                <Statistic title="预测置信度" value={(data.prediction?.confidence * 100)?.toFixed(0)} suffix="%" />
              </Col>
            </Row>
            {data.suggestions?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <strong>优化建议：</strong>
                <ul>
                  {data.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </Card>
        )

      default:
        return null
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>内容分析</h2>
        <p>分析内容情感、关键词、话题和爆款潜力</p>
      </div>

      <Card title="分析工具">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Select value={contentType} onChange={setContentType} style={{ width: 200 }}>
            <Option value="sentiment">情感分析</Option>
            <Option value="keywords">关键词提取</Option>
            <Option value="topics">话题识别</Option>
            <Option value="viral">爆款预测</Option>
          </Select>

          <TextArea
            rows={6}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="输入要分析的内容文本..."
          />

          <Button
            type="primary"
            icon={<LineChartOutlined />}
            loading={loading}
            onClick={handleAnalyze}
          >
            开始分析
          </Button>
        </Space>
      </Card>

      {renderResult()}
    </div>
  )
}

export default Analysis
