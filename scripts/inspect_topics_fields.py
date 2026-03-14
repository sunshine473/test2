"""检查选题库数据库字段"""

import io
import os
import sys
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client


def inspect_topics_db():
    """检查选题库数据库字段"""
    print("=== 检查选题库数据库字段 ===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))
    topics_id = os.getenv("NOTION_TOPICS_DB_ID")

    db = client.databases.retrieve(database_id=topics_id)
    data_sources = db.get("data_sources", [])

    if data_sources:
        ds_id = data_sources[0]["id"]
        ds_detail = client.data_sources.retrieve(data_source_id=ds_id)
        properties = ds_detail.get("properties", {})
    else:
        properties = db.get("properties", {})

    print(f"选题库字段列表 (共 {len(properties)} 个):\n")

    for name, config in properties.items():
        prop_type = config.get("type", "unknown")
        print(f"  - {name}: {prop_type}")

        if prop_type == "relation":
            relation_config = config.get("relation", {})
            print(f"    → 关联到: {relation_config.get('database_id', 'N/A')}")

    # 检查是否有重复的 "关联素材" 字段
    print("\n检查 '关联素材' 字段:")
    if "关联素材" in properties:
        field_type = properties["关联素材"].get("type")
        print(f"  ✓ 找到 '关联素材' 字段，类型: {field_type}")
        if field_type == "relation":
            print("  → 这是 relation 类型（正确）")
        else:
            print(f"  ⚠ 这是 {field_type} 类型（需要删除或改名）")
    else:
        print("  ✗ 未找到 '关联素材' 字段")

    print("\n检查 '素材链接' 字段:")
    if "素材链接" in properties:
        field_type = properties["素材链接"].get("type")
        print(f"  ✓ 找到 '素材链接' 字段，类型: {field_type}")
    else:
        print("  ✗ 未找到 '素材链接' 字段（需要创建）")


if __name__ == "__main__":
    inspect_topics_db()
