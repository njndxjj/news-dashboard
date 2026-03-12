"""
36 氪科技新闻爬虫
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class Kr36Crawler(BaseCrawler):
    """36 氪科技新闻爬虫"""

    platform = "kr36"
    platform_name = "36 氪科技"

    async def fetch(self) -> List[NewsItem]:
        """抓取 36 氪热门新闻"""
        news_list = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )
            page = await context.new_page()

            try:
                # 访问 36 氪首页
                await page.goto('https://www.36kr.com/', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(5)

                # 滚动页面以加载更多内容
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(3)

                # 查找文章容器（按优先级使用多个选择器）
                articles = []
                selectors = [
                    '.article-item-info.clearfloat',  # 主要文章列表
                    '.banner-left-item-article',      # 轮播文章
                    '.banner-right-item-article',     # 右侧文章
                    '.hotlist-item-other-pic',        # 热门列表
                ]
                for selector in selectors:
                    items = await page.query_selector_all(selector)
                    articles.extend(items)

                logger.info(f"找到文章容器：{len(articles)} 个")

                seen_urls = set()

                # 只取前 15 条，符合用户个性化推荐的数量要求
                for rank, article in enumerate(articles[:15], 1):
                    try:
                        # 从容器内查找链接
                        link_elem = await article.query_selector('a[href*="/p/"]')
                        if not link_elem:
                            continue

                        href = await link_elem.get_attribute('href')
                        if not href or '/p/' not in href:
                            continue

                        # 去重
                        if href in seen_urls:
                            continue
                        seen_urls.add(href)

                        url = f"https://www.36kr.com{href}" if href.startswith('/') else href

                        # 获取标题 - 直接从链接元素获取文本
                        title = await link_elem.inner_text()
                        title = self.clean_text(title)

                        if not title or len(title) < 5:
                            continue

                        # 过滤无效标题
                        if any(word in title for word in ['广告', '推广', '赞助']):
                            continue

                        # 获取摘要 - 从父容器查找
                        parent = await article.evaluate_handle('el => el.parentElement')
                        summary = None
                        if parent:
                            summary_elem = await parent.query_selector('p, .desc, [class*="summary"], [class*="abstract"]')
                            if summary_elem:
                                summary = await summary_elem.inner_text()
                                summary = self.clean_text(summary)
                                if len(summary) < 10:
                                    summary = None

                        # 获取时间
                        time_elem = await article.query_selector('time, [class*="time"], [class*="date"], [class*="Time"]')
                        publish_time_str = await time_elem.inner_text() if time_elem else None

                        # 解析相对时间
                        publish_time = None
                        if publish_time_str:
                            try:
                                if '小时前' in publish_time_str:
                                    hours = int(publish_time_str.replace('小时前', '').strip())
                                    publish_time = datetime.now() - timedelta(hours=hours)
                                elif '分钟前' in publish_time_str:
                                    minutes = int(publish_time_str.replace('分钟前', '').strip())
                                    publish_time = datetime.now() - timedelta(minutes=minutes)
                                elif '天前' in publish_time_str:
                                    days = int(publish_time_str.replace('天前', '').strip())
                                    publish_time = datetime.now() - timedelta(days=days)
                            except:
                                pass

                        # 获取图片
                        image_url = None
                        img_elem = await article.query_selector('img')
                        if img_elem:
                            image_url = await img_elem.get_attribute('src')
                            if image_url and image_url.startswith('//'):
                                image_url = f"https:{image_url}"

                        news_list.append(NewsItem(
                            title=title,
                            url=url,
                            source=self.platform_name,
                            rank=rank,
                            summary=summary,
                            image_url=image_url,
                            publish_time=publish_time,
                        ))

                    except Exception as e:
                        logger.warning(f"解析文章失败：{e}")
                        continue

            except Exception as e:
                logger.error(f"36 氪抓取失败：{e}")
            finally:
                await browser.close()

        logger.info(f"36 氪抓取完成，共 {len(news_list)} 条")
        return news_list
