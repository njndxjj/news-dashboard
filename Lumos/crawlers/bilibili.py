"""
B 站热搜爬虫
"""

import asyncio
import logging
from typing import List
import httpx
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """B 站热搜爬虫"""

    platform = "bilibili-hot-search"
    platform_name = "B 站热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取 B 站热搜"""
        # 优先使用 API 方式
        try:
            return await self._fetch_api()
        except Exception as e:
            logger.warning(f"API 方式失败，尝试浏览器方式：{e}")
            return await self._fetch_browser()

    async def _fetch_api(self) -> List[NewsItem]:
        """使用 B 站 API 抓取"""
        news_list = []
        url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            if response.status_code != 200:
                raise Exception(f"API 返回状态码：{response.status_code}")

            data = response.json()
            videos = data.get('data', {}).get('list', [])

            for rank, video in enumerate(videos[:50], 1):
                try:
                    title = video.get('title', '')
                    bvid = video.get('bvid', '')
                    url = video.get('short_link', '') or f'https://www.bilibili.com/video/{bvid}'
                    hot_value = video.get('play', 0)

                    if title:
                        news_list.append(NewsItem(
                            title=title.strip(),
                            url=url,
                            source=self.platform_name,
                            hot_value=hot_value,
                            rank=rank,
                        ))
                except Exception as e:
                    logger.warning(f"解析 B 站 API 项失败：{e}")
                    continue

        logger.info(f"B 站热搜 API 抓取完成，共 {len(news_list)} 条")
        return news_list

    async def _fetch_browser(self) -> List[NewsItem]:
        """浏览器方式（备用）"""
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

                # 访问 B 站热门
                await page.goto('https://www.bilibili.com/v/popular/rank/all', wait_until='networkidle', timeout=60000)
                await asyncio.sleep(5)

                # 查找热门视频列表 - 更新选择器
                news_items = await page.query_selector_all('li .video-info-card')
                print(f"找到 B 站热门项：{len(news_items)}")

                for rank, item in enumerate(news_items[:50], 1):
                    try:
                        # 提取标题
                        title_elem = await item.query_selector('.video-title')
                        title = await title_elem.inner_text() if title_elem else ''

                        # 提取链接
                        link_elem = await item.query_selector('a')
                        href = await link_elem.get_attribute('href') if link_elem else ''

                        if title and href:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=href if href.startswith('http') else f'https://www.bilibili.com{href}',
                                source=self.platform_name,
                                rank=rank,
                            ))
                    except Exception as e:
                        logger.warning(f"解析 B 站热搜项失败：{e}")
                        continue

                logger.info(f"B 站热搜浏览器抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"B 站热搜浏览器抓取失败：{e}")

            finally:
                await browser.close()

        return news_list
