"""
Redis 缓存工具模块
提供统一的缓存接口和装饰器
"""

import redis
import json
import os
from functools import wraps
import hashlib

# Redis 配置
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# 缓存键前缀
CACHE_PREFIX = 'lumos:'

# 默认缓存时间（秒）
DEFAULT_TTL = {
    'news_list': 600,  # 新闻列表 10 分钟
    'user_interests': 3600,  # 用户兴趣 1 小时
    'industry_summary': 3600,  # 行业总结 1 小时
    'hot_news': 300,  # 热点新闻 5 分钟
    'recommendation': 600,  # 推荐结果 10 分钟
    'user_subscription': 1800,  # 用户订阅 30 分钟
}


class RedisCache:
    """Redis 缓存管理类"""

    def __init__(self):
        self.client = None
        self.enabled = False
        self._connect()

    def _connect(self):
        """连接 Redis"""
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            self.client.ping()
            self.enabled = True
            print(f"✅ Redis 连接成功：{REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"⚠️  Redis 连接失败，缓存功能已禁用：{e}")
            self.enabled = False

    def _make_key(self, key):
        """生成完整缓存键"""
        return f"{CACHE_PREFIX}{key}"

    def get(self, key):
        """获取缓存数据"""
        if not self.enabled:
            return None

        try:
            data = self.client.get(self._make_key(key))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis GET 错误：{e}")
            return None

    def set(self, key, value, ttl=None):
        """设置缓存数据"""
        if not self.enabled:
            return False

        try:
            ttl = ttl or DEFAULT_TTL.get(key.split(':')[0], 600)
            data = json.dumps(value, ensure_ascii=False)
            self.client.setex(self._make_key(key), ttl, data)
            return True
        except Exception as e:
            print(f"Redis SET 错误：{e}")
            return False

    def delete(self, key):
        """删除缓存"""
        if not self.enabled:
            return False

        try:
            self.client.delete(self._make_key(key))
            return True
        except Exception as e:
            print(f"Redis DELETE 错误：{e}")
            return False

    def delete_pattern(self, pattern):
        """批量删除匹配模式的缓存"""
        if not self.enabled:
            return False

        try:
            keys = self.client.keys(self._make_key(pattern))
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis DELETE PATTERN 错误：{e}")
            return False

    def clear_all(self):
        """清空所有缓存"""
        if not self.enabled:
            return False

        try:
            keys = self.client.keys(f"{CACHE_PREFIX}*")
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis CLEAR ALL 错误：{e}")
            return False

    def incr(self, key, amount=1):
        """计数器自增"""
        if not self.enabled:
            return 0

        try:
            return self.client.incr(self._make_key(key), amount)
        except Exception as e:
            print(f"Redis INCR 错误：{e}")
            return 0

    def get_stats(self):
        """获取缓存统计信息"""
        if not self.enabled:
            return {'enabled': False}

        try:
            info = self.client.info('stats')
            keys_count = self.client.dbsize()

            return {
                'enabled': True,
                'keys_count': keys_count,
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)),
                'memory_usage': self.client.info('memory').get('used_memory_human', 'unknown')
            }
        except Exception as e:
            return {'enabled': False, 'error': str(e)}


# 全局缓存实例
cache = RedisCache()


def cache_with_redis(key_pattern, ttl=None):
    """
    Redis 缓存装饰器

    用法:
        @cache_with_redis('news:{user_id}:{limit}')
        def get_news(user_id='default', limit=300):
            # 原始函数逻辑
            return news_list

    参数:
        key_pattern: 缓存键模式，支持 {参数名} 占位符
        ttl: 缓存时间（秒），可选
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # 生成缓存键
            try:
                cache_key = key_pattern.format(**bound.arguments)
            except KeyError as e:
                raise ValueError(f"缓存键模式中的参数 {e} 未在函数参数中找到")

            # 尝试从缓存获取
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            # 执行原函数
            result = func(*args, **kwargs)

            # 写入缓存
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    """
    缓存失效装饰器（用于写操作后清除缓存）

    用法:
        @invalidate_cache('news:*')
        def refresh_news():
            # 刷新新闻逻辑
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)
            # 清除缓存
            cache.delete_pattern(key_pattern)
            return result
        return wrapper
    return decorator


# 便捷函数
def get_cache(key):
    """获取缓存"""
    return cache.get(key)


def set_cache(key, value, ttl=None):
    """设置缓存"""
    cache.set(key, value, ttl)


def delete_cache(key):
    """删除缓存"""
    cache.delete(key)


def clear_news_cache():
    """清除新闻相关缓存"""
    cache.delete_pattern('news:*')
    cache.delete_pattern('hot:*')
    cache.delete_pattern('recommend:*')
