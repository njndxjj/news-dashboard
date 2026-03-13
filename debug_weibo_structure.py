"""调试微博详细结构"""
import asyncio
from playwright.async_api import async_playwright


async def debug_weibo_structure():
    print('开始调试微博详细结构...')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/lobsterai-debug-profile3',
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-gpu', '--no-sandbox', '--no-first-run'],
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print('访问微博热搜页面...')
        await page.goto('https://s.weibo.com/top/summary', timeout=60000)
        await page.wait_for_timeout(8000)

        # 查找所有 li 元素
        li_elements = await page.query_selector_all('li')
        print(f'找到 {len(li_elements)} 个 li 元素')

        # 查找所有包含数字的列表项
        for i, li in enumerate(li_elements[:5]):
            text = await li.inner_text()
            if '万' in text or (text and any(c.isdigit() for c in text)):
                print(f'\n--- li[{i}] ---')
                print(f'内容：{text[:200]}')
                # 获取类名
                class_name = await li.get_attribute('class')
                print(f'类名：{class_name}')
                # 查找内部的链接
                links = await li.query_selector_all('a')
                for j, link in enumerate(links):
                    href = await link.get_attribute('href')
                    title = await link.inner_text()
                    print(f'  链接[{j}]: {title[:50]} - {href[:50] if href else "N/A"}')

        # 尝试查找特定的列表容器
        print('\n--- 查找列表容器 ---')
        containers = await page.query_selector_all('.wrap-list ul')
        print(f'找到 {len(containers)} 个 .wrap-list ul')

        if containers:
            items = await containers[0].query_selector_all('li')
            print(f'容器内有 {len(items)} 个 li 元素')
            for i, item in enumerate(items[:3]):
                text = await item.inner_text()
                print(f'  [{i}] {text[:100]}')

        await context.close()


if __name__ == '__main__':
    asyncio.run(debug_weibo_structure())
