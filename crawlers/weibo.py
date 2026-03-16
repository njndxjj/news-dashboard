"""
微博热搜爬虫 - API 方式
"""

import asyncio
import logging
from typing import List
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""

    platform = "weibo"
    platform_name = "微博热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取微博热搜 - 使用 API 方式"""
        news_list = []

        # 微博热搜 API
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://s.weibo.com/top/summary'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)

                if response.status_code != 200:
                    raise Exception(f"API 返回状态码：{response.status_code}")

                data = response.json()

                # 提取数据
                hot_list = data.get('data', {}).get('realtime', [])

                for rank, item in enumerate(hot_list[:50], 1):
                    try:
                        title = item.get('word', '')
                        hot_value = item.get('num', 0)
                        url = item.get('word_scheme', '') or f"https://s.weibo.com/weibo?q={title}"

                        # 判断是否是置顶
                        is_top = item.get('flag', '') == '置顶'

                        if title:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=url,
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                                extra={
                                    'is_top': is_top,
                                }
                            ))
                    except Exception as e:
                        logger.warning(f"解析微博热搜项失败：{e}")
                        continue

                logger.info(f"微博热搜 API 抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"微博热搜 API 抓取失败：{e}")
                raise

        return news_list
