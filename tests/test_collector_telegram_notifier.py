"""test_collector_telegram_notifier.py — Telegram 通知内容格式测试"""

from collector.telegram_notifier import TelegramNotifier


def test_build_message_is_summary_first():
    notifier = TelegramNotifier()
    search_result = {
        "date": "2026-02-27",
        "raw_total": 120,
        "dedup_total": 36,
        "cluster_summary": {"cluster_count": 14},
    }
    plan_result = {
        "tech_ai": {
            "label": "AI 科技",
            "filtered_count": 20,
            "score_summary": {"avg": 63.2},
            "items": [
                {"title": "OpenAI 新发布模型能力解读", "source_name": "Hacker News",
                 "published_at": "2026-02-27T10:00:00+00:00", "summary": "OpenAI发布新模型，性能大幅提升",
                 "raw_data": {"score": 88}},
                {"title": "Agent 工程化实践路线", "source_name": "36kr AI",
                 "published_at": "", "summary": "Agent工程化的最佳实践",
                 "raw_data": {"score": 79}},
                {"title": "多模态推理成本下降", "source_name": "GitHub Trending",
                 "published_at": "2026-02-25T08:00:00+00:00", "summary": "多模态推理成本持续下降",
                 "raw_data": {"score": 74}},
                {"title": "会被截断的第四条", "raw_data": {"score": 70}},
            ],
        },
        "auto": {
            "label": "汽车",
            "filtered_count": 11,
            "score_summary": {"avg": 58.4},
            "items": [
                {"title": "城区 NOA 最新进展", "source_name": "懂车帝资讯",
                 "published_at": "2026-02-26T12:00:00+00:00", "summary": "城区NOA覆盖范围扩大",
                 "raw_data": {"score": 82}},
                {"title": "增程与快充路线之争", "source_name": "汽车之家",
                 "published_at": "", "summary": "增程和快充技术路线对比",
                 "raw_data": {"score": 71}},
            ],
        },
    }

    msg = notifier._build_message(search_result, plan_result)

    assert "🧠 今日总结" in msg
    assert "建议优先写：《OpenAI 新发布模型能力解读》" in msg
    assert "📌 分方向推荐（Top3）" in msg
    assert "会被截断的第四条" not in msg
    assert "素材池: content/pool/2026-02-27-pool.json" in msg
    # 新增：验证摘要、来源、时间
    assert "Hacker News" in msg
    assert "OpenAI发布新模型" in msg
    assert "时间未知" in msg  # Agent 工程化无 published_at
