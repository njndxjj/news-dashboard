#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""运行所有爬虫更新数据"""

import asyncio
from crawlers import ToutiaoCrawler, WeiboCrawler, ZhihuCrawler, BaiduCrawler, BilibiliCrawler, Kr36Crawler
from database import save_news, init_db
import time
import json
import os
import sqlite3
from datetime import datetime
import urllib.request

# 飞书 Webhook 配置
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')

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
    # 确保数据库已初始化（带重试机制）
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            init_db()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries - 1:
                print(f'数据库被锁定，等待 3 秒后重试... (尝试 {attempt + 1}/{max_retries})')
                time.sleep(3)
            else:
                raise

    results = []
    total_saved = 0
    total_fetched = 0

    for name, crawler in crawlers:
        try:
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 开始爬取：{name}')
            news_items = await crawler.fetch()
            # 转换为 save_news 需要的格式
            news_list = [item.to_dict() for item in news_items]
            saved_count = save_news(news_list)
            msg = f'✓ {name} 爬取完成，新增 {saved_count}/{len(news_items)} 条新闻'
            print(msg)
            results.append({
                'name': name,
                'success': True,
                'total': len(news_items),
                'saved': saved_count,
                'message': msg
            })
            total_saved += saved_count
            total_fetched += len(news_items)
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
    summary = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 所有爬虫执行完成，总计：成功 {len([r for r in results if r["success"]])}/{len(crawlers)} 个平台，新增 {total_saved}/{total_fetched} 条新闻'
    print(f'\n{summary}')

    # 发送到飞书
    if FEISHU_WEBHOOK and total_saved > 0:
        try:
            send_feishu_notification(results, total_saved, total_fetched)
        except Exception as e:
            print(f'发送飞书通知失败：{e}')

    return {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'total_saved': total_saved,
        'total_fetched': total_fetched
    }


def send_feishu_notification(results, total_saved, total_fetched):
    """发送执行结果到飞书"""
    success_count = len([r for r in results if r['success']])

    # 构建消息内容
    lines = []
    lines.append(f"**🤖 新闻爬虫执行完成**")
    lines.append(f"**执行时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**平台状态:** 成功 {success_count}/{len(results)} 个")
    lines.append(f"**新增新闻:** {total_saved}/{total_fetched} 条")
    lines.append("")
    lines.append("**各平台详情:**")

    for r in results:
        icon = "✅" if r['success'] else "❌"
        if r['success']:
            lines.append(f"{icon} {r['name']}: 新增 {r['saved']}/{r['total']} 条")
        else:
            lines.append(f"{icon} {r['name']}: 失败 - {r.get('error', '未知错误')}")

    content = "\n".join(lines)

    # 构建飞书消息
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }

    # 发送请求
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req, timeout=10)
    print(f'已发送飞书通知')


if __name__ == '__main__':
    result = asyncio.run(run_all_crawlers())
    # 输出 JSON 日志，便于定时任务系统记录
    print(f"\n###LOG_START###\n{json.dumps(result, ensure_ascii=False)}\n###LOG_END###")
