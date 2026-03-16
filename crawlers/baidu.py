"""
百度热搜爬虫 - API 方式
"""

import asyncio
import logging
import re
import json
from typing import List
import httpx
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class BaiduCrawler(BaseCrawler):
    """百度热搜爬虫"""

    platform = "baidu"
    platform_name = "百度热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取百度热搜 - 使用 API 方式"""
        news_list = []

        # 百度热搜 API - 直接使用 board 接口
        url = "https://top.baidu.com/api/board?platform=pc&tab=realtime"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://top.baidu.com/',
            'Accept': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)

                if response.status_code != 200:
                    raise Exception(f"API 返回状态码：{response.status_code}")

                data = response.json()

                # 提取热搜列表
                hot_list = data.get('data', {}).get('cards', [{}])[0].get('content', [])

                for rank, item in enumerate(hot_list[:50], 1):
                    try:
                        title = item.get('query', '') or item.get('word', '')
                        hot_score = item.get('hotScore', 0)
                        show = item.get('show', '')
                        url_item = item.get('url', '') or f"https://www.baidu.com/s?wd={title}"

                        # 解析热度值
                        hot_value = hot_score
                        if not hot_value and show:
                            hot_value = self.parse_hot_value(show.replace('热度', '').strip())

                        if title:
                            news_list.append(NewsItem(
                                title=title.strip(),
                                url=url_item if url_item.startswith('http') else f"https://www.baidu.com{s}",
                                source=self.platform_name,
                                hot_value=hot_value,
                                rank=rank,
                            ))
                    except Exception as e:
                        logger.warning(f"解析百度热搜项失败：{e}")
                        continue

                logger.info(f"百度热搜 API 抓取完成，共 {len(news_list)} 条")

            except Exception as e:
                logger.error(f"百度热搜 API 抓取失败：{e}")
                # 备用方案：解析 HTML 页面
                return await self._fetch_from_html()

        return news_list

    async def _fetch_from_html(self) -> List[NewsItem]:
        """备用方案：从 HTML 页面解析"""
        logger.info("百度使用备用 HTML 解析方案")
        news_list = []

        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://top.baidu.com/'
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                html = response.text

                # 提取 JSON 数据 - 多种 pattern
                patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
                    r'__INITIAL_STATE__\s*=\s*({.*?});'
                ]

                for pattern in patterns:
                    match = re.search(pattern, html, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        # 提取热搜列表
                        hot_list = data.get('cards', {}).get('index', [{}])[0].get('content', [])

                        for rank, item in enumerate(hot_list[:50], 1):
                            try:
                                title = item.get('query', '') or item.get('word', '')
                                hot_value = item.get('hotScore', 0) or item.get('show', '')
                                url = f"https://www.baidu.com/s?wd={title}"

                                if isinstance(hot_value, str):
                                    hot_value = self.parse_hot_value(hot_value.replace('热度', '').strip())

                                if title:
                                    news_list.append(NewsItem(
                                        title=title.strip(),
                                        url=url,
                                        source=self.platform_name,
                                        hot_value=hot_value,
                                        rank=rank,
                                    ))
                            except Exception as e:
                                logger.warning(f"解析百度热搜项失败：{e}")
                                continue
                        break

            except Exception as e:
                logger.error(f"百度备用方案失败：{e}")

        return news_list
