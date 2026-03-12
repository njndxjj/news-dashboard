"""
B 站热搜爬虫
"""

import asyncio
import logging
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """B 站热搜爬虫"""

    platform = "bilibili-hot-search"
    platform_name = "B 站热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取 B 站热搜"""
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
                # 访问 B 站热门
                await page.goto('https://www.bilibili.com/v/popular/rank/all', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # 查找热门视频列表
                news_items = await page.query_selector_all('#rank-list .rank-item')

                for rank, item in enumerate(news_items[:50], 1):
                    try:
                        # 提取标题
                        title_elem = await item.query_selector('.rank-title')
                        title = await title_elem.inner_text() if title_elem else ''

                        # 提取链接
                        link_elem = await item.query_selector('a')
                        href = await link_elem.get_attribute('href') if link_elem else ''

                        # 提取播放量/热度
                        hot_elem = await item.query_selector('.detail-info .up-name')
                        hot_text = await hot_elem.inner_text() if hot_elem else ''
                        hot_value = self.parse_hot_value(hot_text)

                        if title and href:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=href if href.startswith('http') else f'https://www.bilibili.com{href}',
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                            ))
                    except Exception as e:
                        logger.warning(f"解析 B 站热搜项失败：{e}")
                        continue

                logger.info(f"B 站热搜抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"B 站热搜抓取失败：{e}")
                news_list = await self._fetch_backup()

            finally:
                await browser.close()

        return news_list

    async def _fetch_backup(self) -> List[NewsItem]:
        """备用方案"""
        logger.info("B 站热搜使用备用 API 方案")
        return []
