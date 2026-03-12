"""
知乎热榜爬虫
"""

import asyncio
import logging
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""

    platform = "zhihu"
    platform_name = "知乎热榜"

    async def fetch(self) -> List[NewsItem]:
        """抓取知乎热榜"""
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
                await page.goto('https://www.zhihu.com/hot', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)

                # 查找热榜列表项 - 使用 SSR 后的 HTML 结构
                # 知乎使用动态加载，需要等待内容出现
                await page.wait_for_selector('.HotItem', timeout=10000)
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

                logger.info(f"知乎热榜抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"知乎热榜抓取失败：{e}")

            finally:
                await browser.close()

        return news_list
