"""
爬虫基类
定义爬虫的通用接口和方法
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NewsItem:
    """新闻条目"""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        hot_value: Optional[float] = None,
        rank: Optional[int] = None,
        summary: Optional[str] = None,
        image_url: Optional[str] = None,
        publish_time: Optional[datetime] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.url = url
        self.source = source
        self.hot_value = hot_value  # 热度值
        self.rank = rank  # 排名
        self.summary = summary  # 摘要
        self.image_url = image_url  # 图片 URL
        self.publish_time = publish_time  # 发布时间
        self.extra = extra or {}
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'hot_value': self.hot_value,
            'rank': self.rank,
            'summary': self.summary,
            'image_url': self.image_url,
            'published': self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None,
            'publish_time': self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None,
            'extra': self.extra,
        }

    def __repr__(self):
        return f"NewsItem(title={self.title!r}, rank={self.rank}, hot_value={self.hot_value})"


class BaseCrawler(ABC):
    """爬虫基类"""

    # 子类需要覆盖的属性
    platform: str = "base"  # 平台标识
    platform_name: str = "Base Platform"  # 平台中文名

    @abstractmethod
    async def fetch(self) -> List[NewsItem]:
        """
        抓取数据
        返回 NewsItem 列表
        """
        pass

    def parse_hot_value(self, hot_str: str) -> Optional[float]:
        """解析热度值"""
        if not hot_str:
            return None
        try:
            # 移除"万"、"亿"等单位
            hot_str = hot_str.strip().lower()
            if '亿' in hot_str:
                return float(hot_str.replace('亿', '')) * 10000
            elif '万' in hot_str:
                return float(hot_str.replace('万', ''))
            else:
                # 尝试直接转换数字
                return float(hot_str.replace(',', ''))
        except (ValueError, AttributeError):
            return None

    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        return text.strip()
