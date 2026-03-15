#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复兴趣标签系统
将预设兴趣标签迁移到 default 用户，使个性化推荐生效
"""
import sqlite3
import os

DB_PATH = '/Users/bs-00008898/OpenClaw_Data/Lumos/database.sqlite3'

# 预设兴趣分类（与 database.py 保持一致）
PRESET_INTEREST_CATEGORIES = {
    "宏观政策": ["政策", "法规", "税收", "补贴", "监管", "产业支持", "专精特新", "中小企业", "营商环境", "外贸", "出口", "进口", "关税", "信贷", "融资支持"],
    "行业趋势": ["转型", "数字化", "智能化", "升级", "创新", "技术突破", "国产替代", "供应链", "产业链", "产业集群", "行业报告", "市场分析", "竞争格局"],
    "经营管理": ["管理", "组织", "人才", "招聘", "培训", "绩效", "激励", "股权", "薪酬", "企业文化", "团队建设", "领导力", "战略", "商业模式"],
    "市场营销": ["营销", "品牌", "渠道", "客户", "销售", "推广", "获客", "私域", "直播", "电商", "跨境电商", "展会", "招商", "经销商", "代理商"],
    "财税金融": ["财税", "税务", "发票", "审计", "会计", "贷款", "融资", "银行", "担保", "保险", "理财", "现金流", "成本控制", "预算", "上市", "IPO", "新三板"],
    "法律合规": ["法律", "合规", "合同", "劳动", "知识产权", "专利", "商标", "诉讼", "仲裁", "工商", "质检", "环保", "安全生产", "数据合规"],
    "技术升级": ["自动化", "机器人", "智能制造", "工业互联网", "物联网", "5G", "云计算", "AI 应用", "数字化转型", "MES", "ERP", "信息化", "设备升级"],
    "供应链": ["供应链", "采购", "供应商", "物流", "仓储", "库存", "配送", "跨境电商物流", "冷链", "原材料", "价格上涨", "缺货", "产能"],
}


def migrate_interests_to_default():
    """将预设兴趣标签迁移到 default 用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("修复兴趣标签系统...")
    print("=" * 60)

    # 1. 检查 default 用户当前的兴趣标签数量
    cursor.execute('SELECT COUNT(*) FROM user_interests WHERE user_id = ?', ('default',))
    default_count = cursor.fetchone()[0]
    print(f"\ndefault 用户当前兴趣标签数：{default_count}")

    # 2. 检查 preset_*用户的兴趣标签数量
    cursor.execute('''
        SELECT user_id, COUNT(*) as count
        FROM user_interests
        WHERE user_id LIKE 'preset_%'
        GROUP BY user_id
    ''')
    preset_users = cursor.fetchall()
    print(f"preset_* 用户数：{len(preset_users)}")
    for user_id, count in preset_users[:5]:
        print(f"  - {user_id}: {count} 个标签")

    # 3. 迁移预设分类到 default 用户
    if default_count == 0:
        print("\n正在将预设分类迁移到 default 用户...")
        migrated_count = 0

        for category, keywords in PRESET_INTEREST_CATEGORIES.items():
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO user_interests (user_id, keyword, weight, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', ('default', keyword, 1.0))
                if cursor.rowcount > 0:
                    migrated_count += 1

        print(f"✓ 已迁移 {migrated_count} 个兴趣标签到 default 用户")
    else:
        print("\n✓ default 用户已有兴趣标签，无需迁移")

    # 4. 重建索引
    print("\n重建索引...")
    try:
        cursor.execute('DROP INDEX IF EXISTS idx_user_interests')
        cursor.execute('CREATE INDEX idx_user_interests ON user_interests(user_id, weight DESC)')
        print("✓ 索引重建完成")
    except Exception as e:
        print(f"索引重建失败：{e}")

    # 5. 验证结果
    cursor.execute('''
        SELECT keyword, weight
        FROM user_interests
        WHERE user_id = 'default'
        ORDER BY weight DESC
        LIMIT 20
    ''')
    default_interests = cursor.fetchall()

    print(f"\ndefault 用户兴趣标签（前 20 个）：")
    for keyword, weight in default_interests:
        print(f"  - {keyword} (权重：{weight})")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✓ 兴趣标签系统修复完成！")
    print("提示：个性化推荐现在会根据您的兴趣标签进行匹配")
    print("=" * 60)


def show_interest_stats():
    """显示兴趣标签统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("兴趣标签系统统计")
    print("=" * 60)

    # 所有用户 ID
    cursor.execute('SELECT DISTINCT user_id FROM user_interests')
    user_ids = [row[0] for row in cursor.fetchall()]
    print(f"\n用户总数：{len(user_ids)}")

    # 每个用户的标签数
    cursor.execute('''
        SELECT user_id, COUNT(*) as count
        FROM user_interests
        GROUP BY user_id
        ORDER BY count DESC
    ''')

    print("\n各用户标签分布：")
    for user_id, count in cursor.fetchall()[:10]:
        bar = "█" * (count // 10)
        print(f"  {user_id:20} {count:4} 个标签 {bar}")

    # default 用户的标签
    cursor.execute('''
        SELECT keyword, weight
        FROM user_interests
        WHERE user_id = 'default'
        ORDER BY weight DESC
        LIMIT 10
    ''')

    print("\ndefault 用户热门兴趣（Top 10）：")
    for keyword, weight in cursor.fetchall():
        print(f"  - {keyword} (权重：{weight})")

    conn.close()
    print("=" * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_interest_stats()
    else:
        migrate_interests_to_default()
