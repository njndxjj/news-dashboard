import React, { useState, useEffect } from 'react';
import { apiRequest } from './services/api.js';
import { useToast } from './hooks/useToast.js';
import { trackPageView } from './utils/tracking.js';
import UserBehaviorDashboard from './components/UserBehaviorDashboard.js';
import './App.css';

// 预设兴趣标签（来自数据库设计）
const PRESET_INTEREST_CATEGORIES = {
  "科技领域": ["创业", "startups", "融资", "风险投资", "天使投资", "孵化器", "加速器", "科技创新", "硬科技", "科创", "科技创业", "创始人", "CEO", "科技融资", "科技投资", "股权投资", "Pre-A 轮", "A 轮", "B 轮", "C 轮", "D 轮", "IPO", "上市", "科创板", "创业板"],
  "宏观政策": ["政策", "法规", "税收", "补贴", "监管", "产业支持", "专精特新", "中小企业", "营商环境", "外贸", "出口", "进口", "关税", "信贷", "融资支持"],
  "行业趋势": ["转型", "数字化", "智能化", "升级", "创新", "技术突破", "国产替代", "供应链", "产业链", "产业集群", "行业报告", "市场分析", "竞争格局"],
  "经营管理": ["管理", "组织", "人才", "招聘", "培训", "绩效", "激励", "股权", "薪酬", "企业文化", "团队建设", "领导力", "战略", "商业模式"],
  "市场营销": ["营销", "品牌", "渠道", "客户", "销售", "推广", "获客", "私域", "直播", "电商", "跨境电商", "展会", "招商", "经销商", "代理商"],
  "财税金融": ["财税", "税务", "发票", "审计", "会计", "贷款", "融资", "银行", "担保", "保险", "理财", "现金流", "成本控制", "预算", "上市", "IPO", "新三板"],
  "法律合规": ["法律", "合规", "合同", "劳动", "知识产权", "专利", "商标", "诉讼", "仲裁", "工商", "质检", "环保", "安全生产", "数据合规"],
  "技术升级": ["自动化", "机器人", "智能制造", "工业互联网", "物联网", "5G", "云计算", "AI 应用", "数字化转型", "MES", "ERP", "信息化", "设备升级"],
  "供应链": ["供应链", "采购", "供应商", "物流", "仓储", "库存", "配送", "跨境电商物流", "冷链", "原材料", "价格上涨", "缺货", "产能"],
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [uniqueId, setUniqueId] = useState(null);
  const [isGuest, setIsGuest] = useState(true);
  const [username, setUsername] = useState('');
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [keywords, setKeywords] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('科技领域');
  const [insights, setInsights] = useState(null);
  const [news, setNews] = useState([]);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loadingNews, setLoadingNews] = useState(false);
  const [showSubscribe, setShowSubscribe] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [showBehaviorDashboard, setShowBehaviorDashboard] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false); // 防止重复点击登录按钮

  // Toast 通知
  const { success, error, info, ToastContainer } = useToast();

  // 页面浏览埋点
  useEffect(() => {
    trackPageView('home', {
      unique_id: uniqueId || 'guest',
      is_logged_in: isLoggedIn,
    });
  }, []);

  // 检查是否已登录
  useEffect(() => {
    const storedId = localStorage.getItem('unique_id');
    if (storedId) {
      setUniqueId(storedId);
      setIsLoggedIn(true);
      loadUserSubscriptions(storedId);
    }
  }, []);

  // 页面加载后自动获取 AI 分析和推荐新闻（首次访问自动触发）
  useEffect(() => {
    const storedId = localStorage.getItem('unique_id');
    const hasAutoTriggered = localStorage.getItem('has_auto_triggered');

    console.log('[自动触发检查] isLoggedIn:', isLoggedIn, 'storedId:', storedId, 'hasAutoTriggered:', hasAutoTriggered, 'keywords:', keywords, 'hasInitialized:', hasInitialized);

    // 如果是未登录用户首次访问，使用默认 AI 关键词并自动获取
    if (!storedId && !hasAutoTriggered) {
      const defaultKeywords = ['AI', '人工智能', '大模型', 'AIGC', '机器学习'];
      setKeywords(defaultKeywords);
      localStorage.setItem('has_auto_triggered', 'true');

      console.log('[初始化] 未登录用户，默认选中 AI 关键词:', defaultKeywords);

      // 设置关键词后，keywords 变化会重新触发这个 useEffect，那时再调用 API
      return;
    }

    // 已登录用户或有关键词时，自动触发 API（不再依赖 hasInitialized，改为检查是否已设置 keywords）
    if (keywords.length > 0 && !hasInitialized) {
      console.log('[自动触发] 关键词已就绪，开始获取 AI 分析和推荐新闻');
      setHasInitialized(true);
      setTimeout(() => {
        fetchInsights(true); // 使用 silent = true 避免失败时弹 toast
        fetchNews(true);     // 使用 silent = true 避免失败时弹 toast
      }, 500);
    }
  }, [isLoggedIn, keywords, hasInitialized]);

  // 加载用户订阅（从后端 API 获取）
  const loadUserSubscriptions = async (id, force = false) => {
    // 防止重复加载
    if (!force && keywords.length > 0) {
      console.log('[订阅加载] 已加载过订阅数据，跳过重复加载');
      return;
    }

    try {
      const response = await apiRequest('get', `/users/subscriptions?user_id=${id}`);
      const userKeywords = response?.keywords || [];
      const isDefault = response?.is_default || false;
      console.log('[订阅加载] 用户订阅数据:', userKeywords, '是否默认:', isDefault);

      // 如果用户订阅为空，使用默认关键词
      if (userKeywords.length === 0) {
        const defaultKeywords = PRESET_INTEREST_CATEGORIES['科技领域'].slice(0, 5);
        console.log('[订阅加载] 用户订阅为空，使用默认关键词:', defaultKeywords);
        setKeywords(defaultKeywords);
      } else {
        setKeywords(userKeywords);
      }

      setShowSubscribe(true);
      console.log('[订阅加载] 关键词已设置，将自动触发 AI 分析和推荐新闻');
    } catch (error) {
      console.error('获取订阅失败:', error);
      // 如果获取订阅失败（如 404），使用默认关键词
      const defaultKeywords = PRESET_INTEREST_CATEGORIES['科技领域'].slice(0, 5);
      setKeywords(defaultKeywords);
      setShowSubscribe(true);
      console.log('[订阅加载] 使用默认关键词:', defaultKeywords);
    }
  };

  // 处理登录（调用后端 API）
  const handleLogin = async () => {
    // 防止重复点击
    if (isLoggingIn) {
      console.log('[登录] 正在登录中，请勿重复点击');
      return;
    }

    setIsLoggingIn(true);
    console.log('[登录] 开始登录流程');

    try {
      if (isGuest) {
        // 游客登录：调用后端创建游客用户
        const response = await apiRequest('post', '/users/register', {
          username: 'Guest',
          phone: '',
          keywords: '',
        });
        console.log('[Login] 游客登录响应:', response);
        const { unique_id } = response;
        console.log('[Login] 获取到 unique_id:', unique_id);
        localStorage.setItem('unique_id', unique_id);
        setUniqueId(unique_id);
        setIsLoggedIn(true);
        setIsGuest(true);
        // 加载默认订阅数据
        loadUserSubscriptions(unique_id);
        success('游客登录成功！欢迎使用 Lumos 资讯平台。');
      } else {
        // 注册用户：调用后端注册接口，使用手机号 + 验证码
        const response = await apiRequest('post', '/users/register', {
          username,
          phone,
          verification_code: verificationCode,
        });
        console.log('[Login] 注册用户响应:', response);
        const { unique_id } = response;
        console.log('[Login] 获取到 unique_id:', unique_id);
        localStorage.setItem('unique_id', unique_id);
        setUniqueId(unique_id);
        setIsLoggedIn(true);
        // 加载默认订阅数据
        loadUserSubscriptions(unique_id);
        success(`欢迎 ${username}！注册成功。`);
      }
    } catch (error) {
      console.error('登录失败:', error);
      error('登录失败，请稍后重试');
    } finally {
      // 重置登录状态，允许再次点击
      setIsLoggingIn(false);
      console.log('[登录] 登录流程结束');
    }
  };

  // 发送验证码
  const handleSendCode = async () => {
    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(phone)) {
      error('请输入有效的 11 位手机号');
      return;
    }

    // 防止重复发送
    if (codeSent) {
      console.log('[发送验证码] 正在倒计时中，请勿重复发送');
      return;
    }

    try {
      const response = await apiRequest('post', '/users/send-code', {
        phone,
      });
      console.log('[发送验证码] 响应:', response);
      setCodeSent(true);
      success('验证码已发送，请注意查收');

      // 开始倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            setCodeSent(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      console.error('发送验证码失败:', error);
      error('发送验证码失败，请稍后重试');
    }
  };

  // 处理兴趣标签选择
  const handleSelectKeyword = (keyword) => {
    if (keywords.includes(keyword)) {
      setKeywords(keywords.filter(k => k !== keyword));
    } else {
      setKeywords([...keywords, keyword]);
    }
  };

  // 保存订阅（调用后端 API 保存到数据库）
  const handleSaveSubscriptions = async () => {
    if (keywords.length === 0) {
      error('请至少选择一个兴趣标签');
      return;
    }
    try {
      await apiRequest('put', `/users/subscriptions?user_id=${uniqueId}`, {
        keywords,
      });
      success('订阅保存成功！正在刷新 AI 总结和热点资讯...');
      setShowSubscribe(false);
      // 自动获取 AI 总结和推荐（异步刷新，不阻塞 UI）
      fetchInsights(false);
      fetchNews(false);
    } catch (error) {
      console.error('保存订阅失败:', error);
      error('保存失败，请稍后重试');
    }
  };

  // 获取 AI 行业总结
  const fetchInsights = async (silent = false) => {
    if (keywords.length === 0) {
      if (!silent) {
        error('请先选择兴趣标签');
      }
      return;
    }
    setLoadingInsights(true);
    try {
      const response = await apiRequest('post', '/analyze', { keywords });
      console.log('[AI 总结] 原始响应:', response);
      // apiRequest 已解包，response 即为 insights 对象
      const insightsData = response;
      console.log('[AI 总结] 解析后的数据:', insightsData);

      // 兼容两种后端返回格式：
      // 1. backend/app.py: { status: 'success', core_summary, trends, competitors, risks, opportunities_and_actions, analyzed_count }
      // 2. monitor_app.py: { summary, analysis_type, source, news_count, raw_data }
      const isValidData = insightsData && (
        (insightsData.status === 'success' && insightsData.core_summary) ||
        (insightsData.summary && insightsData.raw_data) ||
        (insightsData.core_summary)
      );

      if (isValidData) {
        // 如果是 monitor_app.py 格式，转换为 frontend 期望的格式
        if (insightsData.raw_data && !insightsData.status) {
          const rawData = insightsData.raw_data;
          const convertedData = {
            status: 'success',
            core_summary: rawData.executive_summary || insightsData.summary || '',
            // monitor_app.py 字段映射：trending_topics -> trends
            trends: rawData.trending_topics?.map(t => ({
              topic: t.topic,
              description: t.description,
              heat_level: t.heat_level,
              related_news_count: t.related_news_count
            })) || [],
            // monitor_app.py 字段映射：competitive_landscape -> competitors
            competitors: rawData.competitive_landscape?.map(c => ({
              company: c.company,
              key_move: c.key_move,
              our_response: c.our_response,
              strategic_intent: c.strategic_intent,
              threat_level: c.threat_level
            })) || [],
            // monitor_app.py 字段映射：risk_alerts -> risks
            risks: rawData.risk_alerts?.map(r => ({
              description: r.description,
              risk_type: r.risk_type,
              severity: r.severity,
              early_signals: r.early_signals,
              mitigation: r.mitigation
            })) || [],
            // monitor_app.py 字段映射：opportunities + recommended_actions -> opportunities_and_actions
            opportunities_and_actions: {
              opportunities: rawData.opportunities?.map(o => ({
                type: o.type,
                description: o.description,
                action: o.action,
                window: o.window
              })) || [],
              actions: rawData.recommended_actions?.map(a => ({
                action: a.action,
                owner: a.owner,
                priority: a.priority,
                timeline: a.timeline
              })) || []
            },
            analyzed_count: rawData.analyzed_news_count || rawData.news_count || insightsData.news_count || 0
          };
          setInsights(convertedData);
        } else {
          setInsights(insightsData);
        }
      } else {
        console.error('[AI 总结] 数据格式异常:', insightsData);
        if (!silent) {
          error('AI 分析数据格式异常');
        }
      }
    } catch (error) {
      console.error('获取洞察失败:', error);
      if (!silent) {
        error('获取洞察失败，请稍后重试');
      }
    } finally {
      setLoadingInsights(false);
    }
  };

  // 获取推荐新闻（热点资讯）
  const fetchNews = async (silent = false) => {
    setLoadingNews(true);
    try {
      // 热点资讯调用 /api/news 接口获取新闻列表
      const response = await apiRequest('get', '/news', { limit: 20 });
      console.log('[热点资讯] 原始响应:', response);

      // 后端返回格式：{ news: [...] } 或直接返回数组
      let newsData = response?.news || response?.data || response || [];

      // 如果是对象包含 news 数组，提取出来
      if (!Array.isArray(newsData) && response?.news && Array.isArray(response.news)) {
        newsData = response.news;
      }

      console.log('[热点资讯] 解析后的数据:', newsData);

      if (Array.isArray(newsData)) {
        // 转换数据格式：确保 score 是数字类型
        const normalizedNews = newsData.map(item => ({
          ...item,
          score: typeof item.score === 'string' ? parseFloat(item.score) : (item.score || item.hot_score || 0)
        }));
        setNews(normalizedNews);
      } else {
        console.error('[热点资讯] 数据格式异常:', response);
        if (!silent) {
          error('热点资讯数据格式异常');
        }
        setNews([]);
      }
    } catch (error) {
      console.error('获取新闻失败:', error);
      if (!silent) {
        error('获取热点资讯失败，请稍后重试');
      }
      setNews([]);
    } finally {
      setLoadingNews(false);
    }
  };

  // 登出
  const handleLogout = () => {
    localStorage.removeItem('unique_id');
    setUniqueId(null);
    setIsLoggedIn(false);
    setKeywords([]);
    setInsights(null);
    setNews([]);
    setShowSubscribe(false);
  };

  // 未登录时显示登录界面
  if (!isLoggedIn) {
    return (
      <div className="login-wrapper">
        <div className="login-container">
          <div className="login-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1>Lumos Platform</h1>
          <p className="login-subtitle">智能资讯监控 · 洞察行业先机</p>

          {!isGuest && (
            <>
              <div className="form-group">
                <label className="form-label">用户名</label>
                <input
                  type="text"
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input-field"
                  style={{ color: '#2D2D2D', backgroundColor: '#fff' }}
                />
              </div>
              <div className="form-group">
                <label className="form-label">手机号</label>
                <input
                  type="tel"
                  placeholder="请输入 11 位手机号"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  maxLength={11}
                  className="input-field"
                  style={{ color: '#2D2D2D', backgroundColor: '#fff' }}
                />
              </div>
              <div className="form-group">
                <label className="form-label">验证码</label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    placeholder="请输入验证码"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    maxLength={6}
                    className="input-field"
                    style={{ color: '#2D2D2D', backgroundColor: '#fff', flex: 1 }}
                  />
                  <button
                    onClick={handleSendCode}
                    disabled={codeSent || countdown > 0}
                    className="btn btn-secondary"
                    style={{
                      minWidth: '120px',
                      opacity: codeSent || countdown > 0 ? 0.6 : 1,
                      cursor: codeSent || countdown > 0 ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {countdown > 0 ? `${countdown}秒后重试` : codeSent ? '已发送' : '获取验证码'}
                  </button>
                </div>
              </div>
            </>
          )}

          <div className="button-group">
            <button
              onClick={handleLogin}
              disabled={isLoggingIn}
              className="btn-login"
              style={{ opacity: isLoggingIn ? 0.6 : 1, cursor: isLoggingIn ? 'not-allowed' : 'pointer' }}
            >
              {isLoggingIn ? '登录中...' : (isGuest ? '游客登录' : '注册并登录')}
            </button>

            <div className="login-divider">
              <span>或者</span>
            </div>

            <button
              onClick={() => setIsGuest(!isGuest)}
              className="btn-guest"
            >
              {isGuest ? '使用账号登录' : '游客快速访问'}
            </button>
          </div>

          <div className="login-toggle">
            <span>powered by Lumos AI</span>
          </div>
        </div>
      </div>
    );
  }

  // 已登录时显示主界面
  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>Lumos Platform</h1>
          <div className="header-actions">
            <button onClick={() => setShowSubscribe(!showSubscribe)} className="btn btn-secondary">
              {showSubscribe ? '收起订阅' : '管理订阅'}
            </button>
            <button onClick={() => setShowBehaviorDashboard(!showBehaviorDashboard)} className="btn btn-secondary">
              📊 行为分析
            </button>
            <button onClick={handleLogout} className="btn btn-outline">
              登出
            </button>
          </div>
        </div>
      </header>

      <main className="App-main">
        {/* 用户行为分析看板 */}
        {showBehaviorDashboard && (
          <section className="section">
            <UserBehaviorDashboard />
          </section>
        )}

        {/* Hero Section - 首屏设计 */}
        <section className="hero-section">
          {/* 📋 核心摘要卡片 - 显示在 Hero Section 左侧 */}
          <div className="hero-summary-card">
            {insights?.core_summary ? (
              <>
                <div className="hero-summary-header">
                  <span className="hero-summary-icon">📋</span>
                  <h3>核心摘要</h3>
                </div>
                <p className="hero-summary-content">{insights.core_summary}</p>
              </>
            ) : (
              <>
                <div className="hero-summary-empty">
                  <svg viewBox="0 0 80 80" fill="none" stroke="currentColor" strokeWidth="1">
                    <circle cx="40" cy="40" r="30" strokeDasharray="4 2" />
                    <path d="M40 25v30M25 40h30" strokeLinecap="round" />
                    <circle cx="40" cy="40" r="8" fill="rgba(232, 93, 63, 0.1)" stroke="none" />
                  </svg>
                  <p>点击"生成行业总结"</p>
                  <p style={{ fontSize: '12px', marginTop: '8px' }}>查看核心摘要</p>
                </div>
              </>
            )}
          </div>

          <div className="hero-content">
            <h1 className="hero-title">
              <div className="hero-title-line1">智能资讯监控</div>
              <div className="hero-title-line2">洞察行业先机</div>
            </h1>
            <p className="hero-subtitle">
              掌握实时动态 · 把握发展趋势
            </p>

            <div className="hero-stats">
              <div className="stat-item">
                <span className="stat-number">9</span>
                <span className="stat-label">兴趣分类</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">100+</span>
                <span className="stat-label">关键词标签</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">实时</span>
                <span className="stat-label">数据更新</span>
              </div>
            </div>
          </div>
        </section>

        {/* 订阅管理模块 */}
        {showSubscribe && (
          <section className="section subscribe-section">
            <h2>订阅兴趣点</h2>
            <p className="section-desc">选择您关注的行业和话题，我们将为您推荐相关内容</p>
            <p className="section-hint">💡 已为您默认选中科技领域相关关键词</p>

            <div className="category-tabs">
              {Object.keys(PRESET_INTEREST_CATEGORIES).map(category => (
                <button
                  key={category}
                  className={`tab ${selectedCategory === category ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </button>
              ))}
            </div>

            <div className="keyword-grid">
              {PRESET_INTEREST_CATEGORIES[selectedCategory].map(keyword => (
                <button
                  key={keyword}
                  className={`keyword-tag ${keywords.includes(keyword) ? 'selected' : ''}`}
                  onClick={() => handleSelectKeyword(keyword)}
                >
                  {keyword}
                  {keywords.includes(keyword) && ' ✓'}
                </button>
              ))}
            </div>

            <div className="selected-keywords">
              <h4>已选择 ({keywords.length}):</h4>
              <div className="selected-tags">
                {keywords.map(keyword => (
                  <span key={keyword} className="selected-tag">
                    {keyword}
                    <button onClick={() => handleSelectKeyword(keyword)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <button onClick={handleSaveSubscriptions} className="btn btn-primary btn-large">
              保存订阅
            </button>
          </section>
        )}

        {/* AI 行业总结模块 */}
        <section className="section">
          <div className="section-header">
            <h2>AI 行业总结</h2>
            <button
              onClick={() => fetchInsights(false)}
              disabled={loadingInsights || keywords.length === 0}
              className="btn btn-primary"
            >
              {loadingInsights ? '分析中...' : '生成行业总结'}
            </button>
          </div>

          {insights ? (
            <div className="insights-container">
              {/* 🔍 趋势洞察 */}
              {insights.trends && insights.trends.length > 0 && (
                <div className="insight-card">
                  <h3>🔍 趋势洞察</h3>
                  <div className="trends-list">
                    {insights.trends.map((trend, idx) => (
                      <div key={idx} className="trend-item">
                        <div className="trend-header">
                          <span className="trend-title">{trend.title}</span>
                          <span className={`trend-priority priority-${trend.priority}`}>
                            {trend.priority === 'high' ? '🔴 高' : trend.priority === 'medium' ? '🟡 中' : '🟢 低'}
                          </span>
                        </div>
                        <p className="trend-description">{trend.description}</p>
                        <p className="trend-impact">{trend.impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 🏢 竞争情报 */}
              {insights.competitors && insights.competitors.length > 0 && (
                <div className="insight-card">
                  <h3>🏢 竞争情报</h3>
                  <div className="competitors-list">
                    {insights.competitors.map((comp, idx) => (
                      <div key={idx} className="competitor-item">
                        <div className="competitor-header">
                          <span className="competitor-company">{comp.company}</span>
                          <span className="competitor-action">{comp.action}</span>
                        </div>
                        <p className="competitor-impact">{comp.impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ⚠️ 风险预警 */}
              {insights.risks && insights.risks.length > 0 && (
                <div className="insight-card">
                  <h3>⚠️ 风险预警</h3>
                  <div className="risks-list">
                    {insights.risks.map((risk, idx) => (
                      <div key={idx} className="risk-item">
                        <div className="risk-header">
                          <span className="risk-title">{risk.title}</span>
                          <span className={`risk-priority priority-${risk.priority}`}>
                            {risk.priority === 'high' ? '🔴 高' : risk.priority === 'medium' ? '🟡 中' : '🟢 低'}
                          </span>
                        </div>
                        <p className="risk-mitigation">{risk.mitigation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 💡 机会与建议 */}
              {insights.opportunities_and_actions && (
                <div className="insight-card">
                  <h3>💡 机会与建议</h3>
                  {insights.opportunities_and_actions.opportunities && insights.opportunities_and_actions.opportunities.length > 0 && (
                    <div className="opportunities-section">
                      <h4>市场机会：</h4>
                      <ul>
                        {insights.opportunities_and_actions.opportunities.map((opp, idx) => (
                          <li key={idx}>
                            <strong>{opp.type || opp.description}</strong>
                            {opp.description && opp.type && <p style={{ fontSize: '13px', marginTop: '4px' }}>{opp.description}</p>}
                            {opp.action && <p style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>行动：{opp.action}</p>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {insights.opportunities_and_actions.actions && insights.opportunities_and_actions.actions.length > 0 && (
                    <div className="actions-section">
                      <h4>行动建议：</h4>
                      <ul>
                        {insights.opportunities_and_actions.actions.map((action, idx) => (
                          <li key={idx}>
                            <strong>{action.action || action}</strong>
                            {action.owner && <span style={{ fontSize: '12px', color: '#666', marginLeft: '8px' }}>负责人：{action.owner}</span>}
                            {action.priority && <span style={{ fontSize: '12px', color: '#999', marginLeft: '8px' }}>优先级：{action.priority}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <p>点击上方按钮获取基于您订阅兴趣的 AI 行业分析报告</p>
            </div>
          )}
        </section>

        {/* 热点资讯推荐模块 */}
        <section className="section">
          <div className="section-header">
            <h2>热点资讯推荐</h2>
            <button
              onClick={() => fetchNews(false)}
              disabled={loadingNews || keywords.length === 0}
              className="btn btn-primary"
            >
              {loadingNews ? '加载中...' : '刷新推荐'}
            </button>
          </div>

          {loadingNews ? (
            <div className="loading">加载中...</div>
          ) : news.length > 0 ? (
            <div className="news-grid">
              {news.map((item, index) => {
                // 解析 score：后端返回字符串格式如 "0.85" 或 "1.00"
                const scoreNum = typeof item.score === 'string' ? parseFloat(item.score) : (item.score || 0);
                // 如果分数大于 1，说明是百分比格式（如 85.00），直接取整；否则是小数格式（如 0.85），乘以 100
                const matchPercent = scoreNum > 1 ? Math.round(scoreNum) : Math.round(scoreNum * 100);

                // 格式化时间显示
                const formatTimeAgo = (timeStr) => {
                  if (!timeStr) return '';
                  const now = new Date();
                  const past = new Date(timeStr);
                  const diffMs = now - past;
                  const diffMins = Math.floor(diffMs / 60000);
                  const diffHours = Math.floor(diffMins / 60);
                  const diffDays = Math.floor(diffHours / 24);

                  if (diffMins < 1) return '刚刚';
                  if (diffMins < 60) return `${diffMins}分钟之前`;
                  if (diffHours < 24) return `${diffHours}小时之前`;
                  if (diffDays < 7) return `${diffDays}天之前`;
                  return past.toLocaleDateString('zh-CN');
                };

                const timeDisplay = formatTimeAgo(item.time || item.created_at);

                return (
                  <div key={index} className="news-card">
                    <div className="news-card-header">
                      <h3>{item.title || '无标题'}</h3>
                      {item.source && (
                        <span className="source-tag">{item.source}</span>
                      )}
                    </div>
                    {scoreNum > 0 && (
                      <span className="score-tag">匹配度：{matchPercent}分</span>
                    )}
                    {timeDisplay && (
                      <span className="time-tag">{timeDisplay}</span>
                    )}
                    {item.summary && <p className="summary">{item.summary}</p>}
                    {item.link && (
                      <a href={item.link} target="_blank" rel="noopener noreferrer" className="read-more">
                        阅读全文 →
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <p>暂无推荐文章，请保存订阅后刷新推荐</p>
            </div>
          )}
        </section>

        {/* 更多解读模块 */}
        <section className="more-insights-section">
          <h2>更多解读 | 专家预判 | 商机探索</h2>
          <p>深度行业报告、专家分析和商机探索，添加博商战略老师企业微信</p>

          {/* 二维码 */}
          <div className="qr-code-container" style={{ marginTop: '30px' }}>
            <div className="qr-code-placeholder">
              <svg viewBox="0 0 100 100" fill="none">
                <rect x="10" y="10" width="30" height="30" stroke="currentColor" strokeWidth="2" />
                <rect x="15" y="15" width="20" height="20" fill="currentColor" />
                <rect x="60" y="10" width="30" height="30" stroke="currentColor" strokeWidth="2" />
                <rect x="65" y="15" width="20" height="20" fill="currentColor" />
                <rect x="10" y="60" width="30" height="30" stroke="currentColor" strokeWidth="2" />
                <rect x="15" y="65" width="20" height="20" fill="currentColor" />
                <rect x="50" y="50" width="10" height="10" fill="currentColor" />
                <rect x="70" y="50" width="10" height="10" fill="currentColor" />
                <rect x="50" y="70" width="10" height="10" fill="currentColor" />
                <rect x="70" y="70" width="10" height="10" fill="currentColor" />
                <rect x="60" y="60" width="10" height="10" fill="currentColor" />
              </svg>
            </div>
            <p className="qr-hint">扫码关注公众号</p>
          </div>
        </section>
      </main>

      <footer className="App-footer">
        <p>© 2026 Lumos Platform - 智能资讯监控平台</p>
      </footer>

      {/* Toast 通知容器 */}
      <ToastContainer />
    </div>
  );
}

export default App;
