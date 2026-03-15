"""
新闻平台爬虫模块
支持多个新闻平台的数据抓取
"""

from .base import BaseCrawler
from .toutiao import ToutiaoCrawler
from .weibo import WeiboCrawler
from .zhihu import ZhihuCrawler
from .baidu import BaiduCrawler
from .bilibili import BilibiliCrawler
from .kr36 import Kr36Crawler

__all__ = [
    'BaseCrawler',
    'ToutiaoCrawler',
    'WeiboCrawler',
    'ZhihuCrawler',
    'BaiduCrawler',
    'BilibiliCrawler',
    'Kr36Crawler',
]
