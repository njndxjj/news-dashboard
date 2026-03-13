"""
浏览器自动化搜索模块 - 使用 Playwright 进行实时搜索
支持来源：微博热搜、知乎热议、36 氪、Google/Bing 新闻搜索
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 搜索结果限制
MIN_RESULTS = 50
MAX_RESULTS = 100
SEARCH_TIMEOUT = 30000  # 30 秒超时
PAGE_TIMEOUT = 15000  # 15 秒页面加载超时


class BrowserSearcher:
    """浏览器自动化搜索类"""
    
    def __init__(self, proxy: Optional[str] = None):
        """
        初始化浏览器搜索器
        
        :param proxy: 代理地址，格式如 "http://host:port" 或 "socks5://host:port"
        """
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def init_browser(self):
        """初始化浏览器"""
        if self.browser is None:
            playwright = await async_playwright().start()
            
            # 浏览器启动参数
            launch_args = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            }
            
            # 代理配置
            proxy_config = None
            if self.proxy:
                proxy_config = self._parse_proxy(self.proxy)
                logger.info(f"使用代理：{proxy_config}")
            
            self.browser = await playwright.chromium.launch(**launch_args)
            
            # 创建浏览器上下文
            context_args = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'locale': 'zh-CN',
                'timezone_id': 'Asia/Shanghai',
                'bypass_csp': True,
                'ignore_https_errors': True,
            }
            
            if proxy_config:
                context_args['proxy'] = proxy_config
            
            self.context = await self.browser.new_context(**context_args)
            logger.info("浏览器初始化完成")
    
    def _parse_proxy(self, proxy_url: str) -> Dict:
        """解析代理地址"""
        proxy_config = {}
        
        # 移除协议前缀
        url = proxy_url
        if '://' in url:
            protocol, rest = url.split('://', 1)
            proxy_config['server'] = f"{protocol}://{rest}"
        else:
            proxy_config['server'] = url
            
        # 处理用户名密码
        if '@' in proxy_config.get('server', ''):
            # 格式：http://user:pass@host:port
            match = re.match(r'(\w+)://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
            if match:
                proxy_config['server'] = f"{match.group(1)}://{match.group(4)}:{match.group(5)}"
                proxy_config['username'] = match.group(2)
                proxy_config['password'] = match.group(3)
        
        return proxy_config
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def search_weibo(self, keyword: str) -> List[Dict]:
        """
        微博热搜搜索
        
        :param keyword: 搜索关键词
        :return: 搜索结果列表
        """
        results = []
        page = None
        
        try:
            await self.init_browser()
            page = await self.context.new_page()
            
            # 访问微博热搜页面
            await page.goto('https://s.weibo.com/top/summary', 
                          timeout=PAGE_TIMEOUT,
                          wait_until='domcontentloaded')
            
            # 等待页面加载
            await page.wait_for_timeout(2000)
            
            # 提取热搜列表
            热搜条目 = await page.query_selector_all('#pl_top_realtimehot .td-02')
            
            for 条目 in 热搜条目[:50]:
                try:
                    标题元素 = await 条目.query_selector('a')
                    热度元素 = await 条目.query_selector('span')
                    
                    if 标题元素:
                        标题 = await 标题元素.inner_text()
                        链接 = await 标题元素.get_attribute('href')
                        
                        # 只保留包含关键词的结果
                        if keyword and keyword not in 标题:
                            continue
                        
                        热度 = await 热度元素.inner_text() if 热度元素 else ''
                        
                        # 清理链接
                        if 链接 and not 链接.startswith('http'):
                            链接 = f"https://s.weibo.com{链接}"
                        
                        results.append({
                            'title': 标题.strip(),
                            'original_title': 标题.strip(),
                            'source': '微博热搜',
                            'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'sentiment': 'neutral',
                            'hot_score': self._parse_hot_score(热度),
                            'link': 链接 or 'https://s.weibo.com/top/summary',
                            'lang': 'zh',
                            'content': 标题.strip(),
                            'priority': 'crawler'
                        })
                except Exception as e:
                    logger.warning(f"解析微博热搜条目失败：{e}")
                    continue
            
            logger.info(f"微博热搜搜索完成，获取 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"微博热搜搜索失败：{e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    async def search_zhihu(self, keyword: str) -> List[Dict]:
        """
        知乎热议搜索
        
        :param keyword: 搜索关键词
        :return: 搜索结果列表
        """
        results = []
        page = None
        
        try:
            await self.init_browser()
            page = await self.context.new_page()
            
            # 访问知乎热榜
            await page.goto('https://www.zhihu.com/hot', 
                          timeout=PAGE_TIMEOUT,
                          wait_until='domcontentloaded')
            
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 提取热榜列表
            问题条目 = await page.query_selector_all('.HotItem-list .HotItem')
            
            for 条目 in 问题条目[:50]:
                try:
                    标题元素 = await 条目.query_selector('.HotItem-title')
                    热度元素 = await 条目.query_selector('.HotItem-debate')
                    
                    if 标题元素:
                        标题 = await 标题元素.inner_text()
                        链接元素 = await 条目.query_selector('a')
                        链接 = await 链接元素.get_attribute('href') if 链接元素 else ''
                        
                        # 只保留包含关键词的结果
                        if keyword and keyword not in 标题:
                            continue
                        
                        热度 = await 热度元素.inner_text() if 热度元素 else ''
                        
                        # 清理链接
                        if 链接 and not 链接.startswith('http'):
                            链接 = f"https://www.zhihu.com{链接}"
                        
                        results.append({
                            'title': 标题.strip(),
                            'original_title': 标题.strip(),
                            'source': '知乎热议',
                            'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'sentiment': 'neutral',
                            'hot_score': self._parse_hot_score(热度),
                            'link': 链接 or 'https://www.zhihu.com/hot',
                            'lang': 'zh',
                            'content': 标题.strip(),
                            'priority': 'crawler'
                        })
                except Exception as e:
                    logger.warning(f"解析知乎热榜条目失败：{e}")
                    continue
            
            logger.info(f"知乎热议搜索完成，获取 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"知乎热议搜索失败：{e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    async def search_36kr(self, keyword: str) -> List[Dict]:
        """
        36 氪搜索
        
        :param keyword: 搜索关键词
        :return: 搜索结果列表
        """
        results = []
        page = None
        
        try:
            await self.init_browser()
            page = await self.context.new_page()
            
            # 访问 36 氪首页
            await page.goto('https://36kr.com/', 
                          timeout=PAGE_TIMEOUT,
                          wait_until='domcontentloaded')
            
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 提取新闻列表
            新闻条目 = await page.query_selector_all('.hot-ranking-item, .article-item')
            
            for 条目 in 新闻条目[:50]:
                try:
                    标题元素 = await 条目.query_selector('a')
                    
                    if 标题元素:
                        标题 = await 标题元素.inner_text()
                        链接 = await 标题元素.get_attribute('href')
                        
                        # 只保留包含关键词的结果
                        if keyword and keyword not in 标题:
                            continue
                        
                        # 清理链接
                        if 链接 and not 链接.startswith('http'):
                            链接 = f"https://36kr.com{链接}"
                        
                        results.append({
                            'title': 标题.strip(),
                            'original_title': 标题.strip(),
                            'source': '36 氪',
                            'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'sentiment': 'neutral',
                            'hot_score': 50,
                            'link': 链接 or 'https://36kr.com/',
                            'lang': 'zh',
                            'content': 标题.strip(),
                            'priority': 'crawler'
                        })
                except Exception as e:
                    logger.warning(f"解析 36 氪条目失败：{e}")
                    continue
            
            logger.info(f"36 氪搜索完成，获取 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"36 氪搜索失败：{e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    async def search_bing_news(self, keyword: str) -> List[Dict]:
        """
        Bing 新闻搜索
        
        :param keyword: 搜索关键词
        :return: 搜索结果列表
        """
        results = []
        page = None
        
        try:
            await self.init_browser()
            page = await self.context.new_page()
            
            # 访问 Bing 新闻搜索
            搜索链接 = f"https://www.bing.com/news/search?q={keyword}&cc=zh-CN&setlang=zh-CN"
            await page.goto(搜索链接,
                          timeout=PAGE_TIMEOUT,
                          wait_until='domcontentloaded')
            
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 提取新闻列表
            新闻条目 = await page.query_selector_all('.news-card, .news-card-group')
            
            for 条目 in 新闻条目[:50]:
                try:
                    标题元素 = await 条目.query_selector('.title')
                    if not 标题元素:
                        标题元素 = await 条目.query_selector('a')
                    
                    if 标题元素:
                        标题 = await 标题元素.inner_text()
                        链接 = await 标题元素.get_attribute('href')
                        
                        # 提取来源和发布时间
                        来源元素 = await 条目.query_selector('.source, .snippet')
                        来源 = await 来源元素.inner_text() if 来源元素 else '未知来源'
                        
                        results.append({
                            'title': 标题.strip(),
                            'original_title': 标题.strip(),
                            'source': 来源.strip()[:20] if 来源 else 'Bing 新闻',
                            'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'sentiment': 'neutral',
                            'hot_score': 40,
                            'link': 链接 or '#',
                            'lang': 'zh',
                            'content': 标题.strip(),
                            'priority': 'overseas'
                        })
                except Exception as e:
                    logger.warning(f"解析 Bing 新闻条目失败：{e}")
                    continue
            
            logger.info(f"Bing 新闻搜索完成，获取 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"Bing 新闻搜索失败：{e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    def _parse_hot_score(self, hot_text: str) -> int:
        """解析热度字符串为数字"""
        if not hot_text:
            return 50
        
        # 提取数字
        数字 = re.findall(r'\d+', hot_text.replace(',', ''))
        if 数字:
            return int(数字[-1])
        
        # 根据热度描述返回
        if '爆' in hot_text:
            return 100
        elif '热' in hot_text:
            return 80
        elif '新' in hot_text:
            return 60
        
        return 50
    
    async def search_all(self, keyword: str = '') -> List[Dict]:
        """
        执行全平台搜索
        
        :param keyword: 搜索关键词
        :return: 合并去重后的搜索结果
        """
        all_results = []
        
        # 并发执行各平台搜索
        tasks = []
        
        if keyword:
            # 有关键词时，执行定向搜索
            tasks.append(self.search_bing_news(keyword))
            tasks.append(self.search_weibo(keyword))
            tasks.append(self.search_zhihu(keyword))
            tasks.append(self.search_36kr(keyword))
        else:
            # 无关键词时，获取各平台热榜
            tasks.append(self.search_weibo(''))
            tasks.append(self.search_zhihu(''))
            tasks.append(self.search_36kr(''))
            tasks.append(self.search_bing_news('热门新闻'))
        
        # 并发执行搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"搜索任务异常：{result}")
        
        # 去重处理
        deduplicated = self._deduplicate_results(all_results)
        
        # 限制结果数量
        if len(deduplicated) > MAX_RESULTS:
            deduplicated = deduplicated[:MAX_RESULTS]
        
        logger.info(f"全平台搜索完成，共获取 {len(deduplicated)} 条结果")
        
        return deduplicated
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        对搜索结果进行去重
        
        去重策略：
        1. 基于标题的哈希值
        2. 相同标题只保留一个
        
        :param results: 搜索结果列表
        :return: 去重后的结果
        """
        seen_hashes = set()
        unique_results = []
        
        for item in results:
            # 生成标题哈希
            title = item.get('title', '').strip()
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_results.append(item)
        
        return unique_results


# 同步包装函数（用于 Flask 路由）
def sync_search(keyword: str = '', proxy: Optional[str] = None) -> List[Dict]:
    """
    同步搜索接口（用于 Flask 路由）
    
    :param keyword: 搜索关键词
    :param proxy: 代理地址
    :return: 搜索结果列表
    """
    searcher = BrowserSearcher(proxy=proxy)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(searcher.search_all(keyword))
        return results
    finally:
        loop.close()


# 获取代理配置
def get_proxy_from_env() -> Optional[str]:
    """从环境变量获取代理配置"""
    # 尝试多个常见的代理环境变量
    proxy_vars = [
        'HTTP_PROXY',
        'HTTPS_PROXY', 
        'PROXY_SERVER',
        'PROXY_HOST',
        'ALL_PROXY'
    ]
    
    for var in proxy_vars:
        proxy = os.environ.get(var)
        if proxy:
            return proxy
    
    return None
