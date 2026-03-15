"""
百度热搜爬虫
"""

import asyncio
import logging
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class BaiduCrawler(BaseCrawler):
    """百度热搜爬虫"""

    platform = "baidu"
    platform_name = "百度热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取百度热搜"""
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
                await page.goto('https://top.baidu.com/board?tab=realtime', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)

                # 查找所有包含 hot-index 的父容器（即热搜项）
                # 使用 XPath 查找包含"热搜指数"的容器
                items = await page.query_selector_all('div[class*="hot-index"]')
                print(f"找到热度指数元素：{len(items)}")

                # 获取所有的内容容器
                contents = await page.query_selector_all('div[class*="content_"]')
                print(f"找到内容容器：{len(contents)}")

                for rank, content in enumerate(contents[:50], 1):
                    try:
                        # 提取标题和链接
                        link = await content.query_selector('a')
                        if not link:
                            continue

                        title = await link.inner_text()
                        href = await link.get_attribute('href')

                        # 提取热度指数（查找相邻的 hot-index 元素）
                        hot_value = None
                        # 尝试从父元素中查找
                        parent = await content.evaluate_handle('el => el.parentElement')
                        if parent:
                            hot_elem = await parent.query_selector('div[class*="hot-index"]')
                            if hot_elem:
                                hot_text = await hot_elem.inner_text()
                                hot_value = self.parse_hot_value(hot_text)

                        if title:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=href or '',
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                            ))
                    except Exception as e:
                        logger.warning(f"解析百度热搜项失败：{e}")
                        continue

                logger.info(f"百度热搜抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"百度热搜抓取失败：{e}")

            finally:
                await browser.close()

        return news_list
