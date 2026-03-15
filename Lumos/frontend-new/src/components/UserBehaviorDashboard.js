import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Typography,
  Space,
  Progress,
  DatePicker,
  Select,
  Button,
} from 'antd';
const { RangePicker } = DatePicker;
import {
  FireOutlined,
  EyeOutlined,
  StarOutlined,
  ShareAltOutlined,
  SearchOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { fetchUserBehaviorStats, fetchUserBehaviorEvents } from '../services/api.js';
import dayjs from 'dayjs';

const { Title } = Typography;

function UserBehaviorDashboard() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [dateRange, setDateRange] = useState([dayjs().subtract(7, 'day'), dayjs()]);
  const [eventType, setEventType] = useState('all');

  // 加载统计数据
  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await fetchUserBehaviorStats({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      });
      setStats(data);
    } catch (error) {
      console.error('加载统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载行为事件列表
  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await fetchUserBehaviorEvents({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        event_type: eventType !== 'all' ? eventType : undefined,
      });
      setEvents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('加载事件列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadEvents();
  }, [dateRange]);

  // 刷新数据
  const handleRefresh = () => {
    loadStats();
    loadEvents();
  };

  // 导出 CSV
  const handleExport = () => {
    const headers = ['时间', '用户 ID', '事件类型', '内容 ID', '内容标题', '频道', '额外数据'];
    const rows = events.map((e) => [
      e.timestamp,
      e.user_id,
      e.event_type,
      e.content_id,
      e.content_title,
      e.channel,
      JSON.stringify(e.metadata || {}),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `user_behavior_${dateRange[0].format('YYYYMMDD')}_${dateRange[1].format('YYYYMMDD')}.csv`;
    link.click();
  };

  // 事件类型颜色
  const getEventColor = (type) => {
    const colorMap = {
      page_view: 'blue',
      click: 'green',
      like: 'red',
      favorite: 'gold',
      share: 'purple',
      search: 'cyan',
    };
    return colorMap[type] || 'default';
  };

  // 事件类型图标
  const getEventIcon = (type) => {
    const iconMap = {
      page_view: <EyeOutlined />,
      click: <FireOutlined />,
      like: <StarOutlined />,
      favorite: <StarOutlined />,
      share: <ShareAltOutlined />,
      search: <SearchOutlined />,
    };
    return iconMap[type] || <ClockCircleOutlined />;
  };

  // 事件表格列
  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      width: 180,
      sorter: (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
    },
    {
      title: '用户 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 150,
    },
    {
      title: '事件类型',
      dataIndex: 'event_type',
      key: 'event_type',
      render: (type) => (
        <Tag color={getEventColor(type)} icon={getEventIcon(type)}>
          {type}
        </Tag>
      ),
      width: 120,
      filters: [
        { text: '浏览', value: 'page_view' },
        { text: '点击', value: 'click' },
        { text: '点赞', value: 'like' },
        { text: '收藏', value: 'favorite' },
        { text: '分享', value: 'share' },
        { text: '搜索', value: 'search' },
      ],
      onFilter: (value, record) => record.event_type === value,
    },
    {
      title: '内容标题',
      dataIndex: 'content_title',
      key: 'content_title',
      ellipsis: true,
    },
    {
      title: '频道',
      dataIndex: 'channel',
      key: 'channel',
      width: 100,
      render: (channel) => channel || '-',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>📊 用户行为分析看板</Title>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates)}
            style={{ width: 250 }}
          />
          <Select
            value={eventType}
            onChange={setEventType}
            options={[
              { value: 'all', label: '全部事件' },
              { value: 'page_view', label: '浏览' },
              { value: 'click', label: '点击' },
              { value: 'like', label: '点赞' },
              { value: 'favorite', label: '收藏' },
              { value: 'share', label: '分享' },
              { value: 'search', label: '搜索' },
            ]}
            style={{ width: 120 }}
          />
          <Button icon={<SyncOutlined />} onClick={handleRefresh} loading={loading}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总活跃用户"
              value={stats?.total_users || 0}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总行为事件"
              value={stats?.total_events || 0}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总点击次数"
              value={stats?.total_clicks || 0}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总搜索次数"
              value={stats?.total_searches || 0}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 行为分布 */}
      {stats?.event_type_distribution && (
        <Card title="📈 行为类型分布" style={{ marginBottom: 24 }} loading={loading}>
          <Row gutter={16}>
            {Object.entries(stats.event_type_distribution).map(([type, count]) => (
              <Col span={4} key={type}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: 8 }}>{getEventIcon(type)}</div>
                  <Statistic
                    title={type}
                    value={count}
                    valueStyle={{ color: `var(--ant-${getEventColor(type)}-color)` }}
                  />
                  <Progress
                    percent={Math.round((count / stats.total_events) * 100)}
                    strokeColor={getEventColor(type) === 'default' ? '#1890ff' : getEventColor(type)}
                    showInfo={false}
                    size="small"
                    style={{ marginTop: 8 }}
                  />
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 热门内容 */}
      {stats?.top_content && stats.top_content.length > 0 && (
        <Card title="🔥 热门内容 TOP 10" style={{ marginBottom: 24 }} loading={loading}>
          <Row gutter={[16, 16]}>
            {stats.top_content.map((item, index) => (
              <Col span={8} key={index}>
                <Card size="small" hoverable>
                  <Card.Meta
                    title={
                      <Space>
                        <Tag color={index < 3 ? 'red' : 'gold'}>TOP {index + 1}</Tag>
                        <span style={{ fontSize: 14 }}>{item.title}</span>
                      </Space>
                    }
                    description={
                      <Space split={<span>|</span>}>
                        <span>👁️ {item.view_count}</span>
                        <span>👆 {item.click_count}</span>
                        <span>⭐ {item.like_count}</span>
                      </Space>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 事件列表 */}
      <Card title="📋 行为事件列表" loading={loading}>
        <Table
          columns={columns}
          dataSource={events}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
}

export default UserBehaviorDashboard;
