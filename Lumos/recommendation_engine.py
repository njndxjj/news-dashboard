"""
推荐系统模块 - 纯 API + 算法模式（无需浏览器）
支持：协同过滤推荐、内容推荐、混合推荐
策略：使用搜索引擎 API + 本地算法，不依赖 Playwright
"""

import hashlib
from datetime import datetime
from typing import List, Dict
import requests
import os


def get_proxy_from_env():
    """从环境变量获取代理配置"""
    proxy_server = os.environ.get('PROXY_SERVER')
    if proxy_server:
        return proxy_server

    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')

    if https_proxy:
        return https_proxy
    elif http_proxy:
        return http_proxy
    return None


class HybridRecommender:
    """
    混合推荐系统（无需浏览器）
    结合：实时热度 API + 内容相似度 + 协同过滤算法
    """

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.user_history_cache = {}

    def fetch_similar_items_api(self, title: str, limit: int = 10) -> List[Dict]:
        """
        基于内容相似度推荐
        使用 Bing News API 搜索相似内容
        """
        results = []

        try:
            # 使用 Bing News Search（无需 API key 的替代方案）
            search_query = title.replace(' ', '+')
            url = f'https://www.bing.com/news/search?q={search_query}&format=rss'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10, proxies={
                'http': self.proxy,
                'https': self.proxy
            } if self.proxy else None)

            if response.status_code == 200:
                # 简单解析 RSS（实际项目可用 xml.etree.ElementSelector）
                import re
                items = re.findall(r'<item>.*?</item>', response.text, re.DOTALL)

                for idx, item in enumerate(items[:limit]):
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    source_match = re.search(r'<source[^>]*>(.*?)</source>', item)

                    if title_match and link_match:
                        results.append({
                            'title': title_match.group(1),
                            'link': link_match.group(1),
                            'source': source_match.group(1) if source_match else 'Bing News',
                            'recommendation_type': 'similar_content',
                            'score': max(0, 100 - idx * 10),
                            'reason': f'与"{title[:20]}..."相关内容'
                        })

            if results:
                print(f'[相似内容 API] 成功获取 {len(results)} 条推荐')
                return results

        except Exception as e:
            print(f'[相似内容 API] 获取失败：{e}')

        # 降级：返回基于关键词的本地推荐
        return self._local_content_recommendation(title, limit)

    def _local_content_recommendation(self, title: str, limit: int = 10) -> List[Dict]:
        """
        本地内容推荐（降级方案）
        基于关键词匹配
        """
        # 简单实现：基于标题关键词生成推荐
        keywords = self._extract_keywords(title)
        results = []

        # 模拟推荐数据（实际可连接本地数据库）
        for idx, keyword in enumerate(keywords[:3]):
            results.append({
                'title': f'深度解读：{keyword} 最新进展',
                'link': f'https://www.bing.com/news/search?q={keyword}',
                'source': '聚合推荐',
                'recommendation_type': 'similar_content',
                'score': 90 - idx * 10,
                'reason': f'匹配关键词：{keyword}'
            })

        return results[:limit]

    def _extract_keywords(self, text: str) -> List[str]:
        """简单关键词提取"""
        # 移除常见停用词
        stop_words = {'的', '了', '在', '是', '和', '与', '或', '就', '都', '而', '及', '到', '着', '过', '看', '让', '对', '为', '就'}
        words = []
        current = ''

        for char in text:
            if char.isalpha() or char.isdigit():
                current += char
            else:
                if current and current not in stop_words and len(current) > 1:
                    words.append(current)
                current = ''

        if current and current not in stop_words and len(current) > 1:
            words.append(current)

        return words[:5]

    def fetch_trending_topics_api(self, category: str = 'all', limit: int = 10) -> List[Dict]:
        """
        获取 trending 话题推荐
        使用公开 API 获取实时热点
        """
        results = []

        # 热点数据源
        sources = [
            {
                'name': '微博热搜',
                'api_url': 'https://weibo.com/ajax/side/hotSearch',
                'type': 'weibo'
            },
            {
                'name': '知乎热榜',
                'api_url': 'https://www.zhihu.com/api/v3/feed/topstory/hot-list?limit=10',
                'type': 'zhihu'
            },
            {
                'name': '36 氪热点',
                'api_url': 'https://api.36kr.com/api/visitor/news/hot',
                'type': '36kr'
            }
        ]

        for source in sources:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }

                response = requests.get(source['api_url'], headers=headers, timeout=8, proxies={
                    'http': self.proxy,
                    'https': self.proxy
                } if self.proxy else None)

                if response.status_code == 200:
                    data = response.json()

                    if source['type'] == 'weibo' and data.get('ok') == 1:
                        hot_data = data.get('data', {}).get('realtime', [])
                        for idx, item in enumerate(hot_data[:5], 1):
                            results.append({
                                'title': item.get('note', ''),
                                'link': f"https://s.weibo.com/weibo?q={item.get('note', '')}",
                                'source': source['name'],
                                'recommendation_type': 'trending',
                                'score': 100 - idx * 15,
                                'reason': f'{source["name"]} 热榜 TOP{idx}',
                                'rank': idx
                            })

                    elif source['type'] == 'zhihu' and 'data' in data:
                        for idx, item in enumerate(data['data'][:5], 1):
                            target = item.get('target', {})
                            results.append({
                                'title': target.get('title', ''),
                                'link': target.get('url', '').replace('api.', ''),
                                'source': source['name'],
                                'recommendation_type': 'trending',
                                'score': 100 - idx * 15,
                                'reason': f'{source["name"]} 热榜 TOP{idx}',
                                'rank': idx
                            })

            except Exception as e:
                print(f'获取{source["name"]}热点失败：{e}')

        return results[:limit]

    def get_collaborative_recommendations(self, user_keywords: List[str], limit: int = 10) -> List[Dict]:
        """
        基于用户兴趣的协同过滤推荐
        使用搜索 API 获取相关领域内容
        """
        results = []

        if not user_keywords:
            return results

        query = ' '.join(user_keywords[:3])

        try:
            # 使用 Bing News 搜索
            url = f'https://www.bing.com/news/search?q={query}&format=rss'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10, proxies={
                'http': self.proxy,
                'https': self.proxy
            } if self.proxy else None)

            if response.status_code == 200:
                import re
                items = re.findall(r'<item>.*?</item>', response.text, re.DOTALL)

                for idx, item in enumerate(items[:limit]):
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)

                    if title_match and link_match:
                        results.append({
                            'title': title_match.group(1),
                            'link': link_match.group(1),
                            'source': '协同推荐',
                            'recommendation_type': 'collaborative',
                            'score': 85 + (5 if idx < 3 else 0),
                            'reason': f'匹配您的兴趣：{", ".join(user_keywords[:2])}'
                        })

            if results:
                print(f'[协同推荐 API] 成功获取 {len(results)} 条推荐')
                return results

        except Exception as e:
            print(f'[协同推荐 API] 获取失败：{e}')

        # 降级：本地推荐
        return self._local_collaborative_recommendation(user_keywords, limit)

    def _local_collaborative_recommendation(self, user_keywords: List[str], limit: int = 10) -> List[Dict]:
        """本地协同过滤推荐（降级方案）"""
        results = []

        for idx, keyword in enumerate(user_keywords[:limit]):
            results.append({
                'title': f'专题：{keyword} 深度解析',
                'link': f'https://www.bing.com/news/search?q={keyword}',
                'source': '兴趣推荐',
                'recommendation_type': 'collaborative',
                'score': 85,
                'reason': f'匹配兴趣：{keyword}'
            })

        return results[:limit]

    def generate_hybrid_recommendations(
        self,
        news_list: List[Dict],
        user_keywords: List[str] = None,
        history: List[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        生成混合推荐结果
        结合：协同过滤 + 内容推荐 + 实时热度
        """
        all_recommendations = []

        # 1. 趋势推荐（API）
        try:
            trending = self.fetch_trending_topics_api(limit=5)
            all_recommendations.extend(trending)
        except Exception as e:
            print(f'趋势推荐失败：{e}')

        # 2. 协同过滤推荐（API 优先）
        if user_keywords:
            try:
                collab = self.get_collaborative_recommendations(user_keywords, limit=5)
                all_recommendations.extend(collab)
            except Exception as e:
                print(f'协同推荐失败：{e}')

        # 3. 相似内容推荐（API 优先）
        if news_list and len(news_list) > 0:
            top_news = news_list[:3]
            for news in top_news:
                title = news.get('title', '')
                if title:
                    try:
                        similar = self.fetch_similar_items_api(title, limit=3)
                        all_recommendations.extend(similar)
                    except Exception as e:
                        print(f'相似内容推荐失败：{e}')

        # 去重（基于标题哈希）
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            title = rec.get('title', '')
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique_recommendations.append(rec)

        # 按推荐分数排序
        unique_recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)

        return unique_recommendations[:limit]


def sync_generate_recommendations(
    news_list: List[Dict],
    user_keywords: List[str] = None,
    history: List[Dict] = None,
    limit: int = 10,
    proxy: str = None
) -> List[Dict]:
    """
    同步包装函数，供 Flask 使用
    """
    recommender = HybridRecommender(proxy=proxy)
    return recommender.generate_hybrid_recommendations(
        news_list=news_list,
        user_keywords=user_keywords,
        history=history,
        limit=limit
    )


if __name__ == '__main__':
    # 测试
    proxy = get_proxy_from_env()
    print(f'使用代理：{proxy or "无"}')

    test_news = [
        {'title': '人工智能大模型技术突破'},
        {'title': '新能源汽车销量创新高'}
    ]

    test_keywords = ['人工智能', '科技创新']

    recommendations = sync_generate_recommendations(
        news_list=test_news,
        user_keywords=test_keywords,
        limit=10,
        proxy=proxy
    )

    print(f'\n生成 {len(recommendations)} 条推荐:')
    for rec in recommendations[:5]:
        print(f"- {rec['title']} (分数：{rec['score']}, 类型：{rec['recommendation_type']})")
