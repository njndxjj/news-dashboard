import React, { useState, useEffect } from 'react';
import {
  Card,
  Tag,
  Input,
  Button,
  Space,
  List,
  message,
  Modal,
  Form,
  Select,
  Divider,
  Typography,
  Empty,
  Popconfirm,
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  DeleteOutlined,
  ClearOutlined,
  StarOutlined,
} from '@ant-design/icons';
import {
  getUserInterests,
  getInterestCategories,
  addUserInterest,
  followCategory,
  unfollowCategory,
  deleteUserInterest,
  clearUserInterests,
} from '../services/api.js';

const { Title, Text } = Typography;

function UserInterests() {
  const [interests, setInterests] = useState([]);
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const userId = localStorage.getItem('userId') || 'default';

  // 加载用户兴趣
  const loadInterests = async () => {
    setLoading(true);
    try {
      const data = await getUserInterests(userId);
      setInterests(data.interests || []);
    } catch (error) {
      message.error('加载兴趣标签失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载兴趣分类
  const loadCategories = async () => {
    try {
      const data = await getInterestCategories();
      setCategories(data.categories || {});
    } catch (error) {
      console.error('加载分类失败:', error);
    }
  };

  useEffect(() => {
    loadInterests();
    loadCategories();
  }, []);

  // 添加兴趣标签
  const handleAddInterest = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入关键词');
      return;
    }

    setAdding(true);
    try {
      await addUserInterest(inputValue.trim(), 1.0, userId);
      message.success('添加成功');
      setInputValue('');
      loadInterests();
    } catch (error) {
      message.error('添加失败');
    } finally {
      setAdding(false);
    }
  };

  // 删除兴趣标签
  const handleDeleteInterest = async (keyword) => {
    try {
      await deleteUserInterest(keyword, userId);
      message.success('删除成功');
      loadInterests();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 清空所有兴趣
  const handleClearAll = () => {
    Modal.confirm({
      title: '确认清空',
      content: '确定要清空所有兴趣标签吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await clearUserInterests(userId);
          message.success('已清空所有兴趣标签');
          loadInterests();
        } catch (error) {
          message.error('清空失败');
        }
      },
    });
  };

  // 关注分类
  const handleFollowCategory = async (category) => {
    try {
      await followCategory(category, userId);
      message.success(`已关注 ${category} 分类`);
      loadInterests();
    } catch (error) {
      message.error('关注失败');
    }
  };

  // 取消关注分类
  const handleUnfollowCategory = async (category) => {
    try {
      await unfollowCategory(category, userId);
      message.success(`已取消关注 ${category} 分类`);
      loadInterests();
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 16 }}>
        <UserOutlined /> 兴趣管理
      </Title>

      {/* 添加兴趣标签 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="输入关键词，按回车添加"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleAddInterest}
            allowClear
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddInterest}
            loading={adding}
          >
            添加
          </Button>
        </Space.Compact>
        <Divider />
        <Space>
          <Button
            icon={<ClearOutlined />}
            danger
            onClick={handleClearAll}
            disabled={interests.length === 0}
          >
            清空所有
          </Button>
          <Button
            icon={<StarOutlined />}
            onClick={() => setModalVisible(true)}
          >
            关注分类
          </Button>
        </Space>
      </Card>

      {/* 当前兴趣标签 */}
      <Card
        size="small"
        title={`我的兴趣标签 (${interests.length})`}
      >
        {interests.length === 0 ? (
          <Empty description="暂无兴趣标签" />
        ) : (
          <Space wrap>
            {interests.map((item, index) => (
              <Tag
                key={index}
                color="blue"
                closable
                onClose={() => handleDeleteInterest(item.keyword)}
                style={{ fontSize: 14, padding: '6px 12px' }}
              >
                {item.keyword} {item.weight && item.weight !== 1.0 && `(${item.weight})`}
              </Tag>
            ))}
          </Space>
        )}
      </Card>

      {/* 兴趣分类 */}
      <Card
        size="small"
        title="关注分类"
        style={{ marginTop: 16 }}
      >
        {Object.keys(categories).length === 0 ? (
          <Empty description="暂无分类数据" />
        ) : (
          <List
            grid={{ gutter: 16, column: 3 }}
            dataSource={Object.entries(categories)}
            renderItem={([category, keywords]) => {
              const isFollowing = keywords.some((kw) =>
                interests.some((i) => i.keyword === kw)
              );

              return (
                <List.Item>
                  <Card
                    size="small"
                    title={category}
                    extra={
                      isFollowing ? (
                        <Popconfirm
                          title="确定取消关注？"
                          onConfirm={() => handleUnfollowCategory(category)}
                        >
                          <Button size="small" danger>
                            已关注
                          </Button>
                        </Popconfirm>
                      ) : (
                        <Button
                          size="small"
                          type="primary"
                          onClick={() => handleFollowCategory(category)}
                        >
                          关注
                        </Button>
                      )
                    }
                  >
                    <Space wrap>
                      {keywords.slice(0, 10).map((kw, index) => (
                        <Tag key={index} color="gray">
                          {kw}
                        </Tag>
                      ))}
                      {keywords.length > 10 && (
                        <Text type="secondary">+{keywords.length - 10}</Text>
                      )}
                    </Space>
                  </Card>
                </List.Item>
              );
            }}
          />
        )}
      </Card>

      {/* 关注分类弹窗 */}
      <Modal
        title="关注分类"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <List
          grid={{ gutter: 16, column: 2 }}
          dataSource={Object.entries(categories)}
          renderItem={([category, keywords]) => {
            const isFollowing = keywords.some((kw) =>
              interests.some((i) => i.keyword === kw)
            );

            return (
              <List.Item>
                <Card
                  size="small"
                  title={category}
                  extra={
                    isFollowing ? (
                      <Button
                        size="small"
                        danger
                        onClick={() => handleUnfollowCategory(category)}
                      >
                        已关注
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        type="primary"
                        onClick={() => handleFollowCategory(category)}
                      >
                        关注
                      </Button>
                    )
                  }
                >
                  <Text type="secondary">{keywords.length} 个关键词</Text>
                </Card>
              </List.Item>
            );
          }}
        />
      </Modal>
    </div>
  );
}

export default UserInterests;
