"""
今日头条爬虫 - API 方式
"""

import asyncio
import logging
from typing import List
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class ToutiaoCrawler(BaseCrawler):
    """今日头条爬虫"""

    platform = "toutiao"
    platform_name = "今日头条"

    async def fetch(self) -> List[NewsItem]:
        """抓取今日头条热榜 - 使用 API 方式"""
        news_list = []

        # 今日头条热榜 API
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.toutiao.com/'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)

                if response.status_code != 200:
                    raise Exception(f"API 返回状态码：{response.status_code}")

                data = response.json()

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

                logger.info(f"今日头条 API 抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"今日头条 API 抓取失败：{e}")
                raise

        return news_list
