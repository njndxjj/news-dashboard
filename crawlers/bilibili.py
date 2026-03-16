"""
B 站热搜爬虫 - API 方式
"""

import logging
from typing import List
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """B 站热搜爬虫"""

    platform = "bilibili-hot-search"
    platform_name = "B 站热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取 B 站热搜 - 使用搜索热搜 API"""
        return await self._fetch_search_hot()

    async def _fetch_search_hot(self) -> List[NewsItem]:
        """使用搜索热搜榜 API"""
        logger.info("B 站使用搜索热搜方案")
        news_list = []

        url = 'https://s.search.bilibili.com/main/hotword'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    # B 站 API 数据结构：data.list
                    hotwords = data.get('list', [])

                    for rank, item in enumerate(hotwords[:20], 1):
                        try:
                            # 数据结构可能是 {'keyword': 'xxx'} 或字符串
                            if isinstance(item, dict):
                                title = item.get('keyword', '') or item.get('hotword', '')
                                hot_value = item.get('score', 0) or item.get('hot', 0)
                            elif isinstance(item, str):
                                title = item
                                hot_value = 0
                            else:
                                continue

                            url = f"https://search.bilibili.com/all?keyword={title}"

                            if title:
                                news_list.append(NewsItem(
                                    title=title.strip(),
                                    url=url,
                                    source=self.platform_name,
                                    hot_value=hot_value,
                                    rank=rank,
                                ))
                        except Exception as e:
                            logger.warning(f"解析 B 站搜索热搜失败：{e}")
                            continue

                    logger.info(f"B 站搜索热搜抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"B 站搜索热搜抓取失败：{e}")

        return news_list
