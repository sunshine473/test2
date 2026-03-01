"""Notion 素材库查询工具

用法:
    python src/collector/notion_search.py --keywords "AI编程助手,Copilot,代码生成" --limit 10
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()


def search_notion(keywords: list[str], limit: int = 10) -> list[dict]:
    """从 Notion 数据库中搜索相关素材"""
    api_key = os.getenv("NOTION_API_KEY", "")
    db_id = os.getenv("NOTION_DATABASE_ID", "")

    if not api_key or not db_id:
        return []

    try:
        from notion_client import Client
    except ImportError:
        print("需要安装: pip install notion-client", file=sys.stderr)
        return []

    client = Client(auth=api_key)

    # 动态获取标题字段名（与 notion_output.py 逻辑一致）
    try:
        db = client.databases.retrieve(database_id=db_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            ds_id = data_sources[0]["id"]
            schema = client.data_sources.retrieve(data_source_id=ds_id).get("properties", {})
        else:
            schema = db.get("properties", {})

        title_key = next((k for k, v in schema.items() if v.get("type") == "title"), None)
        if not title_key:
            print("未找到标题字段", file=sys.stderr)
            return []
    except Exception as e:
        print(f"获取数据库 schema 失败: {e}", file=sys.stderr)
        return []

    # 按关键词搜索
    results = []
    for kw in keywords[:5]:  # 最多搜索前 5 个关键词
        try:
            if data_sources:
                # data_sources 模式：使用 data_sources.query
                resp = client.data_sources.query(
                    data_source_id=ds_id,
                    filter={"property": title_key, "title": {"contains": kw}},
                    page_size=limit,
                )
            else:
                # 普通数据库模式：限定在目标数据库内查询，避免全局 search 混入其他页面
                resp = client.databases.query(
                    database_id=db_id,
                    filter={"property": title_key, "title": {"contains": kw}},
                    page_size=limit,
                )

            for page in resp.get("results", []):
                props = page.get("properties", {})

                # 提取标题
                title_arr = props.get(title_key, {}).get("title", [])
                title = title_arr[0]["plain_text"] if title_arr else ""

                # 提取 URL
                url = props.get("URL", {}).get("url", "")

                # 提取摘要
                summary_arr = props.get("摘要", {}).get("rich_text", [])
                summary = summary_arr[0]["plain_text"][:200] if summary_arr else ""

                if title:
                    results.append({
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "keyword": kw,
                    })
        except Exception as e:
            print(f"关键词 '{kw}' 查询失败: {e}", file=sys.stderr)

    # 去重（按 URL 或标题）
    seen = set()
    unique = []
    for r in results:
        key = r["url"] or r["title"]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:limit]


def main():
    parser = argparse.ArgumentParser(description="Notion 素材库查询")
    parser.add_argument("--keywords", required=True, help="关键词，逗号分隔")
    parser.add_argument("--limit", type=int, default=10, help="最多返回条数")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("请提供至少一个关键词", file=sys.stderr)
        sys.exit(1)

    results = search_notion(keywords, args.limit)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
