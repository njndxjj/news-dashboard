import React, { useState, useEffect } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  HomeOutlined,
  BarChartOutlined,
  FireOutlined,
  UserOutlined,
  BellOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import NewsList from '../components/NewsList.js';
import AIAnalysis from '../components/AIAnalysis.js';
import HotNews from '../components/HotNews.js';
import UserInterests from '../components/UserInterests.js';
import PushManagement from '../components/PushManagement.js';
import Recommendation from '../components/Recommendation.js';
import './App.css';

const { Header, Content, Sider } = Layout;

// 菜单项配置
const menuItems = [
  {
    key: 'news',
    icon: <HomeOutlined />,
    label: '新闻舆情',
  },
  {
    key: 'hot',
    icon: <FireOutlined />,
    label: '热点榜单',
  },
  {
    key: 'analysis',
    icon: <BarChartOutlined />,
    label: 'AI 分析',
  },
  {
    key: 'recommendation',
    icon: <ThunderboltOutlined />,
    label: '智能推荐',
  },
  {
    key: 'interests',
    icon: <UserOutlined />,
    label: '兴趣管理',
  },
  {
    key: 'push',
    icon: <BellOutlined />,
    label: '推送管理',
  },
];

function App() {
  const [current, setCurrent] = useState('news');
  const [collapsed, setCollapsed] = useState(false);

  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 渲染页面内容
  const renderContent = () => {
    switch (current) {
      case 'news':
        return <NewsList />;
      case 'hot':
        return <HotNews />;
      case 'analysis':
        return <AIAnalysis />;
      case 'recommendation':
        return <Recommendation />;
      case 'interests':
        return <UserInterests />;
      case 'push':
        return <PushManagement />;
      default:
        return <NewsList />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: colorBgContainer,
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <div style={{ fontSize: '20px', fontWeight: 'bold', marginRight: '24px' }}>
          🔍 Lumos 舆情监控系统
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: '14px', color: '#666' }}>
          智能 · 实时 · 精准
        </div>
      </Header>
      <Layout>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          theme="light"
          style={{
            background: colorBgContainer,
            borderRight: '1px solid #f0f0f0',
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[current]}
            items={menuItems}
            onClick={({ key }) => setCurrent(key)}
            style={{ borderInlineEnd: 'none' }}
          />
        </Sider>
        <Content
          style={{
            padding: '24px',
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            margin: '16px',
          }}
        >
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
