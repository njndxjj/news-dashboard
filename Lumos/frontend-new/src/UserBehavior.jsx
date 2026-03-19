import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import UserBehaviorDashboard from './components/UserBehaviorDashboard';
import './index.css';
import './App.css';

// 用户行为分析页面容器
function UserBehaviorPage() {
  const handleGoBack = () => {
    window.location.href = '/admin';
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h1>Lumos 管理后台</h1>
            <span style={{ color: 'rgba(255,255,255,0.65)' }}>/</span>
            <span style={{ color: 'rgba(255,255,255,0.85)' }}>用户行为分析</span>
          </div>
          <div className="header-actions">
            <button onClick={handleGoBack} className="btn btn-outline">
              ← 返回管理后台
            </button>
          </div>
        </div>
      </header>

      <main className="App-main">
        <ConfigProvider locale={zhCN}>
          <UserBehaviorDashboard />
        </ConfigProvider>
      </main>

      <footer className="App-footer">
        <p>© 2026 Lumos Platform - 用户行为分析</p>
      </footer>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<UserBehaviorPage />);
