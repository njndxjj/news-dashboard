"""调试浏览器爬取"""
import asyncio
from playwright.async_api import async_playwright


async def debug_weibo():
    print('开始调试微博爬取...')

    async with async_playwright() as p:
        # 启动系统 Chrome
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-debug-profile',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check',
            ],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问微博热搜页面...')
        await page.goto('https://s.weibo.com/top/summary', timeout=60000, wait_until='domcontentloaded')
        print('页面加载完成！')

        # 等待页面内容
        await page.wait_for_timeout(10000)

        # 保存页面截图
        await page.screenshot(path='/tmp/weibo_debug.png')
        print('已保存截图到 /tmp/weibo_debug.png')

        # 获取页面 HTML
        html = await page.content()
        print(f'页面 HTML 长度：{len(html)}')

        # 尝试查找热榜表格
        table = await page.query_selector('#pl_top_realtimehot_table')
        if table:
            print('找到热榜表格！')
            rows = await table.query_selector_all('tbody tr')
            print(f'找到 {len(rows)} 行')
        else:
            print('未找到热榜表格，尝试其他选择器...')
            # 尝试其他可能的选择器
            all_tables = await page.query_selector_all('table')
            print(f'找到 {len(all_tables)} 个表格')

        # 关闭
        await context.close()
        print('调试完成！')


if __name__ == '__main__':
    asyncio.run(debug_weibo())
