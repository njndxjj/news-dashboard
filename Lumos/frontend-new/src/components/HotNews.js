import React, { useState, useEffect } from 'react';
import { Card, List, Tag, Statistic, Spin, Empty, Typography, Progress } from 'antd';
import { FireOutlined, TrophyOutlined, TrendUpOutlined } from '@ant-design/icons';
import { fetchHotNews } from '../services/api.js';
import { trackEvent } from '../utils/tracking.js';

const { Title, Text } = Typography;

function HotNews() {
  const [loading, setLoading] = useState(false);
  const [hotNews, setHotNews] = useState([]);

  const loadHotNews = async () => {
    setLoading(true);
    try {
      const data = await fetchHotNews(20);
      setHotNews(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('加载热点新闻失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHotNews();
  }, []);

  // 获取热度颜色
  const getHotColor = (score) => {
    if (score >= 90) return '#f5222d';
    if (score >= 70) return '#fa8c16';
    if (score >= 50) return '#faad14';
    return '#52c41a';
  };

  // 获取排名图标
  const getRankIcon = (index) => {
    if (index === 0) return <TrophyOutlined style={{ color: '#ffd700' }} />;
    if (index === 1) return <TrophyOutlined style={{ color: '#c0c0c0' }} />;
    if (index === 2) return <TrophyOutlined style={{ color: '#cd7f32' }} />;
    return <Text strong>{index + 1}</Text>;
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 16 }}>
        <FireOutlined /> 热点榜单
      </Title>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" tip="加载热点数据..." />
        </div>
      ) : hotNews.length === 0 ? (
        <Empty description="暂无热点数据" />
      ) : (
        <List
          grid={{ gutter: 16, column: 1 }}
          dataSource={hotNews}
          renderItem={(news, index) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => {
                  // 埋点：记录热点新闻点击
                  trackEvent('hotnews_click', {
                    news_id: news.id || news.link,
                    title: news.title,
                    hot_score: news.hot_score,
                    rank: index + 1,
                  });
                  news.link && window.open(news.link, '_blank');
                }}
                style={{
                  borderLeft: `4px solid ${getHotColor(news.hot_score || 50)}`,
                }}
              >
                <Card.Meta
                  avatar={
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        background: getHotColor(news.hot_score || 50),
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 16,
                      }}
                    >
                      {getRankIcon(index)}
                    </div>
                  }
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Title level={5} style={{ margin: 0, flex: 1 }}>
                        {news.title}
                      </Title>
                      <Tag color="red">TOP {index + 1}</Tag>
                    </div>
                  }
                  description={
                    <div style={{ marginTop: 12 }}>
                      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                        <Tag>{news.source}</Tag>
                        {news.sentiment && (
                          <Tag
                            color={
                              news.sentiment === 'positive'
                                ? 'success'
                                : news.sentiment === 'negative'
                                ? 'error'
                                : 'default'
                            }
                          >
                            {news.sentiment === 'positive'
                              ? '正面'
                              : news.sentiment === 'negative'
                              ? '负面'
                              : '中性'}
                          </Tag>
                        )}
                      </div>
                      <Progress
                        percent={news.hot_score || 50}
                        strokeColor={getHotColor(news.hot_score || 50)}
                        showInfo={false}
                        size="small"
                      />
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: 8,
                        }}
                      >
                        <Text type="secondary">
                          热度分数：<strong style={{ color: getHotColor(news.hot_score || 50) }}>
                            {news.hot_score || 50}
                          </strong>
                        </Text>
                        <Text type="secondary">
                          {news.published
                            ? new Date(news.published).toLocaleString('zh-CN')
                            : ''}
                        </Text>
                      </div>
                    </div>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

export default HotNews;
