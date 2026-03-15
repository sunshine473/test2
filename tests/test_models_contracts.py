"""test_models_contracts.py — 六层契约模型测试"""

from collector.models import CollectedItem
from models import MaterialPool, RawMaterial


def test_raw_material_round_trip_with_collected_item():
    item = CollectedItem(
        title="  AI <b>标题</b>  ",
        url="https://example.com",
        source_name="RSS",
        source_type="rss",
        category="tech_ai",
        summary="摘要",
        content="正文",
        published_at="2026-03-15T10:00:00Z",
        raw_data={"score": 1},
    )

    material = RawMaterial.from_collected_item(item)
    restored = material.to_collected_item()

    assert material.title == item.title
    assert restored.raw_data == {"score": 1}
    assert restored.content == "正文"


def test_material_pool_from_dict_builds_raw_materials():
    pool = MaterialPool.from_dict(
        {
            "date": "2026-03-15",
            "stage": "search",
            "raw_total": 1,
            "source_stats": {"rss": 1},
            "dedup_total": 1,
            "cluster_summary": {"cluster_count": 1, "max_cluster_size": 1},
            "items": [
                {
                    "title": "标题",
                    "url": "https://example.com",
                    "source_name": "RSS",
                    "source_type": "rss",
                    "category": "tech_ai",
                }
            ],
        }
    )

    assert len(pool.items) == 1
    assert pool.items[0].title == "标题"
