"""Notion 数据库自动配置脚本

使用方法：
1. 在 Notion 中手动创建 3 个空数据库（选题库、草稿库、发布记录）
2. 将数据库 ID 填入 .env 文件
3. 运行此脚本自动配置字段：python scripts/setup_notion_databases.py
"""

import io
import os
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client


def setup_topics_database():
    """配置选题库数据库字段"""
    db_id = os.getenv("NOTION_TOPICS_DB_ID")
    if not db_id:
        print("! NOTION_TOPICS_DB_ID 未配置，跳过选题库")
        return False

    try:
        client = Client(auth=os.getenv("NOTION_API_KEY"))
        db = client.databases.retrieve(database_id=db_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            schema_obj = client.data_sources.retrieve(data_source_id=data_source_id)
            properties = schema_obj.get("properties", {})
        else:
            properties = db.get("properties", {})

        # 检查是否有 title 字段
        title_key = next((k for k, v in properties.items() if v.get("type") == "title"), None)
        if not title_key:
            print("X 选题库缺少 title 字段，请确保数据库已创建")
            return False

        # 需要添加的字段（不包含关联字段）
        required = {
            "方向": {"select": {"options": []}},
            "评分": {"number": {"format": "number"}},
            "推荐理由": {"rich_text": {}},
            "关联素材": {"rich_text": {}},
            "状态": {"select": {"options": []}},
            "推荐日期": {"date": {}},
            "选中日期": {"date": {}},
        }

        missing = {name: spec for name, spec in required.items() if name not in properties}

        if missing:
            if data_sources:
                client.data_sources.update(data_source_id=data_source_id, properties=missing)
            else:
                client.databases.update(database_id=db_id, properties=missing)
            print(f"OK 选题库已配置 {len(missing)} 个字段")
        else:
            print("OK 选题库字段已完整")
        return True

    except Exception as e:
        print(f"X 选题库配置失败: {e}")
        return False


def setup_drafts_database():
    """配置草稿库数据库字段"""
    db_id = os.getenv("NOTION_DRAFTS_DB_ID")
    if not db_id:
        print("! NOTION_DRAFTS_DB_ID 未配置，跳过草稿库")
        return False

    try:
        client = Client(auth=os.getenv("NOTION_API_KEY"))
        db = client.databases.retrieve(database_id=db_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            schema_obj = client.data_sources.retrieve(data_source_id=data_source_id)
            properties = schema_obj.get("properties", {})
        else:
            properties = db.get("properties", {})

        title_key = next((k for k, v in properties.items() if v.get("type") == "title"), None)
        if not title_key:
            print("X 草稿库缺少 title 字段，请确保数据库已创建")
            return False

        required = {
            "文件路径": {"url": {}},
            "字数": {"number": {"format": "number"}},
            "质量评级": {"select": {"options": []}},
            "质量评分": {"rich_text": {}},
            "标签": {"multi_select": {"options": []}},
            "摘要": {"rich_text": {}},
            "状态": {"select": {"options": []}},
            "生成日期": {"date": {}},
            "审核日期": {"date": {}},
        }

        missing = {name: spec for name, spec in required.items() if name not in properties}

        if missing:
            if data_sources:
                client.data_sources.update(data_source_id=data_source_id, properties=missing)
            else:
                client.databases.update(database_id=db_id, properties=missing)
            print(f"OK 草稿库已配置 {len(missing)} 个字段")
        else:
            print("OK 草稿库字段已完整")
        return True

    except Exception as e:
        print(f"X 草稿库配置失败: {e}")
        return False


def setup_publish_database():
    """配置发布记录数据库字段"""
    db_id = os.getenv("NOTION_PUBLISH_DB_ID")
    if not db_id:
        print("! NOTION_PUBLISH_DB_ID 未配置，跳过发布记录")
        return False

    try:
        client = Client(auth=os.getenv("NOTION_API_KEY"))
        db = client.databases.retrieve(database_id=db_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            schema_obj = client.data_sources.retrieve(data_source_id=data_source_id)
            properties = schema_obj.get("properties", {})
        else:
            properties = db.get("properties", {})

        title_key = next((k for k, v in properties.items() if v.get("type") == "title"), None)
        if not title_key:
            print("X 发布记录缺少 title 字段，请确保数据库已创建")
            return False

        required = {
            "平台": {"select": {"options": []}},
            "状态": {"select": {"options": []}},
            "发布链接": {"url": {}},
            "发布消息": {"rich_text": {}},
            "发布日期": {"date": {}},
        }

        missing = {name: spec for name, spec in required.items() if name not in properties}

        if missing:
            if data_sources:
                client.data_sources.update(data_source_id=data_source_id, properties=missing)
            else:
                client.databases.update(database_id=db_id, properties=missing)
            print(f"OK 发布记录已配置 {len(missing)} 个字段")
        else:
            print("OK 发布记录字段已完整")
        return True

    except Exception as e:
        print(f"X 发布记录配置失败: {e}")
        return False


def main():
    print("=== Notion 数据库自动配置 ===\n")

    # 检查必需配置
    if not os.getenv("NOTION_API_KEY"):
        print("X NOTION_API_KEY 未配置，请先在 .env 中配置")
        sys.exit(1)

    print("开始配置数据库字段...\n")

    results = []
    results.append(("选题库", setup_topics_database()))
    results.append(("草稿库", setup_drafts_database()))
    results.append(("发布记录", setup_publish_database()))

    print("\n=== 配置完成 ===")
    success = sum(1 for _, ok in results if ok)
    total = len([r for r in results if r[1] is not False])
    print(f"成功: {success}/{total}")

    if success < total:
        print("\n提示：请确保在 Notion 中创建了对应的数据库，并在 .env 中配置了数据库 ID")

    print("\n注意：关联字段（Relation）需要在 Notion UI 中手动创建")
    print("  - 选题库 → 草稿库：创建 '关联草稿' 字段")
    print("  - 草稿库 → 选题库：创建 '关联选题' 字段")
    print("  - 发布记录 → 草稿库：创建 '关联草稿' 字段")


if __name__ == "__main__":
    main()
