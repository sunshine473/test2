"""使用正确的方式创建 Notion 关联字段"""

import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client


def create_relations_correctly():
    """使用正确的 API 方式创建关联字段"""
    print("=== 创建 Notion 关联字段（正确方式）===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))

    topics_id = os.getenv("NOTION_TOPICS_DB_ID")
    drafts_id = os.getenv("NOTION_DRAFTS_DB_ID")
    publish_id = os.getenv("NOTION_PUBLISH_DB_ID")

    # 获取所有数据库的 data_source_id
    topics_db = client.databases.retrieve(database_id=topics_id)
    drafts_db = client.databases.retrieve(database_id=drafts_id)
    publish_db = client.databases.retrieve(database_id=publish_id)

    topics_ds_id = topics_db['data_sources'][0]['id']
    drafts_ds_id = drafts_db['data_sources'][0]['id']
    publish_ds_id = publish_db['data_sources'][0]['id']

    print(f"选题库 Data Source ID: {topics_ds_id}")
    print(f"草稿库 Data Source ID: {drafts_ds_id}")
    print(f"发布记录 Data Source ID: {publish_ds_id}\n")

    # 1. 选题库 → 草稿库
    print("1. 创建 选题库 → 草稿库 关联...")
    try:
        client.data_sources.update(
            data_source_id=topics_ds_id,
            properties={
                "关联草稿": {
                    "relation": {
                        "data_source_id": drafts_ds_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            }
        )
        print("   ✅ 选题库 '关联草稿' 字段已创建\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")

    # 2. 草稿库 → 选题库
    print("2. 创建 草稿库 → 选题库 关联...")
    try:
        client.data_sources.update(
            data_source_id=drafts_ds_id,
            properties={
                "关联选题": {
                    "relation": {
                        "data_source_id": topics_ds_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            }
        )
        print("   ✅ 草稿库 '关联选题' 字段已创建\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")

    # 3. 发布记录 → 草稿库
    print("3. 创建 发布记录 → 草稿库 关联...")
    try:
        client.data_sources.update(
            data_source_id=publish_ds_id,
            properties={
                "关联草稿": {
                    "relation": {
                        "data_source_id": drafts_ds_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            }
        )
        print("   ✅ 发布记录 '关联草稿' 字段已创建\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")

    print("=== 完成 ===")
    print("\n验证关联字段...")

    # 验证字段是否创建成功
    topics_updated = client.data_sources.retrieve(data_source_id=topics_ds_id)
    drafts_updated = client.data_sources.retrieve(data_source_id=drafts_ds_id)
    publish_updated = client.data_sources.retrieve(data_source_id=publish_ds_id)

    results = []
    results.append(("选题库 → 关联草稿", "关联草稿" in topics_updated.get('properties', {})))
    results.append(("草稿库 → 关联选题", "关联选题" in drafts_updated.get('properties', {})))
    results.append(("发布记录 → 关联草稿", "关联草稿" in publish_updated.get('properties', {})))

    print("\n验证结果:")
    for name, exists in results:
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {'已创建' if exists else '未找到'}")

    success_count = sum(1 for _, e in results if e)
    print(f"\n总计: {success_count}/3 成功")


if __name__ == "__main__":
    create_relations_correctly()
