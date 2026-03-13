"""调试微博 HTML 结构"""
import asyncio
from playwright.async_api import async_playwright
import re


async def debug_weibo_html():
    print('开始调试微博 HTML 结构...')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-debug-profile4',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-gpu', '--no-sandbox', '--no-first-run'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问微博热搜页面...')
        await page.goto('https://s.weibo.com/top/summary', timeout=60000)
        await page.wait_for_timeout(8000)

        # 获取页面 HTML
        html = await page.content()

        # 查找包含热搜内容的 div
        pattern = re.compile(r'(<div[^>]*class="[^"]*hot[^"]*"[^>]*>.*?</div>)', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(html)
        print(f'找到 {len(matches)} 个包含 "hot" 的 div')

        # 查找列表结构
        list_pattern = re.compile(r'(<ul[^>]*>.*?</ul>)', re.DOTALL)
        lists = list_pattern.findall(html)
        print(f'找到 {len(lists)} 个 ul 列表')

        for i, lst in enumerate(lists[:3]):
            li_count = lst.count('<li')
            if li_count > 5:
                print(f'\n--- 列表 [{i}] 有 {li_count} 个 li ---')
                # 提取第一个 li
                li_match = re.search(r'<li[^>]*>(.*?)</li>', lst, re.DOTALL)
                if li_match:
                    print(f'第一个 li: {li_match.group(1)[:300]}')

        # 查找包含"序号"或"关键词"的内容
        if '序号' in html or '关键词' in html:
            print('\n找到包含"序号"或"关键词"的表格结构')
            # 找到表格开始位置
            idx = html.find('序号')
            print(f'内容片段：{html[idx-50:idx+500]}')

        await context.close()


if __name__ == '__main__':
    asyncio.run(debug_weibo_html())
