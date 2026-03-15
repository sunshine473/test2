"""test_normalizer_main.py — 整理层编排测试"""

from collector.models import CollectedItem
from normalizer.main import normalize


def test_normalize_cleans_and_deduplicates():
    raw_items = [
        CollectedItem(
            title="  AI <b>新模型</b> ",
            url="https://example.com/a",
            source_name="RSS",
            source_type="rss",
            category="tech_ai",
            summary="<p>摘要</p>",
            content="",
        ),
        CollectedItem(
            title="AI 新模型",
            url="https://example.com/a?ref=dup",
            source_name="RSS",
            source_type="rss",
            category="tech_ai",
            summary="摘要",
            content="更完整的内容",
        ),
    ]

    pool = normalize(raw_items, {"rss": 2})

    assert pool.raw_total == 2
    assert pool.dedup_total == 1
    assert pool.items[0].title == "AI 新模型"
    assert pool.items[0].content == "更完整的内容"
    assert pool.cluster_summary["cluster_count"] >= 1
