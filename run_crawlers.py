#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""运行所有爬虫更新数据"""

import asyncio
from crawlers import ToutiaoCrawler, WeiboCrawler, ZhihuCrawler, BaiduCrawler, BilibiliCrawler, Kr36Crawler
from database import save_news, init_db
import time
import json
from datetime import datetime

crawlers = [
    ('今日头条', ToutiaoCrawler()),
    ('微博热搜', WeiboCrawler()),
    ('知乎热榜', ZhihuCrawler()),
    ('百度热搜', BaiduCrawler()),
    ('B 站热搜', BilibiliCrawler()),
    ('36 氪科技', Kr36Crawler()),
]

async def run_all_crawlers():
    """异步运行所有爬虫"""
    # 确保数据库已初始化
    init_db()

    results = []
    for name, crawler in crawlers:
        try:
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 开始爬取：{name}')
            news_items = await crawler.fetch()
            # 转换为 save_news 需要的格式
            news_list = [item.to_dict() for item in news_items]
            saved_count = save_news(news_list)
            msg = f'✓ {name} 爬取完成，新增 {saved_count}/{len(news_list)} 条新闻'
            print(msg)
            results.append({
                'name': name,
                'success': True,
                'total': len(news_list),
                'saved': saved_count,
                'message': msg
            })
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            msg = f'✗ {name} 爬取失败：{e}'
            print(msg)
            results.append({
                'name': name,
                'success': False,
                'error': str(e),
                'message': msg
            })

    # 输出汇总日志
    print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 所有爬虫执行完成')
    print(f'总计：成功 {len([r for r in results if r["success"]])}/{len(crawlers)} 个平台')

    return {
        'timestamp': datetime.now().isoformat(),
        'results': results
    }

if __name__ == '__main__':
    result = asyncio.run(run_all_crawlers())
    # 输出 JSON 日志，便于定时任务系统记录
    print(f"\n###LOG_START###\n{json.dumps(result, ensure_ascii=False)}\n###LOG_END###")
