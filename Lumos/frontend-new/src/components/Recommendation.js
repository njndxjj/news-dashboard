import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Tag,
  Space,
  Button,
  message,
  Spin,
  Empty,
  Typography,
  Row,
  Col,
  Statistic,
  Divider,
  Progress,
} from 'antd';
import {
  ThunderboltOutlined,
  StarOutlined,
  FireOutlined,
  LinkOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { recommendNews, fetchNews, getUserInterests } from '../services/api.js';
import { trackEvent } from '../utils/tracking.js';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

function Recommendation() {
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [newsList, setNewsList] = useState([]);
  const [userInterests, setUserInterests] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    trending: 0,
    interestMatched: 0,
    semantic: 0,
  });

  const userId = localStorage.getItem('userId') || 'default';

  // 加载新闻
  const loadNews = async () => {
    try {
      const data = await fetchNews();
      setNewsList(Array.isArray(data) ? data.slice(0, 100) : []);
    } catch (error) {
      console.error('加载新闻失败:', error);
    }
  };

  // 加载用户兴趣
  const loadInterests = async () => {
    try {
      const data = await getUserInterests(userId);
      setUserInterests(data.interests || []);
    } catch (error) {
      console.error('加载兴趣失败:', error);
    }
  };

  // 获取推荐
  const handleGetRecommendations = async () => {
    if (newsList.length === 0) {
      message.warning('暂无数据，请先刷新新闻');
      return;
    }

    setLoading(true);
    try {
      // 默认不使用外部 API，优先使用本地数据库数据
      const result = await recommendNews(newsList, [], false, userId);
      const recs = result.recommendations || [];
      setRecommendations(recs);

      // 统计数据
      setStats({
        total: recs.length,
        trending: recs.filter((r) => r.recommendation_type === 'trending').length,
        interestMatched: recs.filter(
          (r) => r.recommendation_type === 'collaborative' || r.recommendation_type === 'hybrid'
        ).length,
        semantic: recs.filter((r) => r.recommendation_type === 'semantic').length,  // 语义推荐数量
      });

      message.success(`生成 ${recs.length} 条推荐`);
      // 埋点：记录获取推荐事件
      trackEvent('recommendation_generate', {
        total_count: recs.length,
        trending_count: stats.trending,
        interest_matched_count: stats.interestMatched,
        semantic_count: stats.semantic,
      });
    } catch (error) {
      message.error('获取推荐失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNews();
    loadInterests();
  }, []);

  // 获取推荐类型标签
  const getRecTypeTag = (type) => {
    const typeMap = {
      trending: { color: 'red', text: '🔥 实时热点' },
      collaborative: { color: 'blue', text: '❤️ 兴趣匹配' },
      similar_content: { color: 'purple', text: '📌 相关内容' },
      hybrid: { color: 'green', text: '✨ 混合推荐' },
      semantic: { color: 'cyan', text: '🧠 语义推荐' },  // 大模型语义分析
      keyword: { color: 'orange', text: '🔑 关键词匹配' },  // 关键词匹配兜底
    };
    const config = typeMap[type] || { color: 'default', text: '为您推荐' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取推荐原因（支持大模型语义分析结果）
  const getReasonIcon = (reason) => {
    if (!reason) return <ThunderboltOutlined style={{ color: '#fa8c16' }} />;
    if (reason.includes('兴趣')) {
      return <StarOutlined style={{ color: '#1890ff' }} />;
    } else if (reason.includes('热门')) {
      return <FireOutlined style={{ color: '#f5222d' }} />;
    }
    return <ThunderboltOutlined style={{ color: '#fa8c16' }} />;
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 16 }}>
        <ThunderboltOutlined /> 智能推荐
      </Title>

      {/* 用户兴趣概览 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={24 / 5}>
            <Statistic
              title="我的兴趣标签"
              value={userInterests.length}
              prefix={<StarOutlined />}
            />
          </Col>
          <Col span={24 / 5}>
            <Statistic
              title="推荐总数"
              value={stats.total}
              prefix={<ThunderboltOutlined />}
            />
          </Col>
          <Col span={24 / 5}>
            <Statistic
              title="热点推荐"
              value={stats.trending}
              prefix={<FireOutlined />}
            />
          </Col>
          <Col span={24 / 5}>
            <Statistic
              title="兴趣匹配"
              value={stats.interestMatched}
              prefix={<StarOutlined />}
            />
          </Col>
          <Col span={24 / 5}>
            <Statistic
              title="🧠 语义推荐"
              value={stats.semantic}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Col>
        </Row>
      </Card>

      {/* 操作栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleGetRecommendations}
            loading={loading}
            size="large"
          >
            获取智能推荐
          </Button>
          <Button
            icon={<SyncOutlined />}
            onClick={loadNews}
            size="large"
          >
            刷新新闻
          </Button>
        </Space>
        <Divider type="vertical" />
        <Text type="secondary">
          基于您的兴趣标签和浏览历史，AI 为您个性化推荐内容
        </Text>
      </Card>

      {/* 推荐列表 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" tip="AI 正在计算推荐..." />
        </div>
      ) : recommendations.length === 0 ? (
        <Empty
          description="点击上方"获取智能推荐"按钮开始推荐"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          grid={{ gutter: 16, column: 1 }}
          dataSource={recommendations}
          renderItem={(rec) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => {
                  // 埋点：记录推荐新闻点击
                  trackEvent('recommendation_click', {
                    news_id: rec.id || rec.link,
                    title: rec.title,
                    recommendation_type: rec.recommendation_type,
                    matched_keywords: rec.matched_keywords,
                    semantic_tags: rec.semantic_tags,
                  });
                  if (rec.link) window.open(rec.link, '_blank');
                }}
                style={{
                  borderLeft: `4px solid ${
                    rec.recommendation_type === 'trending'
                      ? '#f5222d'
                      : rec.recommendation_type === 'collaborative' ||
                        rec.recommendation_type === 'hybrid'
                      ? '#1890ff'
                      : '#fa8c16'
                  }`,
                }}
                title={
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    <Title level={5} style={{ margin: 0 }}>
                      {rec.title}
                    </Title>
                    <Space wrap>
                      {getRecTypeTag(rec.recommendation_type)}
                      {rec.matched_keywords && rec.matched_keywords.length > 0 && (
                        <>
                          <Text type="secondary">匹配关键词:</Text>
                          {rec.matched_keywords.slice(0, 5).map((kw, index) => (
                            <Tag key={index} color="blue">
                              {kw}
                            </Tag>
                          ))}
                        </>
                      )}
                      {rec.semantic_tags && rec.semantic_tags.length > 0 && (
                        <>
                          <Text type="secondary">语义标签:</Text>
                          {rec.semantic_tags.slice(0, 3).map((tag, index) => (
                            <Tag key={index} color="cyan">
                              {tag}
                            </Tag>
                          ))}
                        </>
                      )}
                    </Space>
                  </Space>
                }
                extra={
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ marginBottom: 8 }}>
                      <Text type="secondary">{rec.time_ago || '刚刚'}</Text>
                    </div>
                  </div>
                }
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    {getReasonIcon(rec.reason)}
                    <Text type="secondary">{rec.reason}</Text>
                  </Space>
                  {rec.source && (
                    <Tag color="gray">{rec.source}</Tag>
                  )}
                </div>
                {rec.link && rec.link !== '#' && (
                  <div style={{ marginTop: 8, textAlign: 'right' }}>
                    <Button type="link" icon={<LinkOutlined />}>
                      查看详情
                    </Button>
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

export default Recommendation;
