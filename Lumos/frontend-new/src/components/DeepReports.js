import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Modal,
  Typography,
  Tag,
  Space,
  message,
  Result,
  Spin,
  Divider,
} from 'antd';
import {
  FileTextOutlined,
  LockOutlined,
  UnlockOutlined,
  StarOutlined,
} from '@ant-design/icons';
import {
  getDeepReports,
  getDeepReport,
  consumeReportQuota,
  getUserSubscription,
  getRecommendation,
} from '../services/api.js';
import ReactMarkdown from 'react-markdown';

const { Title, Paragraph } = Typography;

function DeepReports() {
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportContent, setReportContent] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [consuming, setConsuming] = useState(false);

  // 加载报告列表
  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await getDeepReports();
      setReports(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('加载报告列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载用户订阅状态
  const loadSubscription = async () => {
    try {
      const data = await getUserSubscription();
      setSubscription(data);
    } catch (error) {
      console.error('加载订阅状态失败:', error);
    }
  };

  useEffect(() => {
    loadReports();
    loadSubscription();
  }, []);

  // 查看报告详情
  const handleViewReport = async (report) => {
    setSelectedReport(report);
    setModalVisible(true);
    setReportContent(null);

    // 如果报告未锁定，直接加载内容
    if (!report.is_locked) {
      try {
        const data = await getDeepReport(report.id);
        setReportContent(data);
      } catch (error) {
        message.error('加载报告失败');
      }
      return;
    }

    // 检查用户订阅状态
    if (subscription?.is_premium) {
      // 会员直接加载
      try {
        const data = await getDeepReport(report.id);
        setReportContent(data);
      } catch (error) {
        message.error('加载报告失败');
      }
    } else if (subscription?.reports_remaining > 0) {
      // 免费用户有剩余额度，提示消耗
      Modal.confirm({
        title: '解锁深度报告',
        content: `您将消耗 1 次免费报告额度（剩余${subscription.reports_remaining}次）`,
        okText: '确认解锁',
        cancelText: '取消',
        onOk: async () => {
          setConsuming(true);
          try {
            await consumeReportQuota();
            const data = await getDeepReport(report.id);
            setReportContent(data);
            message.success('解锁成功');
            loadSubscription(); // 刷新订阅状态
          } catch (error) {
            message.error(error.response?.data?.error || '解锁失败');
          } finally {
            setConsuming(false);
          }
        },
      });
    } else {
      // 额度用完，引导升级
      setReportContent({
        is_locked: true,
        message: '免费额度已用完，请升级会员解锁无限报告'
      });
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>📊 深度报告</Title>
        <Paragraph type="secondary">
          AI 生成的行业深度分析报告，免费订阅用户每月可阅读 3 篇
        </Paragraph>
        {subscription && (
          <Space style={{ marginTop: 8 }}>
            <Tag color={subscription.is_premium ? 'gold' : 'blue'}>
              {subscription.is_premium ? '👑 会员' : '免费订阅'}
            </Tag>
            {!subscription.is_premium && (
              <Tag color="green">
                本月剩余：{subscription.reports_remaining}篇
              </Tag>
            )}
          </Space>
        )}
      </div>

      <List
        grid={{ gutter: 16, column: 2 }}
        loading={loading}
        dataSource={reports}
        renderItem={(report) => (
          <List.Item>
            <Card
              hoverable
              onClick={() => handleViewReport(report)}
              cover={
                <div style={{ height: 160, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <FileTextOutlined style={{ fontSize: 64, color: '#1890ff' }} />
                </div>
              }
              actions={[
                <Button
                  key="view"
                  type="link"
                  icon={report.is_locked ? <LockOutlined /> : <UnlockOutlined />}
                >
                  {report.is_locked ? '解锁阅读' : '阅读全文'}
                </Button>
              ]}
            >
              <Card.Meta
                title={
                  <Space>
                    {report.title}
                    {report.is_locked && <LockOutlined style={{ color: '#faad14' }} />}
                  </Space>
                }
                description={
                  <div>
                    <Tag>{report.industry}</Tag>
                    <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                      👁️ {report.view_count}次阅读
                    </div>
                  </div>
                }
              />
            </Card>
          </List.Item>
        )}
      />

      {/* 报告详情弹窗 */}
      <Modal
        title={selectedReport?.title}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={900}
        footer={null}
      >
        {reportContent ? (
          reportContent.is_locked ? (
            <Result
              status="warning"
              icon={<LockOutlined />}
              title="需要解锁"
              subTitle={reportContent.message}
              extra={[
                <Button key="upgrade" type="primary">
                  升级会员
                </Button>,
              ]}
            />
          ) : (
            <div style={{ maxHeight: '70vh', overflow: 'auto', padding: '20px 0' }}>
              <div style={{ marginBottom: 16 }}>
                <Tag>{reportContent.industry}</Tag>
                <span style={{ marginLeft: 16, color: '#999' }}>
                  生成时间：{new Date(reportContent.generated_at).toLocaleDateString()}
                </span>
              </div>
              <Divider />
              <article className="markdown-body">
                <ReactMarkdown>{reportContent.content}</ReactMarkdown>
              </article>
            </div>
          )
        ) : (
          <div style={{ padding: 60, textAlign: 'center' }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>
              {consuming ? '正在解锁报告...' : '正在加载报告内容...'}
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default DeepReports;
