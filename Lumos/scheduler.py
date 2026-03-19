#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lumos 定时任务调度器
- 每 10 分钟执行一次 RSS 爬取
- 每天早上 9 点发送邮件日报
- 支持自定义调度任务
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加 backend 目录到 Python 路径
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))


def load_rss_feeds():
    """加载 RSS 源列表"""
    rss_file = backend_path / 'rss_feeds.yaml'
    if rss_file.exists():
        import yaml
        with open(rss_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('rss_feeds', [])
    return []


def fetch_rss_feed(url):
    """抓取单个 RSS 源"""
    try:
        import feedparser
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:10]:  # 每个源最多取 10 篇
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', ''),
                'source': feed.feed.get('title', url)
            })
        logger.info(f"✅ 抓取成功：{url} - {len(articles)} 篇文章")
        return articles
    except Exception as e:
        logger.error(f"❌ 抓取失败：{url} - {e}")
        return []


def crawl_rss_task():
    """RSS 爬取任务（每 10 分钟执行）"""
    logger.info("=" * 50)
    logger.info(f"🕐 开始执行 RSS 爬取任务 - {datetime.now()}")

    feeds = load_rss_feeds()
    if not feeds:
        logger.warning("⚠️  未找到 RSS 源配置")
        return

    all_articles = []
    for feed_url in feeds:
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)
        time.sleep(1)  # 避免请求过快

    logger.info(f"📊 本次爬取共 {len(all_articles)} 篇文章")
    logger.info("=" * 50)

    # TODO: 将文章保存到数据库
    # from data_processing import save_to_neo4j
    # save_to_neo4j(all_articles)


def daily_report_task():
    """每日日报任务（每天早上 9 点执行）"""
    logger.info("=" * 50)
    logger.info(f"📧 开始发送每日日报 - {datetime.now()}")

    # TODO: 从数据库获取昨天的热点文章
    # TODO: 生成摘要
    # TODO: 发送邮件

    logger.info("✅ 每日日报发送完成")
    logger.info("=" * 50)


def cleanup_cache_task():
    """清理缓存任务（每天凌晨 3 点执行）"""
    logger.info("🧹 开始清理缓存...")

    # TODO: 清理 Redis 缓存
    # from cache import cache_manager
    # cache_manager.clear_all()

    logger.info("✅ 缓存清理完成")


def setup_scheduler():
    """设置定时任务"""
    logger.info("🚀 启动 Lumos 定时任务调度器")

    # RSS 爬取：每 10 分钟
    schedule.every(10).minutes.do(crawl_rss_task)
    logger.info("✓ 已添加 RSS 爬取任务（每 10 分钟）")

    # 每日日报：每天早上 9 点
    schedule.every().day.at("09:00").do(daily_report_task)
    logger.info("✓ 已添加每日日报任务（09:00）")

    # 清理缓存：每天凌晨 3 点
    schedule.every().day.at("03:00").do(cleanup_cache_task)
    logger.info("✓ 已添加缓存清理任务（03:00）")


def run_scheduler():
    """运行调度器"""
    setup_scheduler()

    logger.info("\n按 Ctrl+C 停止调度器\n")
    logger.info("当前任务列表:")
    logger.info(f"  - RSS 爬取：每 10 分钟")
    logger.info(f"  - 每日日报：每天 09:00")
    logger.info(f"  - 清理缓存：每天 03:00")
    logger.info("")

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 收到停止信号，正在退出...")
            break
        except Exception as e:
            logger.error(f"❌ 调度器异常：{e}")
            time.sleep(5)


if __name__ == "__main__":
    run_scheduler()
