"""
小红书热搜爬虫
"""

import asyncio
import logging
from typing import List
from playwright.async_api import async_playwright
from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class XiaohongshuCrawler(BaseCrawler):
    """小红书热搜爬虫"""

    platform = "xiaohongshu"
    platform_name = "小红书热搜"

    async def fetch(self) -> List[NewsItem]:
        """抓取小红书热搜"""
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
                viewport={'width': 414, 'height': 896},  # 模拟 iPhone
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                device_scale_factor=2,
            )
            page = await context.new_page()

            try:
                # 访问小红书首页
                await page.goto('https://www.xiaohongshu.com/', wait_until='domcontentloaded', timeout=30000)

                # 等待页面加载
                await asyncio.sleep(3)

                # 关闭可能出现的弹窗
                try:
                    await page.click('button[class*="close"]', timeout=2000)
                except:
                    pass

                # 滚动页面以加载内容
                await page.evaluate('window.scrollTo(0, 500)')
                await asyncio.sleep(2)

                # 查找推荐笔记卡片
                # 小红书首页会展示推荐内容
                cards = await page.query_selector_all('div[class*="note"]')
                print(f"找到笔记卡片：{len(cards)}")

                # 查找所有笔记链接
                links = await page.query_selector_all('a[href*="/explore/"]')
                print(f"找到笔记链接：{len(links)}")

                # 去重
                seen_urls = set()

                for rank, link in enumerate(links[:50], 1):
                    try:
                        href = await link.get_attribute('href')

                        # 去重
                        if href in seen_urls:
                            continue
                        seen_urls.add(href)

                        # 获取标题 - 尝试多种选择器
                        title = None
                        # 方式 1：查找子元素中的标题
                        title_elem = await link.query_selector('div[class*="title"]')
                        if title_elem:
                            title = await title_elem.inner_text()

                        # 方式 2：如果 link 本身就是卡片，找相邻的标题元素
                        if not title:
                            title = await link.inner_text()

                        if not title or not title.strip():
                            continue

                        # 清理标题
                        title = title.strip().replace('\n', ' ').replace('\r', ' ')
                        # 限制长度
                        if len(title) > 100:
                            title = title[:100]

                        if href:
                            # 构建完整 URL
                            if href.startswith('/'):
                                href = f'https://www.xiaohongshu.com{href}'

                            news_list.append(NewsItem(
                                title=title,
                                url=href,
                                source=self.platform_name,
                                rank=rank,
                            ))
                    except Exception as e:
                        print(f"解析单条失败：{e}")
                        continue

                print(f"成功解析：{len(news_list)} 条")

            except Exception as e:
                logger.error(f"小红书抓取失败：{e}")
                print(f"小红书抓取失败：{e}")

            finally:
                await browser.close()

        return news_list


async def test():
    """测试爬虫"""
    print("测试小红书热搜爬虫...")
    crawler = XiaohongshuCrawler()
    result = await crawler.fetch()
    print(f"抓取成功！共 {len(result)} 条笔记")
    if result:
        print("前 5 条:")
        for item in result[:5]:
            print(f"{item.rank}. {item.title}")


if __name__ == '__main__':
    asyncio.run(test())
