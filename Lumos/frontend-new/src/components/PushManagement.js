import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Tag,
  Switch,
  message,
  Modal,
  Form,
  Select,
  Divider,
  Typography,
  Empty,
  Popconfirm,
  List,
} from 'antd';
import {
  BellOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined,
  SendOutlined,
} from '@ant-design/icons';
import {
  getPushRules,
  createPushRule,
  updatePushRule,
  deletePushRule,
  getPushSettings,
  updatePushSettings,
  testPush,
  getPushLogs,
} from '../services/api.js';

const { Title } = Typography;

function PushManagement() {
  const [rules, setRules] = useState([]);
  const [settings, setSettings] = useState({});
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form] = Form.useForm();

  // 加载推送规则
  const loadRules = async () => {
    setLoading(true);
    try {
      const data = await getPushRules();
      setRules(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('加载推送规则失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载推送设置
  const loadSettings = async () => {
    try {
      const data = await getPushSettings();
      setSettings(data || {});
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  };

  // 加载推送记录
  const loadLogs = async () => {
    try {
      const data = await getPushLogs(50);
      setLogs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('加载日志失败:', error);
    }
  };

  useEffect(() => {
    loadRules();
    loadSettings();
    loadLogs();
  }, []);

  // 创建/更新规则
  const handleSaveRule = async () => {
    try {
      const values = await form.validateFields();
      if (editingRule) {
        await updatePushRule(
          editingRule.id,
          values.rule_name,
          values.keywords || [],
          values.hot_threshold,
          values.enabled
        );
        message.success('更新成功');
      } else {
        await createPushRule(
          values.rule_name,
          values.keywords || [],
          values.hot_threshold,
          values.enabled
        );
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingRule(null);
      loadRules();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 删除规则
  const handleDeleteRule = async (ruleId) => {
    try {
      await deletePushRule(ruleId);
      message.success('删除成功');
      loadRules();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 编辑规则
  const handleEditRule = (rule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      rule_name: rule.rule_name,
      keywords: rule.keywords,
      hot_threshold: rule.hot_threshold,
      enabled: rule.enabled,
    });
    setModalVisible(true);
  };

  // 测试推送
  const handleTestPush = async () => {
    try {
      const result = await testPush();
      if (result.success) {
        message.success('测试推送成功');
      } else {
        message.error('测试推送失败：' + result.message);
      }
    } catch (error) {
      message.error('测试推送失败');
    }
  };

  // 更新设置
  const handleUpdateSettings = async (key, value) => {
    try {
      await updatePushSettings({ [key]: value });
      message.success('设置已更新');
      loadSettings();
    } catch (error) {
      message.error('更新设置失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      render: (keywords) => (
        <Space wrap>
          {keywords?.slice(0, 5).map((kw, index) => (
            <Tag key={index} color="blue">
              {kw}
            </Tag>
          ))}
          {keywords?.length > 5 && <Tag>+{keywords.length - 5}</Tag>}
        </Space>
      ),
    },
    {
      title: '热度阈值',
      dataIndex: 'hot_threshold',
      key: 'hot_threshold',
      render: (threshold) => (
        <Tag color={threshold >= 80 ? 'red' : threshold >= 60 ? 'orange' : 'green'}>
          {threshold}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditRule(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除？"
            onConfirm={() => handleDeleteRule(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 16 }}>
        <BellOutlined /> 推送管理
      </Title>

      {/* 推送设置 */}
      <Card
        size="small"
        title="推送设置"
        extra={
          <Button icon={<SendOutlined />} onClick={handleTestPush}>
            测试推送
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Text>飞书 Webhook:</Text>
            <Input
              value={settings.feishu_webhook || ''}
              placeholder="未配置"
              readOnly
              style={{ width: 300 }}
            />
          </Space>
          <Space>
            <Text>每日摘要推送:</Text>
            <Switch
              checked={settings.daily_summary_enabled}
              onChange={(checked) =>
                handleUpdateSettings('daily_summary_enabled', checked)
              }
            />
          </Space>
          <Space>
            <Text>实时推送:</Text>
            <Switch
              checked={settings.realtime_push_enabled}
              onChange={(checked) =>
                handleUpdateSettings('realtime_push_enabled', checked)
              }
            />
          </Space>
        </Space>
      </Card>

      {/* 推送规则 */}
      <Card
        size="small"
        title="推送规则"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingRule(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            新建规则
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          columns={columns}
          dataSource={rules}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 推送记录 */}
      <Card size="small" title="推送记录">
        {logs.length === 0 ? (
          <Empty description="暂无推送记录" />
        ) : (
          <List
            dataSource={logs}
            renderItem={(log) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Tag color={log.success ? 'success' : 'error'}>
                        {log.success ? '成功' : '失败'}
                      </Tag>
                      <Text>{log.rule_name || '测试推送'}</Text>
                    </Space>
                  }
                  description={
                    <>
                      <div>推送时间：{log.pushed_at || log.created_at}</div>
                      {log.message && <div>消息：{log.message}</div>}
                    </>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* 新建/编辑规则弹窗 */}
      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={modalVisible}
        onOk={handleSaveRule}
        onCancel={() => {
          setModalVisible(false);
          setEditingRule(null);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="例如：AI 行业重大新闻" />
          </Form.Item>
          <Form.Item
            name="keywords"
            label="关键词（用逗号分隔）"
            rules={[{ required: true, message: '请输入关键词' }]}
          >
            <Input placeholder="例如：人工智能，大模型，GPT" />
          </Form.Item>
          <Form.Item
            name="hot_threshold"
            label="热度阈值"
            initialValue={90}
            rules={[{ required: true, message: '请输入热度阈值' }]}
          >
            <Input.Number min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default PushManagement;
