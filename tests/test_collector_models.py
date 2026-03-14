"""test_collector_models.py — CollectedItem 数据模型测试"""

from collector.models import CollectedItem


def test_collected_item_to_dict_includes_content():
    item = CollectedItem(
        title="标题",
        url="https://example.com",
        source_name="RSS",
        source_type="rss",
        category="tech_ai",
        summary="短摘要",
        content="更完整的主要内容",
        language="zh",
    )

    data = item.to_dict()

    assert data["summary"] == "短摘要"
    assert data["content"] == "更完整的主要内容"
