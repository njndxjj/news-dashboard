import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Tag,
  Space,
  Button,
  Input,
  Select,
  message,
  Spin,
  Empty,
  Badge,
  Typography,
  Divider,
} from 'antd';
import {
  SyncOutlined,
  SearchOutlined,
  FireOutlined,
  ClockCircleOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { fetchNews, searchNews, refreshNews, recordUserClick } from '../services/api.js';
import { trackEvent, trackPageView, trackSearch } from '../utils/tracking.js';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { Title } = Typography;
const { Search } = Input;

function NewsList() {
  const [loading, setLoading] = useState(false);
  const [newsList, setNewsList] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [searchSource, setSearchSource] = useState('browser');

  // 加载新闻
  const loadNews = async () => {
    setLoading(true);
    try {
      const data = await fetchNews();
      setNewsList(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('加载新闻失败');
    } finally {
      setLoading(false);
    }
  };

  // 手动刷新
  const handleRefresh = async () => {
    try {
      const data = await refreshNews();
      message.success(`刷新成功，共 ${data.count} 条新闻`);
      loadNews();
    } catch (error) {
      message.error('刷新失败');
    }
  };

  // 搜索
  const handleSearch = async (value) => {
    if (!value.trim()) {
      loadNews();
      return;
    }

    setSearchLoading(true);
    try {
      const data = await searchNews(value, searchSource);
      setNewsList(Array.isArray(data) ? data : []);
      message.success(`搜索到 ${data.length} 条结果`);
      // 前端埋点：记录搜索事件
      trackSearch(value, searchSource, data.length);
    } catch (error) {
      message.error('搜索失败');
    } finally {
      setSearchLoading(false);
    }
  };

  // 记录点击
  const handleNewsClick = async (news) => {
    const userId = localStorage.getItem('userId') || 'default';
    try {
      // 调用后端 API 记录点击
      await recordUserClick(
        news.id || news.link,
        news.title,
        news.source,
        userId
      );
      // 前端埋点：记录点击事件
      trackEvent('news_click', {
        news_id: news.id || news.link,
        title: news.title,
        source: news.source,
        channel: news.channel,
      });
    } catch (error) {
      // 静默失败
    }
  };

  useEffect(() => {
    loadNews();
  }, []);

  // 获取热度标签颜色
  const getHotBadge = (score) => {
    if (!score) return null;
    if (score >= 80) {
      return <Badge count="🔥" style={{ backgroundColor: '#f5222d' }} />;
    } else if (score >= 60) {
      return <Badge count="🔥" style={{ backgroundColor: '#fa8c16' }} />;
    }
    return null;
  };

  // 获取情感标签
  const getSentimentTag = (sentiment) => {
    const colorMap = {
      positive: 'success',
      neutral: 'default',
      negative: 'error',
    };
    const textMap = {
      positive: '正面',
      neutral: '中性',
      negative: '负面',
    };
    return (
      <Tag color={colorMap[sentiment] || 'default'}>
        {textMap[sentiment] || '中性'}
      </Tag>
    );
  };

  // 获取来源标签
  const getSourceTag = (source, priority) => {
    let color = 'default';
    if (priority === 'crawler') {
      color = 'orange';
    } else if (priority === 'domestic') {
      color = 'blue';
    } else if (priority === 'overseas') {
      color = 'purple';
    }

    return <Tag color={color}>{source}</Tag>;
  };

  return (
    <div>
      {/* 顶部操作栏 */}
      <div style={{ marginBottom: 24, display: 'flex', gap: 12, alignItems: 'center' }}>
        <Search
          placeholder="搜索新闻关键词"
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          style={{ flex: 1, maxWidth: 500 }}
          onSearch={handleSearch}
          loading={searchLoading}
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
        />
        <Select
          value={searchSource}
          onChange={setSearchSource}
          options={[
            { value: 'browser', label: '浏览器搜索' },
            { value: 'database', label: '数据库搜索' },
            { value: 'all', label: '全部' },
          ]}
          style={{ width: 120 }}
        />
        <Button
          type="primary"
          icon={<SyncOutlined spin={loading} />}
          onClick={handleRefresh}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 统计信息 */}
      <Card style={{ marginBottom: 16 }} size="small">
        <Space split={<Divider type="vertical" />}>
          <span>📊 共 <strong>{newsList.length}</strong> 条新闻</span>
          <span>🔥 热点 <strong>{newsList.filter(n => (n.hot_score || 0) >= 80).length}</strong> 条</span>
          <span>🤖 爬虫 <strong>{newsList.filter(n => n.priority === 'crawler').length}</strong> 条</span>
          <span>📰 国内 <strong>{newsList.filter(n => n.priority === 'domestic').length}</strong> 条</span>
          <span>🌍 国外 <strong>{newsList.filter(n => n.priority === 'overseas').length}</strong> 条</span>
        </Space>
      </Card>

      {/* 新闻列表 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" tip="加载中..." />
        </div>
      ) : newsList.length === 0 ? (
        <Empty description="暂无新闻数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          grid={{ gutter: 16, column: 1 }}
          dataSource={newsList}
          renderItem={(news) => (
            <List.Item>
              <Card
                hoverable
                className="news-card"
                onClick={() => {
                  handleNewsClick(news);
                  if (news.link) window.open(news.link, '_blank');
                }}
                title={
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Title level={5} style={{ margin: 0, flex: 1 }}>
                        {news.title}
                      </Title>
                      {getHotBadge(news.hot_score)}
                    </div>
                    <Space wrap>
                      {getSourceTag(news.source, news.priority)}
                      {getSentimentTag(news.sentiment)}
                      {news.original_title && (
                        <Tag color="gray">原文</Tag>
                      )}
                    </Space>
                  </Space>
                }
                extra={
                  <Space direction="vertical" align="end" size={4}>
                    <Space>
                      <ClockCircleOutlined />
                      <span style={{ fontSize: 12, color: '#8c8c8c' }}>
                        {dayjs(news.published).fromNow()}
                      </span>
                    </Space>
                    {news.hot_score && (
                      <Tag color="red">热度：{news.hot_score}</Tag>
                    )}
                  </Space>
                }
              >
                {news.original_title && (
                  <div style={{ color: '#8c8c8c', fontSize: 13, marginBottom: 8 }}>
                    <LinkOutlined /> 原文：{news.original_title}
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#8c8c8c', fontSize: 13 }}>
                    来自：{news.source}
                  </span>
                  <Button type="link" icon={<LinkOutlined />}>
                    查看详情
                  </Button>
                </div>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

export default NewsList;
