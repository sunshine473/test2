"""查找 Notion 数据库位置"""

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


def main():
    print("=== 查找 Notion 数据库 ===\n")

    client = Client(auth=os.getenv("NOTION_API_KEY"))

    db_ids = {
        "选题库": os.getenv("NOTION_TOPICS_DB_ID"),
        "草稿库": os.getenv("NOTION_DRAFTS_DB_ID"),
        "发布记录": os.getenv("NOTION_PUBLISH_DB_ID"),
    }

    for name, db_id in db_ids.items():
        if not db_id:
            print(f"X {name}: 未配置")
            continue

        try:
            db = client.databases.retrieve(database_id=db_id)
            title = db.get("title", [{}])[0].get("plain_text", "无标题")
            url = db.get("url", "N/A")

            print(f"OK {name}:")
            print(f"   标题: {title}")
            print(f"   URL: {url}")
            print(f"   ID: {db_id}")
            print()

        except Exception as e:
            print(f"X {name}: 无法访问 - {e}\n")


if __name__ == "__main__":
    main()
