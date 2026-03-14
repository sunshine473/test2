"""深入研究 Notion data_sources API 结构"""

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


def inspect_database_structure():
    """详细检查数据库结构"""
    print("=== 深入分析 Notion 数据库结构 ===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))

    topics_id = os.getenv("NOTION_TOPICS_DB_ID")
    drafts_id = os.getenv("NOTION_DRAFTS_DB_ID")

    print("1. 选题库数据库结构")
    print("-" * 50)
    db = client.databases.retrieve(database_id=topics_id)

    print(f"Database ID: {db['id']}")
    print(f"Title: {db.get('title', [{}])[0].get('plain_text', 'N/A')}")
    print(f"Has data_sources: {bool(db.get('data_sources'))}")

    if db.get('data_sources'):
        data_source = db['data_sources'][0]
        print(f"\nData Source:")
        print(f"  ID: {data_source['id']}")
        print(f"  Type: {data_source.get('type', 'N/A')}")
        print(f"  Name: {data_source.get('name', 'N/A')}")

        # 获取 data source 详细信息
        print(f"\n2. Data Source 详细信息")
        print("-" * 50)
        ds_id = data_source['id']
        ds_detail = client.data_sources.retrieve(data_source_id=ds_id)

        print(f"Data Source ID: {ds_detail['id']}")
        print(f"Type: {ds_detail.get('type', 'N/A')}")

        # 检查现有的 relation 字段
        properties = ds_detail.get('properties', {})
        print(f"\n现有字段数量: {len(properties)}")

        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get('type', 'unknown')
            if prop_type == 'relation':
                print(f"\n找到 Relation 字段: {prop_name}")
                print(f"  配置: {json.dumps(prop_config, indent=2, ensure_ascii=False)}")

    print("\n\n3. 草稿库数据库结构")
    print("-" * 50)
    drafts_db = client.databases.retrieve(database_id=drafts_id)

    if drafts_db.get('data_sources'):
        drafts_ds = drafts_db['data_sources'][0]
        print(f"Data Source ID: {drafts_ds['id']}")

        drafts_detail = client.data_sources.retrieve(data_source_id=drafts_ds['id'])
        properties = drafts_detail.get('properties', {})

        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get('type', 'unknown')
            if prop_type == 'relation':
                print(f"\n找到 Relation 字段: {prop_name}")
                print(f"  配置: {json.dumps(prop_config, indent=2, ensure_ascii=False)}")

    print("\n\n4. 尝试创建 Relation 字段")
    print("-" * 50)

    # 获取两个数据库的 data_source_id
    topics_ds_id = db['data_sources'][0]['id']
    drafts_ds_id = drafts_db['data_sources'][0]['id']

    print(f"选题库 Data Source ID: {topics_ds_id}")
    print(f"草稿库 Data Source ID: {drafts_ds_id}")

    # 尝试不同的配置方式
    test_configs = [
        {
            "name": "方式 1: 使用 data_source_id + single_property",
            "config": {
                "关联草稿_测试1": {
                    "relation": {
                        "data_source_id": drafts_ds_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            }
        },
        {
            "name": "方式 2: 使用 data_source_id + dual_property",
            "config": {
                "关联草稿_测试2": {
                    "relation": {
                        "data_source_id": drafts_ds_id,
                        "type": "dual_property",
                        "dual_property": {
                            "synced_property_name": "关联选题_测试2"
                        }
                    }
                }
            }
        },
        {
            "name": "方式 3: 使用 database_id（传统方式）",
            "config": {
                "关联草稿_测试3": {
                    "relation": {
                        "database_id": drafts_id
                    }
                }
            }
        }
    ]

    for test in test_configs:
        print(f"\n测试 {test['name']}...")
        try:
            client.data_sources.update(
                data_source_id=topics_ds_id,
                properties=test['config']
            )
            print(f"  ✅ 成功！")

            # 验证字段是否创建
            updated = client.data_sources.retrieve(data_source_id=topics_ds_id)
            field_name = list(test['config'].keys())[0]
            if field_name in updated.get('properties', {}):
                print(f"  ✅ 字段 '{field_name}' 已创建")
                print(f"  配置: {json.dumps(updated['properties'][field_name], indent=2, ensure_ascii=False)}")

                # 清理测试字段
                print(f"  清理测试字段...")
                client.data_sources.update(
                    data_source_id=topics_ds_id,
                    properties={field_name: None}
                )
            break

        except Exception as e:
            print(f"  ❌ 失败: {e}")


if __name__ == "__main__":
    inspect_database_structure()
