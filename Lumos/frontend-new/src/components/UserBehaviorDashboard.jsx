import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Row, Col, Statistic, Button, Table, Tag, Space, message } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  FireOutlined,
  LineChartOutlined,
  ReloadOutlined,
  DownloadOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';

// API 请求函数
const apiRequest = async (method, url, data = null) => {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  if (data) {
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  return await response.json();
};

// 用户行为分析仪表板组件
function UserBehaviorDashboard() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [interestRanking, setInterestRanking] = useState([]);
  const [userList, setUserList] = useState([]);
  const [distributionData, setDistributionData] = useState([]);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '', captcha: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [showCaptcha, setShowCaptcha] = useState(false);
  const trendChartRef = useRef(null);
  const distributionChartRef = useRef(null);

  // 检查管理员登录状态
  useEffect(() => {
    checkAdminStatus();
  }, []);

  // 页面加载后自动刷新数据
  useEffect(() => {
    if (isLoggedIn) {
      refreshAllData();
    }
  }, [isLoggedIn]);

  const checkAdminStatus = async () => {
    try {
      const response = await apiRequest('get', '/api/admin/check');
      if (response.is_admin) {
        setCurrentUser(response);
        setIsLoggedIn(true);
      } else {
        setShowLoginModal(true);
      }
    } catch (error) {
      console.error('检查登录状态失败:', error);
      setShowLoginModal(true);
    }
  };

  const refreshAllData = () => {
    loadStats();
    loadTrendData();
    loadInterestRanking();
    loadUserList();
    loadDistributionData();
  };

  const loadStats = async () => {
    try {
      const response = await apiRequest('get', '/api/user/behavior/stats/global');
      if (response.success) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  const loadTrendData = async () => {
    try {
      const response = await apiRequest('get', '/api/user/behavior/trend?days=7');
      if (response.success && response.chart_data) {
        setTrendData(response.chart_data);
      }
    } catch (error) {
      console.error('加载趋势数据失败:', error);
    }
  };

  const loadInterestRanking = async () => {
    try {
      const response = await apiRequest('get', '/api/user/interests/categories');
      if (response.success && response.categories) {
        const sorted = response.categories
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);
        setInterestRanking(sorted);
      }
    } catch (error) {
      console.error('加载兴趣排行失败:', error);
    }
  };

  const loadUserList = async () => {
    try {
      const response = await apiRequest('get', '/api/user/behavior/stats/global');
      if (response.success) {
        if (response.stats.active_users_list && response.stats.active_users_list.length > 0) {
          setUserList(response.stats.active_users_list.slice(0, 10));
        } else {
          setUserList([]);
        }
      }
    } catch (error) {
      console.error('加载用户列表失败:', error);
    }
  };

  const loadDistributionData = async () => {
    try {
      const response = await apiRequest('get', '/api/user/interests/categories');
      if (response.success && response.categories) {
        const sorted = response.categories
          .sort((a, b) => b.count - a.count)
          .slice(0, 8);
        setDistributionData(sorted);
      }
    } catch (error) {
      console.error('加载分布数据失败:', error);
    }
  };

  const handleLogin = async () => {
    setLoginLoading(true);
    try {
      const requestBody = {
        username: loginForm.username,
        password: loginForm.password,
      };
      if (loginForm.captcha) {
        requestBody.captcha = loginForm.captcha;
      }

      const response = await apiRequest('post', '/api/admin/login', requestBody);

      if (response.success) {
        setCurrentUser(response);
        setIsLoggedIn(true);
        setShowLoginModal(false);
        message.success('登录成功');
        setLoginForm({ username: '', password: '', captcha: '' });
        setShowCaptcha(false);
        refreshAllData();
      } else if (response.captcha_required) {
        setShowCaptcha(true);
        message.warning('需要验证码');
      } else {
        message.error(response.error || '登录失败');
      }
    } catch (error) {
      message.error('登录失败：' + error.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiRequest('post', '/api/admin/logout');
    } catch (error) {
      console.error('登出失败:', error);
    }
    setCurrentUser(null);
    setIsLoggedIn(false);
    setStats(null);
    setTrendData(null);
    setInterestRanking([]);
    setUserList([]);
    setDistributionData([]);
    message.info('已退出登录');
  };

  const handleGoBack = () => {
    window.location.href = '/admin';
  };

  // 趋势图表配置
  const getTrendOption = () => {
    if (!trendData) return {};
    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        textStyle: { color: '#fff' },
      },
      legend: {
        data: ['点击', '浏览', '搜索', '收藏'],
        textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
        bottom: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trendData.dates || [],
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.3)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.7)' },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.3)' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.7)' },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      },
      series: trendData.series || [],
    };
  };

  // 分布图配置
  const getDistributionOption = () => {
    if (!distributionData || distributionData.length === 0) return {};
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        textStyle: { color: '#fff' },
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: 'rgba(26, 26, 46, 0.5)',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 18,
              fontWeight: 'bold',
              color: '#fff',
            },
          },
          labelLine: {
            show: false,
          },
          data: distributionData.map((item) => ({
            value: item.count,
            name: item.name,
          })),
        },
      ],
    };
  };

  // 用户列表表格列定义
  const userColumns = [
    {
      title: '用户',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600,
              fontSize: 16,
              color: '#fff',
            }}
          >
            {(name || record.user_id || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600 }}>{name || `用户 ${record.user_id}`}</div>
            <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.5)' }}>
              {record.action_count || 0} 次行为 · {record.interests_count || 0} 个兴趣
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <a
          onClick={() =>
            window.open(
              '/interest-graph?user_id=' + encodeURIComponent(record.user_id),
              '_blank'
            )
          }
        >
          查看详情 ›
        </a>
      ),
    },
  ];

  // 渲染登录模态框
  if (showLoginModal) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
      >
        <div
          style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            borderRadius: 16,
            padding: 40,
            width: '100%',
            maxWidth: 400,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
          }}
        >
          <h2
            style={{
              textAlign: 'center',
              marginBottom: 30,
              fontSize: 24,
              background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            🔐 管理员登录
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 14,
                  color: 'rgba(255, 255, 255, 0.7)',
                  marginBottom: 8,
                }}
              >
                用户名
              </label>
              <input
                type="text"
                placeholder="请输入用户名"
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                style={{
                  padding: 12,
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#fff',
                  fontSize: 14,
                  width: '100%',
                }}
              />
            </div>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 14,
                  color: 'rgba(255, 255, 255, 0.7)',
                  marginBottom: 8,
                }}
              >
                密码
              </label>
              <input
                type="password"
                placeholder="请输入密码"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                style={{
                  padding: 12,
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 8,
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#fff',
                  fontSize: 14,
                  width: '100%',
                }}
              />
            </div>
            {showCaptcha && (
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: 14,
                    color: 'rgba(255, 255, 255, 0.7)',
                    marginBottom: 8,
                  }}
                >
                  验证码（4 位数字）
                </label>
                <input
                  type="text"
                  placeholder="请输入验证码"
                  maxLength="4"
                  value={loginForm.captcha}
                  onChange={(e) => setLoginForm({ ...loginForm, captcha: e.target.value })}
                  style={{
                    padding: 12,
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 8,
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: '#fff',
                    fontSize: 14,
                    width: '100%',
                  }}
                />
              </div>
            )}
            <button
              onClick={handleLogin}
              disabled={loginLoading}
              style={{
                padding: 14,
                background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 16,
                fontWeight: 600,
                cursor: loginLoading ? 'not-allowed' : 'pointer',
                opacity: loginLoading ? 0.5 : 1,
                marginTop: 10,
              }}
            >
              {loginLoading ? '登录中...' : '登录'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 未登录时不显示内容
  if (!isLoggedIn) {
    return null;
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 顶部操作栏 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Button onClick={handleGoBack} icon={<ArrowLeftOutlined />}>
          返回管理后台
        </Button>
        <Space>
          {currentUser && (
            <Space style={{ marginRight: 16 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: 14,
                  color: '#fff',
                }}
              >
                {(currentUser.name || currentUser.username).charAt(0).toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 600 }}>
                  {currentUser.name || currentUser.username}
                </div>
                <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.5)' }}>管理员</div>
              </div>
            </Space>
          )}
          <Button onClick={refreshAllData} icon={<ReloadOutlined />}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />} onClick={() => message.info('导出功能开发中...')}>
            导出
          </Button>
          <Button onClick={handleLogout}>退出</Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={20} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃用户数"
              value={stats?.active_users || 0}
              prefix="👥"
              valueStyle={{
                background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                fontSize: 32,
                fontWeight: 700,
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日行为数"
              value={stats?.today_actions || 0}
              prefix="📝"
              valueStyle={{
                background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                fontSize: 32,
                fontWeight: 700,
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="热门兴趣 TOP3"
              value={
                stats?.top_interests && stats.top_interests.length > 0
                  ? stats.top_interests.slice(0, 3).map((i) => i.keyword).join(', ')
                  : '-'
              }
              prefix="🔥"
              suffix={<Tag color="green">实时更新</Tag>}
              valueStyle={{
                fontSize: 16,
                fontWeight: 600,
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="用户留存率"
              value={stats?.retention_rate || 0}
              suffix="%"
              prefix="📈"
              valueStyle={{
                background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                fontSize: 32,
                fontWeight: 700,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容区 */}
      <Row gutter={20} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="📊 行为趋势">
            {trendData ? (
              <ReactECharts
                option={getTrendOption()}
                style={{ height: 400 }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: 400,
                  color: 'rgba(0,0,0,0.5)',
                }}
              >
                加载中...
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="🔥 热门兴趣排行">
            {interestRanking.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {interestRanking.map((item, index) => {
                  let rankColor = '';
                  if (index === 0) rankColor = 'linear-gradient(90deg, #FFD700, #FFA500)';
                  else if (index === 1)
                    rankColor = 'linear-gradient(90deg, #C0C0C0, #A8A8A8)';
                  else if (index === 2)
                    rankColor = 'linear-gradient(90deg, #CD7F32, #B87333)';
                  else rankColor = 'linear-gradient(90deg, #4CAF50, #2196F3)';

                  return (
                    <div
                      key={item.name}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        padding: 12,
                        background: 'rgba(0, 0, 0, 0.03)',
                        borderRadius: 8,
                      }}
                    >
                      <div
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          background: rankColor,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: 12,
                          color: '#fff',
                        }}
                      >
                        {index + 1}
                      </div>
                      <div style={{ flex: 1, fontSize: 14 }}>{item.name}</div>
                      <div style={{ fontWeight: 600, color: '#4CAF50' }}>
                        {item.count} 人
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: 300,
                  color: 'rgba(0,0,0,0.5)',
                }}
              >
                暂无数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 用户列表和分布 */}
      <Row gutter={20}>
        <Col xs={24} lg={16}>
          <Card title="👥 活跃用户">
            {userList.length > 0 ? (
              <Table
                columns={userColumns}
                dataSource={userList.map((user, index) => ({
                  ...user,
                  key: user.user_id || index,
                }))}
                pagination={false}
                onRow={(record) => ({
                  style: { cursor: 'pointer' },
                  onClick: () =>
                    window.open(
                      '/interest-graph?user_id=' + encodeURIComponent(record.user_id),
                      '_blank'
                    ),
                })}
              />
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: 300,
                  color: 'rgba(0,0,0,0.5)',
                }}
              >
                暂无活跃用户
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="🎯 兴趣分布">
            {distributionData.length > 0 ? (
              <ReactECharts
                option={getDistributionOption()}
                style={{ height: 400 }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: 400,
                  color: 'rgba(0,0,0,0.5)',
                }}
              >
                暂无数据
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default UserBehaviorDashboard;
