"""
社交数据抓取模块 - 混合模式（API 优先 + 浏览器降级）
支持：微博、知乎、微信公众号、Twitter/X
策略：优先调用公开 API，失败时降级到浏览器爬取
"""

import asyncio
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
import requests
import json
from playwright.async_api import async_playwright


def get_proxy_from_env():
    """从环境变量获取代理配置"""
    proxy_server = os.environ.get('PROXY_SERVER')
    if proxy_server:
        return proxy_server

    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')

    if https_proxy:
        return https_proxy
    elif http_proxy:
        return http_proxy
    return None


def _deduplicate_results(results: list) -> list:
    """基于标题哈希去重"""
    seen = set()
    unique = []
    for item in results:
        title = item.get('title', '')
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        if title_hash not in seen:
            seen.add(title_hash)
            unique.append(item)
    return unique


# ============== API 优先实现 ==============

def fetch_weibo_hot_search_api() -> Optional[List[Dict]]:
    """
    微博热搜 API 实现（优先）
    使用微博开放平台或第三方 API
    """
    try:
        # 方案 1：使用微博公开 API（无需认证）
        url = 'https://weibo.com/ajax/side/hotSearch'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        if data.get('ok') == 1 and data.get('data'):
            hot_search_data = data['data'].get('realtime', [])
            for idx, item in enumerate(hot_search_data[:10], 1):
                results.append({
                    'title': item.get('note', ''),
                    'link': f"https://s.weibo.com/weibo?q={item.get('note', '')}",
                    'source': '微博',
                    'hot_value': int(item.get('num', 0)),
                    'rank': idx,
                    'tag': item.get('icon', ''),
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {
                        'search_rank': idx,
                        'hot_tag': item.get('icon', ''),
                        'trend': item.get('trend', '')
                    }
                })

        if results:
            print('[微博 API] 成功获取热搜数据')
            return results
        return None

    except Exception as e:
        print(f'[微博 API] 获取失败：{e}')
        return None


def fetch_zhihu_hot_api() -> Optional[List[Dict]]:
    """
    知乎热榜 API 实现（优先）
    使用知乎公开 API
    """
    try:
        # 知乎热榜 API（无需认证）
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-list?limit=10&reverse_order=0'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        if 'data' in data:
            for idx, item in enumerate(data['data'][:10], 1):
                target = item.get('target', {})
                results.append({
                    'title': target.get('title', ''),
                    'link': target.get('url', '').replace('api.', ''),
                    'source': '知乎',
                    'hot_value': int(target.get('follower_count', 0)),
                    'rank': idx,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {
                        'answer_count': int(target.get('answer_count', 0)),
                        'follower_count': int(target.get('follower_count', 0))
                    }
                })

        if results:
            print('[知乎 API] 成功获取热榜数据')
            return results
        return None

    except Exception as e:
        print(f'[知乎 API] 获取失败：{e}')
        return None


def fetch_twitter_trends_api() -> Optional[List[Dict]]:
    """
    Twitter 趋势 API 实现
    使用第三方聚合 API（如 trends24）
    """
    try:
        # 使用 trends24（无需 API  key）
        url = 'https://api.trends24.vn/trends/global'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        if 'data' in data:
            for idx, item in enumerate(data['data'][:10], 1):
                results.append({
                    'title': item.get('name', ''),
                    'link': f"https://twitter.com/search?q={item.get('name', '').replace(' ', '%20')}",
                    'source': 'Twitter/X',
                    'hot_value': int(item.get('tweet_count', idx * 10000)),
                    'rank': idx,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {
                        'tweet_count': item.get('tweet_count', 'Unknown'),
                        'category': item.get('type', '')
                    }
                })

        if results:
            print('[Twitter API] 成功获取趋势数据')
            return results
        return None

    except Exception as e:
        print(f'[Twitter API] 获取失败：{e}')
        return None


# ============== 浏览器降级实现 ==============

# 全局变量，用于保存已连接的浏览器实例
_local_browser_context = None


async def _get_browser_context(p, proxy=None):
    """
    获取浏览器上下文 - 优先连接本地浏览器，失败则启动系统 Chrome
    """
    # 尝试连接到本地已打开的浏览器（CDP 端口 9222）
    try:
        browser = await p.chromium.connect_over_cdp(
            endpoint_url='http://127.0.0.1:9222',
            timeout=3000
        )
        print('[浏览器] 已连接到本地浏览器 (CDP 9222)')

        # 使用第一个可用的 context 或者创建新的
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            context = await browser.new_context()
            page = await context.new_page()

        return browser, context, page
    except Exception as e:
        print(f'[浏览器] 连接本地浏览器失败：{e}，启动系统 Chrome...')
        # 使用系统 Chrome 浏览器
        import os
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        if not os.path.exists(chrome_path):
            chrome_path = None  # 使用默认 Chromium

        user_data_dir = '/tmp/lobsterai-chrome-profile'

        # 启动系统 Chrome
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            executable_path=chrome_path,
            proxy={'server': proxy} if proxy else None,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check',
                '--remote-debugging-port=9222'
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()
        # 等待页面稳定
        await page.wait_for_timeout(2000)

        return context.browser, context, page


async def _fetch_twitter_browser(proxy=None) -> List[Dict]:
    """浏览器爬取实现（降级方案）"""
    results = []
    print('[Twitter] 启动浏览器爬取...')

    async with async_playwright() as p:
        browser, context, page = await _get_browser_context(p, proxy)
        print('[Twitter] 访问 Twitter 趋势页面...')

        try:
            await page.goto('https://twitter.com/i/trends', timeout=30000, wait_until='domcontentloaded')
            await page.wait_for_timeout(5000)

            trend_items = await page.query_selector_all('[data-testid="trend"]')

            for idx, item in enumerate(trend_items[:10], 1):
                try:
                    name_elem = await item.query_selector('[data-testid="trend-name"]')
                    name = await name_elem.inner_text() if name_elem else ''

                    tweet_count_elem = await item.query_selector('[data-testid="trend-tweet-count"]')
                    tweet_count = await tweet_count_elem.inner_text() if tweet_count_elem else '0'

                    import re
                    numbers = re.findall(r'[\d.]+[KMB]?', tweet_count)
                    tweet_count_num = numbers[0] if numbers else '0'

                    multiplier = 1
                    if 'K' in tweet_count_num:
                        multiplier = 1000
                    elif 'M' in tweet_count_num:
                        multiplier = 1000000
                    elif 'B' in tweet_count_num:
                        multiplier = 1000000000

                    clean_num = re.sub(r'[KMB]', '', tweet_count_num)
                    hot_value = int(float(clean_num) * multiplier) if clean_num.replace('.', '').isdigit() else idx * 10000

                    results.append({
                        'title': name,
                        'link': f'https://twitter.com/search?q={name.replace(" ", "%20")}',
                        'source': 'Twitter/X',
                        'hot_value': hot_value,
                        'rank': idx,
                        'timestamp': datetime.now().isoformat(),
                        'metrics': {
                            'tweet_count': tweet_count_num,
                            'category': ''
                        }
                    })
                except Exception as e:
                    print(f'解析 Twitter 趋势失败：{e}')
                    continue

        except Exception as e:
            print(f'获取 Twitter 趋势失败：{e}')
        finally:
            # 关闭上下文（persistent context 不需要手动关闭 browser）
            if context:
                await context.close()

    return results


async def fetch_twitter_trends(proxy=None):
    """
    获取 Twitter/X 趋势数据（混合模式：API 优先 + 浏览器降级）
    """
    api_result = fetch_twitter_trends_api()
    if api_result:
        return api_result

    print('[Twitter] API 失败，降级到浏览器爬取...')
    return await _fetch_twitter_browser(proxy)


async def fetch_weibo_hot_search(proxy=None):
    """
    获取微博热搜数据（混合模式：API 优先 + 浏览器降级）
    """
    # 优先尝试 API
    api_result = fetch_weibo_hot_search_api()
    if api_result:
        return api_result

    # API 失败，降级到浏览器
    print('[微博] API 失败，降级到浏览器爬取...')
    return await _fetch_weibo_browser(proxy)


async def _fetch_weibo_browser(proxy=None) -> List[Dict]:
    """浏览器爬取实现（降级方案）"""
    results = []
    print('[微博] 启动浏览器爬取...')

    async with async_playwright() as p:
        browser, context, page = await _get_browser_context(p, proxy)
        print('[微博] 访问微博热搜页面...')

        try:
            await page.goto('https://s.weibo.com/top/summary', timeout=60000, wait_until='domcontentloaded')
            await page.wait_for_timeout(8000)  # 等待页面内容加载

            # 查找所有表格行（微博热搜使用表格布局）
            hot_searchs = await page.query_selector_all('tbody tr')
            print(f'找到 {len(hot_searchs)} 个热搜条目')

            for idx, tr in enumerate(hot_searchs[:15], 1):
                try:
                    # 查找标题单元格
                    td_title = await tr.query_selector('td.td-02')
                    if not td_title:
                        continue

                    # 获取标题文本
                    title_links = await td_title.query_selector_all('a')
                    if not title_links:
                        continue

                    # 第一个 a 标签是标题
                    title_link = title_links[0]
                    title = await title_link.inner_text()
                    title = title.strip()
                    if not title:
                        continue

                    # 获取链接
                    link_href = await title_link.get_attribute('href')
                    link = f'https://s.weibo.com{link_href}' if link_href else ''

                    # 获取热度值（第二个 a 标签或 span）
                    hot_num = '0'
                    if len(title_links) > 1:
                        hot_text = await title_links[1].inner_text()
                        hot_num = ''.join(filter(str.isdigit, hot_text)) or '0'

                    # 获取标签（新、爆、热等）
                    tag = ''
                    tag_elem = await td_title.query_selector('.icon-top')
                    if tag_elem:
                        tag_class = await tag_elem.get_attribute('class')
                        if 'icon-top-1' in (tag_class or ''):
                            tag = '爆'
                        elif 'icon-top-2' in (tag_class or ''):
                            tag = '热'
                        elif 'icon-top-3' in (tag_class or ''):
                            tag = '新'

                    # 查找是否有其他标签（如"官宣"等）
                    other_tag = await td_title.query_selector('.icon-bot')
                    if other_tag:
                        bot_class = await other_tag.get_attribute('class')
                        if 'icon-bot-1' in (bot_class or ''):
                            tag = '新'
                        elif 'icon-bot-2' in (bot_class or ''):
                            tag = '热'

                    results.append({
                        'title': title,
                        'link': link,
                        'source': '微博',
                        'hot_value': int(hot_num) if hot_num.isdigit() else (15 - idx) * 10000,
                        'rank': idx,
                        'tag': tag,
                        'timestamp': datetime.now().isoformat(),
                        'metrics': {
                            'search_rank': idx,
                            'hot_tag': tag
                        }
                    })
                    print(f'  [{idx}] {title[:30]}... 热度：{hot_num}')
                except Exception as e:
                    print(f'解析微博热搜项失败：{e}')
                    continue

            print(f'[微博] 成功获取 {len(results)} 条热搜')

        except Exception as e:
            print(f'获取微博热搜失败：{e}')
        finally:
            # 关闭上下文
            if context:
                await context.close()

    return results


async def fetch_zhihu_hot(proxy=None):
    """
    获取知乎热榜数据（混合模式：API 优先 + 浏览器降级）
    """
    # 优先尝试 API
    api_result = fetch_zhihu_hot_api()
    if api_result:
        return api_result

    # API 失败，降级到浏览器
    print('[知乎] API 失败，降级到浏览器爬取...')
    return await _fetch_zhihu_browser(proxy)


async def _fetch_zhihu_browser(proxy=None) -> List[Dict]:
    """浏览器爬取实现（降级方案）- 使用知乎 API"""
    results = []
    print('[知乎] 启动浏览器爬取...')

    async with async_playwright() as p:
        browser, context, page = await _get_browser_context(p, proxy)
        print('[知乎] 访问知乎热榜 API...')

        try:
            # 直接调用知乎热榜 API（不需要登录）
            api_url = 'https://api.zhihu.com/topstory/hot-list?limit=20&reverse_order=0'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            }

            # 使用 requests 库直接获取 API 数据
            import requests
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            for idx, item in enumerate(data.get('data', [])[:10], 1):
                target = item.get('target', {})
                title = target.get('title', '')
                url = target.get('url', '')
                excerpt = target.get('excerpt', '')

                # 热度计算
                metrics = item.get('children', [{}])[0] if item.get('children') else {}
                hot_text = metrics.get('text', '0')
                # 提取数字
                import re
                hot_num = ''.join(filter(str.isdigit, str(hot_text))) or '0'

                results.append({
                    'title': title,
                    'link': url if url.startswith('http') else f'https://www.zhihu.com{url}',
                    'source': '知乎',
                    'hot_value': int(hot_num) if hot_num.isdigit() else (10 - idx) * 10000,
                    'rank': idx,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {
                        'excerpt': excerpt[:50] if excerpt else ''
                    }
                })
                print(f'  [{idx}] {title[:40]}...')

            print(f'[知乎] 成功获取 {len(results)} 条热榜数据')

        except Exception as e:
            print(f'获取知乎热榜失败：{e}')
        finally:
            # 关闭上下文
            if context:
                await context.close()

    return results


async def fetch_wechat_articles(proxy=None):
    """
    获取微信公众号热门文章
    通过搜狗微信搜索获取公开文章
    """
    results = []
    print('[微信] 启动浏览器爬取...')

    async with async_playwright() as p:
        browser, context, page = await _get_browser_context(p, proxy)
        print('[微信] 访问搜狗微信搜索页面...')

        try:
            # 使用热门关键词搜索微信文章
            keywords = ['两会', 'AI', '人工智能', '科技', '财经']
            import random
            keyword = random.choice(keywords)

            search_url = f'https://weixin.sogou.com/weixin?type=2&query={keyword}'
            await page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
            await page.wait_for_timeout(8000)

            # 尝试获取文章列表
            articles = await page.query_selector_all('ul.news-list li')
            print(f'找到 {len(articles)} 个文章条目')

            for idx, article in enumerate(articles[:10], 1):
                try:
                    # 标题
                    title_elem = await article.query_selector('h3 a')
                    title = await title_elem.inner_text() if title_elem else ''
                    if not title:
                        continue

                    # 链接
                    link = ''
                    if title_elem:
                        link = await title_elem.get_attribute('href')

                    # 公众号名称
                    account_elem = await article.query_selector('.s2 a')
                    account_name = await account_elem.inner_text() if account_elem else ''

                    # 发布时间
                    time_elem = await article.query_selector('span[sourcetype="time"]')
                    publish_time = await time_elem.inner_text() if time_elem else ''

                    # 摘要
                    snippet_elem = await article.query_selector('p.txt-info')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ''

                    results.append({
                        'title': title,
                        'link': link,
                        'source': '微信公众号',
                        'hot_value': (10 - idx) * 1000,
                        'rank': idx,
                        'timestamp': datetime.now().isoformat(),
                        'metrics': {
                            'account_name': account_name,
                            'publish_time': publish_time,
                            'snippet': snippet[:50] if snippet else ''
                        }
                    })
                    print(f'  [{idx}] {title[:30]}... - {account_name}')
                except Exception as e:
                    print(f'解析微信文章失败：{e}')
                    continue

            print(f'[微信] 成功获取 {len(results)} 篇文章')

        except Exception as e:
            print(f'获取微信公众号文章失败：{e}')
        finally:
            # 关闭上下文
            if context:
                await context.close()

    return results


async def fetch_twitter_trends(proxy=None):
    """
    获取 Twitter/X 趋势数据（混合模式：API 优先 + 浏览器降级）
    """
    # 优先尝试 API
    api_result = fetch_twitter_trends_api()
    if api_result:
        return api_result

    # API 失败，降级到浏览器
    print('[Twitter] API 失败，降级到浏览器爬取...')
    return await _fetch_twitter_browser(proxy)


async def fetch_all_social_data(proxy=None):
    """
    并发抓取所有社交平台数据
    返回：去重后的社交指标数据
    """
    print('[社交数据] 开始抓取社交平台数据...')

    # 并发抓取所有平台
    tasks = [
        fetch_weibo_hot_search(proxy),  # 混合模式：API 优先 + 浏览器降级
        fetch_zhihu_hot(proxy),
        fetch_wechat_articles(proxy),
        fetch_twitter_trends(proxy)
    ]

    results = []

    try:
        # 并发执行
        import asyncio
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for platform_result in completed:
            if isinstance(platform_result, list):
                results.extend(platform_result)
            elif isinstance(platform_result, Exception):
                print(f'[社交数据] 平台抓取异常：{platform_result}')

        # 去重
        results = _deduplicate_results(results)

        print(f'[社交数据] 抓取完成，共 {len(results)} 条数据')

    except Exception as e:
        print(f'[社交数据] 抓取失败：{e}')

    return results


def sync_fetch_all_social(proxy=None):
    """
    同步包装函数，供 Flask 使用
    """
    return asyncio.run(fetch_all_social_data(proxy))


if __name__ == '__main__':
    # 测试
    proxy = get_proxy_from_env()
    print(f'使用代理：{proxy or "无"}')

    data = sync_fetch_all_social(proxy)
    print(f'\n获取到 {len(data)} 条社交数据')

    for item in data[:5]:
        print(f"- {item['source']}: {item['title']} (热度：{item['hot_value']})")
