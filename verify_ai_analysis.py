#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据库中的 AI 分析记录
"""
from database import get_ai_analysis
import json

print("=" * 60)
print("查询数据库中所有 AI 分析记录")
print("=" * 60)

# 查询所有类型的分析记录
all_history = get_ai_analysis(limit=10)

print(f"\n📊 共找到 {len(all_history)} 条分析记录\n")

for idx, record in enumerate(all_history, 1):
    print(f"{'='*60}")
    print(f"记录 #{idx}")
    print(f"{'='*60}")
    print(f"📝 ID: {record['id']}")
    print(f"📊 类型：{record['analysis_type']}")
    print(f"📰 分析新闻数：{record['news_count']}")
    print(f"📅 创建时间：{record['created_at']}")
    print()

    print(f"💡 执行摘要:")
    print(f"   {record['executive_summary']}")
    print()

    print(f"📈 情感分析:")
    print(f"   整体倾向：{record['sentiment_overall']}")
    print(f"   正面率：{record['sentiment_positive_rate']}")
    if record['sentiment_drivers']:
        drivers = json.loads(record['sentiment_drivers']) if isinstance(record['sentiment_drivers'], str) else record['sentiment_drivers']
        print(f"   关键驱动：{', '.join(drivers[:3])}")
    print()

    if record['trend_insights']:
        print(f"🔮 趋势洞察 ({len(record['trend_insights'])}条):")
        for trend in record['trend_insights'][:3]:
            print(f"   • {trend.get('trend', 'N/A')}")
            print(f"     置信度：{trend.get('confidence', 'N/A')}")
            print(f"     影响：{trend.get('impact', 'N/A')[:50]}...")
        print()

    if record['competitive_intelligence']:
        print(f"🏢 竞争情报 ({len(record['competitive_intelligence'])}条):")
        for comp in record['competitive_intelligence'][:2]:
            print(f"   • {comp.get('company', 'N/A')}: {comp.get('action', 'N/A')[:30]}...")
        print()

    if record['risk_warnings']:
        print(f"⚠️ 风险警告 ({len(record['risk_warnings'])}条):")
        for risk in record['risk_warnings'][:2]:
            print(f"   • {risk.get('risk', 'N/A')[:40]}...")
            print(f"     严重性：{risk.get('severity', 'N/A')}")
            print(f"     建议：{risk.get('suggestion', 'N/A')[:40]}...")
        print()

    if record['opportunities']:
        print(f"🎯 机遇建议 ({len(record['opportunities'])}条):")
        for opp in record['opportunities'][:3]:
            print(f"   • {opp}")
        print()

    if record['recommended_actions']:
        print(f"📋 推荐行动 ({len(record['recommended_actions'])}条):")
        for action in record['recommended_actions'][:3]:
            print(f"   • {action}")
        print()

print("=" * 60)
print("查询完成！")
print("=" * 60)
