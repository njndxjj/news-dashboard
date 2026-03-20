/**
 * 用户行为埋点工具
 *
 * 功能：
 * 1. 自动追踪用户行为（点击、浏览、搜索等）
 * 2. 支持停留时长统计
 * 3. 批量上报优化性能
 * 4. 支持离线缓存（网络恢复后上报）
 * 5. 异步上报不阻塞主流程
 */

import {
  recordUserBehavior,
  recordUserSearch,
  getUserBehaviorStats
} from '../services/api.js';

// 行为类型常量
export const ACTION_TYPES = {
  CLICK: 'click',      // 点击
  LIKE: 'like',        // 点赞
  COLLECT: 'collect',  // 收藏
  SHARE: 'share',      // 分享
  COMMENT: 'comment',  // 评论
  SEARCH: 'search',    // 搜索
  VIEW: 'view',        // 浏览
};

/**
 * 配置常量
 */
const CONFIG = {
  API_BASE_URL: '/api',  // 使用相对路径，通过 Nginx 代理
  FLUSH_INTERVAL: 3000,        // 3 秒批量上报一次
  MAX_QUEUE_SIZE: 50,          // 最大缓存条数
  BATCH_SIZE: 20,              // 每批最多 20 条
  STORAGE_KEY: 'lumos_behavior_queue',  // localStorage 存储键
  MAX_RETRY_COUNT: 3,          // 最大重试次数
  RETRY_DELAY: 5000,           // 重试延迟（毫秒）
};

// 本地缓存队列
let behaviorQueue = [];
let isProcessing = false;
let flushTimer = null;
let retryCount = 0;

/**
 * 获取用户 ID
 */
const getUserId = () => {
  return localStorage.getItem('unique_id') || 'default';
};

/**
 * 从 localStorage 获取当前浏览的新闻 ID
 */
const getCurrentNewsId = () => {
  const current = localStorage.getItem('current_news');
  return current ? JSON.parse(current) : null;
};

/**
 * 从 localStorage 加载缓存的行为队列（离线缓存）
 */
const loadQueuedBehaviors = () => {
  try {
    const stored = localStorage.getItem(CONFIG.STORAGE_KEY);
    if (stored) {
      const queued = JSON.parse(stored);
      // 只保留最近 7 天的数据
      const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      behaviorQueue = queued.filter(b => b.timestamp > sevenDaysAgo);
      console.log(`[Tracking] Loaded ${behaviorQueue.length} behaviors from offline storage`);
    }
  } catch (error) {
    console.error('[Tracking] Failed to load queued behaviors:', error);
  }
};

/**
 * 核心函数：追踪行为（异步入队，不阻塞）
 */
const trackBehavior = (actionType, newsId, title, source, extraData = {}, stayDuration = 0) => {
  const userId = getUserId();

  const behavior = {
    user_id: userId,
    action_type: actionType,
    news_id: newsId,
    title,
    source,
    extra_data: extraData,
    stay_duration: stayDuration,
    timestamp: Date.now(),
    page_url: window.location.href,
    page_title: document.title,
    user_agent: navigator.userAgent,
  };

  // 入队
  behaviorQueue.push(behavior);
  console.log(`[Tracking] ${actionType} queued:`, { newsId, title, queueSize: behaviorQueue.length });

  // 如果队列满了，立即上报
  if (behaviorQueue.length >= CONFIG.MAX_QUEUE_SIZE) {
    flushImmediately();
  } else {
    // 否则延迟上报（合并短时间内的多个行为）
    scheduleFlush();
  }

  // 更新离线缓存
  saveQueuedBehaviors();
};

/**
 * 保存行为队列到 localStorage（离线缓存）
 */
const saveQueuedBehaviors = () => {
  try {
    localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(behaviorQueue));
  } catch (error) {
    console.error('[Tracking] Failed to save queued behaviors:', error);
    // 如果 localStorage 满了，清理一半数据
    if (error.name === 'QuotaExceededError') {
      behaviorQueue = behaviorQueue.slice(Math.floor(behaviorQueue.length / 2));
      localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(behaviorQueue));
    }
  }
};

/**
 * 异步批量上报（使用 sendBeacon 或 fetch）
 */
const flushQueue = async () => {
  if (isProcessing || behaviorQueue.length === 0) {
    return;
  }

  isProcessing = true;

  // 取出一批数据
  const batch = behaviorQueue.splice(0, CONFIG.BATCH_SIZE);

  try {
    // 方式 1: 使用 sendBeacon（推荐，浏览器会自动在后台发送，不阻塞页面卸载）
    const blob = new Blob([JSON.stringify(batch)], { type: 'application/json' });

    // 优先使用 sendBeacon（异步，不阻塞）
    if (navigator.sendBeacon) {
      const success = navigator.sendBeacon(`${CONFIG.API_BASE_URL}/user/behavior/batch`, blob);
      if (success) {
        console.log(`[Tracking] Batch sent (${batch.length} behaviors) via sendBeacon`);
        retryCount = 0; // 重置重试计数
      } else {
        // sendBeacon 失败，放回队列
        behaviorQueue.unshift(...batch);
        console.warn('[Tracking] sendBeacon failed, will retry');
      }
    } else {
      // 方式 2: 降级使用 fetch（异步）
      fetch(`${CONFIG.API_BASE_URL}/user/behavior/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(batch),
        keepalive: true, // 页面卸载后继续发送
      }).then(() => {
        console.log(`[Tracking] Batch sent (${batch.length} behaviors) via fetch`);
        retryCount = 0;
      }).catch(err => {
        console.error('[Tracking] fetch failed:', err);
        // 放回队列头部
        behaviorQueue.unshift(...batch);
      });
    }
  } catch (error) {
    console.error('[Tracking] flushQueue error:', error);
    // 失败时放回队列
    behaviorQueue.unshift(...batch);
  }

  isProcessing = false;
  retryCount = 0;

  // 如果还有剩余，继续处理
  if (behaviorQueue.length > 0) {
    scheduleFlush();
  }

  // 更新离线缓存
  saveQueuedBehaviors();
};

/**
 * 延迟上报（合并短时间内的多个行为）
 */
const scheduleFlush = () => {
  if (flushTimer) {
    clearTimeout(flushTimer);
  }

  // CONFIG.FLUSH_INTERVAL 后上报
  flushTimer = setTimeout(() => {
    flushQueue();
  }, CONFIG.FLUSH_INTERVAL);
};

/**
 * 立即上报（用于页面卸载前）
 */
export const flushImmediately = () => {
  if (flushTimer) {
    clearTimeout(flushTimer);
  }
  flushQueue();
};

/**
 * 追踪点击行为
 */
export const trackClick = (newsId, title, source) => {
  trackBehavior(ACTION_TYPES.CLICK, newsId, title, source);
};

/**
 * 追踪点赞行为
 */
export const trackLike = (newsId, title, source) => {
  trackBehavior(ACTION_TYPES.LIKE, newsId, title, source);
};

/**
 * 追踪收藏行为
 */
export const trackCollect = (newsId, title, source) => {
  trackBehavior(ACTION_TYPES.COLLECT, newsId, title, source);
};

/**
 * 追踪分享行为
 */
export const trackShare = (newsId, title, source, platform = '') => {
  trackBehavior(ACTION_TYPES.SHARE, newsId, title, source, { platform });
};

/**
 * 追踪搜索行为
 */
export const trackSearch = (keyword, resultCount = 0) => {
  const userId = getUserId();
  recordUserSearch(keyword, resultCount, userId);
};

/**
 * 追踪页面浏览行为
 */
export const trackPageView = (pageName, extraData = {}) => {
  const userId = getUserId();
  const newsId = extraData.unique_id || userId;
  const title = `Page: ${pageName}`;
  const source = 'web';

  // 使用 VIEW 类型上报页面浏览
  trackBehavior(ACTION_TYPES.VIEW, newsId, title, source, {
    page_name: pageName,
    ...extraData,
  });
};

/**
 * 追踪浏览行为（带停留时长和滚动深度统计）
 */
let viewStartTime = null;
let viewTimer = null;
let maxScrollDepth = 0;
let scrollCheckTimer = null;

/**
 * 计算当前滚动深度百分比
 */
const calculateScrollDepth = () => {
  const scrollTop = window.scrollY || window.pageYOffset;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  return docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
};

/**
 * 监听滚动深度
 */
const startScrollTracking = () => {
  const updateScrollDepth = () => {
    const depth = calculateScrollDepth();
    if (depth > maxScrollDepth) {
      maxScrollDepth = depth;
    }

    // 继续监听
    scrollCheckTimer = setTimeout(updateScrollDepth, 1000);
  };

  updateScrollDepth();
};

export const stopScrollTracking = () => {
  if (scrollCheckTimer) {
    clearTimeout(scrollCheckTimer);
    scrollCheckTimer = null;
  }
};

export const startTrackingView = (newsId, title, source) => {
  // 保存当前浏览的新闻信息
  localStorage.setItem('current_news', JSON.stringify({ newsId, title, source }));

  viewStartTime = Date.now();
  maxScrollDepth = 0;

  // 开始滚动追踪
  startScrollTracking();

  // 设置停留时长上报（30 秒后开始统计）
  if (viewTimer) {
    clearTimeout(viewTimer);
  }

  viewTimer = setTimeout(() => {
    const duration = Math.floor((Date.now() - viewStartTime) / 1000);
    if (duration >= 5) { // 至少停留 5 秒才算有效浏览
      trackBehavior(ACTION_TYPES.VIEW, newsId, title, source, { scroll_depth: maxScrollDepth }, duration);
    }
  }, 5000); // 5 秒后开始追踪
};

export const stopTrackingView = () => {
  if (viewTimer) {
    clearTimeout(viewTimer);
    viewTimer = null;
  }

  stopScrollTracking();

  if (viewStartTime) {
    const duration = Math.floor((Date.now() - viewStartTime) / 1000);
    const currentNews = getCurrentNewsId();

    if (currentNews && duration >= 5) {
      trackBehavior(
        ACTION_TYPES.VIEW,
        currentNews.newsId,
        currentNews.title,
        currentNews.source,
        { scroll_depth: maxScrollDepth },
        duration
      );
    }

    viewStartTime = null;
    maxScrollDepth = 0;
  }
};

/**
 * 页面切换时，自动切换浏览追踪
 */
export const switchTrackingView = (newsId, title, source) => {
  stopTrackingView();
  startTrackingView(newsId, title, source);
};

/**
 * 初始化埋点系统
 */
export const initTracking = () => {
  // 加载离线缓存的行为
  loadQueuedBehaviors();

  // 页面可见性变化时，停止/开始追踪
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // 页面隐藏，停止追踪
      stopTrackingView();
    } else {
      // 页面显示，重新开始追踪当前新闻
      const currentNews = getCurrentNewsId();
      if (currentNews) {
        startTrackingView(currentNews.newsId, currentNews.title, currentNews.source);
      }
    }
  });

  // 页面关闭前，上报所有缓存行为
  window.addEventListener('beforeunload', () => {
    stopTrackingView();
    // 同步上报（不等待）
    if (behaviorQueue.length > 0) {
      navigator.sendBeacon?.(`${CONFIG.API_BASE_URL}/user/behavior/batch`, JSON.stringify(behaviorQueue));
    }
  });

  // 定期刷新（每 30 秒）
  setInterval(() => {
    if (behaviorQueue.length > 0) {
      flushImmediately();
    }
  }, 30000);

  console.log('[Tracking] initialized with queue size:', behaviorQueue.length);

  // 启动定时上报
  scheduleFlush();
};

export default {
  initTracking,
  trackPageView,
  trackClick,
  trackLike,
  trackCollect,
  trackShare,
  trackSearch,
  startTrackingView,
  stopTrackingView,
  switchTrackingView,
  calculateScrollDepth,
  ACTION_TYPES,
};
