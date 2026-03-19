import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  message,
  Popconfirm,
  Switch,
  Drawer,
  Statistic,
  Row,
  Col,
  Typography,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  SyncOutlined,
  DeleteOutlined,
  EditOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LinkOutlined,
  FireOutlined,
} from '@ant-design/icons';
import {
  getRssFeeds,
  createRssFeed,
  updateRssFeed,
  deleteRssFeed,
  testRssFeed,
  runAdminCrawlers,
  getCrawlersStatus,
} from '../services/api.js';

const { Title } = Typography;
const { TextArea } = Input;

function CrawlerManagement() {
  const [loading, setLoading] = useState(false);
  const [feeds, setFeeds] = useState([]);
  const [crawlerStatus, setCrawlerStatus] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [testDrawerVisible, setTestDrawerVisible] = useState(false);
  const [currentFeed, setCurrentFeed] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [form] = Form.useForm();

  // 加载 RSS 源列表
  const loadFeeds = async () => {
    setLoading(true);
    try {
      const data = await getRssFeeds();
      setFeeds(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('加载 RSS 源列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载爬虫状态
  const loadCrawlerStatus = async () => {
    try {
      const data = await getCrawlersStatus();
      setCrawlerStatus(data);
    } catch (error) {
      console.error('加载爬虫状态失败:', error);
    }
  };

  useEffect(() => {
    loadFeeds();
    loadCrawlerStatus();
  }, []);

  // 手动运行爬虫
  const handleRunCrawlers = async () => {
    try {
      await runAdminCrawlers();
      message.success('爬虫已启动，请在后台查看运行状态');
      setTimeout(loadCrawlerStatus, 3000);
    } catch (error) {
      message.error('启动爬虫失败');
    }
  };

  // 测试 RSS 源
  const handleTestFeed = async (feed) => {
    setCurrentFeed(feed);
    setTestDrawerVisible(true);
    setTestResult(null);

    try {
      const data = await testRssFeed(feed.id);
      setTestResult(data);
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    }
  };

  // 创建 RSS 源
  const handleCreate = () => {
    form.resetFields();
    setModalVisible(true);
  };

  const handleCreateSubmit = async (values) => {
    try {
      await createRssFeed(values);
      message.success('RSS 源添加成功');
      setModalVisible(false);
      loadFeeds();
    } catch (error) {
      message.error(error.response?.data?.error || '添加失败');
    }
  };

  // 更新 RSS 源
  const handleUpdate = (feed) => {
    form.setFieldsValue(feed);
    setCurrentFeed(feed);
    setModalVisible(true);
  };

  const handleUpdateSubmit = async (values) => {
    try {
      await updateRssFeed(currentFeed.id, values);
      message.success('RSS 源已更新');
      setModalVisible(false);
      loadFeeds();
    } catch (error) {
      message.error(error.response?.data?.error || '更新失败');
    }
  };

  // 删除 RSS 源
  const handleDelete = async (feedId) => {
    try {
      await deleteRssFeed(feedId);
      message.success('RSS 源已删除');
      loadFeeds();
    } catch (error) {
      message.error(error.response?.data?.error || '删除失败');
    }
  };

  // 切换启用状态
  const handleToggleEnabled = async (feed, enabled) => {
    try {
      await updateRssFeed(feed.id, { enabled });
      message.success(enabled ? '已启用' : '已禁用');
      loadFeeds();
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 200,
    },
    {
      title: 'URL',
      dataIndex: 'url',
      ellipsis: true,
      render: (url) => (
        <a href={url} target="_blank" rel="noopener noreferrer">
          <LinkOutlined /> {url.substring(0, 50)}...
        </a>
      ),
    },
    {
      title: '行业',
      dataIndex: 'industry',
      width: 120,
      render: (industry) => industry || '-',
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 80,
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '最后抓取',
      dataIndex: 'last_crawled',
      width: 180,
      render: (time) => time || '从未',
    },
    {
      title: '抓取次数',
      dataIndex: 'crawl_count',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => handleTestFeed(record)}
          >
            测试
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleUpdate(record)}
          >
            <EditOutlined />
          </Button>
          <Switch
            checked={record.enabled}
            onChange={(checked) => handleToggleEnabled(record, checked)}
            size="small"
          />
          <Popconfirm
            title="确定删除此 RSS 源？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger>
              <DeleteOutlined />
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>🕷️ 爬虫管理中心</Title>
        <Divider />
      </div>

      {/* 爬虫状态概览 */}
      {crawlerStatus && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="RSS 源总数"
                value={crawlerStatus.total_feeds}
                prefix={<LinkOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="活跃源数"
                value={crawlerStatus.active_feeds}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="近 1 小时文章"
                value={crawlerStatus.recent_articles}
                prefix={<FireOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="爬虫状态" suffix={
                <Button type="primary" icon={<SyncOutlined spin />} onClick={handleRunCrawlers}>
                  立即运行
                </Button>
              } />
            </Card>
          </Col>
        </Row>
      )}

      {/* RSS 源列表 */}
      <Card
        title="RSS 源管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            添加 RSS 源
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={feeds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 创建/编辑弹窗 */}
      <Modal
        title={currentFeed ? '编辑 RSS 源' : '添加 RSS 源'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          setCurrentFeed(null);
          form.resetFields();
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={currentFeed ? (values) => handleUpdateSubmit(values) : handleCreateSubmit}
        >
          <Form.Item
            name="name"
            label="源名称"
            rules={[{ required: true, message: '请输入源名称' }]}
          >
            <Input placeholder="例如：36 氪" />
          </Form.Item>
          <Form.Item
            name="url"
            label="RSS URL"
            rules={[
              { required: true, message: '请输入 RSS URL' },
              { type: 'url', message: '请输入有效的 URL' }
            ]}
          >
            <Input placeholder="https://example.com/rss" disabled={!!currentFeed} />
          </Form.Item>
          <Form.Item
            name="industry"
            label="所属行业"
          >
            <Select placeholder="选择行业">
              <Select.Option value="AI">AI</Select.Option>
              <Select.Option value="科技">科技</Select.Option>
              <Select.Option value="金融">金融</Select.Option>
              <Select.Option value="电商">电商</Select.Option>
              <Select.Option value="教育">教育</Select.Option>
              <Select.Option value="医疗">医疗</Select.Option>
              <Select.Option value="其他">其他</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 测试抽屉 */}
      <Drawer
        title={`测试 RSS 源：${currentFeed?.name}`}
        placement="right"
        width={600}
        open={testDrawerVisible}
        onClose={() => setTestDrawerVisible(false)}
      >
        {testResult ? (
          testResult.success ? (
            <div>
              <Space style={{ marginBottom: 16 }}>
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                <Title level={5}>测试成功</Title>
              </Space>
              <Card size="small" title={`获取到 ${testResult.entries_count} 篇文章`}>
                {testResult.latest_entries && testResult.latest_entries.map((entry, idx) => (
                  <div key={idx} style={{ marginBottom: 12 }}>
                    <div style={{ fontWeight: 500 }}>{entry.title}</div>
                    <div style={{ fontSize: 12, color: '#999' }}>
                      {entry.published} · <a href={entry.link} target="_blank">查看</a>
                    </div>
                  </div>
                ))}
              </Card>
            </div>
          ) : (
            <div>
              <Space>
                <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
                <Title level={5}>测试失败</Title>
              </Space>
              <Card size="small" type="inner">
                <p style={{ color: '#ff4d4f' }}>{testResult.error}</p>
              </Card>
            </div>
          )
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <SyncOutlined spin style={{ fontSize: 24 }} />
            <p>正在测试 RSS 源可用性...</p>
          </div>
        )}
      </Drawer>
    </div>
  );
}

export default CrawlerManagement;
