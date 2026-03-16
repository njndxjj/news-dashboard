"""
知乎热榜爬虫 - API 方式
"""

import logging
from typing import List
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""

    platform = "zhihu"
    platform_name = "知乎热榜"

    async def fetch(self) -> List[NewsItem]:
        """抓取知乎热榜 - 使用 API 方式"""
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
