from flask import Flask, render_template, jsonify, request
import feedparser
import datetime
import hashlib
from concurrent.futures import ThreadPoolExecutor
import time
import re
import urllib.request
import json
import os
import yaml

# 通义千问 API 配置
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')

# 飞书 Webhook 配置
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')

app = Flask(__name__, template_folder='templates')

# 导入数据库和推送模块
from database import (
    init_db, get_news, get_hot_news, get_news_by_keywords, save_news,
    get_push_rules, save_push_rule, update_push_rule, delete_push_rule,
    get_push_logs, get_setting, update_setting, get_all_settings,
    get_news_count, get_latest_published, save_push_log, get_news_by_channel,
    get_user_interests, record_user_click, get_user_click_history, get_personalized_news
)
from feishu_push import (
    send_feishu_message, format_single_news_card, format_breaking_news_batch,
    format_daily_summary, check_and_push_notifications, send_test_push,
    send_daily_summary_push
)

# 导入爬虫模块
import asyncio
from crawlers import ToutiaoCrawler, WeiboCrawler, ZhihuCrawler, BaiduCrawler, BilibiliCrawler, Kr36Crawler

# 初始化数据库
init_db()

# 如果环境变量配置了飞书 Webhook，则更新到数据库
if FEISHU_WEBHOOK:
    update_setting('feishu_webhook', FEISHU_WEBHOOK)


# ==================== 从配置文件加载平台配置 ====================

def load_platforms():
    """从 config/config.yaml 加载平台配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')

    if not os.path.exists(config_path):
        print(f"警告：配置文件不存在：{config_path}")
        return []

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        platforms = config.get('platforms', [])
        # 过滤掉被注释的平台（在 YAML 中不会被加载）
        enabled_platforms = [p for p in platforms if isinstance(p, dict)]

        print(f"已加载 {len(enabled_platforms)} 个监控平台")
        return enabled_platforms
    except Exception as e:
        print(f"加载配置文件失败：{e}")
        return []


def load_rss_mapping():
    """从 config/rss_mapping.yaml 加载 RSS 映射"""
    mapping_path = os.path.join(os.path.dirname(__file__), 'config', 'rss_mapping.yaml')

    if not os.path.exists(mapping_path):
        print(f"警告：RSS 映射文件不存在：{mapping_path}")
        return {}

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('rss_mapping', {})
    except Exception as e:
        print(f"加载 RSS 映射失败：{e}")
        return {}


# 加载平台配置和 RSS 映射
PLATFORMS = load_platforms()
RSS_MAPPING = load_rss_mapping()

# 构建可用的 RSS 源列表（按地区分类）
RSS_FEEDS_DOMESTIC = []
RSS_FEEDS_OVERSEAS = []

for platform in PLATFORMS:
    platform_id = platform.get('id', '')
    platform_name = platform.get('name', platform_id)

    if platform_id in RSS_MAPPING:
        rss_config = RSS_MAPPING[platform_id]

        # 支持新旧两种格式
        if isinstance(rss_config, dict):
            rss_url = rss_config.get('url', '')
            requires_crawler = rss_config.get('requires_crawler', False)
            region = rss_config.get('region', 'domestic')
        else:
            rss_url = rss_config
            requires_crawler = False
            region = 'domestic'

        # 跳过需要爬虫的接口地址
        if requires_crawler or 'cls.cn/api' in rss_url:
            continue

        feed_info = {
            "name": platform_name,
            "url": rss_url,
            "region": region
        }

        if region == 'overseas':
            RSS_FEEDS_OVERSEAS.append(feed_info)
        else:
            RSS_FEEDS_DOMESTIC.append(feed_info)

# 需要爬虫抓取的平台 ID 列表（没有 RSS 源的）
# 已实现爬虫的平台
CRAWLER_IMPLEMENTED = ['toutiao', 'baidu', 'weibo', 'zhihu', 'bilibili-hot-search', 'kr36']
# 待实现爬虫的平台
CRAWLER_PENDING = [
    'douyin', 'tieba', 'hupu', 'nowcoder', 'pcbeta', 'sspai',
    'chongbuluo', 'jin10', 'fastbull', 'tencent-hot', 'cls-telegraph',
    'cls-depth', 'cls-hot', 'wallstreetcn-quick', 'kaopu', 'mktnews',
    'cankaoxiaoxi', 'sputniknewscn'
]
CRAWLER_PLATFORMS = CRAWLER_IMPLEMENTED + CRAWLER_PENDING

print(f"当前启用 {len(RSS_FEEDS_DOMESTIC)} 个国内 RSS 源，{len(RSS_FEEDS_OVERSEAS)} 个国外 RSS 源")
print(f"另有 {len(CRAWLER_IMPLEMENTED)} 个平台通过爬虫获取")

# 缓存数据
cached_news = []
last_update = None
ai_analysis_cache = None  # AI 分析结果缓存

def ai_deep_analysis(news_list):
    """使用通义千问进行深度 AI 分析"""
    if not DASHSCOPE_API_KEY:
        return None  # API Key 未配置，返回 None 使用备用方案

    try:
        import dashscope
        from dashscope import Generation

        # 设置 API Key
        dashscope.api_key = DASHSCOPE_API_KEY

        # 准备分析的新闻数据（精选 20 条代表性新闻）
        精选新闻 = news_list[:20]
        news_summary = "\n".join([
            f"- [{n['source']}] {n['title']} ({n['original_title'] or n['title']})"
            for n in 精选新闻
        ])

        # 构建分析提示词（专家视角，面向高管汇报）
        prompt = f"""你是一位资深商业情报专家，正在为企业高管和决策者撰写舆情分析报告。请基于以下最新新闻进行高度概括和深度分析：

{news_summary}

**报告定位**：
- 受众：企业老板、高管、战略观察员
- 风格：专业、精炼、有洞察力，避免冗余信息
- 目标：让决策者在 3 分钟内掌握核心动态和关键行动点

请输出 JSON 格式的分析报告，包含以下字段：
{{
    "executive_summary": "100 字以内的核心摘要，高度概括，直击要点，让高管一眼看懂当前局势",
    "sentiment_analysis": {{
        "overall": "positive/neutral/negative",
        "positive_rate": 0.0-1.0,
        "key_drivers": ["正面驱动因素 1", "正面驱动因素 2", ...]
    }},
    "trend_insights": [
        {{"trend": "趋势名称", "confidence": "high/medium/low", "evidence": "支撑证据（具体新闻事件）", "impact": "对本企业的潜在影响"}}
    ],
    "competitive_intelligence": [
        {{"company": "公司/机构名", "action": "关键动态/战略举措", "implication": "对我方的启示或威胁"}}
    ],
    "risk_warnings": [
        {{"risk": "风险描述（具体且可操作）", "severity": "high/medium/low", "suggestion": "应对建议（可落地的行动方案）"}}
    ],
    "opportunities": ["具体市场机会 1", "具体市场机会 2", ...],
    "recommended_actions": ["高管应采取的行动 1", "高管应采取的行动 2", ...]
}}

**撰写要求**：
1. 用中文输出，语言专业、精准
2. 核心摘要必须高度凝练，体现情报价值
3. 趋势洞察要有前瞻性，体现专家视角
4. 竞争情报要聚焦头部玩家和颠覆性动态
5. 风险预警要具体可感知，避免空泛
6. 行动建议要可执行、可落地、有优先级
7. 基于新闻事实，不要臆测或编造
8. 如果没有明显风险或机会，对应字段可以是空数组"""

        # 调用通义千问 API
        response = Generation.call(
            model='qwen-max',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        print(f"API 响应状态码：{response.status_code}")

        if response.status_code == 200:
            # dashscope 响应结构：response.output.text 或 response.output.choices[0].message.content
            content = None
            if hasattr(response.output, 'text') and response.output.text:
                content = response.output.text
            elif hasattr(response.output, 'choices') and response.output.choices:
                content = response.output.choices[0].message.content

            if not content:
                print(f"AI 分析：无法获取响应内容")
                return None

            # 尝试解析 JSON
            try:
                # 清理可能的 markdown 标记
                content = content.replace('```json', '').replace('```', '').strip()
                analysis_result = json.loads(content)
                return analysis_result
            except json.JSONDecodeError as e:
                print(f"AI 分析：JSON 解析失败：{e}")
                return None
        else:
            print(f"AI 分析：API 调用失败：{response.code} - {response.message}")
            return None

    except Exception as e:
        print(f"AI 分析异常：{e}")
        return None

def fallback_analysis(news_list):
    """备用分析方案（当 API 不可用时）"""
    total = len(news_list)
    if total == 0:
        return None

    # 简单情感统计
    positive = sum(1 for n in news_list if n.get('sentiment') == 'positive')
    negative = sum(1 for n in news_list if n.get('sentiment') == 'negative')
    neutral = total - positive - negative

    # 提取关键词（基于词频）
    all_titles = ' '.join([n['title'] for n in news_list])
    # 简单分词（按标点和空格）
    words = re.findall(r'[\u4e00-\u9fff]+|[A-Za-z]+', all_titles)
    # 过滤常见停用词
    stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '了', '一个']
    filtered_words = [w for w in words if w.lower() not in stopwords and len(w) > 1]

    from collections import Counter
    word_freq = Counter(filtered_words)
    top_keywords = word_freq.most_common(5)

    # 行业分类（基于关键词匹配）
    industry_keywords = {
        '人工智能': ['AI', '人工智能', '大模型', 'GPT', '智能', '算法', '机器学习'],
        '智能汽车': ['汽车', '新能源', '电动车', '智能驾驶', '特斯拉', '比亚迪'],
        '消费电子': ['手机', '折叠屏', 'iPhone', '华为', '小米', '消费电子'],
        '企业服务': ['SaaS', '云计算', '企业', '数字化', 'B 端'],
        '金融财经': ['金融', '银行', '投资', '融资', '上市', 'IPO', '财报'],
        '医疗健康': ['医疗', '健康', '生物', '医药', '创新药'],
        '电商零售': ['电商', '零售', '消费', '淘宝', '京东', '拼多多']
    }

    industry_count = Counter()
    for title in [n['title'] for n in news_list]:
        for industry, keywords in industry_keywords.items():
            if any(kw.lower() in title.lower() for kw in keywords):
                industry_count[industry] += 1

    top_industries = industry_count.most_common(3)

    return {
        "executive_summary": f"本次共分析 {total} 条新闻，平均热度 {sum(n.get('hot_score', 0) for n in news_list)/total:.1f} 分。正面舆情 {positive/total*100:.1f}%，负面舆情 {negative/total*100:.1f}%。",
        "sentiment_analysis": {
            "overall": "positive" if positive > negative else "negative" if negative > positive else "neutral",
            "positive_rate": round(positive / total, 2),
            "key_drivers": []
        },
        "trend_insights": [{"trend": kw[0], "confidence": "medium", "evidence": f"提及{kw[1]}次", "impact": "持续关注"} for kw in top_keywords[:3]],
        "competitive_intelligence": [],
        "risk_warnings": [],
        "opportunities": [f"{ind[0]}领域活跃（{ind[1]}条新闻）" for ind in top_industries],
        "recommended_actions": ["持续关注重点行业动态", "建立负面舆情预警机制"]
    }

def analyze_sentiment(title):
    """简单的情感分析（基于关键词）"""
    positive_words = ['增长', '复苏', '利好', '突破', '创新', '领先', '成功', '发布', '新', '升级', '助力']
    negative_words = ['泄露', '危机', '下跌', '亏损', '调查', '监管', '处罚', '衰退', '下滑', '风险', '问题']

    score = 0
    for word in positive_words:
        if word in title:
            score += 1
    for word in negative_words:
        if word in title:
            score -= 1

    if score > 0:
        return 'positive'
    elif score < 0:
        return 'negative'
    return 'neutral'

def calculate_hot_score(published_time):
    """计算热度分数（基于时间新鲜度）"""
    try:
        if published_time:
            pub_datetime = datetime.datetime.strptime(published_time, '%Y-%m-%d %H:%M:%S')
            hours_diff = (datetime.datetime.now() - pub_datetime).total_seconds() / 3600
            # 越新闻越热，24 小时内从 100 递减到 50
            score = max(50, 100 - (hours_diff * 2))
            return min(100, int(score))
    except:
        pass
    return 50  # 默认分数

def detect_language(text):
    """检测文本语言（简单判断是否包含中文）"""
    # 如果包含中文字符，认为是中文
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    return 'en'


def fetch_platform_crawler(platform_id, platform_name):
    """
    爬虫抓取平台热搜/榜单
    使用 Playwright 浏览器自动化抓取
    """
    try:
        # 映射平台 ID 到爬虫类
        crawler_map = {
            'toutiao': ToutiaoCrawler,
            'baidu': BaiduCrawler,
            'weibo': WeiboCrawler,
            'zhihu': ZhihuCrawler,
            'bilibili-hot-search': BilibiliCrawler,
            'kr36': Kr36Crawler,
        }

        if platform_id not in crawler_map:
            print(f"[爬虫] 平台 {platform_id} 暂未实现爬虫支持")
            return []

        # 创建爬虫实例并执行
        crawler = crawler_map[platform_id]()

        # 运行异步爬虫
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            news_items = loop.run_until_complete(crawler.fetch())
        finally:
            loop.close()

        print(f"[爬虫] {platform_name} 抓取完成，共 {len(news_items)} 条")
        return news_items

    except Exception as e:
        print(f"[爬虫] 抓取 {platform_id} 失败：{e}")
        return []

def translate_text(text):
    """使用免费 API 翻译英文到中文"""
    try:
        # 检测语言，如果是中文直接返回
        if detect_language(text) == 'zh':
            return text

        # 使用 Google Translate API（免费）
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={urllib.request.quote(text)}"

        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            translated = ''.join([item[0] for item in data[0] if item[0]])
            return translated
        else:
            return text  # 翻译失败返回原文

    except Exception as e:
        print(f"Translation error: {e}")
        return text  # 翻译失败返回原文

def fetch_single_feed(feed_info):
    """抓取单个 RSS 源"""
    try:
        # 设置 User-Agent 避免被部分网站屏蔽
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # 先获取 RSS 内容
        req = urllib.request.Request(feed_info['url'], headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_content = response.read()

        # 解析 RSS
        feed = feedparser.parse(xml_content)
        news_items = []

        for entry in feed.entries[:10]:  # 每个源取 10 条
            title = entry.get('title', '无标题')
            link = entry.get('link', '#')
            published = entry.get('published', '')

            # 格式化时间
            if published:
                try:
                    # 尝试解析 RSS 时间格式
                    time_struct = feedparser._parse_date(published)
                    if time_struct:
                        published = datetime.datetime(*time_struct[:6]).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        published = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                except:
                    published = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                published = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 生成唯一 ID
            id_hash = hashlib.md5(f"{link}{title}".encode()).hexdigest()[:8]
            id_num = int(id_hash, 16) % 100000

            # 检测语言并翻译
            lang = detect_language(title)
            original_title = title
            translated_title = None

            # 如果是英文，进行翻译
            if lang == 'en':
                translated_title = translate_text(title)

            news_items.append({
                "id": id_num,
                "title": translated_title if translated_title else title,  # 默认显示翻译后的标题
                "original_title": original_title if lang == 'en' else None,  # 保留英文原文
                "source": feed_info['name'],
                "published": published,
                "sentiment": analyze_sentiment(title),
                "hot_score": calculate_hot_score(published),
                "link": link,  # 真实链接
                "lang": lang  # 语言标记
            })

        return news_items
    except Exception as e:
        print(f"Error fetching {feed_info['name']}: {e}")
        return []

def fetch_all_news():
    """并发抓取所有 RSS 源和爬虫平台，按顺序：爬虫平台 → 国内 RSS → 国外 RSS"""
    global cached_news, last_update

    all_news = []

    # 1. 优先抓取爬虫平台（微博、36 氪、知乎等）
    platforms_to_crawl = [p for p in PLATFORMS if p.get('id') in CRAWLER_IMPLEMENTED]

    if platforms_to_crawl:
        print("[爬虫] 开始抓取爬虫平台...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交爬虫任务
            future_to_platform = {
                executor.submit(fetch_platform_crawler, p.get('id'), p.get('name')): p
                for p in platforms_to_crawl
            }

            for future in future_to_platform:
                try:
                    news_items = future.result(timeout=60)  # 每个平台最多 60 秒
                    # 添加来源标记（NewsItem 对象需要转换为字典）
                    for item in news_items:
                        if hasattr(item, 'to_dict'):
                            item_dict = item.to_dict()
                            item_dict['priority'] = 'crawler'
                            item_dict['link'] = item_dict.get('url', '')  # 统一使用 link 字段
                            all_news.append(item_dict)
                        else:
                            item['priority'] = 'crawler'
                            all_news.append(item)
                except Exception as e:
                    platform = future_to_platform[future]
                    print(f"[爬虫] {platform.get('name')} 抓取失败：{e}")

        print(f"[爬虫] 爬虫平台抓取完成，共 {len([n for n in all_news if n.get('priority') == 'crawler'])} 条")

    # 2. 抓取国内 RSS 源
    if RSS_FEEDS_DOMESTIC:
        print("[RSS] 开始抓取国内 RSS 源...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            rss_results = list(executor.map(fetch_single_feed, RSS_FEEDS_DOMESTIC))
            time.sleep(0.5)

        for news_list in rss_results:
            for item in news_list:
                item['priority'] = 'domestic'
            all_news.extend(news_list)

        print(f"[RSS] 国内 RSS 抓取完成，共 {len([n for n in all_news if n.get('priority') == 'domestic'])} 条")

    # 3. 抓取国外 RSS 源
    if RSS_FEEDS_OVERSEAS:
        print("[RSS] 开始抓取国外 RSS 源...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            rss_results = list(executor.map(fetch_single_feed, RSS_FEEDS_OVERSEAS))
            time.sleep(0.5)

        for news_list in rss_results:
            for item in news_list:
                item['priority'] = 'overseas'
            all_news.extend(news_list)

        print(f"[RSS] 国外 RSS 抓取完成，共 {len([n for n in all_news if n.get('priority') == 'overseas'])} 条")

    # 按优先级和时间排序：爬虫平台 > 国内 RSS > 国外 RSS，然后按时间降序
    priority_order = {'crawler': 0, 'domestic': 1, 'overseas': 2}
    # 先按优先级排序，再在优先级内按时间降序（支持 published 和 publish_time 两种字段）
    def get_published_timestamp(news):
        pub_time = news.get('published') or news.get('publish_time')
        if not pub_time:
            # 爬虫数据没有时间戳时，使用当前时间（确保爬虫数据排在同类优先级的最前面）
            # 对于 crawler 类型，返回最大可能值
            if news.get('priority') == 'crawler':
                return 9999999999  # 很大的时间戳，确保排在前面
            return 0
        try:
            # 支持多种时间格式
            if isinstance(pub_time, str):
                # 尝试 ISO 格式（爬虫）或 YYYY-MM-DD HH:MM:SS 格式（RSS）
                if 'T' in pub_time:
                    pub_time = pub_time.replace('Z', '+00:00')
                    if '+' in pub_time or pub_time.endswith('Z'):
                        # ISO 格式带时区，转换为本地时间
                        from datetime import timezone
                        dt = datetime.datetime.fromisoformat(pub_time)
                        # 转换为本地时间（Asia/Shanghai UTC+8）
                        local_dt = dt.astimezone(timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=8)
                        return local_dt.timestamp()
                    else:
                        return datetime.datetime.fromisoformat(pub_time).timestamp()
                else:
                    return datetime.datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S').timestamp()
            elif isinstance(pub_time, datetime.datetime):
                return pub_time.timestamp()
            else:
                return 0
        except (ValueError, TypeError):
            # 解析失败时，如果是爬虫数据返回大值
            if news.get('priority') == 'crawler':
                return 9999999999
            return 0

    all_news.sort(key=lambda x: (priority_order.get(x.get('priority', 'overseas'), 2), -get_published_timestamp(x)))

    cached_news = all_news[:300]
    last_update = datetime.datetime.now()

    # 保存到数据库（自动去重）
    if all_news:
        saved_count = save_news(all_news)
        if saved_count > 0:
            print(f"新增 {saved_count} 条新闻到数据库")

    # 触发推送检查
    if all_news:
        try:
            push_result = check_and_push_notifications(all_news)
            if push_result.get('pushed_count', 0) > 0:
                print(f"推送成功：{push_result}")
        except Exception as e:
            print(f"推送检查异常：{e}")

    return cached_news

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news_route():
    """获取最新新闻（从数据库）"""
    news = get_news(limit=300)
    return jsonify(news)

@app.route('/api/news/by-channel')
def get_news_by_channel_route():
    """按频道分组获取新闻（爬虫平台在前，每个频道最新的 15 条）"""
    # 支持个性化推荐：从查询参数获取用户 ID
    user_id = request.args.get('user_id', 'default')
    news_by_channel = get_personalized_news(user_id, channel_limit=15)
    return jsonify(news_by_channel)


@app.route('/api/user/interests', methods=['GET'])
def api_get_user_interests():
    """获取用户兴趣标签"""
    user_id = request.args.get('user_id', 'default')
    interests = get_user_interests(user_id)
    return jsonify({'interests': interests})


@app.route('/api/user/click', methods=['POST'])
def api_record_user_click():
    """记录用户点击行为"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')
    news_id = data.get('news_id')
    title = data.get('title')
    source = data.get('source')

    if not news_id or not title:
        return jsonify({'error': '缺少必要参数'}), 400

    record_user_click(user_id, news_id, title, source)
    return jsonify({'success': True})


@app.route('/api/user/click-history', methods=['GET'])
def api_get_user_click_history():
    """获取用户点击历史"""
    user_id = request.args.get('user_id', 'default')
    limit = request.args.get('limit', 50, type=int)
    history = get_user_click_history(user_id, limit)
    return jsonify({'history': history})

@app.route('/api/refresh', methods=['POST'])
def refresh_news():
    """手动刷新新闻数据"""
    fetch_all_news()
    return jsonify({
        'success': True,
        'count': len(cached_news),
        'update_time': last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else None
    })

@app.route('/api/hot')
def get_hot():
    """获取热点新闻（从数据库）"""
    news = get_hot_news(limit=10)
    return jsonify(news)

@app.route('/api/search')
def search_news():
    """搜索新闻"""
    query = request.args.get('q', '')
    if not query:
        news = get_news(limit=100)
        return jsonify(news)

    # 从数据库搜索
    keywords = query.split()
    news = get_news_by_keywords(keywords, limit=100)
    return jsonify(news)

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    return jsonify({
        'total_news': get_news_count(),
        'latest_published': get_latest_published(),
        'settings': get_all_settings()
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_news():
    """AI 深度分析接口"""
    global ai_analysis_cache

    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({'error': '暂无数据可分析'}), 400

    # 尝试使用 AI 深度分析
    ai_result = ai_deep_analysis(news_list)

    if ai_result:
        # AI 分析成功，格式化输出
        analysis_html = format_ai_analysis_html(ai_result, len(news_list))
        return jsonify({
            'summary': analysis_html,
            'analysis_type': 'ai_deep',
            'raw_data': ai_result
        })
    else:
        # AI 分析失败，使用备用方案
        fallback_result = fallback_analysis(news_list)
        analysis_html = format_fallback_analysis_html(fallback_result, len(news_list))
        return jsonify({
            'summary': analysis_html,
            'analysis_type': 'fallback',
            'raw_data': fallback_result
        })


@app.route('/api/analyze/keywords', methods=['POST'])
def analyze_keywords():
    """关键词分析接口"""
    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({'keywords': [], 'user_interests': [], 'hot_topics': []})

    # 提取所有标题
    all_titles = ' '.join([n['title'] for n in news_list])
    words = re.findall(r'[\u4e00-\u9fff]+|[A-Za-z]+', all_titles)

    # 过滤停用词
    stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '一个', '可以', '没有', '我们', '他们']
    filtered_words = [w for w in words if w.lower() not in stopwords and len(w) > 1]

    from collections import Counter
    word_freq = Counter(filtered_words)

    # 获取高频词作为关键词
    top_keywords = [kw for kw, _ in word_freq.most_common(15)]

    # 从数据库获取用户兴趣关键词
    user_id = request.headers.get('X-User-ID', 'default')
    user_interests_data = get_user_interests(user_id)
    user_interests = [item['keyword'] for item in user_interests_data[:5]]

    # 热门话题（高频词前 3 个）
    hot_topics = [kw for kw, _ in word_freq.most_common(3)]

    return jsonify({
        'keywords': top_keywords,
        'user_interests': user_interests,
        'hot_topics': hot_topics
    })


@app.route('/api/recommend', methods=['POST'])
def recommend_news():
    """AI 推荐接口 - 基于用户兴趣的个性化推荐"""
    data = request.get_json()
    news_list = data.get('news', [])
    history = data.get('history', [])

    if not news_list:
        return jsonify({'recommendations': []})

    # 从数据库获取用户兴趣
    user_id = request.headers.get('X-User-ID', 'default')
    user_interests_data = get_user_interests(user_id)
    user_keywords = [item['keyword'] for item in user_interests_data[:10]]

    # 如果没有用户兴趣，则从历史点击中提取
    if not user_keywords and history:
        all_history_titles = ' '.join([h.get('title', '') for h in history])
        user_keywords = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', all_history_titles)
        # 过滤停用词
        stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都']
        user_keywords = [w for w in user_keywords if w.lower() not in stopwords]

    # 推荐算法：计算每条新闻与用户兴趣的匹配度
    recommendations = []
    scored_news = []

    for news in news_list:
        title = news.get('title', '')
        hot_score = news.get('hot_score') or 50  # 处理 None 的情况

        # 计算兴趣匹配分
        interest_score = 0
        matched_keywords = []
        for kw in user_keywords:
            if kw in title:
                interest_score += 1
                matched_keywords.append(kw)

        # 综合得分 = 兴趣分 * 0.7 + 热度分 * 0.3
        combined_score = (interest_score * 0.7) + (hot_score / 100 * 0.3)

        scored_news.append({
            'news': news,
            'score': combined_score,
            'interest_score': interest_score,
            'matched_keywords': matched_keywords
        })

    # 按得分排序
    scored_news.sort(key=lambda x: x['score'], reverse=True)

    # 取前 5 条推荐
    for item in scored_news[:5]:
        news = item['news']
        reason = '根据您的兴趣' if item['interest_score'] > 0 else '热门内容'
        if item['matched_keywords']:
            reason = f"匹配兴趣：{', '.join(item['matched_keywords'][:3])}"

        recommendations.append({
            'title': news.get('title', ''),
            'score': f'{item["score"]:.0%}',
            'reason': reason
        })

    return jsonify({'recommendations': recommendations})


@app.route('/api/analyze/social', methods=['POST'])
def analyze_social():
    """社交分析接口"""
    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({'metrics': {}, 'trends': []})

    # 简单的社交指标计算（实际应用中应接入真实社交 API）
    total_count = len(news_list)

    # 模拟社交互动数据
    total_engagement = total_count * 150  # 假设每条新闻平均 150 次互动
    viral_count = sum(1 for n in news_list if (n.get('hot_score') or 0) > 80)
    sentiment_scores = {'positive': 1, 'neutral': 0.5, 'negative': 0}
    avg_sentiment = sum(sentiment_scores.get(n.get('sentiment', 'neutral'), 0.5) for n in news_list) / total_count if total_count > 0 else 0.5
    trend_velocity = viral_count * 2.5

    # 社交趋势
    all_titles = ' '.join([n['title'] for n in news_list])
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', all_titles)
    stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都']
    filtered_words = [w for w in words if w.lower() not in stopwords and len(w) > 1]

    from collections import Counter
    word_freq = Counter(filtered_words)
    trends = [
        {'topic': kw, 'engagement': count * 50}
        for kw, count in word_freq.most_common(3)
    ]

    return jsonify({
        'metrics': {
            'total_engagement': total_engagement,
            'viral_count': viral_count,
            'sentiment_score': f'{avg_sentiment:.2f}',
            'trend_velocity': f'{trend_velocity:.1f}'
        },
        'trends': trends
    })

def format_ai_analysis_html(analysis, total_count):
    """格式化 AI 分析结果为 HTML"""
    html = f"""
    <div class="ai-analysis-report">
        <!-- 核心摘要 -->
        <div class="analysis-section">
            <h4>📋 核心摘要</h4>
            <p class="executive-summary">{analysis.get('executive_summary', '')}</p>
        </div>

        <!-- 情感分析 -->
        <div class="analysis-section">
            <h4>📊 情感分析</h4>
            <div class="sentiment-grid">
                <div class="sentiment-item">
                    <span class="sentiment-label">整体舆情</span>
                    <span class="sentiment-value sentiment-{analysis.get('sentiment_analysis', {}).get('overall', 'neutral')}">
                        {'正面' if analysis.get('sentiment_analysis', {}).get('overall') == 'positive' else '负面' if analysis.get('sentiment_analysis', {}).get('overall') == 'negative' else '中性'}
                    </span>
                </div>
                <div class="sentiment-item">
                    <span class="sentiment-label">正面率</span>
                    <span class="sentiment-value">{analysis.get('sentiment_analysis', {}).get('positive_rate', 0) * 100:.1f}%</span>
                </div>
            </div>
            {format_key_drivers(analysis.get('sentiment_analysis', {}).get('key_drivers', []))}
        </div>

        <!-- 趋势洞察 -->
        {format_trend_insights(analysis.get('trend_insights', []))}

        <!-- 竞争情报 -->
        {format_competitive_intelligence(analysis.get('competitive_intelligence', []))}

        <!-- 风险预警 -->
        {format_risk_warnings(analysis.get('risk_warnings', []))}

        <!-- 机会与建议 -->
        <div class="analysis-section">
            <h4>💡 机会与建议</h4>
            {format_opportunities(analysis.get('opportunities', []))}
            {format_recommended_actions(analysis.get('recommended_actions', []))}
        </div>
    </div>
    """
    return html

def format_key_drivers(drivers):
    if not drivers:
        return ''
    items = ''.join([f'<li>{d}</li>' for d in drivers])
    return f'<div class="key-drivers"><strong>正面驱动因素：</strong><ul>{items}</ul></div>'

def format_trend_insights(insights):
    if not insights:
        return ''
    items = ''
    for insight in insights:
        confidence_class = 'high' if insight.get('confidence') == 'high' else 'medium' if insight.get('confidence') == 'medium' else 'low'
        items += f"""
        <div class="trend-item">
            <div class="trend-header">
                <span class="trend-name">{insight.get('trend', '')}</span>
                <span class="confidence-badge {confidence_class}">{insight.get('confidence', '')}</span>
            </div>
            <p class="trend-evidence">{insight.get('evidence', '')}</p>
            <p class="trend-impact">{insight.get('impact', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>🔍 趋势洞察</h4>{items}</div>'

def format_competitive_intelligence(intel_list):
    if not intel_list:
        return ''
    items = ''
    for intel in intel_list:
        items += f"""
        <div class="intel-item">
            <span class="company-name">{intel.get('company', '')}</span>
            <p class="company-action">{intel.get('action', '')}</p>
            <p class="company-implication">{intel.get('implication', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>🏢 竞争情报</h4>{items}</div>'

def format_risk_warnings(risks):
    if not risks:
        return ''
    items = ''
    for risk in risks:
        severity_class = 'high' if risk.get('severity') == 'high' else 'medium' if risk.get('severity') == 'medium' else 'low'
        items += f"""
        <div class="risk-item">
            <div class="risk-header">
                <span class="risk-text">{risk.get('risk', '')}</span>
                <span class="severity-badge {severity_class}">{risk.get('severity', '')}</span>
            </div>
            <p class="risk-suggestion">{risk.get('suggestion', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>⚠️ 风险预警</h4>{items}</div>'

def format_opportunities(opportunities):
    if not opportunities:
        return ''
    items = ''.join([f'<li>{opp}</li>' for opp in opportunities])
    return f'<div class="opportunities"><strong>市场机会：</strong><ul>{items}</ul></div>'

def format_recommended_actions(actions):
    if not actions:
        return ''
    items = ''.join([f'<li>{action}</li>' for action in actions])
    return f'<div class="recommended-actions"><strong>行动建议：</strong><ul>{items}</ul></div>'

def format_fallback_analysis_html(analysis, total_count):
    """格式化备用分析结果为 HTML"""
    if not analysis:
        return '<p>分析失败</p>'

    html = f"""
    <div class="ai-analysis-report">
        <div class="analysis-section">
            <h4>📊 数据概览</h4>
            <p>{analysis.get('executive_summary', '')}</p>
        </div>

        <div class="analysis-section">
            <h4>😊 情感分布</h4>
            <p>正面率：{analysis.get('sentiment_analysis', {}).get('positive_rate', 0) * 100:.1f}%</p>
        </div>

        <div class="analysis-section">
            <h4>🔍 趋势洞察</h4>
            {format_trend_insights(analysis.get('trend_insights', []))}
        </div>

        <div class="analysis-section">
            <h4>💡 机会与建议</h4>
            {format_opportunities(analysis.get('opportunities', []))}
            {format_recommended_actions(analysis.get('recommended_actions', []))}
        </div>
    </div>
    """
    return html


# ==================== 推送管理 API ====================

@app.route('/api/push/rules', methods=['GET'])
def api_get_push_rules():
    """获取所有推送规则"""
    rules = get_push_rules()
    return jsonify(rules)

@app.route('/api/push/rules', methods=['POST'])
def api_create_push_rule():
    """创建推送规则"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    rule_id = save_push_rule({
        'rule_name': data.get('rule_name', '新规则'),
        'keywords': data.get('keywords', []),
        'hot_threshold': data.get('hot_threshold', 90),
        'enabled': data.get('enabled', True)
    })

    return jsonify({'success': True, 'rule_id': rule_id})

@app.route('/api/push/rules/<int:rule_id>', methods=['PUT'])
def api_update_push_rule(rule_id):
    """更新推送规则"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    success = update_push_rule(rule_id, {
        'rule_name': data.get('rule_name'),
        'keywords': data.get('keywords', []),
        'hot_threshold': data.get('hot_threshold'),
        'enabled': data.get('enabled', True)
    })

    return jsonify({'success': success})

@app.route('/api/push/rules/<int:rule_id>', methods=['DELETE'])
def api_delete_push_rule(rule_id):
    """删除推送规则"""
    success = delete_push_rule(rule_id)
    return jsonify({'success': success})

@app.route('/api/push/settings', methods=['GET'])
def api_get_settings():
    """获取推送设置"""
    settings = get_all_settings()
    return jsonify(settings)

@app.route('/api/push/settings', methods=['PUT'])
def api_update_settings():
    """更新推送设置"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    for key, value in data.items():
        update_setting(key, value)

    return jsonify({'success': True})

@app.route('/api/push/test', methods=['POST'])
def api_test_push():
    """测试推送"""
    webhook_url = get_setting('feishu_webhook', '')
    if not webhook_url:
        return jsonify({'success': False, 'message': '飞书 Webhook 未配置'}), 400

    success, message = send_test_push(webhook_url)
    return jsonify({'success': success, 'message': message})

@app.route('/api/push/daily', methods=['POST'])
def api_daily_push():
    """定时汇总推送"""
    period = request.args.get('period', 'morning')  # morning or evening
    success, message = send_daily_summary_push(period)
    return jsonify({'success': success, 'message': message})

@app.route('/api/push/logs', methods=['GET'])
def api_get_push_logs():
    """获取推送记录"""
    limit = request.args.get('limit', 50, type=int)
    logs = get_push_logs(limit)
    return jsonify(logs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
