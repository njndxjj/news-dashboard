"""调试微博选择器"""
import asyncio
from playwright.async_api import async_playwright


async def debug_weibo_selectors():
    print('开始调试微博选择器...')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-debug-profile2',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-gpu', '--no-sandbox', '--no-first-run'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问微博热搜页面...')
        await page.goto('https://s.weibo.com/top/summary', timeout=60000)
        await page.wait_for_timeout(8000)

        # 尝试多种选择器
        selectors_to_try = [
            '.twitter-type',
            '.hot-search',
            '.tab_list li',
            '[class*="hot"]',
            '.searching-hot',
            'ul.list li',
            '.wrap-list ul li',
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f'✓ {selector}: 找到 {len(elements)} 个元素')
                    # 打印第一个元素的内容
                    first = elements[0]
                    text = await first.inner_text()
                    print(f'  第一个元素内容：{text[:100]}')
                else:
                    print(f'✗ {selector}: 0 个元素')
            except Exception as e:
                print(f'✗ {selector}: 错误 - {e}')

        await context.close()


if __name__ == '__main__':
    asyncio.run(debug_weibo_selectors())
