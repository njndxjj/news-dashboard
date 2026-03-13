"""调试搜狗微信搜索"""
import asyncio
from playwright.async_api import async_playwright


async def debug_wechat():
    print('开始调试搜狗微信搜索...')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-wechat-profile',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-gpu', '--no-sandbox', '--no-first-run'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问搜狗微信搜索页面...')
        await page.goto('https://weixin.sogou.com/', timeout=60000)
        await page.wait_for_timeout(10000)

        # 保存截图
        await page.screenshot(path='/tmp/wechat_debug.png')
        print('已保存截图到 /tmp/wechat_debug.png')

        # 获取页面 HTML
        html = await page.content()
        print(f'页面 HTML 长度：{len(html)}')

        # 查找搜索框
        search_box = await page.query_selector('input[type="text"]')
        if search_box:
            print('找到搜索框')
        else:
            print('未找到搜索框')

        # 查找热门文章
        articles = await page.query_selector_all('.news-list li')
        print(f'找到 {len(articles)} 个文章条目')

        # 尝试查找所有链接
        links = await page.query_selector_all('a')
        print(f'找到 {len(links)} 个链接')

        for i, link in enumerate(links[:10]):
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and text:
                print(f'  [{i}] {text[:30]}... - {href[:50]}')

        await context.close()
        print('调试完成！')


if __name__ == '__main__':
    asyncio.run(debug_wechat())
