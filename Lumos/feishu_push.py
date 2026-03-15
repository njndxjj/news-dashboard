"""
飞书 Webhook 推送模块 - 舆情监控工具
"""
import json
import urllib.request
import urllib.error
from datetime import datetime
from database import (
    get_push_rules, save_push_log, get_setting,
    update_setting, get_news, get_hot_news
)


def send_feishu_message(webhook_url, message):
    """
    发送飞书消息
    :param webhook_url: 飞书机器人 Webhook URL
    :param message: 消息内容（字典格式）
    :return: (success: bool, response: str)
    """
    if not webhook_url:
        return False, "Webhook URL 未配置"

    try:
        # 构建请求
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        # 发送请求
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

        # 检查响应
        if result.get('StatusCode') == 0 or result.get('code') == 0:
            return True, "推送成功"
        else:
            return False, f"推送失败：{result}"

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        return False, f"HTTP 错误 {e.code}: {error_body}"
    except urllib.error.URLError as e:
        return False, f"网络错误：{e.reason}"
    except Exception as e:
        return False, f"推送异常：{str(e)}"


def format_single_news_card(news):
    """
    格式化单条新闻为飞书卡片
    :param news: 新闻字典
    :return: 卡片消息字典
    """
    title = news.get('title', '无标题')
    source = news.get('source', '未知来源')
    hot_score = news.get('hot_score', 0)
    link = news.get('link', '#')
    published = news.get('published', '')

    # 热度标识
    if hot_score >= 90:
        hot_badge = "🔥 高热"
        template = "red"
    elif hot_score >= 70:
        hot_badge = "📈 关注"
        template = "orange"
    else:
        hot_badge = "📰 资讯"
        template = "blue"

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{hot_badge} {title[:50]}"
                },
                "template": template
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**来源**: {source}\n**📅 时间**: {published}\n**🔥 热度**: {hot_score}分"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "elements": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🔗 查看详情"
                            },
                            "url": link,
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }

    return card


def format_breaking_news_batch(news_list, rule_name="热点预警"):
    """
    格式化批量新闻为突发快讯卡片
    :param news_list: 新闻列表
    :param rule_name: 触发规则名称
    :return: 卡片消息字典
    """
    if not news_list:
        return None

    # 构建新闻列表
    news_items = []
    for i, news in enumerate(news_list[:5], 1):  # 最多显示 5 条
        title = news.get('title', '无标题')
        source = news.get('source', '未知')
        hot_score = news.get('hot_score', 0)
        news_items.append(f"{i}. **[{source}]** {title[:40]} (🔥{hot_score}分)")

    news_content = "\n".join(news_items)

    more_count = len(news_list) - 5
    if more_count > 0:
        news_content += f"\n\n... 还有 {more_count} 条，请前往应用查看"

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🚨 {rule_name}"
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{news_content}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "elements": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📊 查看全部"
                            },
                            "url": "http://localhost:5000",  # 应用地址
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }

    return card


def format_daily_summary(news_list, period="早报"):
    """
    格式化每日汇总简报
    :param news_list: 新闻列表
    :param period: 早报/晚报
    :return: 卡片消息字典
    """
    if not news_list:
        return None

    # 热度统计
    avg_hot = sum(n.get('hot_score', 0) for n in news_list) / len(news_list) if news_list else 0

    # 热点新闻 TOP5
    hot_news = sorted(news_list, key=lambda x: x.get('hot_score', 0), reverse=True)[:5]
    hot_items = []
    for i, news in enumerate(hot_news, 1):
        title = news.get('title', '无标题')
        source = news.get('source', '未知')
        hot_score = news.get('hot_score', 0)
        hot_items.append(f"{i}. 🔥{hot_score}分 [{source}] {title[:35]}")

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📰 舆情{period} | {datetime.now().strftime('%m月%d日')}"
                },
                "template": "blue" if period == "早报" else "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📊 数据概览**\n"
                                   f"• 共监测 {len(news_list)} 条新闻\n"
                                   f"• 平均热度 {avg_hot:.1f}分"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🔥 热点 TOP5**\n" + "\n".join(hot_items)
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "elements": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📊 查看详细报告"
                            },
                            "url": "http://localhost:5000",
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }

    return card


def check_keywords_match(title, keywords):
    """
    检查标题是否匹配关键词
    :param title: 新闻标题
    :param keywords: 关键词列表
    :return: 是否匹配
    """
    if not keywords:
        return False
    return any(kw.lower() in title.lower() for kw in keywords)


def check_and_push_notifications(news_list):
    """
    检查推送规则并执行推送
    :param news_list: 新闻列表
    :return: 推送结果统计
    """
    # 获取 Webhook 配置
    webhook_url = get_setting('feishu_webhook', '')
    if not webhook_url:
        return {"status": "skip", "reason": "飞书 Webhook 未配置"}

    # 获取所有启用的推送规则
    rules = get_push_rules(enabled_only=True)
    if not rules:
        return {"status": "skip", "reason": "无启用的推送规则"}

    # 统计结果
    results = {
        "total_news": len(news_list),
        "pushed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "details": []
    }

    for rule in rules:
        rule_id = rule.get('id')
        rule_name = rule.get('rule_name', '未命名规则')
        keywords = rule.get('keywords', [])
        hot_threshold = rule.get('hot_threshold', 90)

        # 筛选匹配的新闻
        matched_news = []
        for news in news_list:
            title = news.get('title', '')
            hot_score = news.get('hot_score', 0)

            # 关键词匹配 或 热度匹配
            if check_keywords_match(title, keywords) or hot_score >= hot_threshold:
                matched_news.append(news)

        if not matched_news:
            continue

        # 高热新闻推送规则只推送 1 条（热度最高的）
        if rule_name == "高热新闻推送":
            matched_news = [max(matched_news, key=lambda x: x.get('hot_score', 0))]

        # 推送消息
        card = format_breaking_news_batch(matched_news, rule_name)
        success, message = send_feishu_message(webhook_url, card)

        # 记录推送日志
        for news in matched_news:
            news_id = news.get('news_id') or news.get('id')
            save_push_log(
                news_id=news_id,
                rule_id=rule_id,
                status='success' if success else 'failed',
                message=message
            )

        # 更新统计
        results["pushed_count"] += len(matched_news)
        if success:
            results["success_count"] += 1
            results["details"].append({
                "rule": rule_name,
                "count": len(matched_news),
                "status": "success"
            })
        else:
            results["failed_count"] += 1
            results["details"].append({
                "rule": rule_name,
                "count": len(matched_news),
                "status": "failed",
                "error": message
            })

    return results


def send_test_push(webhook_url):
    """
    发送测试推送
    :param webhook_url: 飞书 Webhook URL
    :return: (success, message)
    """
    test_card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "✅ 舆情监控 - 推送测试"
                },
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**飞书推送配置成功！**\n\n"
                                   f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                   f"如有任何问题，请检查系统配置。"
                    }
                }
            ]
        }
    }

    return send_feishu_message(webhook_url, test_card)


def send_daily_summary_push(period="morning"):
    """
    发送每日汇总推送
    :param period: morning/evening
    :return: (success, message)
    """
    webhook_url = get_setting('feishu_webhook', '')
    if not webhook_url:
        return False, "飞书 Webhook 未配置"

    # 获取今日新闻
    all_news = get_news(limit=50)
    if not all_news:
        return False, "暂无新闻数据"

    # 格式化简报
    period_name = "早报" if period == "morning" else "晚报"
    card = format_daily_summary(all_news, period_name)

    if not card:
        return False, "无法生成简报"

    return send_feishu_message(webhook_url, card)
