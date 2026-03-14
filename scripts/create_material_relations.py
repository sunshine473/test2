"""为素材池创建关联字段，建立完整数据链路"""

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


def create_material_pool_relations():
    """为素材池创建关联字段"""
    print("=== 为素材池创建关联字段 ===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))

    material_id = os.getenv("NOTION_DATABASE_ID")
    topics_id = os.getenv("NOTION_TOPICS_DB_ID")

    if not material_id:
        print("X NOTION_DATABASE_ID 未配置")
        return False

    if not topics_id:
        print("X NOTION_TOPICS_DB_ID 未配置")
        return False

    # 获取数据库的 data_source_id
    material_db = client.databases.retrieve(database_id=material_id)
    topics_db = client.databases.retrieve(database_id=topics_id)

    material_ds = material_db.get('data_sources', [])
    topics_ds = topics_db.get('data_sources', [])

    if not material_ds:
        print("! 素材池数据库不使用 data_sources 架构，尝试传统方式...")
        try:
            client.databases.update(
                database_id=material_id,
                properties={
                    "关联选题": {
                        "relation": {
                            "database_id": topics_id
                        }
                    }
                }
            )
            print("✅ 素材池 '关联选题' 字段已创建（传统方式）\n")
            return True
        except Exception as e:
            print(f"❌ 失败: {e}\n")
            return False

    material_ds_id = material_ds[0]['id']
    topics_ds_id = topics_ds[0]['id']

    print(f"素材池 Data Source ID: {material_ds_id}")
    print(f"选题库 Data Source ID: {topics_ds_id}\n")

    # 1. 素材池 → 选题库
    print("1. 创建 素材池 → 选题库 关联...")
    try:
        client.data_sources.update(
            data_source_id=material_ds_id,
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
        print("   ✅ 素材池 '关联选题' 字段已创建\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")
        return False

    # 2. 选题库 → 素材池（反向关联）
    print("2. 创建 选题库 → 素材池 关联...")
    try:
        client.data_sources.update(
            data_source_id=topics_ds_id,
            properties={
                "关联素材": {
                    "relation": {
                        "data_source_id": material_ds_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            }
        )
        print("   ✅ 选题库 '关联素材' 字段已创建\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")
        return False

    print("=== 完成 ===")
    print("\n验证关联字段...")

    # 验证
    material_updated = client.data_sources.retrieve(data_source_id=material_ds_id)
    topics_updated = client.data_sources.retrieve(data_source_id=topics_ds_id)

    results = []
    results.append(("素材池 → 关联选题", "关联选题" in material_updated.get('properties', {})))
    results.append(("选题库 → 关联素材", "关联素材" in topics_updated.get('properties', {})))

    print("\n验证结果:")
    for name, exists in results:
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {'已创建' if exists else '未找到'}")

    success_count = sum(1 for _, e in results if e)
    print(f"\n总计: {success_count}/2 成功")

    if success_count == 2:
        print("\n✅ 完整数据链路已建立：")
        print("   素材池 ↔ 选题库 ↔ 草稿库 ↔ 发布记录")

    return success_count == 2


if __name__ == "__main__":
    create_material_pool_relations()
