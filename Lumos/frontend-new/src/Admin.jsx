import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { apiRequest } from './services/api.js';
import { useToast } from './hooks/useToast.js';
import './App.css';
import './index.css';

// 管理后台组件
function Admin() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [pushRules, setPushRules] = useState([]);
  const [loadingRules, setLoadingRules] = useState(false);
  const [showAddRule, setShowAddRule] = useState(false);
  const [newRule, setNewRule] = useState({
    keywords: '',
    channels: '',
    priority: 'normal',
    push_enabled: true,
  });
  const [stats, setStats] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [isRunningCrawlers, setIsRunningCrawlers] = useState(false);
  const [crawlerResult, setCrawlerResult] = useState(null);

  const { success, error, info, ToastContainer } = useToast();

  // 检查管理员登录状态
  useEffect(() => {
    const storedAdmin = localStorage.getItem('admin_logged_in');
    if (storedAdmin === 'true') {
      setIsLoggedIn(true);
      fetchStats();
      fetchPushRules();
      fetchSchedulerStatus();
    }
  }, []);

  // 获取定时任务状态
  const fetchSchedulerStatus = async () => {
    try {
      const response = await apiRequest('get', '/scheduler/status');
      setSchedulerStatus(response);
    } catch (err) {
      console.error('获取调度器状态失败:', err);
    }
  };

  // 立即运行爬虫
  const handleRunCrawlers = async () => {
    if (!confirm('确定要立即运行爬虫吗？这可能会消耗一些系统资源。')) {
      return;
    }

    setIsRunningCrawlers(true);
    setCrawlerResult(null);

    try {
      const response = await apiRequest('post', '/crawlers/run');
      setCrawlerResult(response);
      if (response.status === 'success' || response.status === 'partial') {
        success('爬虫执行完成！');
        fetchStats(); // 更新统计
        fetchSchedulerStatus(); // 更新状态
      } else {
        error(response.message || '爬虫执行失败');
      }
    } catch (err) {
      error('爬虫执行失败，请稍后重试');
      console.error('爬虫执行失败:', err);
    } finally {
      setIsRunningCrawlers(false);
    }
  };

  // 管理员登录
  const handleAdminLogin = async () => {
    if (!adminUsername || !adminPassword) {
      error('请输入用户名和密码');
      return;
    }
    try {
      const response = await apiRequest('post', '/admin/login', {
        username: adminUsername,
        password: adminPassword,
      });
      if (response.success) {
        localStorage.setItem('admin_logged_in', 'true');
        localStorage.setItem('admin_username', adminUsername);
        // 保存 admin token（如果后端返回）
        if (response.token) {
          localStorage.setItem('admin_token', response.token);
        }
        setIsLoggedIn(true);
        success('管理员登录成功');
        fetchStats();
        fetchPushRules();
      } else {
        error(response.message || '登录失败');
      }
    } catch (err) {
      error('登录失败，请检查用户名和密码');
    }
  };

  // 管理员登出
  const handleAdminLogout = async () => {
    try {
      await apiRequest('post', '/admin/logout');
    } catch (err) {
      // 忽略登出错误
    }
    localStorage.removeItem('admin_logged_in');
    localStorage.removeItem('admin_username');
    localStorage.removeItem('admin_token');
    setIsLoggedIn(false);
    success('已退出登录');
  };

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const response = await apiRequest('get', '/stats');
      setStats({
        total_users: response.total_users || 0,
        total_news: response.total_news || 0,
        push_rules_count: response.push_rules_count || 0,
        today_views: response.today_views || 0,
        latest_published: response.latest_published || '-',
      });
    } catch (err) {
      console.error('获取统计数据失败:', err);
    }
  };

  // 获取推送规则列表
  const fetchPushRules = async () => {
    setLoadingRules(true);
    try {
      const response = await apiRequest('get', '/push/rules');
      // API 返回的是数组
      setPushRules(Array.isArray(response) ? response : []);
    } catch (err) {
      error('获取推送规则失败');
      console.error('获取推送规则失败:', err);
      setPushRules([]);
    } finally {
      setLoadingRules(false);
    }
  };

  // 添加推送规则
  const handleAddRule = async () => {
    if (!newRule.keywords) {
      error('请输入关键词');
      return;
    }
    try {
      const keywords = newRule.keywords.split(',').map(k => k.trim()).filter(k => k);

      await apiRequest('post', '/push/rules', {
        rule_name: `规则-${new Date().toLocaleDateString()}`,
        keywords,
        hot_threshold: 90,
        enabled: newRule.push_enabled,
      });
      success('推送规则添加成功');
      setShowAddRule(false);
      setNewRule({ keywords: '', channels: '', priority: 'normal', push_enabled: true });
      fetchPushRules();
      fetchStats(); // 更新统计
    } catch (err) {
      error('添加推送规则失败');
      console.error('添加推送规则失败:', err);
    }
  };

  // 删除推送规则
  const handleDeleteRule = async (ruleId) => {
    if (!confirm('确定要删除这条推送规则吗？')) {
      return;
    }
    try {
      await apiRequest('delete', `/push/rules/${ruleId}`);
      success('推送规则已删除');
      fetchPushRules();
      fetchStats(); // 更新统计
    } catch (err) {
      error('删除推送规则失败');
      console.error('删除推送规则失败:', err);
    }
  };

  // 切换推送规则启用状态
  const toggleRuleEnabled = async (ruleId, currentEnabled) => {
    try {
      await apiRequest('put', `/push/rules/${ruleId}`, {
        enabled: !currentEnabled,
      });
      success('规则状态已更新');
      fetchPushRules();
      fetchStats(); // 更新统计
    } catch (err) {
      error('更新规则状态失败');
      console.error('更新规则状态失败:', err);
    }
  };

  // 未登录时显示登录界面
  if (!isLoggedIn) {
    return (
      <div className="login-wrapper">
        <div className="login-container" style={{ maxWidth: '400px' }}>
          <div className="login-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1>Lumos 管理后台</h1>
          <p className="login-subtitle">管理员登录</p>

          <div className="form-group">
            <label className="form-label">管理员账号</label>
            <input
              type="text"
              placeholder="请输入管理员账号"
              value={adminUsername}
              onChange={(e) => setAdminUsername(e.target.value)}
              className="input-field"
              style={{ color: '#2D2D2D', backgroundColor: '#fff' }}
            />
          </div>

          <div className="form-group">
            <label className="form-label">密码</label>
            <input
              type="password"
              placeholder="请输入密码"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              className="input-field"
              style={{ color: '#2D2D2D', backgroundColor: '#fff' }}
            />
          </div>

          <button onClick={handleAdminLogin} className="btn-login" style={{ marginTop: '20px' }}>
            登录
          </button>

          <div className="login-toggle" style={{ marginTop: '20px' }}>
            <span>powered by Lumos AI</span>
          </div>
        </div>
      </div>
    );
  }

  // 已登录时显示管理后台
  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>Lumos 管理后台</h1>
          <div className="header-actions">
            <a href="/" target="_blank" rel="noopener noreferrer" className="btn btn-outline" style={{ marginRight: '10px' }}>
              用户端 →
            </a>
            <button onClick={handleAdminLogout} className="btn btn-outline">
              登出
            </button>
          </div>
        </div>
      </header>

      <main className="App-main">
        {/* 统计概览 */}
        <section className="section">
          <h2>数据概览</h2>
          <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
            <div className="stat-card" style={{ padding: '24px', background: 'linear-gradient(135deg, #e85d3f 0%, #f0937e 100%)', borderRadius: '12px', color: 'white' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats?.total_users || '-'}</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>总用户数</div>
            </div>
            <div className="stat-card" style={{ padding: '24px', background: 'linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)', borderRadius: '12px', color: 'white' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats?.total_news || '-'}</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>新闻总数</div>
            </div>
            <div className="stat-card" style={{ padding: '24px', background: 'linear-gradient(135deg, #00b894 0%, #55efc4 100%)', borderRadius: '12px', color: 'white' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats?.push_rules_count || '-'}</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>推送规则</div>
            </div>
            <div className="stat-card" style={{ padding: '24px', background: 'linear-gradient(135deg, #fd79a8 0%, #fab1c0 100%)', borderRadius: '12px', color: 'white' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats?.today_views || '-'}</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>今日浏览</div>
            </div>
          </div>
        </section>

        {/* 推送规则管理 */}
        <section className="section">
          <div className="section-header">
            <h2>推送规则管理</h2>
            <button onClick={() => setShowAddRule(!showAddRule)} className="btn btn-primary">
              {showAddRule ? '取消添加' : '+ 添加规则'}
            </button>
          </div>

          {/* 添加规则表单 */}
          {showAddRule && (
            <div className="add-rule-form" style={{ marginTop: '20px', padding: '20px', background: '#f9f9f9', borderRadius: '8px' }}>
              <div className="form-group" style={{ marginBottom: '15px' }}>
                <label className="form-label">关键词（逗号分隔）</label>
                <input
                  type="text"
                  placeholder="例如：AI, 人工智能，大模型"
                  value={newRule.keywords}
                  onChange={(e) => setNewRule({ ...newRule, keywords: e.target.value })}
                  className="input-field"
                  style={{ width: '100%', color: '#2D2D2D', backgroundColor: '#fff' }}
                />
              </div>
              <div className="form-group" style={{ marginBottom: '15px' }}>
                <label className="form-label">推送渠道（逗号分隔，留空表示全部）</label>
                <input
                  type="text"
                  placeholder="例如：wechat, email"
                  value={newRule.channels}
                  onChange={(e) => setNewRule({ ...newRule, channels: e.target.value })}
                  className="input-field"
                  style={{ width: '100%', color: '#2D2D2D', backgroundColor: '#fff' }}
                />
              </div>
              <div className="form-group" style={{ marginBottom: '15px' }}>
                <label className="form-label">优先级</label>
                <select
                  value={newRule.priority}
                  onChange={(e) => setNewRule({ ...newRule, priority: e.target.value })}
                  className="input-field"
                  style={{ width: '100%', color: '#2D2D2D', backgroundColor: '#fff' }}
                >
                  <option value="low">低</option>
                  <option value="normal">普通</option>
                  <option value="high">高</option>
                  <option value="urgent">紧急</option>
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={newRule.push_enabled}
                    onChange={(e) => setNewRule({ ...newRule, push_enabled: e.target.checked })}
                    style={{ marginRight: '8px' }}
                  />
                  启用推送
                </label>
              </div>
              <button onClick={handleAddRule} className="btn btn-primary">保存规则</button>
            </div>
          )}

          {/* 规则列表 */}
          {loadingRules ? (
            <div className="loading">加载中...</div>
          ) : pushRules.length > 0 ? (
            <div className="rules-list" style={{ marginTop: '20px' }}>
              {pushRules.map((rule, index) => (
                <div key={rule.id || index} className="rule-card" style={{ padding: '16px', marginBottom: '12px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                      <span style={{ marginRight: '8px' }}>{rule.enabled ? '✅' : '⏸️'}</span>
                      {rule.rule_name || '未命名规则'}
                    </div>
                    <div style={{ fontSize: '13px', color: '#666' }}>
                      关键词：{rule.keywords?.join(', ') || '无'} | 热度阈值：{rule.hot_threshold || 90}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={() => toggleRuleEnabled(rule.id, rule.enabled)} className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '13px' }}>
                      {rule.enabled ? '禁用' : '启用'}
                    </button>
                    <button onClick={() => handleDeleteRule(rule.id)} className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '13px', color: '#e85d3f', borderColor: '#e85d3f' }}>
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ marginTop: '20px' }}>
              <p>暂无推送规则，点击右上角添加规则</p>
            </div>
          )}
        </section>

        {/* 用户行为分析入口 */}
        <section className="section">
          <h2>数据分析</h2>
          <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            <div
              onClick={() => { window.location.href = '/admin/behavior'; }}
              className="stat-card"
              style={{ padding: '24px', background: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)', borderRadius: '12px', color: 'white', cursor: 'pointer' }}
            >
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>📊 用户行为分析</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>查看用户浏览、点击等行为数据</div>
            </div>
            <div
              onClick={() => { window.location.href = '/admin/interest-graph'; }}
              className="stat-card"
              style={{ padding: '24px', background: 'linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%)', borderRadius: '12px', color: 'white', cursor: 'pointer' }}
            >
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>🕸️ 兴趣图谱</div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>可视化展示用户兴趣关系网络</div>
            </div>
          </div>
        </section>

        {/* 数据采集管理 */}
        <section className="section">
          <h2>数据采集管理</h2>

          {/* 定时任务状态 */}
          <div style={{ marginTop: '20px', padding: '20px', background: '#f9f9f9', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '15px', fontSize: '16px' }}>⏰ 定时任务状态</h3>
            {schedulerStatus ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontSize: '24px', marginRight: '10px' }}>
                    {schedulerStatus.scheduler?.running ? '🟢' : '🔴'}
                  </span>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>
                      {schedulerStatus.scheduler?.running ? '运行中' : '已停止'}
                    </div>
                    {schedulerStatus.scheduler?.pid && (
                      <div style={{ fontSize: '13px', color: '#666' }}>
                        进程 ID: {schedulerStatus.scheduler.pid}
                      </div>
                    )}
                  </div>
                </div>

                {schedulerStatus.scheduler?.last_run_time && (
                  <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>
                    最近执行：{schedulerStatus.scheduler.last_run_time}
                    {schedulerStatus.scheduler.last_run_result && (
                      <span style={{ marginLeft: '8px' }}>
                        {schedulerStatus.scheduler.last_run_result === 'success' ? '✅' : '❌'}
                      </span>
                    )}
                  </div>
                )}

                <div style={{ marginTop: '15px', padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                  <div style={{ fontSize: '13px', marginBottom: '8px' }}><strong>📰 新闻采集：</strong>每 10 分钟一次</div>
                  <div style={{ fontSize: '13px', marginBottom: '8px' }}><strong>🔄 推荐更新：</strong>每小时一次</div>
                  <div style={{ fontSize: '13px', marginBottom: '8px' }}><strong>🧹 数据清理：</strong>每天 02:00</div>
                  <div style={{ fontSize: '13px' }}><strong>📊 健康检查：</strong>每天 09:00</div>
                </div>
              </div>
            ) : (
              <div className="loading">加载状态中...</div>
            )}
          </div>

          {/* 手动运行爬虫 */}
          <div style={{ marginTop: '20px', padding: '20px', background: '#f9f9f9', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '15px', fontSize: '16px' }}>🚀 手动采集</h3>
            <p style={{ fontSize: '13px', color: '#666', marginBottom: '15px' }}>
              立即运行所有爬虫（今日头条、微博热搜、知乎热榜、百度热搜、B 站热搜、36 氪科技）
            </p>
            <button
              onClick={handleRunCrawlers}
              disabled={isRunningCrawlers}
              className="btn btn-primary"
              style={{ opacity: isRunningCrawlers ? 0.7 : 1, cursor: isRunningCrawlers ? 'not-allowed' : 'pointer' }}
            >
              {isRunningCrawlers ? '⏳ 运行中...' : '▶️ 立即运行爬虫'}
            </button>

            {/* 运行结果 */}
            {crawlerResult && (
              <div style={{ marginTop: '15px', padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>执行状态：</strong>
                  <span style={{ marginLeft: '8px', color: crawlerResult.status === 'success' ? '#00b894' : '#e85d3f' }}>
                    {crawlerResult.status === 'success' ? '✅ 成功' : crawlerResult.status === 'partial' ? '⚠️ 部分成功' : '❌ 失败'}
                  </span>
                </div>
                {crawlerResult.data && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px', marginBottom: '10px' }}>
                    <div style={{ padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{crawlerResult.data.total_saved || 0}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>新增新闻</div>
                    </div>
                    <div style={{ padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{crawlerResult.data.total_fetched || 0}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>获取总数</div>
                    </div>
                    <div style={{ padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                        {crawlerResult.results ? crawlerResult.results.filter(r => r.success).length : 0}/{crawlerResult.results?.length || 0}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>成功平台</div>
                    </div>
                  </div>
                )}
                {crawlerResult.output && (
                  <details style={{ marginTop: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#666' }}>查看执行日志</summary>
                    <pre style={{ marginTop: '10px', padding: '10px', background: '#2d2d2d', color: '#f8f8f2', borderRadius: '4px', fontSize: '11px', overflow: 'auto', maxHeight: '200px' }}>
                      {crawlerResult.output}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="App-footer">
        <p>© 2026 Lumos Platform - 管理后台</p>
      </footer>

      <ToastContainer />
    </div>
  );
}

export default Admin;

// 渲染管理后台
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Admin />);
