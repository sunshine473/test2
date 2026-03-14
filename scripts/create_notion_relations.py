"""尝试通过 API 创建 Notion 关联字段"""

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


def create_relations():
    """尝试创建关联字段"""
    print("=== 创建 Notion 关联字段 ===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))

    topics_id = os.getenv("NOTION_TOPICS_DB_ID")
    drafts_id = os.getenv("NOTION_DRAFTS_DB_ID")
    publish_id = os.getenv("NOTION_PUBLISH_DB_ID")

    # 1. 选题库 → 草稿库
    print("1. 创建 选题库 → 草稿库 关联...")
    try:
        db = client.databases.retrieve(database_id=topics_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            # 使用 data_sources API
            data_source_id = data_sources[0]["id"]
            client.data_sources.update(
                data_source_id=data_source_id,
                properties={
                    "关联草稿": {
                        "relation": {
                            "database_id": drafts_id,
                            "type": "dual_property",
                            "dual_property": {}
                        }
                    }
                }
            )
        else:
            # 使用传统 API
            client.databases.update(
                database_id=topics_id,
                properties={
                    "关联草稿": {
                        "relation": {
                            "database_id": drafts_id
                        }
                    }
                }
            )
        print("   OK 选题库关联字段已创建\n")
    except Exception as e:
        print(f"   X 失败: {e}\n")

    # 2. 草稿库 → 选题库
    print("2. 创建 草稿库 → 选题库 关联...")
    try:
        db = client.databases.retrieve(database_id=drafts_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            client.data_sources.update(
                data_source_id=data_source_id,
                properties={
                    "关联选题": {
                        "relation": {
                            "database_id": topics_id,
                            "type": "dual_property",
                            "dual_property": {}
                        }
                    }
                }
            )
        else:
            client.databases.update(
                database_id=drafts_id,
                properties={
                    "关联选题": {
                        "relation": {
                            "database_id": topics_id
                        }
                    }
                }
            )
        print("   OK 草稿库关联字段已创建\n")
    except Exception as e:
        print(f"   X 失败: {e}\n")

    # 3. 发布记录 → 草稿库
    print("3. 创建 发布记录 → 草稿库 关联...")
    try:
        db = client.databases.retrieve(database_id=publish_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            client.data_sources.update(
                data_source_id=data_source_id,
                properties={
                    "关联草稿": {
                        "relation": {
                            "database_id": drafts_id,
                            "type": "dual_property",
                            "dual_property": {}
                        }
                    }
                }
            )
        else:
            client.databases.update(
                database_id=publish_id,
                properties={
                    "关联草稿": {
                        "relation": {
                            "database_id": drafts_id
                        }
                    }
                }
            )
        print("   OK 发布记录关联字段已创建\n")
    except Exception as e:
        print(f"   X 失败: {e}\n")

    print("=== 完成 ===")


if __name__ == "__main__":
    create_relations()
