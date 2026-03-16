"""
36 氪科技新闻爬虫 - Playwright 方式
"""

import asyncio
import logging
from typing import List
from datetime import datetime
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class Kr36Crawler(BaseCrawler):
    """36 氪科技新闻爬虫"""

    platform = "kr36"
    platform_name = "36 氪科技"

    async def fetch(self) -> List[NewsItem]:
        """抓取 36 氪热门新闻 - 使用 Playwright 方式"""
        news_list = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright 未安装，使用备用 API 方案")
            return await self._fetch_backup()

        url = "https://www.36kr.com/"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)

                # 等待页面加载完成
                await asyncio.sleep(3)

                # 使用正确的选择器
                items = await page.query_selector_all('.kr-flow-article-item')
                logger.info(f"找到 {len(items)} 个文章项")

                for rank, item in enumerate(items[:20], 1):
                    try:
                        # 获取标题
                        title_el = await item.query_selector('.article-item-title')
                        title = await title_el.inner_text() if title_el else ''

                        # 获取链接
                        link_el = await item.query_selector('a')
                        href = await link_el.get_attribute('href') if link_el else ''
                        url = href if href and href.startswith('http') else f"https://www.36kr.com{href}" if href else ''

                        # 获取摘要
                        summary_el = await item.query_selector('.article-item-description')
                        summary = await summary_el.inner_text() if summary_el else ''

                        if title and len(title) < 100:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=url,
                                source=self.platform_name,
                                rank=rank,
                                summary=summary[:200] if summary else '',
                            ))
                    except Exception as e:
                        logger.warning(f"解析 36 氪新闻项失败：{e}")
                        continue

                logger.info(f"36 氪 Playwright 抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"36 氪 Playwright 抓取失败：{e}")
                news_list = await self._fetch_backup()
            finally:
                await browser.close()

        return news_list

    async def _fetch_backup(self) -> List[NewsItem]:
        """备用方案：返回空列表"""
        logger.warning("36 氪抓取失败，返回空列表")
        return []
