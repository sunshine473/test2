"""自动创建 Notion 数据库脚本

此脚本会自动创建 3 个数据库：选题库、草稿库、发布记录
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client


def get_parent_page():
    """获取父页面 ID（需要用户提供或搜索）"""
    # 尝试从环境变量获取
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
    if parent_page_id:
        return parent_page_id

    # 如果没有配置，尝试搜索工作区
    client = Client(auth=os.getenv("NOTION_API_KEY"))
    try:
        # 搜索最近的页面
        results = client.search(filter={"property": "object", "value": "page"}, page_size=1)
        if results.get("results"):
            page_id = results["results"][0]["id"]
            print(f"找到页面: {results['results'][0].get('url', page_id)}")
            return page_id
    except Exception as e:
        print(f"搜索页面失败: {e}")

    return None


def create_topics_database(client, parent_id):
    """创建选题库数据库"""
    print("\n创建选题库数据库...")

    try:
        database = client.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "选题库 (Topic Library)"}}],
            properties={
                "选题标题": {"title": {}},
                "方向": {"select": {"options": [
                    {"name": "AI科技", "color": "blue"},
                    {"name": "汽车", "color": "green"}
                ]}},
                "评分": {"number": {"format": "number"}},
                "推荐理由": {"rich_text": {}},
                "关联素材": {"rich_text": {}},
                "状态": {"select": {"options": [
                    {"name": "待选择", "color": "gray"},
                    {"name": "已选中", "color": "yellow"},
                    {"name": "已生成", "color": "blue"},
                    {"name": "已发布", "color": "green"},
                    {"name": "已放弃", "color": "red"}
                ]}},
                "推荐日期": {"date": {}},
                "选中日期": {"date": {}},
            }
        )

        db_id = database["id"]
        print(f"OK 选题库已创建")
        print(f"  数据库 ID: {db_id}")
        print(f"  URL: {database.get('url', 'N/A')}")
        return db_id

    except Exception as e:
        print(f"X 创建失败: {e}")
        return None


def create_drafts_database(client, parent_id, topics_db_id=None):
    """创建草稿库数据库"""
    print("\n创建草稿库数据库...")

    properties = {
        "文章标题": {"title": {}},
        "文件路径": {"url": {}},
        "字数": {"number": {"format": "number"}},
        "质量评级": {"select": {"options": [
            {"name": "A", "color": "green"},
            {"name": "B", "color": "yellow"},
            {"name": "C", "color": "red"}
        ]}},
        "质量评分": {"rich_text": {}},
        "标签": {"multi_select": {"options": []}},
        "摘要": {"rich_text": {}},
        "状态": {"select": {"options": [
            {"name": "待审核", "color": "gray"},
            {"name": "审核通过", "color": "green"},
            {"name": "需修改", "color": "yellow"},
            {"name": "已发布", "color": "blue"}
        ]}},
        "生成日期": {"date": {}},
        "审核日期": {"date": {}},
    }

    # 关联字段在 databases.create 时可以使用 database_id（旧 API）
    # 但在 data_sources 架构下需要手动创建或使用 data_source_id
    if topics_db_id:
        properties["关联选题"] = {"relation": {"database_id": topics_db_id}}

    try:
        database = client.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "草稿库 (Draft Library)"}}],
            properties=properties
        )

        db_id = database["id"]
        print(f"OK 草稿库已创建")
        print(f"  数据库 ID: {db_id}")
        print(f"  URL: {database.get('url', 'N/A')}")
        return db_id

    except Exception as e:
        print(f"X 创建失败: {e}")
        return None


def create_publish_database(client, parent_id, drafts_db_id=None):
    """创建发布记录数据库"""
    print("\n创建发布记录数据库...")

    properties = {
        "标题": {"title": {}},
        "平台": {"select": {"options": [
            {"name": "微信公众号", "color": "green"},
            {"name": "知乎", "color": "blue"},
            {"name": "B站", "color": "pink"},
            {"name": "小红书", "color": "red"},
            {"name": "懂车帝", "color": "orange"},
            {"name": "头条", "color": "yellow"}
        ]}},
        "状态": {"select": {"options": [
            {"name": "成功", "color": "green"},
            {"name": "失败", "color": "red"},
            {"name": "草稿", "color": "gray"}
        ]}},
        "发布链接": {"url": {}},
        "发布消息": {"rich_text": {}},
        "发布日期": {"date": {}},
    }

    # 关联字段在 databases.create 时可以使用 database_id（旧 API）
    # 但在 data_sources 架构下需要手动创建或使用 data_source_id
    if drafts_db_id:
        properties["关联草稿"] = {"relation": {"database_id": drafts_db_id}}

    try:
        database = client.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "发布记录 (Publish Records)"}}],
            properties=properties
        )

        db_id = database["id"]
        print(f"OK 发布记录已创建")
        print(f"  数据库 ID: {db_id}")
        print(f"  URL: {database.get('url', 'N/A')}")
        return db_id

    except Exception as e:
        print(f"X 创建失败: {e}")
        return None


def update_env_file(topics_id, drafts_id, publish_id):
    """更新 .env 文件"""
    print("\n更新 .env 文件...")

    env_path = PROJECT_ROOT / ".env"
    content = env_path.read_text(encoding="utf-8")

    # 替换或添加配置
    lines = content.split("\n")
    updated = False

    for i, line in enumerate(lines):
        if line.startswith("# NOTION_TOPICS_DB_ID=") or line.startswith("NOTION_TOPICS_DB_ID="):
            lines[i] = f"NOTION_TOPICS_DB_ID={topics_id}"
            updated = True
        elif line.startswith("# NOTION_DRAFTS_DB_ID=") or line.startswith("NOTION_DRAFTS_DB_ID="):
            lines[i] = f"NOTION_DRAFTS_DB_ID={drafts_id}"
        elif line.startswith("# NOTION_PUBLISH_DB_ID=") or line.startswith("NOTION_PUBLISH_DB_ID="):
            lines[i] = f"NOTION_PUBLISH_DB_ID={publish_id}"

    if not updated:
        # 如果没有找到，追加到文件末尾
        lines.extend([
            "",
            "# Notion 数据中枢（自动创建）",
            f"NOTION_TOPICS_DB_ID={topics_id}",
            f"NOTION_DRAFTS_DB_ID={drafts_id}",
            f"NOTION_PUBLISH_DB_ID={publish_id}",
        ])

    env_path.write_text("\n".join(lines), encoding="utf-8")
    print("OK .env 文件已更新")


def main():
    # 确保 UTF-8 输出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=== Notion 数据库自动创建 ===")

    # 检查配置
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        print("x NOTION_API_KEY 未配置")
        sys.exit(1)

    client = Client(auth=api_key)

    # 获取父页面
    print("\n查找父页面...")
    parent_id = get_parent_page()

    if not parent_id:
        print("\nX 无法找到父页面")
        print("\n请在 .env 中配置 NOTION_PARENT_PAGE_ID（任意 Notion 页面的 ID）")
        print("或者在 Notion 中创建一个页面，然后从 URL 中复制页面 ID")
        sys.exit(1)

    print(f"OK 使用父页面: {parent_id}")

    # 创建数据库
    topics_id = create_topics_database(client, parent_id)
    if not topics_id:
        sys.exit(1)

    drafts_id = create_drafts_database(client, parent_id, topics_id)
    if not drafts_id:
        sys.exit(1)

    publish_id = create_publish_database(client, parent_id, drafts_id)
    if not publish_id:
        sys.exit(1)

    # 更新关联关系（选题库关联草稿库）
    # 注意：在 data_sources 架构下，relation 字段可能需要手动在 UI 中创建
    print("\n更新数据库关联...")
    try:
        client.databases.update(
            database_id=topics_id,
            properties={"关联草稿": {"relation": {"database_id": drafts_id}}}
        )
        print("OK 选题库已关联草稿库")
    except Exception as e:
        print(f"! 关联更新失败（可能需要在 Notion UI 中手动创建）: {e}")

    # 更新 .env 文件
    update_env_file(topics_id, drafts_id, publish_id)

    print("\n=== 创建完成 ===")
    print(f"\n已创建 3 个数据库并更新 .env 配置")
    print(f"\n你可以在 Notion 中查看这些数据库，或运行以下命令测试：")
    print(f"  python src/collector/planner.py --recommend")
    print(f"  python src/generator/main.py \"测试选题\"")


if __name__ == "__main__":
    main()
