import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  message,
  Spin,
  Empty,
  Typography,
  Select,
  Row,
  Col,
  Statistic,
  Divider,
} from 'antd';
import {
  BarChartOutlined,
  SyncOutlined,
  FireOutlined,
  PieChartOutlined,
  GlobalOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { analyzeNews, analyzeKeywords, analyzeSentiment, analyzeSocial, fetchNews } from '../services/api.js';
import { trackEvent } from '../utils/tracking.js';

const { Title, Paragraph, Text } = Typography;

function AIAnalysis() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisType, setAnalysisType] = useState('summary');
  const [newsList, setNewsList] = useState([]);
  const [keywordsLoading, setKeywordsLoading] = useState(false);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState(false);

  // 加载新闻数据
  const loadNews = async () => {
    try {
      const data = await fetchNews();
      setNewsList(Array.isArray(data) ? data.slice(0, 100) : []);
    } catch (error) {
      console.error('加载新闻失败:', error);
    }
  };

  useEffect(() => {
    loadNews();
  }, []);

  // 执行 AI 深度分析
  const handleAnalyze = async () => {
    if (newsList.length === 0) {
      message.warning('暂无数据可分析，请先刷新新闻');
      return;
    }

    setLoading(true);
    try {
      const result = await analyzeNews(newsList);
      setAnalysisResult(result);
      message.success('AI 分析完成');
      // 埋点：记录 AI 深度分析事件
      trackEvent('ai_analysis', {
        analysis_type: 'deep_summary',
        sample_size: newsList.length,
      });
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 关键词分析
  const handleKeywordsAnalysis = async () => {
    if (newsList.length === 0) {
      message.warning('暂无数据可分析');
      return;
    }

    setKeywordsLoading(true);
    try {
      const result = await analyzeKeywords(newsList);
      setAnalysisResult({
        ...result,
        analysis_type: 'keywords',
      });
      setAnalysisType('keywords');
      message.success('关键词分析完成');
      // 埋点：记录关键词分析事件
      trackEvent('ai_analysis', {
        analysis_type: 'keywords',
        sample_size: newsList.length,
      });
    } catch (error) {
      message.error('分析失败');
    } finally {
      setKeywordsLoading(false);
    }
  };

  // 情感分析
  const handleSentimentAnalysis = async () => {
    if (newsList.length === 0) {
      message.warning('暂无数据可分析');
      return;
    }

    setSentimentLoading(true);
    try {
      const result = await analyzeSentiment(newsList);
      setAnalysisResult({
        ...result,
        analysis_type: 'sentiment',
      });
      setAnalysisType('sentiment');
      message.success('情感分析完成');
      // 埋点：记录情感分析事件
      trackEvent('ai_analysis', {
        analysis_type: 'sentiment',
        sample_size: newsList.length,
      });
    } catch (error) {
      message.error('分析失败');
    } finally {
      setSentimentLoading(false);
    }
  };

  // 社交分析
  const handleSocialAnalysis = async () => {
    if (newsList.length === 0) {
      message.warning('暂无数据可分析');
      return;
    }

    setSocialLoading(true);
    try {
      const result = await analyzeSocial(newsList);
      setAnalysisResult({
        ...result,
        analysis_type: 'social',
      });
      setAnalysisType('social');
      message.success('社交分析完成');
      // 埋点：记录社交分析事件
      trackEvent('ai_analysis', {
        analysis_type: 'social',
        sample_size: newsList.length,
      });
    } catch (error) {
      message.error('分析失败');
    } finally {
      setSocialLoading(false);
    }
  };

  // 渲染 AI 深度分析报告
  const renderDeepAnalysis = () => {
    if (!analysisResult?.raw_data) return null;

    const data = analysisResult.raw_data;

    return (
      <div className="ai-analysis-report">
        {/* 核心摘要 */}
        {data.executive_summary && (
          <div className="analysis-section">
            <Title level={4}>📋 核心摘要</Title>
            <Paragraph className="executive-summary">
              {data.executive_summary}
            </Paragraph>
          </div>
        )}

        {/* 热点话题 */}
        {data.trending_topics && data.trending_topics.length > 0 && (
          <div className="analysis-section">
            <Title level={4}>🔥 热点话题</Title>
            <Row gutter={[16, 16]}>
              {data.trending_topics.map((topic, index) => (
                <Col span={8} key={index}>
                  <Card size="small" className="topic-item">
                    <div className="topic-header">
                      <Text strong>{topic.topic}</Text>
                      <Tag
                        className={`heat-badge heat-badge_${topic.heat_level}`}
                        color={
                          topic.heat_level === 'very_high'
                            ? 'red'
                            : topic.heat_level === 'high'
                            ? 'orange'
                            : 'blue'
                        }
                      >
                        {topic.heat_level}
                      </Tag>
                    </div>
                    <Paragraph className="topic-description" ellipsis={{ rows: 2 }}>
                      {topic.description}
                    </Paragraph>
                    <Text type="secondary" className="topic-count">
                      相关新闻：{topic.related_news_count}条
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* 行业洞察 */}
        {data.industry_insights && data.industry_insights.length > 0 && (
          <div className="analysis-section">
            <Title level={4}>📈 行业洞察</Title>
            <Row gutter={[16, 16]}>
              {data.industry_insights.map((insight, index) => (
                <Col span={8} key={index}>
                  <Card size="small" className="insight-item">
                    <div className="insight-header">
                      <Text strong>{insight.trend}</Text>
                      <Tag
                        color={
                          insight.impact_level === 'high'
                            ? 'red'
                            : insight.impact_level === 'medium'
                            ? 'orange'
                            : 'green'
                        }
                      >
                        {insight.impact_level}
                      </Tag>
                    </div>
                    <Text type="secondary" className="insight-sectors">
                      受影响领域：{insight.affected_sectors?.join('、')}
                    </Text>
                    <Paragraph className="insight-implication" ellipsis={{ rows: 2 }}>
                      {insight.strategic_implication}
                    </Paragraph>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* 机会信号 */}
        {data.opportunities && data.opportunities.length > 0 && (
          <div className="analysis-section">
            <Title level={4}>💡 机会信号</Title>
            <Row gutter={[16, 16]}>
              {data.opportunities.map((opp, index) => (
                <Col span={8} key={index}>
                  <Card size="small" className="opportunity-item">
                    <div className="opportunity-header">
                      <Tag color="green">{opp.type}</Tag>
                      <Tag>{opp.window}</Tag>
                    </div>
                    <Paragraph className="opportunity-description" ellipsis={{ rows: 2 }}>
                      {opp.description}
                    </Paragraph>
                    <Text type="success" strong>
                      建议行动：{opp.action}
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* 行动建议 */}
        {data.recommended_actions && data.recommended_actions.length > 0 && (
          <div className="analysis-section">
            <Title level={4}>✅ 行动建议</Title>
            <Row gutter={[16, 16]}>
              {data.recommended_actions.map((action, index) => (
                <Col span={8} key={index}>
                  <Card size="small" className="action-item">
                    <div className="action-header">
                      <Tag
                        color={
                          action.priority === 'high'
                            ? 'red'
                            : action.priority === 'medium'
                            ? 'orange'
                            : 'blue'
                        }
                      >
                        {action.priority}
                      </Tag>
                      <Text type="secondary">{action.owner}</Text>
                    </div>
                    <Paragraph className="action-text" ellipsis={{ rows: 2 }}>
                      {action.action}
                    </Paragraph>
                    <Text type="secondary" className="action-timeline">
                      完成时间：{action.timeline}
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}
      </div>
    );
  };

  // 渲染关键词分析
  const renderKeywords = () => {
    if (!analysisResult?.keywords) return null;

    return (
      <Card title="🔑 关键词分析" size="small">
        <Space wrap>
          {analysisResult.keywords.map((kw, index) => (
            <Tag key={index} color="blue" style={{ fontSize: 14, padding: '6px 12px' }}>
              {kw}
            </Tag>
          ))}
        </Space>
        {analysisResult.hot_topics && analysisResult.hot_topics.length > 0 && (
          <>
            <Divider />
            <Title level={5}>🔥 热门话题</Title>
            <Space wrap>
              {analysisResult.hot_topics.map((topic, index) => (
                <Tag key={index} color="red" style={{ fontSize: 14, padding: '6px 12px' }}>
                  {topic}
                </Tag>
              ))}
            </Space>
          </>
        )}
      </Card>
    );
  };

  // 渲染情感分析
  const renderSentiment = () => {
    if (!analysisResult?.sentiment_distribution) return null;

    const dist = analysisResult.sentiment_distribution;
    const total = dist.positive + dist.neutral + dist.negative;

    return (
      <Card title="😊 情感分析" size="small">
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="正面"
              value={dist.positive}
              suffix={`/ ${total}`}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="中性"
              value={dist.neutral}
              suffix={`/ ${total}`}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="负面"
              value={dist.negative}
              suffix={`/ ${total}`}
              valueStyle={{ color: '#f5222d' }}
            />
          </Col>
        </Row>
        <Divider />
        <Row gutter={16}>
          <Col span={8}>
            <Text>正面率：<strong style={{ color: '#52c41a' }}>{analysisResult.sentiment_rate?.positive || 0}%</strong></Text>
          </Col>
          <Col span={8}>
            <Text>中性率：<strong style={{ color: '#8c8c8c' }}>{analysisResult.sentiment_rate?.neutral || 0}%</strong></Text>
          </Col>
          <Col span={8}>
            <Text>负面率：<strong style={{ color: '#f5222d' }}>{analysisResult.sentiment_rate?.negative || 0}%</strong></Text>
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染社交分析
  const renderSocial = () => {
    if (!analysisResult?.metrics) return null;

    const metrics = analysisResult.metrics;

    return (
      <Card title="🌐 社交舆情分析" size="small">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="总互动量"
              value={metrics.total_engagement || 0}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="病毒话题"
              value={metrics.viral_count || 0}
              prefix={<TrophyOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="情感得分"
              value={typeof metrics.sentiment_score === 'string' ? parseFloat(metrics.sentiment_score) : metrics.sentiment_score || 0}
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="趋势热度"
              value={typeof metrics.trend_velocity === 'string' ? parseFloat(metrics.trend_velocity) : metrics.trend_velocity || 0}
              prefix={<TrendUpOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
        </Row>
        {analysisResult.trends && analysisResult.trends.length > 0 && (
          <>
            <Divider />
            <Title level={5}>🔥 趋势话题</Title>
            <Space wrap>
              {analysisResult.trends.map((trend, index) => (
                <Tag key={index} color="orange" style={{ fontSize: 14, padding: '6px 12px' }}>
                  {trend.topic}
                </Tag>
              ))}
            </Space>
          </>
        )}
      </Card>
    );
  };

  return (
    <div>
      {/* 操作栏 */}
      <Space style={{ marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<BarChartOutlined />}
          onClick={handleAnalyze}
          loading={loading}
          size="large"
        >
          AI 深度分析
        </Button>
        <Button
          icon={<FireOutlined />}
          onClick={handleKeywordsAnalysis}
          loading={keywordsLoading}
          size="large"
        >
          关键词分析
        </Button>
        <Button
          icon={<PieChartOutlined />}
          onClick={handleSentimentAnalysis}
          loading={sentimentLoading}
          size="large"
        >
          情感分析
        </Button>
        <Button
          icon={<GlobalOutlined />}
          onClick={handleSocialAnalysis}
          loading={socialLoading}
          size="large"
        >
          社交分析
        </Button>
      </Space>

      {/* 数据概览 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="分析样本" value={newsList.length} suffix="条" />
          </Col>
          <Col span={6}>
            <Statistic
              title="分析类型"
              value={
                analysisType === 'summary'
                  ? '深度分析'
                  : analysisType === 'keywords'
                  ? '关键词'
                  : analysisType === 'sentiment'
                  ? '情感'
                  : '社交'
              }
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="分析来源"
              value={analysisResult?.source || '-'}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="分析状态"
              value={analysisResult ? '已完成' : '待分析'}
            />
          </Col>
        </Row>
      </Card>

      {/* 分析结果 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" tip="AI 正在分析中..." />
        </div>
      ) : analysisResult ? (
        <div>
          {analysisType === 'summary' && analysisResult.raw_data && renderDeepAnalysis()}
          {analysisType === 'keywords' && renderKeywords()}
          {analysisType === 'sentiment' && renderSentiment()}
          {analysisType === 'social' && renderSocial()}
        </div>
      ) : (
        <Empty description="点击上方按钮开始 AI 分析" />
      )}
    </div>
  );
}

export default AIAnalysis;
