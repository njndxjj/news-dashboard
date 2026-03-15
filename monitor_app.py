from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
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
from functools import lru_cache
from collections import Counter, defaultdict
import logging
from Lumos.backend.user_module import user_bp

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 通义千问 API 配置
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'sk-1acde23fddbd4a83bd0aa451a6a60a47')

# 飞书 Webhook 配置
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')
# 浏览器搜索配置
BROWSER_SEARCH_ENABLED = os.environ.get('BROWSER_SEARCH_ENABLED', 'false').lower() == 'true'  # 是否启用浏览器搜索
# AI 智能分析配置
AI_ANALYSIS_SOURCE = os.environ.get('AI_ANALYSIS_SOURCE', 'browser')  # 分析数据源：'browser' (浏览器搜索) 或 'rss' (RSS/爬虫)


# ==================== 智能分析模块 - 增强版 ====================

# 扩展停用词表（中英文）
STOPWORDS_ZH = frozenset([
    '的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着',
    '一个', '可以', '没有', '我们', '他们', '什么', '怎么', '为什么', '如何', '是否',
    '这个', '这些', '那些', '这样', '那样', '这里', '那里', '很多', '一些', '一些',
    '之', '乎', '者', '也', '其', '所', '以', '而', '但', '或', '如果', '因为', '所以',
    '虽然', '但是', '而且', '或者', '可能', '应该', '必须', '需要', '能够', '将会',
    '已经', '曾经', '正在', '将要', '不会', '不能', '不想', '不敢', '不可', '不许',
    '我的', '你的', '他的', '她的', '它的', '我们的', '你们的', '他们的',
    '有', '这', '上', '时', '来', '到', '大', '中', '国', '人', '民', '年', '月', '日'
])

STOPWORDS_EN = frozenset([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
    'he', 'she', 'we', 'you', 'i', 'me', 'him', 'her', 'us', 'my', 'your',
    'his', 'our', 'what', 'which', 'who', 'whom', 'when', 'where', 'why',
    'all', 'any', 'some', 'no', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once'
])

# 情感词典（简化版）
SENTIMENT_DICT = {
    'positive': ['好', '优秀', '出色', '成功', '突破', '创新', '领先', '第一', '冠军', '金牌',
                 '高兴', '快乐', '幸福', '满意', '赞', '支持', '认可', '期待', '希望', '信心',
                 'positive', 'great', 'excellent', 'success', 'innovative', 'leading', 'best',
                 'amazing', 'wonderful', 'fantastic', 'awesome', 'perfect', 'love', 'like'],
    'negative': ['坏', '差', '失败', '问题', '风险', '担忧', '批评', '质疑', '下跌', '下滑',
                 '糟糕', '痛苦', '难过', '失望', '讨厌', '恨', '错', '虚假', '负面', '事故',
                 'negative', 'bad', 'worst', 'failed', 'problem', 'risk', 'crisis', 'error',
                 'terrible', 'awful', 'horrible', 'disappointing', 'hate', 'dislike']
}


def get_stopwords(language='auto'):
    """获取停用词（带缓存）"""
    if language == 'zh':
        return STOPWORDS_ZH
    elif language == 'en':
        return STOPWORDS_EN
    else:
        # 自动混合
        return STOPWORDS_ZH.union(STOPWORDS_EN)


def detect_language(text):
    """检测文本主要语言"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[A-Za-z]', text))

    if chinese_chars > english_chars * 2:
        return 'zh'
    elif english_chars > chinese_chars:
        return 'en'
    else:
        return 'mixed'


def extract_keywords_enhanced(texts, top_n=15, language='auto'):
    """
    增强版关键词提取 - 支持多语言、二元词组、缓存

    :param texts: 文本列表
    :param top_n: 返回关键词数量
    :param language: 语言类型 ('zh', 'en', 'auto')
    :return: 关键词列表
    """
    if not texts:
        return []

    # 合并所有文本
    all_text = ' '.join(str(t) for t in texts)

    # 检测语言
    if language == 'auto':
        lang = detect_language(all_text)
    else:
        lang = language

    # 获取停用词
    stopwords = get_stopwords(lang)

    # 分词策略
    if lang == 'zh' or lang == 'mixed':
        # 中文：提取连续汉字（2-4 字优先）+ 英文单词
        words = re.findall(r'[\u4e00-\u9fff]{2,4}|[A-Za-z]{2,}', all_text.lower())
    else:
        # 英文：提取单词
        words = re.findall(r'[A-Za-z]{2,}', all_text.lower())

    # 过滤停用词
    filtered_words = [w for w in words if w not in stopwords and len(w) > 1]

    # 统计词频
    word_freq = Counter(filtered_words)

    # 增加二元词组权重（如果两个词经常相邻出现）
    # 这里简化处理，给 2 字词额外加分
    for word, freq in list(word_freq.items()):
        if len(word) == 2 and lang == 'zh':
            word_freq[word] = freq * 1.3  # 二元词组加权

    return [word for word, _ in word_freq.most_common(top_n)]


def analyze_sentiment_simple(text):
    """
    简单情感分析（基于词典）
    :param text: 文本
    :return: 'positive', 'negative', or 'neutral'
    """
    text_lower = text.lower()
    positive_count = sum(1 for word in SENTIMENT_DICT['positive'] if word.lower() in text_lower)
    negative_count = sum(1 for word in SENTIMENT_DICT['negative'] if word.lower() in text_lower)

    if positive_count > negative_count * 1.5:
        return 'positive'
    elif negative_count > positive_count * 1.5:
        return 'negative'
    else:
        return 'neutral'


def build_user_vector(history, interests, recent_weight=1.5):
    """
    构建用户兴趣向量（带时间衰减）
    :param history: 点击历史列表
    :param interests: 用户兴趣列表
    :param recent_weight: 近期行为权重倍数
    :return: 关键词权重 dict
    """
    keyword_weights = defaultdict(float)
    current_time = datetime.datetime.now()

    # 从兴趣标签获取权重
    for interest in interests:
        kw = interest.get('keyword', '')
        if kw:
            keyword_weights[kw] += 1.0

    # 从点击历史提取（带时间衰减）
    for item in history:
        title = item.get('title', '')
        # 提取标题中的关键词
        words = extract_keywords_enhanced([title], top_n=5)

        # 计算时间衰减
        click_time = item.get('click_time')
        if click_time:
            try:
                if isinstance(click_time, str):
                    click_dt = datetime.datetime.strptime(click_time, '%Y-%m-%d %H:%M:%S')
                else:
                    click_dt = click_time

                days_diff = (current_time - click_dt).days
                time_weight = max(0.1, 1.0 / (1 + days_diff * 0.2))  # 每天衰减 20%
            except:
                time_weight = 0.5 if recent_weight > 1 else 1.0
        else:
            time_weight = 0.5

        # 近期行为加权
        if time_weight > 0.7:
            time_weight *= recent_weight

        for word in words:
            keyword_weights[word] += time_weight

    return dict(keyword_weights)

app = Flask(__name__, template_folder='templates')

# 启用 CORS，允许所有来源访问（仅用于本地测试）
CORS(app)

# 注册 user_module 蓝图
app.register_blueprint(user_bp)

# 导入数据库和推送模块
from database import (
    init_db, get_news, get_hot_news, get_news_by_keywords, save_news,
    get_push_rules, save_push_rule, update_push_rule, delete_push_rule,
    get_push_logs, get_setting, update_setting, get_all_settings,
    get_news_count, get_latest_published, save_push_log, get_news_by_channel,
    get_user_interests, record_user_click, get_user_click_history, get_personalized_news,
    PRESET_INTEREST_CATEGORIES, add_user_interest, get_db_connection, clear_user_interests,
    save_ai_analysis, get_ai_analysis
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
# ai_analysis_cache 已废弃，现在每次用户刷新都重新分析

def ai_deep_analysis(news_list):
    """使用通义千问进行深度 AI 分析 - 基于实时热点数据的智能摘要总结"""
    logger.info(f"[AI 分析] DASHSCOPE_API_KEY 长度：{len(DASHSCOPE_API_KEY) if DASHSCOPE_API_KEY else 0}")

    if not DASHSCOPE_API_KEY:
        logger.warning("[AI 分析] API Key 未配置，返回 None 使用备用方案")
        return None  # API Key 未配置，返回 None 使用备用方案

    try:
        import dashscope
        from dashscope import Generation

        # 设置 API Key
        dashscope.api_key = DASHSCOPE_API_KEY
        logger.info(f"[AI 分析] 开始调用通义千问 API，dashscope.api_key 长度：{len(dashscope.api_key)}")

        # 准备分析的新闻数据（精选 30-50 条代表性新闻）
        精选新闻 = news_list[:50]
        news_summary = "\n".join([
            f"- [{n.get('source', '未知')}] {n.get('title', '')} (热度：{n.get('hot_score') or 50})"
            for n in 精选新闻
        ])

        # 统计来源分布
        sources = [n.get('source', '未知') for n in 精选新闻]
        source_stats = {}
        for s in sources:
            source_stats[s] = source_stats.get(s, 0) + 1
        source_text = "，".join([f"{k}({v}条)" for k, v in source_stats.items()])

        # 构建分析提示词（高管视角 + 行业研究员视角，聚焦摘要总结）
        prompt = f"""你是一位资深商业情报分析师和舆情专家，正在为企业高管和决策者撰写每日舆情摘要报告。

**数据来源**：{source_text}
**分析样本**：共 {len(精选新闻)} 条实时热点新闻

**新闻内容**：
{news_summary}

**报告定位**：
- 受众：企业 CEO、高管、战略决策者、投资人
- 场景：每日晨会、快速决策参考、战略风向标
- 风格：专业、精准、高度凝练、有数据支撑、有前瞻洞察
- 目标：让决策者在 2 分钟内掌握核心动态和关键行动点

请输出 JSON 格式的摘要报告，必须包含以下字段：

{{
    "executive_summary": "150 字以内的核心摘要，高度概括当前舆情态势。要求：① 直击要点 ② 有数据支撑 ③ 体现情报价值 ④ 让高管一眼看懂全局",

    "key_highlights": [
        "重要事件 1（30 字以内，精准描述）",
        "重要事件 2（30 字以内）",
        "重要事件 3（30 字以内）"
    ],

    "trending_topics": [
        {{
            "topic": "热点话题名称（5-15 字，精准提炼）",
            "description": "一句话描述（20-30 字，说明核心进展）",
            "heat_level": "very_high/high/medium/low",
            "related_news_count": 相关新闻数量（整数）
        }}
    ],

    "industry_insights": [
        {{
            "trend": "行业趋势或重大动态（精准描述）",
            "impact_level": "high/medium/low",
            "affected_sectors": ["受影响领域 1", "领域 2"],
            "strategic_implication": "对企业的战略启示（30-50 字，可落地）"
        }}
    ],

    "competitive_landscape": [
        {{
            "company": "公司/机构名称",
            "key_move": "关键动态（20-40 字，精准描述）",
            "strategic_intent": "战略意图分析（30-50 字，有洞察）",
            "threat_level": "high/medium/low",
            "our_response": "我方应对建议（具体可执行）"
        }}
    ],

    "risk_alerts": [
        {{
            "risk_type": "政策/市场/技术/舆情/供应链/其他",
            "description": "风险描述（具体、可感知、30-50 字）",
            "severity": "high/medium/low",
            "early_signals": "早期预警信号（20-40 字）",
            "mitigation": "应对建议（具体可落地，30-50 字）"
        }}
    ],

    "opportunities": [
        {{
            "type": "市场/技术/合作/投资/其他",
            "description": "机会描述（30-50 字，具体且有依据）",
            "window": "short_term/medium_term/long_term",
            "action": "建议采取行动（30-50 字，可执行）"
        }}
    ],

    "recommended_actions": [
        {{
            "priority": "high/medium/low",
            "action": "具体行动项（30-50 字，可落地）",
            "owner": "建议负责部门（如：战略部/市场部/产品部/PR/研发）",
            "timeline": "建议完成时间（如：1 周内/本月内/Q1）"
        }}
    ]
}}

**撰写要求**：
1. 用简体中文输出，语言专业、精准、有洞察力
2. 核心摘要必须高度凝练，体现情报价值，避免空话套话
3. 热点话题要精准提炼，反映真实舆情焦点，不能泛泛而谈
4. 行业洞察要有前瞻性和深度，体现专家视角
5. 竞争情报要聚焦头部玩家和颠覆性动态
6. 风险预警要具体可感知，有早期信号识别
7. 行动建议要可执行、可落地、有明确优先级和责任人
8. 基于新闻事实分析，严禁臆测或编造
9. 如无明显风险/机会/竞争动态，对应字段可为空数组 []
10. 所有字段必须有实际内容，不能使用"暂无"、"待补充"等占位符"""

        # 调用通义千问 API（带超时控制）
        logger.info(f"[AI 分析] 开始调用 Generation.call，model=qwen-max，timeout=30s")
        try:
            response = Generation.call(
                model='qwen-max',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,  # 降低温度让输出更稳定
                max_tokens=2000,  # 减少 token 数量加快响应
                timeout=30  # 30 秒超时（给 AI 足够时间完成深度分析）
            )
        except Exception as api_error:
            logger.error(f"[AI 分析] API 调用超时或异常：{api_error}")
            return None

        logger.info(f"[AI 分析] API 响应状态码：{response.status_code}")
        logger.info(f"[AI 分析] API 响应 code：{response.code}")
        logger.info(f"[AI 分析] API 响应 message：{response.message}")

        if response.status_code == 200:
            # dashscope 响应结构：response.output.text 或 response.output.choices[0].message.content
            content = None
            if hasattr(response.output, 'text') and response.output.text:
                content = response.output.text
            elif hasattr(response.output, 'choices') and response.output.choices:
                content = response.output.choices[0].message.content

            if not content:
                logger.error("[AI 分析] 无法获取响应内容")
                return None

            # 尝试解析 JSON
            try:
                # 清理可能的 markdown 标记
                content = content.replace('```json', '').replace('```', '').strip()
                analysis_result = json.loads(content)
                logger.info(f"[AI 分析] JSON 解析成功")

                # 添加元数据
                analysis_result['source'] = 'qwen-ai'
                analysis_result['analysis_type'] = 'executive_summary'
                analysis_result['news_count'] = len(news_list)
                analysis_result['analyzed_news_count'] = len(精选新闻)

                return analysis_result
            except json.JSONDecodeError as e:
                logger.error(f"[AI 分析] JSON 解析失败：{e}")
                logger.error(f"[AI 分析] 响应内容：{content[:500]}...")
                return None
        else:
            logger.error(f"[AI 分析] API 调用失败：{response.code} - {response.message}")
            return None

    except Exception as e:
        logger.error(f"[AI 分析] 异常：{e}", exc_info=True)
        return None


def parse_ai_response(content):
    """解析 AI 返回的 JSON 响应"""
    try:
        # 清理 markdown 标记
        content = content.replace('```json', '').replace('```', '').strip()
        result = json.loads(content)
        logger.info(f"[AI 解析] JSON 解析成功")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"[AI 解析] JSON 解析失败：{e}")
        logger.error(f"[AI 解析] 响应内容：{content[:500]}...")
        return None


def fallback_analysis(news_list):
    """备用分析方案（当 API 不可用时）- 基于本地算法的摘要总结"""
    total = len(news_list)
    if total == 0:
        return None

    # 提取关键词（基于词频）
    all_titles = ' '.join([n['title'] for n in news_list])
    # 简单分词（按标点和空格）
    words = re.findall(r'[\u4e00-\u9fff]{2,4}|[A-Za-z]{2,}', all_titles)
    # 过滤常见停用词
    stopwords = ['的', '了', '是', '在', '和', '与', '等', '个', '这', '那', '就', '都', '而', '及', '着', '了', '一个']
    filtered_words = [w for w in words if w.lower() not in stopwords and len(w) > 1]

    from collections import Counter
    word_freq = Counter(filtered_words)
    top_keywords = word_freq.most_common(8)

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

    # 计算平均热度（处理 hot_score 为 None 的情况）
    avg_hot_score = sum((n.get('hot_score') or 50) for n in news_list) / total

    # 生成执行摘要
    executive_summary = f"本次共分析 {total} 条热点新闻，平均热度 {avg_hot_score:.1f} 分。"
    if top_industries:
        executive_summary += f" 主要关注领域：{top_industries[0][0]}（{top_industries[0][1]}条）"

    # 构建关键词列表作为关键事件
    key_highlights = [f"{kw[0]}相关：{kw[1]}条" for kw in top_keywords[:5]]

    return {
        "executive_summary": executive_summary,
        "key_highlights": key_highlights,
        "trending_topics": [
            {
                "topic": kw[0],
                "description": f"提及{kw[1]}次",
                "heat_level": "high" if kw[1] > 5 else "medium",
                "related_news_count": kw[1]
            }
            for kw in top_keywords[:5]
        ],
        "industry_insights": [
            {
                "trend": f"{ind[0]}领域活跃",
                "impact_level": "high" if ind[1] > 5 else "medium",
                "affected_sectors": [ind[0]],
                "strategic_implication": f"建议持续关注{ind[0]}领域发展动态"
            }
            for ind in top_industries
        ],
        "competitive_landscape": [],
        "risk_alerts": [],
        "opportunities": [
            {
                "type": "市场",
                "description": f"{ind[0]}领域活跃（{ind[1]}条新闻）",
                "window": "short_term",
                "action": f"关注{ind[0]}领域投资机会"
            }
            for ind in top_industries
        ],
        "recommended_actions": [
            {
                "priority": "high",
                "action": "持续关注重点行业动态",
                "owner": "战略部",
                "timeline": "持续进行"
            },
            {
                "priority": "medium",
                "action": "建立负面舆情预警机制",
                "owner": "PR 部门",
                "timeline": "1 周内"
            }
        ]
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
    """首页 - 添加禁止缓存头"""
    response = render_template('index-elegant.html')
    response = app.make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/news')
def get_news_route():
    """获取最新新闻（从数据库）"""
    limit = request.args.get('limit', 50, type=int)
    news = get_news(limit=limit)
    return jsonify({'news': news, 'count': len(news)})

@app.route('/api/news/by-channel')
def get_news_by_channel_route():
    """按频道分组获取新闻（爬虫平台在前，每个频道最新的 15 条）"""
    # 支持个性化推荐：从查询参数获取用户 ID
    user_id = request.args.get('user_id', 'default')
    news_by_channel = get_personalized_news(user_id, channel_limit=15)
    return jsonify(news_by_channel)


# 预设兴趣分类从 database.py 导入
# PRESET_INTEREST_CATEGORIES = {}


@app.route('/api/user/interests', methods=['GET'])
def api_get_user_interests():
    """获取用户兴趣标签"""
    user_id = request.args.get('user_id', 'default')
    interests = get_user_interests(user_id)
    return jsonify({'interests': interests})


@app.route('/api/user/interests/categories', methods=['GET'])
def api_get_interest_categories():
    """获取预设兴趣分类"""
    return jsonify({'categories': PRESET_INTEREST_CATEGORIES})


@app.route('/api/user/interests', methods=['POST'])
def api_add_user_interest():
    """添加用户兴趣标签（用于领域选择）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')
    keyword = data.get('keyword')
    weight = data.get('weight', 1.0)

    if not keyword:
        return jsonify({'error': '缺少关键词'}), 400

    add_user_interest(user_id, keyword, weight)
    return jsonify({'success': True, 'keyword': keyword})


@app.route('/api/user/interests/follow_category', methods=['POST'])
def api_follow_category():
    """用户关注某个分类（自动添加该分类下所有关键词）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')
    category = data.get('category')

    if not category or category not in PRESET_INTEREST_CATEGORIES:
        return jsonify({'error': '无效分类'}), 400

    # 添加该分类下所有关键词到用户兴趣
    keywords = PRESET_INTEREST_CATEGORIES[category]
    for keyword in keywords:
        add_user_interest(user_id, keyword, weight=1.0)

    return jsonify({'success': True, 'category': category, 'keywords_count': len(keywords)})


@app.route('/api/user/interests/unfollow_category', methods=['POST'])
def api_unfollow_category():
    """用户取消关注某个分类（移除该分类下所有关键词）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')
    category = data.get('category')

    if not category or category not in PRESET_INTEREST_CATEGORIES:
        return jsonify({'error': '无效分类'}), 400

    # 删除该分类下所有关键词
    conn = get_db_connection()
    cursor = conn.cursor()
    keywords = PRESET_INTEREST_CATEGORIES[category]
    for keyword in keywords:
        cursor.execute('DELETE FROM user_interests WHERE user_id = ? AND keyword = ?', (user_id, keyword))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'category': category})


@app.route('/api/user/interests/delete', methods=['POST'])
def api_delete_user_interest():
    """删除用户兴趣标签（用于取消关注领域）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')
    keyword = data.get('keyword')

    if not keyword:
        return jsonify({'error': '缺少关键词'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_interests WHERE user_id = ? AND keyword = ?', (user_id, keyword))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/user/interests/clear', methods=['POST'])
def api_clear_user_interests():
    """清除用户所有兴趣标签"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    user_id = data.get('user_id', 'default')

    clear_user_interests(user_id)
    return jsonify({'success': True})


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
    """
    搜索新闻 - 支持浏览器实时搜索和数据库搜索
    
    查询参数:
    - q: 搜索关键词 (可选)
    - source: 搜索来源，可选值：'browser' (浏览器搜索), 'database' (数据库搜索), 'all' (两者结合)
    - limit: 结果数量限制 (默认 100, 范围 50-100)
    
    返回格式:
    - 与原来一致的 JSON 格式新闻列表
    """
    query = request.args.get('q', '')
    source = request.args.get('source', 'browser' if BROWSER_SEARCH_ENABLED else 'database')
    limit = request.args.get('limit', '100')
    
    try:
        limit = int(limit)
        limit = max(50, min(100, limit))  # 限制在 50-100 之间
    except ValueError:
        limit = 100
    
    # 如果没有关键词，根据 source 决定返回什么
    if not query:
        if source == 'browser':
            # 使用浏览器搜索获取热榜
            try:
                from browser_search import sync_search
                news = sync_search(keyword='')
                logger.info(f"浏览器热榜搜索完成，获取 {len(news)} 条结果")
                return jsonify(news)
            except Exception as e:
                logger.error(f"浏览器搜索失败，降级到数据库搜索：{e}")
                news = get_news(limit=limit)
                return jsonify(news)
        else:
            news = get_news(limit=limit)
            return jsonify(news)
    
    # 根据 source 参数选择搜索方式
    browser_results = []
    database_results = []
    
    if source in ('browser', 'all'):
        # 使用浏览器实时搜索
        try:
            from browser_search import sync_search
            browser_results = sync_search(keyword=query)
            logger.info(f"浏览器关键词搜索完成，获取 {len(browser_results)} 条结果")
        except Exception as e:
            logger.error(f"浏览器搜索失败：{e}")
    
    if source in ('database', 'all'):
        # 从数据库搜索
        keywords = query.split()
        database_results = get_news_by_keywords(keywords, limit=limit)
        logger.info(f"数据库搜索完成，获取 {len(database_results)} 条结果")
    
    # 合并结果
    if source == 'all':
        # 合并并去重
        news = browser_results + database_results
        seen_links = set()
        unique_news = []
        for item in news:
            link = item.get('link', '')
            if link not in seen_links:
                seen_links.add(link)
                unique_news.append(item)
        news = unique_news[:limit]
    elif source == 'browser':
        news = browser_results[:limit]
    else:
        news = database_results[:limit]
    
    return jsonify(news)


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
    """AI 深度分析接口 - 基于浏览器搜索的实时热点数据 + 通义千问大模型摘要总结"""
    global cached_news

    data = request.get_json() or {}
    news_list = data.get('news', [])
    keyword = data.get('keyword', '')  # 可选的定向关键词

    # 策略：不使用缓存，每次用户主动刷新都重新分析，确保数据新鲜度
    # 优化：有传入新闻数据时，跳过浏览器搜索，直接分析
    use_browser = BROWSER_SEARCH_ENABLED and not news_list and not keyword

    # 不再使用缓存，每次都重新分析
    # 注意：移除了 ai_analysis_cache 的缓存判断逻辑

    if use_browser:
        logger.info("[AI 分析] 使用浏览器搜索获取实时热点数据（优化：8s 超时）...")
        try:
            from browser_search import sync_search

            # 优化：缩短超时到 8 秒，加快失败降级
            search_keyword = keyword if keyword else ''
            news_list = sync_search(keyword=search_keyword, timeout=8)
            logger.info(f"[AI 分析] 浏览器搜索获取到 {len(news_list)} 条热点数据")

            # 如果浏览器搜索返回空结果或超时，降级到数据库
            if not news_list:
                logger.warning("[AI 分析] 浏览器搜索返回空结果，降级到数据库数据")
                news_list = get_news(limit=100)

        except Exception as e:
            logger.error(f"[AI 分析] 浏览器搜索失败：{e}，降级到数据库数据")
            # 降级到数据库获取最新新闻
            news_list = get_news(limit=100)
    elif not news_list:
        # 没有使用浏览器搜索且没有传入数据，从缓存或数据库获取
        news_list = cached_news if cached_news else get_news(limit=100)

    if not news_list:
        return jsonify({'error': '暂无数据可分析，请稍后重试'}), 400

    # 精选代表性新闻（最多 50 条）
    sorted_news = sorted(news_list, key=lambda x: x.get('hot_score') or 50, reverse=True)
    selected_news = sorted_news[:50]

    logger.info(f"[AI 分析] 开始分析 {len(selected_news)} 条新闻")

    # 尝试使用 AI 深度分析
    ai_result = ai_deep_analysis(selected_news)

    if ai_result:
        # AI 分析成功，格式化输出
        analysis_html = format_ai_analysis_html(ai_result, len(selected_news))

        # 保存分析结果到数据库（用于历史记录查询）
        save_ai_analysis(ai_result, selected_news, analysis_type='ai_deep')

        # 不再更新缓存，确保每次用户刷新都重新分析
        # ai_analysis_cache 已废弃

        return jsonify({
            'summary': analysis_html,
            'analysis_type': 'ai_deep',
            'source': 'browser' if use_browser and news_list else 'database',
            'news_count': len(selected_news),
            'raw_data': ai_result
        })
    else:
        # AI 分析失败，使用备用方案
        logger.warning("[AI 分析] AI 分析失败，使用备用方案")
        fallback_result = fallback_analysis(selected_news)
        analysis_html = format_fallback_analysis_html(fallback_result, len(selected_news))
        return jsonify({
            'summary': analysis_html,
            'analysis_type': 'fallback',
            'source': 'local',
            'news_count': len(selected_news),
            'raw_data': fallback_result
        })


@app.route('/api/analyze/history', methods=['GET'])
def get_analysis_history():
    """获取历史 AI 分析记录"""
    limit = request.args.get('limit', 10, type=int)
    analysis_type = request.args.get('type', None)

    history = get_ai_analysis(limit=limit, analysis_type=analysis_type)

    return jsonify({
        'history': history,
        'count': len(history)
    })


@app.route('/api/analyze/keywords', methods=['POST'])
def analyze_keywords():
    """关键词分析接口 - 增强版"""
    start_time = time.time()

    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({'keywords': [], 'user_interests': [], 'hot_topics': []})

    # 使用增强版关键词提取
    titles = [n.get('title', '') for n in news_list]
    top_keywords = extract_keywords_enhanced(titles, top_n=15)

    # 从数据库获取用户兴趣关键词
    user_id = request.headers.get('X-User-ID', 'default')
    user_interests_data = get_user_interests(user_id)
    user_interests = [item['keyword'] for item in user_interests_data[:5]]

    # 热门话题（高频词前 3 个）
    hot_topics = top_keywords[:3] if len(top_keywords) >= 3 else top_keywords

    elapsed = time.time() - start_time
    logger.info(f"关键词分析完成，耗时 {elapsed:.3f}s，提取 {len(top_keywords)} 个关键词")

    return jsonify({
        'keywords': top_keywords,
        'user_interests': user_interests,
        'hot_topics': hot_topics
    })


@app.route('/api/analyze/sentiment', methods=['POST'])
def analyze_sentiment_batch():
    """情感分析接口 - 批量分析新闻情感"""
    start_time = time.time()

    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({
            'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
            'sentiment_rate': {'positive': 0, 'neutral': 0, 'negative': 0},
            'total': 0
        })

    # 统计情感分布
    sentiment_count = {'positive': 0, 'neutral': 0, 'negative': 0}
    sentiment_details = []

    for news in news_list:
        title = news.get('title', '')
        sentiment = analyze_sentiment_simple(title)
        sentiment_count[sentiment] += 1
        sentiment_details.append({
            'title': title[:50],
            'sentiment': sentiment
        })

    total = len(news_list)
    positive_rate = round(sentiment_count['positive'] / total, 2) if total > 0 else 0
    neutral_rate = round(sentiment_count['neutral'] / total, 2) if total > 0 else 0
    negative_rate = round(sentiment_count['negative'] / total, 2) if total > 0 else 0

    elapsed = time.time() - start_time
    logger.info(f"情感分析完成，耗时 {elapsed:.3f}s，分析 {total} 条新闻")

    return jsonify({
        'sentiment_distribution': sentiment_count,
        'sentiment_rate': {
            'positive': positive_rate,
            'neutral': neutral_rate,
            'negative': negative_rate
        },
        'total': total,
        'sentiment_details': sentiment_details[:20]  # 只返回前 20 条详情
    })


@app.route('/api/recommend', methods=['POST'])
def recommend_news():
    """AI 推荐接口 - 优先使用本地数据库数据，外部 API 作为补充"""
    start_time = time.time()

    data = request.get_json()
    news_list = data.get('news', [])
    history = data.get('history', [])
    use_external_api = data.get('use_external_api', False)  # 默认不使用外部 API

    # 从请求头或数据中获取用户 ID
    user_id = request.headers.get('X-User-ID', data.get('user_id', 'default'))

    # 从数据库获取用户兴趣
    user_interests_data = get_user_interests(user_id)
    user_keywords = [item['keyword'] for item in user_interests_data[:5]]

    logger.info(f'[推荐系统] 开始生成推荐，用户兴趣：{user_keywords}, 本地新闻数：{len(news_list)}')

    # 优先使用本地推荐算法（基于数据库中的新闻数据），默认显示 20 条
    local_recommendations = []
    if news_list:
        try:
            user_vector = build_user_vector(history, user_interests_data, recent_weight=1.5)

            if not user_vector and history:
                all_history_titles = ' '.join([h.get('title', '') for h in history])
                user_vector = {kw: 1.0 for kw in extract_keywords_enhanced([all_history_titles], top_n=10)}

            scored_news = []
            for news in news_list:
                title = news.get('title', '')
                hot_score = news.get('hot_score') or 50
                news_keywords = extract_keywords_enhanced([title], top_n=5)
                interest_score = 0.0
                matched_keywords = []
                for kw in news_keywords:
                    if kw in user_vector:
                        interest_score += user_vector[kw]
                        matched_keywords.append(kw)
                hot_normalized = (hot_score - 50) / 50 if hot_score > 50 else 0
                combined_score = (interest_score * 0.7) + (hot_normalized * 0.3)
                scored_news.append({'news': news, 'score': combined_score, 'interest_score': interest_score, 'matched_keywords': matched_keywords})

            scored_news.sort(key=lambda x: x['score'], reverse=True)

            # 默认返回 20 条本地推荐
            for item in scored_news[:20]:
                news = item['news']
                link = news.get('link', '#')
                news_id = hashlib.md5(link.encode()).hexdigest()[:16] if link != '#' else 'unknown'
                reason = '热门内容'
                if item['interest_score'] > 0 and item['matched_keywords']:
                    reason = f"匹配兴趣：{', '.join(item['matched_keywords'][:3])}"
                local_recommendations.append({
                    'news_id': news_id,
                    'title': news.get('title', ''),
                    'link': link,
                    'score': f'{item["score"]:.2f}',
                    'reason': reason,
                    'matched_keywords': item['matched_keywords'],
                    'recommendation_type': 'hybrid' if item['interest_score'] > 0 else 'trending',
                    'source_name': news.get('source', '未知'),
                    'time_ago': news.get('time_ago', '刚刚'),
                    'semantic_tags': news.get('semantic_tags', []),
                })

            logger.info(f'[推荐系统] 本地推荐生成 {len(local_recommendations)} 条推荐')
        except Exception as e:
            logger.error(f'[推荐系统] 本地推荐失败：{e}')
    else:
        logger.warning('[推荐系统] 本地新闻数据为空')

    # 如果本地推荐不足 20 条，从数据库补充更多数据
    if len(local_recommendations) < 20:
        try:
            # 从数据库获取最新新闻补充
            db_news = get_news(limit=50)
            if db_news and len(db_news) > len(news_list):
                # 补充数据库中独有的新闻
                existing_links = set(n.get('link') for n in news_list)
                additional_news = [n for n in db_news if n.get('link') not in existing_links]

                # 对补充的新闻重新计算分数
                for news in additional_news[:20 - len(local_recommendations)]:
                    title = news.get('title', '')
                    hot_score = news.get('hot_score') or 50
                    news_keywords = extract_keywords_enhanced([title], top_n=5)
                    interest_score = 0.0
                    matched_keywords = []
                    for kw in news_keywords:
                        if kw in user_vector:
                            interest_score += user_vector[kw]
                            matched_keywords.append(kw)
                    hot_normalized = (hot_score - 50) / 50 if hot_score > 50 else 0
                    combined_score = (interest_score * 0.7) + (hot_normalized * 0.3)

                    link = news.get('link', '#')
                    news_id = hashlib.md5(link.encode()).hexdigest()[:16] if link != '#' else 'unknown'
                    reason = '热门内容'
                    if interest_score > 0 and matched_keywords:
                        reason = f"匹配兴趣：{', '.join(matched_keywords[:3])}"

                    local_recommendations.append({
                        'news_id': news_id,
                        'title': title,
                        'link': link,
                        'score': f'{combined_score:.2f}',
                        'reason': reason,
                        'matched_keywords': matched_keywords,
                        'recommendation_type': 'hybrid' if interest_score > 0 else 'trending',
                        'source_name': news.get('source', '未知'),
                        'time_ago': news.get('time_ago', '刚刚'),
                        'semantic_tags': news.get('semantic_tags', []),
                    })

            logger.info(f'[推荐系统] 从数据库补充后共有 {len(local_recommendations)} 条推荐')
        except Exception as e:
            logger.error(f'[推荐系统] 从数据库补充失败：{e}')

    # 如果本地推荐不足 20 条且用户有关键词，使用外部 API 补充
    external_recommendations = []
    if len(local_recommendations) < 20 and user_keywords:
        try:
            logger.info(f'[推荐系统] 开始调用外部推荐 API 补充（已有{len(local_recommendations)}条）...')
            from recommendation_engine import sync_generate_recommendations

            external_recommendations = sync_generate_recommendations(
                news_list=news_list,
                user_keywords=user_keywords,
                history=history,
                limit=20 - len(local_recommendations)
            )
            logger.info(f'[推荐系统] 获取到 {len(external_recommendations)} 条外部推荐')
        except Exception as e:
            logger.error(f'[推荐系统] 外部 API 调用失败：{e}')

    # 合并推荐结果（本地优先，外部补充）
    if local_recommendations:
        recommendations = local_recommendations[:20]  # 返回 20 条
        elapsed = time.time() - start_time
        logger.info(f"推荐计算完成（本地优先），耗时 {elapsed:.3f}s，生成 {len(recommendations)} 条推荐")
        return jsonify({
            'recommendations': recommendations,
            'source': 'local_priority',
            'recommendation_types': {
                'trending': '实时热点',
                'hybrid': '兴趣 + 热点',
                'collaborative': '兴趣匹配'
            }
        })

    # 本地推荐为空时使用外部 API 结果
    if external_recommendations:
        recommendations = []
        for rec in external_recommendations[:10]:
            link = rec.get('link', '#')
            news_id = hashlib.md5(link.encode()).hexdigest()[:16] if link != '#' else 'unknown'
            recommendations.append({
                'news_id': news_id,
                'title': rec.get('title', ''),
                'link': link,
                'score': f'{rec.get("score", 0):.2f}',
                'reason': rec.get('reason', '为您推荐'),
                'recommendation_type': rec.get('recommendation_type', 'hybrid'),
                'source_name': rec.get('source', ''),
                'time_ago': '刚刚'
            })
        elapsed = time.time() - start_time
        logger.info(f"推荐计算完成（外部 API），耗时 {elapsed:.3f}s，生成 {len(recommendations)} 条推荐")
        return jsonify({'recommendations': recommendations, 'source': 'external_api'})

    # 都没有时返回空
    elapsed = time.time() - start_time
    logger.warning(f"推荐计算完成，无可用推荐，耗时 {elapsed:.3f}s")
    return jsonify({'recommendations': [], 'source': 'none'})


@app.route('/api/analyze/social', methods=['POST'])
def analyze_social():
    """社交分析接口 - 使用通义千问大模型进行深度社交舆情分析"""
    start_time = time.time()

    data = request.get_json()
    news_list = data.get('news', [])

    if not news_list:
        return jsonify({'metrics': {}, 'trends': [], 'ai_insights': None})

    # 尝试使用通义千问 AI 分析
    ai_result = analyze_social_with_qwen(news_list)

    if ai_result:
        elapsed = time.time() - start_time
        logger.info(f"社交分析完成（AI 模式），耗时 {elapsed:.3f}s")
        return jsonify(ai_result)

    # AI 分析失败时的降级方案：本地估算
    logger.warning("[社交分析] AI 分析失败，降级到本地估算模式")
    return fallback_local_social_analysis(news_list)


def analyze_social_with_qwen(news_list):
    """使用通义千问进行社交舆情分析"""
    if not DASHSCOPE_API_KEY:
        return None

    try:
        import dashscope
        from dashscope import Generation

        dashscope.api_key = DASHSCOPE_API_KEY

        # 精选代表性新闻（最多 30 条，覆盖高热度和不同来源）
        sorted_news = sorted(news_list, key=lambda x: x.get('hot_score') or 50, reverse=True)
        selected_news = sorted_news[:30]

        # 构建新闻摘要
        news_summary = "\n".join([
            f"- [{n.get('source', '未知')}] {n.get('title', '')} | 热度：{n.get('hot_score') or 50}"
            for n in selected_news
        ])

        # 构建专业提示词（高管 + 行研双重视角）
        prompt = f"""你是一位资深舆情分析专家，兼具企业高管战略视角和证券行业研究员的专业洞察力。
请基于以下最新热点新闻进行深度社交舆情分析：

{news_summary}

**报告定位**：
- 受众：企业 CEO、高管、战略决策者、行业研究员
- 风格：专业、精准、有数据支撑、有前瞻洞察
- 目标：帮助决策者快速把握舆情态势、识别机会与风险

请输出 JSON 格式的舆情分析报告，包含以下字段：
{{
    "executive_summary": "150 字以内的核心摘要，高度概括当前舆情态势，让高管 30 秒内掌握全局",
    "social_metrics": {{
        "total_engagement_estimate": "预估总互动量（基于热度分估算）",
        "viral_topic_count": "病毒式传播话题数量",
        "avg_sentiment_score": "平均情感得分 (0-1，越接近 1 越正面)",
        "trend_velocity": "趋势热度 (0-100，反映舆情升温速度）",
        "hot_score_avg": "平均热度分"
    }},
    "sentiment_analysis": {{
        "overall": "positive/neutral/negative",
        "positive_rate": 0.0-1.0,
        "neutral_rate": 0.0-1.0,
        "negative_rate": 0.0-1.0,
        "key_drivers": ["驱动情感倾向的关键事件或因素 1", "因素 2", ...]
    }},
    "trending_topics": [
        {{
            "topic": "热点话题名称（精准提炼，5-15 字）",
            "description": "话题详细描述（30-50 字，说明背景和进展）",
            "engagement_level": "high/medium/low",
            "hot_score": 热度分 (0-100),
            "sentiment": "positive/neutral/negative",
            "related_news_count": 相关新闻数量
        }}
    ],
    "industry_insights": [
        {{
            "trend": "行业趋势或动态",
            "impact_level": "high/medium/low",
            "affected_segments": ["受影响的细分领域 1", "细分领域 2"],
            "time_horizon": "short_term/medium_term/long_term",
            "strategic_implication": "对我方的战略启示或行动建议"
        }}
    ],
    "competitive_landscape": [
        {{
            "company": "公司/机构名称",
            "recent_move": "近期关键动态",
            "strategic_intent": "背后的战略意图分析",
            "threat_level": "high/medium/low",
            "our_response": "我方应对建议"
        }}
    ],
    "risk_alerts": [
        {{
            "risk_type": "政策/市场/技术/舆情/供应链/其他",
            "description": "风险描述（具体、可感知）",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "early_signals": "早期预警信号",
            "mitigation_actions": "具体应对建议"
        }}
    ],
    "opportunity_signals": [
        {{
            "opportunity_type": "市场/技术/合作/投资/其他",
            "description": "机会描述",
            "window": "short_term/medium_term/long_term",
            "action_required": "需要采取的行动"
        }}
    ],
    "recommended_actions": [
        {{
            "priority": "high/medium/low",
            "action": "具体行动项",
            "owner": "建议负责部门（如：战略部/市场部/产品部/PR）",
            "timeline": "建议完成时间"
        }}
    ]
}}

**撰写要求**：
1. 用中文输出，语言专业、精准、有洞察力
2. 核心摘要必须高度凝练，体现情报价值
3. 热点话题要精准提炼，反映真实舆情焦点
4. 行业洞察要有前瞻性和深度，体现专家视角
5. 竞争情报要聚焦头部玩家和颠覆性动态
6. 风险预警要具体可感知，有早期信号识别
7. 行动建议要可执行、可落地、有明确优先级
8. 基于新闻事实分析，不要臆测或编造
9. 如无明显风险/机会，对应字段可为空数组"""

        response = Generation.call(
            model='qwen-max',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=3000
        )

        if response.status_code == 200 and response.output and response.output.text:
            ai_content = response.output.text
            logger.info(f"[社交分析] AI 响应长度：{len(ai_content)}")

            # 解析 JSON
            result = parse_ai_response(ai_content)
            if result:
                # 字段名映射：将 AI 返回的字段名映射为前端期望的字段名
                social_metrics = result.get('social_metrics', {})
                metrics = {
                    'total_engagement': social_metrics.get('total_engagement_estimate', 0),
                    'viral_count': social_metrics.get('viral_topic_count', 0),
                    'sentiment_score': social_metrics.get('avg_sentiment_score', 0),
                    'trend_velocity': social_metrics.get('trend_velocity', 0),
                    'avg_hot_score': social_metrics.get('hot_score_avg', 0),
                    'sentiment_distribution': result.get('sentiment_analysis', {}),
                    'source': 'qwen-ai'
                }

                # 将 viral_topics 和 trends 映射为前端期望的格式
                viral_topics = []
                trending_topics = result.get('trending_topics', [])
                for topic in trending_topics[:3]:
                    viral_topics.append({
                        'topic': topic.get('topic', ''),
                        'engagement': topic.get('engagement_level', 'medium'),
                        'hot_score': topic.get('hot_score', 0),
                        'sentiment': topic.get('sentiment', 'neutral')
                    })

                trends = []
                for topic in trending_topics[:5]:
                    trends.append({
                        'topic': topic.get('topic', ''),
                        'engagement': topic.get('hot_score', 0) * 10,
                        'hot_score': topic.get('hot_score', 0)
                    })

                # 添加元数据
                result['metrics'] = metrics
                result['viral_topics'] = viral_topics
                result['trends'] = trends
                result['source'] = 'qwen-ai'
                result['analysis_type'] = 'social_sentiment_deep'
                result['news_count'] = len(news_list)
                result['analyzed_news_count'] = len(selected_news)
                return result

        logger.warning(f"[社交分析] API 调用失败：status={response.status_code}")
        return None

    except Exception as e:
        logger.error(f"[社交分析] 异常：{str(e)}", exc_info=True)
        return None


def fallback_local_social_analysis(news_list):
    """降级方案：本地估算逻辑"""
    total_count = len(news_list)

    total_engagement = 0
    viral_count = 0
    sentiment_sum = 0
    hot_topics = []
    sentiment_distribution = {'positive': 0, 'neutral': 0, 'negative': 0}

    for news in news_list:
        hot_score = news.get('hot_score') or 50
        title = news.get('title', '')
        sentiment = analyze_sentiment_simple(title)

        engagement = int(hot_score * 2.5)
        total_engagement += engagement

        if hot_score > 75:
            viral_count += 1
            hot_topics.append({
                'topic': news.get('title', '')[:30],
                'engagement': engagement,
                'hot_score': hot_score,
                'sentiment': sentiment
            })

        sentiment_scores = {'positive': 1, 'neutral': 0.5, 'negative': 0}
        sentiment_sum += sentiment_scores.get(sentiment, 0.5)
        sentiment_distribution[sentiment] += 1

    avg_sentiment = sentiment_sum / total_count if total_count > 0 else 0.5
    avg_hot_score = sum(n.get('hot_score') or 50 for n in news_list) / total_count if total_count > 0 else 50
    trend_velocity = (viral_count * 3.5) + (avg_hot_score / 10)

    titles = [n.get('title', '') for n in news_list]
    trend_keywords = extract_keywords_enhanced(titles, top_n=10)

    trends = [
        {'topic': kw, 'engagement': (idx + 1) * 100, 'hot_score': (10 - idx) * 5}
        for idx, kw in enumerate(trend_keywords[:5])
    ]

    hot_topics.sort(key=lambda x: x['hot_score'], reverse=True)
    top_viral = hot_topics[:3]

    return {
        'metrics': {
            'total_engagement': total_engagement,
            'viral_count': viral_count,
            'sentiment_score': f'{avg_sentiment:.2f}',
            'trend_velocity': f'{trend_velocity:.1f}',
            'avg_hot_score': f'{avg_hot_score:.1f}',
            'sentiment_distribution': sentiment_distribution,
            'source': 'local_fallback'
        },
        'trends': trends,
        'viral_topics': top_viral,
        'ai_insights': None
    }

    # 使用外部社交数据进行分析和整合
    # 统计各平台数据
    platform_stats = {}
    total_engagement = 0
    viral_count = 0
    sentiment_sum = 0
    sentiment_distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
    hot_topics = []
    trends = []

    for item in social_data:
        source = item.get('source', 'Unknown')
        hot_value = item.get('hot_value', 0)
        rank = item.get('rank', 0)

        # 平台统计
        if source not in platform_stats:
            platform_stats[source] = {'count': 0, 'total_hot': 0}
        platform_stats[source]['count'] += 1
        platform_stats[source]['total_hot'] += hot_value

        # 总互动量
        total_engagement += hot_value

        # 高热内容（hot_value > 10000 或 rank <= 3）
        if hot_value > 10000 or rank <= 3:
            viral_count += 1
            hot_topics.append({
                'topic': item.get('title', '')[:50],
                'engagement': hot_value,
                'hot_score': min(100, hot_value / 1000),
                'sentiment': 'neutral',
                'source': source,
                'link': item.get('link', '')
            })

        # 情感分析（简化版，按内容判断）
        title = item.get('title', '')
        sentiment = analyze_sentiment_simple(title)
        sentiment_scores = {'positive': 1, 'neutral': 0.5, 'negative': 0}
        sentiment_sum += sentiment_scores.get(sentiment, 0.5)
        sentiment_distribution[sentiment] += 1

        # 趋势话题
        trends.append({
            'topic': item.get('title', '')[:30],
            'engagement': hot_value,
            'hot_score': min(100, hot_value / 1000),
            'source': source,
            'rank': rank
        })

    # 计算平均值
    total_count = len(social_data) if social_data else 1
    avg_sentiment = sentiment_sum / total_count
    avg_hot_score = total_engagement / total_count if total_count > 0 else 0
    trend_velocity = (viral_count * 3.5) + (avg_hot_score / 1000)

    # 趋势话题按热度排序，取前 5
    trends.sort(key=lambda x: x['engagement'], reverse=True)
    trends = trends[:5]

    # 病毒话题按热度排序，取前 3
    hot_topics.sort(key=lambda x: x['hot_score'], reverse=True)
    top_viral = hot_topics[:3]

    elapsed = time.time() - start_time
    logger.info(f"社交分析完成（外部 API 模式），耗时 {elapsed:.3f}s，数据来源：{list(platform_stats.keys())}")

    return jsonify({
        'metrics': {
            'total_engagement': total_engagement,
            'viral_count': viral_count,
            'sentiment_score': f'{avg_sentiment:.2f}',
            'trend_velocity': f'{trend_velocity:.1f}',
            'avg_hot_score': f'{avg_hot_score:.1f}',
            'sentiment_distribution': sentiment_distribution,
            'platform_stats': platform_stats,
            'source': 'external_api'
        },
        'trends': trends,
        'viral_topics': top_viral
    })

def format_ai_analysis_html(analysis, total_count):
    """格式化 AI 分析结果为 HTML - 精简版（移除情感倾向、关键主题、信息密度、风险等级）"""
    html = f"""
    <div class="ai-analysis-report">
        <!-- 核心摘要 -->
        <div class="analysis-section">
            <h4>📋 核心摘要</h4>
            <p class="executive-summary">{analysis.get('executive_summary', '')}</p>
        </div>

        <!-- 热点话题 -->
        {format_trending_topics(analysis.get('trending_topics', []))}

        <!-- 行业洞察 -->
        {format_industry_insights(analysis.get('industry_insights', []))}

        <!-- 机会信号 -->
        {format_opportunities_list(analysis.get('opportunities', []))}

        <!-- 行动建议 -->
        {format_recommended_actions_list(analysis.get('recommended_actions', []))}
    </div>
    """
    return html


def format_key_highlights(highlights):
    """格式化关键事件"""
    if not highlights:
        return ''
    items = ''.join([f'<li>{h}</li>' for h in highlights])
    return f'<div class="analysis-section"><h4>🔥 关键事件</h4><ul class="key-highlights">{items}</ul></div>'


def format_trending_topics(topics):
    """格式化热点话题"""
    if not topics:
        return ''

    items = ''
    for topic in topics:
        heat_class = topic.get('heat_level', 'medium')
        items += f"""
        <div class="topic-item">
            <div class="topic-header">
                <span class="topic-name">{topic.get('topic', '')}</span>
                <span class="heat-badge {heat_class}">{topic.get('heat_level', '')}</span>
            </div>
            <p class="topic-description">{topic.get('description', '')}</p>
            <span class="topic-count">相关新闻：{topic.get('related_news_count', 0)}条</span>
        </div>
        """
    return f'<div class="analysis-section"><h4>🔥 热点话题</h4><div class="topics-container">{items}</div></div>'


def format_industry_insights(insights):
    """格式化行业洞察"""
    if not insights:
        return ''

    items = ''
    for insight in insights:
        impact_class = insight.get('impact_level', 'medium')
        items += f"""
        <div class="insight-item">
            <div class="insight-header">
                <span class="insight-trend">{insight.get('trend', '')}</span>
                <span class="impact-badge {impact_class}">{insight.get('impact_level', '')}</span>
            </div>
            <p class="insight-sectors">受影响领域：{', '.join(insight.get('affected_sectors', []))}</p>
            <p class="insight-implication">{insight.get('strategic_implication', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>📈 行业洞察</h4><div class="insights-container">{items}</div></div>'


def format_competitive_landscape(landscape):
    """格式化竞争情报"""
    if not landscape:
        return ''

    items = ''
    for intel in landscape:
        threat_class = intel.get('threat_level', 'medium')
        items += f"""
        <div class="competitive-item">
            <div class="competitive-header">
                <span class="company-name">{intel.get('company', '')}</span>
                <span class="threat-badge {threat_class}">{intel.get('threat_level', '')}</span>
            </div>
            <p class="competitive-move"><strong>关键动态：</strong>{intel.get('key_move', '')}</p>
            <p class="competitive-intent"><strong>战略意图：</strong>{intel.get('strategic_intent', '')}</p>
            <p class="competitive-response"><strong>我方应对：</strong>{intel.get('our_response', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>🏢 竞争情报</h4><div class="competitive-container">{items}</div></div>'


def format_risk_alerts(risks):
    """格式化风险预警"""
    if not risks:
        return ''

    items = ''
    for risk in risks:
        severity_class = risk.get('severity', 'medium')
        items += f"""
        <div class="risk-item">
            <div class="risk-header">
                <span class="risk-type">{risk.get('risk_type', '')}</span>
                <span class="severity-badge {severity_class}">{risk.get('severity', '')}</span>
            </div>
            <p class="risk-description">{risk.get('description', '')}</p>
            <p class="risk-signals"><strong>早期信号：</strong>{risk.get('early_signals', '')}</p>
            <p class="risk-mitigation"><strong>应对建议：</strong>{risk.get('mitigation', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>⚠️ 风险预警</h4><div class="risks-container">{items}</div></div>'


def format_opportunities_list(opportunities):
    """格式化机会信号"""
    if not opportunities:
        return ''

    items = ''
    for opp in opportunities:
        window_class = opp.get('window', 'medium_term')
        items += f"""
        <div class="opportunity-item">
            <div class="opportunity-header">
                <span class="opportunity-type">{opp.get('type', '')}</span>
                <span class="window-badge {window_class}">{opp.get('window', '')}</span>
            </div>
            <p class="opportunity-description">{opp.get('description', '')}</p>
            <p class="opportunity-action"><strong>建议行动：</strong>{opp.get('action', '')}</p>
        </div>
        """
    return f'<div class="analysis-section"><h4>💡 机会信号</h4><div class="opportunities-container">{items}</div></div>'


def format_recommended_actions_list(actions):
    """格式化行动建议"""
    if not actions:
        return ''

    items = ''
    for action in actions:
        priority_class = action.get('priority', 'medium')
        items += f"""
        <div class="action-item">
            <div class="action-header">
                <span class="priority-badge {priority_class}">{action.get('priority', '')} 优先级</span>
                <span class="action-owner">{action.get('owner', '')}</span>
            </div>
            <p class="action-text">{action.get('action', '')}</p>
            <span class="action-timeline">完成时间：{action.get('timeline', '')}</span>
        </div>
        """
    return f'<div class="analysis-section"><h4>✅ 行动建议</h4><div class="actions-container">{items}</div></div>'

def format_key_drivers(drivers):
    if not drivers:
        return ''
    items = ''.join([f'<li>{d}</li>' for d in drivers])
    return f'<div class="key-drivers"><strong>正面驱动因素：</strong><ul>{items}</ul></div>'

def format_trend_insights(insights):
    if not insights:
        return ''

    # 过滤掉没有实际内容的条目
    valid_insights = []
    for insight in insights:
        trend = insight.get('trend', '').strip()
        evidence = insight.get('evidence', '').strip()
        impact = insight.get('impact', '').strip()
        # 至少要有 trend 或 evidence 或 impact 其中之一才显示
        if trend or evidence or impact:
            valid_insights.append(insight)

    if not valid_insights:
        return ''

    items = ''
    for insight in valid_insights:
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
    print('=' * 60)
    print('📊 舆情监控系统启动')
    print('=' * 60)
    print(f'服务地址：http://localhost:5000')
    print(f'数据库路径：/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3')
    print(f'爬虫平台：{len(CRAWLER_IMPLEMENTED)} 个')
    print(f'RSS 源：国内 {len(RSS_FEEDS_DOMESTIC)} 个，国外 {len(RSS_FEEDS_OVERSEAS)} 个')
    print('=' * 60)
    print('提示：爬虫数据会通过定时任务每 10 分钟自动更新')
    print('      可通过 POST /api/refresh 手动刷新数据')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
