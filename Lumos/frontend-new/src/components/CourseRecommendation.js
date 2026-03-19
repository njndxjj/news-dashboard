import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Typography,
  Tag,
  Space,
  message,
  Badge,
} from 'antd';
import {
  ShopOutlined,
  FireOutlined,
  ArrowRightOutlined,
  GiftOutlined,
} from '@ant-design/icons';
import { getCourses } from '../services/api.js';

const { Title, Paragraph, Text } = Typography;

function CourseRecommendation({ industry = '' }) {
  const [loading, setLoading] = useState(false);
  const [courses, setCourses] = useState([]);

  // 加载课程列表
  const loadCourses = async () => {
    setLoading(true);
    try {
      const data = await getCourses(industry);
      setCourses(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('加载课程失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, [industry]);

  // 跳转课程
  const handleJumpToCourse = (course) => {
    // 记录点击行为
    window.open(course.link, '_blank');
    message.success('正在跳转到课程页面...');
  };

  if (courses.length === 0 && !loading) {
    return null; // 没有课程时不显示
  }

  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={4}>
          <ShopOutlined /> 推荐课程
        </Title>
        <Paragraph type="secondary">
          根据您的兴趣标签个性化推荐
        </Paragraph>
      </div>

      <List
        grid={{ gutter: 16, column: 3 }}
        loading={loading}
        dataSource={courses.slice(0, 6)} // 最多显示 6 个
        renderItem={(course) => (
          <List.Item>
            <Card
              hoverable
              cover={
                course.thumbnail_url ? (
                  <img
                    alt={course.title}
                    src={course.thumbnail_url}
                    style={{ height: 160, objectFit: 'cover' }}
                  />
                ) : (
                  <div style={{ height: 160, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ShopOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                  </div>
                )
              }
              actions={[
                <Button
                  key="learn"
                  type="primary"
                  icon={<ArrowRightOutlined />}
                  onClick={() => handleJumpToCourse(course)}
                >
                  立即学习
                </Button>
              ]}
            >
              <Card.Meta
                title={
                  <Space>
                    {course.title}
                    {course.discount && (
                      <Tag color="red">
                        <GiftOutlined /> {course.discount}
                      </Tag>
                    )}
                  </Space>
                }
                description={
                  <div>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ fontSize: 13, color: '#666' }}
                    >
                      {course.description}
                    </Paragraph>
                    <div style={{ marginTop: 12 }}>
                      {course.is_paid ? (
                        <Space>
                          <Text type="danger" strong style={{ fontSize: 16 }}>
                            ¥{course.price}
                          </Text>
                          {course.original_price && (
                            <Text delete style={{ color: '#999' }}>
                              ¥{course.original_price}
                            </Text>
                          )}
                        </Space>
                      ) : (
                        <Tag color="green">免费</Tag>
                      )}
                    </div>
                    <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                      <FireOutlined /> {course.view_count}人在学
                    </div>
                  </div>
                }
              />
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
}

export default CourseRecommendation;
