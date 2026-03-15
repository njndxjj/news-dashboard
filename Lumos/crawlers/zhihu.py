"""
知乎热榜爬虫
"""

import asyncio
import logging
from typing import List
import httpx
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""

    platform = "zhihu"
    platform_name = "知乎热榜"

    async def fetch(self) -> List[NewsItem]:
        """抓取知乎热榜"""
        # 优先尝试 API 方式（避免反爬）
        try:
            return await self._fetch_api()
        except Exception as e:
            logger.warning(f"API 方式失败，尝试浏览器方式：{e}")
            return await self._fetch_browser()

    async def _fetch_api(self) -> List[NewsItem]:
        """使用公开 API 抓取（无需授权）"""
        news_list = []
        # 使用知乎公开的热榜 API
        url = "https://api.zhihu.com/topstory/hot-lists/total?limit=50"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.zhihu.com/hot'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)

            if response.status_code != 200:
                raise Exception(f"API 返回状态码：{response.status_code}")

            data = response.json()

            for rank, item in enumerate(data.get('data', [])[:50], 1):
                try:
                    target = item.get('target', {})
                    title = target.get('title', '')
                    question_id = target.get('id', '')
                    url = f"https://www.zhihu.com/question/{question_id}" if question_id else ''
                    hot_value = target.get('follower_count', 0)

                    if title:
                        news_list.append(NewsItem(
                            title=title.strip(),
                            url=url,
                            source=self.platform_name,
                            hot_value=hot_value,
                            rank=rank,
                        ))
                except Exception as e:
                    logger.warning(f"解析知乎 API 项失败：{e}")
                    continue

        logger.info(f"知乎热榜 API 抓取完成，共 {len(news_list)} 条")
        return news_list

    async def _fetch_browser(self) -> List[NewsItem]:
        """使用浏览器抓取（备用方案）"""
        news_list = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            try:
                # 设置更长的超时时间
                page.set_default_timeout(60000)
                page.set_default_navigation_timeout(60000)

                # 使用 domcontentloaded 避免等待所有网络请求完成
                print("正在访问知乎热榜...")
                response = await page.goto('https://www.zhihu.com/hot', wait_until='domcontentloaded', timeout=60000)
                print(f"页面响应状态：{response.status}")

                # 等待热榜内容加载 - 尝试多个选择器
                print("等待知乎热榜内容加载...")
                try:
                    await page.wait_for_selector('.HotItem', timeout=20000)
                except Exception:
                    # 尝试备用选择器
                    print("主选择器失败，尝试备用选择器...")
                    await page.wait_for_selector('[data-zop-question]', timeout=10000)

                await asyncio.sleep(3)  # 给 JS 执行时间

                news_items = await page.query_selector_all('.HotItem')
                print(f"找到热榜项：{len(news_items)}")

                for rank, item in enumerate(news_items[:50], 1):
                    try:
                        # 提取标题
                        title_elem = await item.query_selector('.HotItem-title')
                        title = await title_elem.inner_text() if title_elem else ''

                        # 提取链接
                        link_elem = await item.query_selector('a.HotItem-link')
                        href = await link_elem.get_attribute('href') if link_elem else ''

                        # 提取热度值
                        hot_elem = await item.query_selector('.HotItem-meta')
                        hot_text = await hot_elem.inner_text() if hot_elem else ''
                        hot_value = self.parse_hot_value(hot_text)

                        if title and href:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=href if href.startswith('http') else f'https://www.zhihu.com{href}',
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                            ))
                    except Exception as e:
                        logger.warning(f"解析知乎热榜项失败：{e}")
                        continue

                logger.info(f"知乎热榜浏览器抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"知乎热榜浏览器抓取失败：{e}")

            finally:
                await browser.close()

        return news_list
