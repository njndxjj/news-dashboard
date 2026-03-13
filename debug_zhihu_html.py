"""调试知乎 HTML 结构"""
import asyncio
from playwright.async_api import async_playwright


async def debug_zhihu_html():
    print('开始调试知乎 HTML 结构...')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-zhihu-profile',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-gpu', '--no-sandbox', '--no-first-run'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问知乎热榜页面...')
        await page.goto('https://www.zhihu.com/hot', timeout=60000)
        await page.wait_for_timeout(10000)

        # 保存截图
        await page.screenshot(path='/tmp/zhihu_debug.png')
        print('已保存截图到 /tmp/zhihu_debug.png')

        # 获取页面 HTML
        html = await page.content()
        print(f'页面 HTML 长度：{len(html)}')

        # 查找 HotItem 元素
        if 'HotItem' in html:
            print('找到 HotItem 类名')
            # 统计数量
            count = html.count('HotItem')
            print(f'HotItem 出现次数：{count}')

        # 查找热榜标题
        import re
        titles = re.findall(r'<h1[^>]*class="HotItem-title"[^>]*>(.*?)</h1>', html, re.DOTALL)
        print(f'找到 {len(titles)} 个热榜标题')
        for i, title in enumerate(titles[:5]):
            # 去除 HTML 标签
            clean_title = re.sub(r'<[^>]+>', '', title)
            print(f'  [{i+1}] {clean_title[:50]}')

        await context.close()
        print('调试完成！')


if __name__ == '__main__':
    asyncio.run(debug_zhihu_html())
