import axios from 'axios';

// 生产环境：直接请求后端 5000 端口
// 开发环境可以通过 webpack devServer 代理配置使用相对路径
const API_BASE_URL = 'http://localhost:5000/api';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 秒 - 适应 AI 分析接口可能需要较长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 unique_id
    const userId = localStorage.getItem('unique_id') || 'default';
    config.headers['X-User-ID'] = userId;

    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API 请求错误:', error);
    return Promise.reject(error);
  }
);

/**
 * 通用 API 请求函数
 * @param {string} method - HTTP 方法 (get, post, put, delete)
 * @param {string} url - 请求 URL
 * @param {object} data - 请求数据 (用于 POST/PUT)
 * @param {object} params - URL 参数
 */
export const apiRequest = async (method, url, data = null, params = {}) => {
  const config = {
    method,
    url,
    params,
  };

  if (data && ['post', 'put', 'patch'].includes(method.toLowerCase())) {
    config.data = data;
  }

  return apiClient(config);
};

// ==================== 新闻相关 API ====================

/**
 * 获取最新新闻（从数据库）
 */
export const fetchNews = async (limit = 300) => {
  return apiClient.get('/news', { params: { limit } });
};

/**
 * 按频道分组获取新闻
 */
export const fetchNewsByChannel = async (userId = 'default') => {
  return apiClient.get('/news/by-channel', { params: { user_id: userId } });
};

/**
 * 获取热点新闻
 */
export const fetchHotNews = async (limit = 10) => {
  return apiClient.get('/hot', { params: { limit } });
};

/**
 * 搜索新闻
 */
export const searchNews = async (keyword, source = 'browser', limit = 100) => {
  return apiClient.get('/search', {
    params: { q: keyword, source, limit },
  });
};

/**
 * 手动刷新新闻数据
 */
export const refreshNews = async () => {
  return apiClient.post('/refresh');
};

// ==================== 用户兴趣相关 API ====================

/**
 * 获取用户兴趣标签
 */
export const getUserInterests = async (userId = 'default') => {
  return apiClient.get('/user/interests', { params: { user_id: userId } });
};

/**
 * 获取预设兴趣分类
 */
export const getInterestCategories = async () => {
  return apiClient.get('/user/interests/categories');
};

/**
 * 添加用户兴趣标签
 */
export const addUserInterest = async (keyword, weight = 1.0, userId = 'default') => {
  return apiClient.post('/user/interests', {
    user_id: userId,
    keyword,
    weight,
  });
};

/**
 * 关注某个分类（自动添加该分类下所有关键词）
 */
export const followCategory = async (category, userId = 'default') => {
  return apiClient.post('/user/interests/follow_category', {
    user_id: userId,
    category,
  });
};

/**
 * 取消关注某个分类
 */
export const unfollowCategory = async (category, userId = 'default') => {
  return apiClient.post('/user/interests/unfollow_category', {
    user_id: userId,
    category,
  });
};

/**
 * 删除用户兴趣标签
 */
export const deleteUserInterest = async (keyword, userId = 'default') => {
  return apiClient.post('/user/interests/delete', {
    user_id: userId,
    keyword,
  });
};

/**
 * 清除用户所有兴趣标签
 */
export const clearUserInterests = async (userId = 'default') => {
  return apiClient.post('/user/interests/clear', {
    user_id: userId,
  });
};

/**
 * 记录用户点击行为
 */
export const recordUserClick = async (newsId, title, source, userId = 'default') => {
  return apiClient.post('/user/click', {
    user_id: userId,
    news_id: newsId,
    title,
    source,
  });
};

// ==================== 用户行为上报 API ====================

/**
 * 记录用户行为（通用接口，支持多种行为类型）
 * @param {string} actionType - 行为类型：click, like, collect, share, comment, search, view
 * @param {number} newsId - 新闻 ID
 * @param {string} title - 新闻标题
 * @param {string} source - 新闻来源
 * @param {object} extraData - 额外数据（JSON 对象）
 * @param {number} stayDuration - 停留时长（秒）
 * @param {string} userId - 用户 ID
 */
export const recordUserBehavior = async (actionType, newsId, title, source, extraData = {}, stayDuration = 0, userId = 'default') => {
  return apiClient.post('/user/behavior/record', {
    user_id: userId,
    action_type: actionType,
    news_id: newsId,
    title,
    source,
    extra_data: extraData,
    stay_duration: stayDuration,
  });
};

/**
 * 批量上报用户行为（异步，不阻塞）
 * @param {Array} behaviors - 行为列表
 */
export const batchRecordBehaviors = async (behaviors) => {
  return apiClient.post('/user/behavior/batch', {
    behaviors,
  });
};

/**
 * 记录用户搜索行为
 */
export const recordUserSearch = async (keyword, resultCount = 0, userId = 'default') => {
  return apiClient.post('/user/behavior/record', {
    user_id: userId,
    action_type: 'search',
    news_id: null,
    title: null,
    source: null,
    extra_data: { keyword, result_count: resultCount },
    stay_duration: 0,
  });
};

/**
 * 获取用户行为历史
 */
export const getUserBehaviorHistory = async (userId = 'default', actionType = null, limit = 100) => {
  return apiClient.get('/user/behavior/history', {
    params: { user_id: userId, action_type: actionType, limit },
  });
};

/**
 * 获取用户行为统计
 */
export const getUserBehaviorStats = async (userId = 'default', days = 7) => {
  return apiClient.get('/user/behavior/stats', {
    params: { user_id: userId, days },
  });
};

/**
 * 获取用户行为趋势
 */
export const getUserBehaviorTrend = async (userId = 'default', days = 30) => {
  return apiClient.get('/user/behavior/trend', {
    params: { user_id: userId, days },
  });
};

/**
 * 获取用户行为统计（全局）
 * @param {object} params - 查询参数 { start_date, end_date }
 */
export const fetchUserBehaviorStats = async (params = {}) => {
  return apiClient.get('/user/behavior/stats/global', { params });
};

/**
 * 获取用户行为事件列表
 * @param {object} params - 查询参数 { start_date, end_date, event_type }
 */
export const fetchUserBehaviorEvents = async (params = {}) => {
  return apiClient.get('/user/behavior/events', { params });
};

/**
 * 获取用户标签
 */
export const getUserTags = async (userId = 'default') => {
  return apiClient.get('/user/tags', {
    params: { user_id: userId },
  });
};

// ==================== AI 分析相关 API ====================

/**
 * AI 深度分析
 */
export const analyzeNews = async (newsList = [], keyword = '') => {
  return apiClient.post('/analyze', {
    news: newsList,
    keyword,
  });
};

/**
 * 获取历史 AI 分析记录
 */
export const getAnalysisHistory = async (limit = 10, type = null) => {
  return apiClient.get('/analyze/history', {
    params: { limit, type },
  });
};

/**
 * 关键词分析
 */
export const analyzeKeywords = async (newsList) => {
  return apiClient.post('/analyze/keywords', {
    news: newsList,
  });
};

/**
 * 情感分析
 */
export const analyzeSentiment = async (newsList) => {
  return apiClient.post('/analyze/sentiment', {
    news: newsList,
  });
};

/**
 * 社交分析
 */
export const analyzeSocial = async (newsList) => {
  return apiClient.post('/analyze/social', {
    news: newsList,
  });
};

// ==================== 推荐系统相关 API ====================

/**
 * AI 推荐新闻（混合推荐系统）
 */
export const recommendNews = async (newsList, history = [], useExternalApi = true, userId = 'default') => {
  return apiClient.post('/recommend', {
    news: newsList,
    history,
    use_external_api: useExternalApi,
    user_id: userId,
  });
};

// ==================== 推送管理相关 API ====================

/**
 * 获取所有推送规则
 */
export const getPushRules = async () => {
  return apiClient.get('/push/rules');
};

/**
 * 创建推送规则
 */
export const createPushRule = async (ruleName, keywords = [], hotThreshold = 90, enabled = true) => {
  return apiClient.post('/push/rules', {
    rule_name: ruleName,
    keywords,
    hot_threshold: hotThreshold,
    enabled,
  });
};

/**
 * 更新推送规则
 */
export const updatePushRule = async (ruleId, ruleName, keywords = [], hotThreshold = 90, enabled = true) => {
  return apiClient.put(`/push/rules/${ruleId}`, {
    rule_name: ruleName,
    keywords,
    hot_threshold: hotThreshold,
    enabled,
  });
};

/**
 * 删除推送规则
 */
export const deletePushRule = async (ruleId) => {
  return apiClient.delete(`/push/rules/${ruleId}`);
};

/**
 * 获取推送设置
 */
export const getPushSettings = async () => {
  return apiClient.get('/push/settings');
};

/**
 * 更新推送设置
 */
export const updatePushSettings = async (settings) => {
  return apiClient.put('/push/settings', settings);
};

/**
 * 测试推送
 */
export const testPush = async () => {
  return apiClient.post('/push/test');
};

/**
 * 定时汇总推送
 */
export const dailyPush = async (period = 'morning') => {
  return apiClient.post('/push/daily', null, { params: { period } });
};

/**
 * 获取推送记录
 */
export const getPushLogs = async (limit = 50) => {
  return apiClient.get('/push/logs', { params: { limit } });
};

// ==================== 统计信息 API ====================

/**
 * 获取统计信息
 */
export const getStats = async () => {
  return apiClient.get('/stats');
};

// ==================== 数据采集管理 API ====================

/**
 * 获取定时任务状态
 */
export const getSchedulerStatus = async () => {
  return apiClient.get('/scheduler/status');
};

/**
 * 立即运行爬虫
 */
export const runCrawlers = async () => {
  return apiClient.post('/crawlers/run');
};

/**
 * 触发数据采集
 */
export const triggerCollection = async () => {
  return apiClient.post('/collect');
};

// ==================== 管理后台 - RSS 源管理 ====================

/**
 * 获取所有 RSS 源
 */
export const getRssFeeds = async () => {
  return apiClient.get('/admin/rss-feeds');
};

/**
 * 创建 RSS 源
 */
export const createRssFeed = async (data) => {
  return apiClient.post('/admin/rss-feeds', data);
};

/**
 * 更新 RSS 源
 */
export const updateRssFeed = async (feedId, data) => {
  return apiClient.put(`/admin/rss-feeds/${feedId}`, data);
};

/**
 * 删除 RSS 源
 */
export const deleteRssFeed = async (feedId) => {
  return apiClient.delete(`/admin/rss-feeds/${feedId}`);
};

/**
 * 测试 RSS 源
 */
export const testRssFeed = async (feedId) => {
  return apiClient.get(`/admin/rss-feeds/${feedId}/test`);
};

/**
 * 获取爬虫状态
 */
export const getCrawlersStatus = async () => {
  return apiClient.get('/admin/crawlers/status');
};

/**
 * 手动运行爬虫（管理后台）
 */
export const runAdminCrawlers = async () => {
  return apiClient.post('/admin/crawlers/run');
};

// ==================== 付费转化 - 深度报告 ====================

/**
 * 获取深度报告列表
 */
export const getDeepReports = async (industry) => {
  const params = industry ? { industry } : {};
  return apiClient.get('/monetization/reports', { params });
};

/**
 * 获取深度报告详情
 */
export const getDeepReport = async (reportId) => {
  return apiClient.get(`/monetization/reports/${reportId}`);
};

/**
 * 消耗报告额度
 */
export const consumeReportQuota = async () => {
  return apiClient.post('/monetization/consume-report');
};

/**
 * 获取用户订阅状态
 */
export const getUserSubscription = async () => {
  return apiClient.get('/monetization/subscription');
};

// ==================== 付费转化 - 课程推荐 ====================

/**
 * 获取课程列表
 */
export const getCourses = async (industry, limit = 20) => {
  const params = {};
  if (industry) params.industry = industry;
  if (limit) params.limit = limit;
  return apiClient.get('/monetization/courses', { params });
};

export default apiClient;
