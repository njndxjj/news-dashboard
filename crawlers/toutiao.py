"""
今日头条爬虫
"""

import asyncio
import logging
import json
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class ToutiaoCrawler(BaseCrawler):
    """今日头条爬虫"""

    platform = "toutiao"
    platform_name = "今日头条"

    async def fetch(self) -> List[NewsItem]:
        """抓取今日头条热榜 - 使用 API 方式"""
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
                # 直接访问热榜 API
                await page.goto('https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # 获取页面文本内容（JSON 格式）
                content = await page.inner_text('body')

                # 解析 JSON
                data = json.loads(content.strip())

                # 提取数据
                if isinstance(data, dict) and 'data' in data:
                    hot_list = data['data']
                    for rank, item in enumerate(hot_list[:50], 1):
                        try:
                            title = item.get('Title', '') or item.get('QueryWord', '')
                            hot_value = item.get('HotValue', 0)
                            url = item.get('Url', '')

                            if title:
                                news_list.append(NewsItem(
                                    title=title.strip(),
                                    url=url,
                                    source=self.platform_name,
                                    hot_value=hot_value,
                                    rank=rank,
                                ))
                        except Exception as e:
                            logger.warning(f"解析头条新闻项失败：{e}")
                            continue

                logger.info(f"今日头条抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"今日头条抓取失败：{e}")

            finally:
                await browser.close()

        return news_list
