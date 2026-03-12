"""
微博热搜爬虫
"""

import asyncio
import logging
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""

    platform = "weibo"
    platform_name = "微博热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取微博热搜"""
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
                # 访问微博热搜
                await page.goto('https://s.weibo.com/top/summary', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # 查找热搜列表
                news_items = await page.query_selector_all('#pl_top_realtimehot table tbody tr')

                for rank, item in enumerate(news_items[:50], 1):
                    try:
                        # 跳过没有数据的行
                        td_list = await item.query_selector_all('td')
                        if len(td_list) < 2:
                            continue

                        # 提取排名（第一个 td）
                        rank_td = td_list[0]
                        rank_class = await rank_td.get_attribute('class') or ''

                        # 提取标题和链接（第二个 td）
                        title_td = td_list[1]
                        title_link = await title_td.query_selector('a')

                        if not title_link:
                            continue

                        title = await title_link.inner_text()
                        href = await title_link.get_attribute('href')

                        # 提取热度值（从相邻的 span 或数据属性）
                        hot_value = None
                        hot_elem = await title_td.query_selector('span')
                        if hot_elem:
                            hot_text = await hot_elem.inner_text()
                            hot_value = self.parse_hot_value(hot_text)

                        # 判断是否是置顶、荐等标签
                        is_top = '置顶' in rank_class or 'top' in rank_class.lower()
                        is_recommend = '荐' in title

                        if title and href:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=href if href.startswith('http') else f'https://s.weibo.com{href}',
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                                extra={
                                    'is_top': is_top,
                                    'is_recommend': is_recommend,
                                }
                            ))
                    except Exception as e:
                        logger.warning(f"解析微博热搜项失败：{e}")
                        continue

                logger.info(f"微博热搜抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"微博热搜抓取失败：{e}")
                news_list = await self._fetch_backup()

            finally:
                await browser.close()

        return news_list

    async def _fetch_backup(self) -> List[NewsItem]:
        """备用方案"""
        logger.info("微博热搜使用备用 API 方案")
        return []
