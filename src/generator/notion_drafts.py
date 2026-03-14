"""Notion 草稿库模块 — 管理生成的文章草稿"""

import os
from datetime import datetime
from typing import Any

from notion_client import Client


class NotionDrafts:
    """管理 Notion 草稿库数据库"""

    def __init__(self):
        api_key = os.getenv("NOTION_API_KEY", "")
        if not api_key:
            raise ValueError("NOTION_API_KEY 未设置，请在 .env 中配置")
        self.client = Client(auth=api_key)
        self.database_id = os.getenv("NOTION_DRAFTS_DB_ID", "")
        if not self.database_id:
            raise ValueError("NOTION_DRAFTS_DB_ID 未设置，请在 .env 中配置")
        self.property_keys, self.parent = self._ensure_schema()

    def save_draft(self, draft_data: dict[str, Any]) -> str | None:
        """将生成的草稿写入 Notion，返回创建的页面 ID

        Args:
            draft_data: 草稿数据，包含：
                - title: 文章标题
                - file_path: 本地文件路径
                - word_count: 字数
                - quality_grade: 质量评级（A/B/C）
                - quality_scores: 质量评分详情
                - tags: 标签列表
                - digest: 摘要
                - topic_title: 关联的选题标题（可选）
        """
        try:
            page = self._create_draft_page(draft_data)
            page_id = page.get("id")
            print(f"  [Notion Drafts] 草稿已写入: {draft_data.get('title', '')[:30]}...")
            return page_id
        except Exception as e:
            print(f"  [Notion Drafts] 写入失败: {draft_data.get('title', '')[:30]}... - {e}")
            return None

    def update_draft_status(self, draft_title: str, status: str, **kwargs):
        """更新草稿状态

        Args:
            draft_title: 草稿标题
            status: 新状态（待审核 / 审核通过 / 需修改 / 已发布）
            **kwargs: 其他要更新的字段（如 review_date）
        """
        pages = self._query_by_title(draft_title)
        if not pages:
            print(f"  [Notion Drafts] 未找到草稿: {draft_title}")
            return

        page_id = pages[0]["id"]
        keys = self.property_keys
        properties = {
            keys["status"]: {"select": {"name": status}}
        }

        # 更新审核日期
        if "review_date" in kwargs:
            properties[keys["review_date"]] = {
                "date": {"start": kwargs["review_date"]}
            }

        self.client.pages.update(page_id=page_id, properties=properties)

    def _create_draft_page(self, draft_data: dict[str, Any]) -> dict:
        """创建单条草稿页面"""
        keys = self.property_keys
        today = datetime.now().strftime("%Y-%m-%d")

        properties = {
            keys["title"]: {"title": [{"text": {"content": draft_data.get("title", "")[:2000]}}]},
            keys["file_path"]: {"url": draft_data.get("file_path", "")},
            keys["word_count"]: {"number": draft_data.get("word_count", 0)},
            keys["quality_grade"]: {"select": {"name": draft_data.get("quality_grade", "B")}},
            keys["status"]: {"select": {"name": "待审核"}},
            keys["create_date"]: {"date": {"start": today}},
        }

        # 质量评分详情
        quality_scores = draft_data.get("quality_scores", "")
        if quality_scores:
            properties[keys["quality_scores"]] = {
                "rich_text": [{"text": {"content": str(quality_scores)[:2000]}}]
            }

        # 标签
        tags = draft_data.get("tags", [])
        if tags and isinstance(tags, list):
            properties[keys["tags"]] = {
                "multi_select": [{"name": tag} for tag in tags[:10]]  # 最多 10 个标签
            }

        # 摘要
        digest = draft_data.get("digest", "")
        if digest:
            properties[keys["digest"]] = {
                "rich_text": [{"text": {"content": digest[:2000]}}]
            }

        # 关联选题（通过标题查询）
        topic_title = draft_data.get("topic_title")
        if topic_title:
            topic_pages = self._query_topic_by_title(topic_title)
            if topic_pages:
                properties[keys["topic_relation"]] = {
                    "relation": [{"id": topic_pages[0]["id"]}]
                }

        return self.client.pages.create(
            parent=self.parent,
            properties=properties,
        )

    def _query_by_title(self, title: str) -> list[dict]:
        """根据标题查询草稿页面"""
        keys = self.property_keys
        response = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": keys["title"],
                "title": {"equals": title}
            }
        )
        return response.get("results", [])

    def _query_topic_by_title(self, title: str) -> list[dict]:
        """根据标题查询选题页面（用于关联）"""
        topics_db_id = os.getenv("NOTION_TOPICS_DB_ID", "")
        if not topics_db_id:
            return []

        try:
            response = self.client.databases.query(
                database_id=topics_db_id,
                filter={
                    "property": "选题标题",  # 假设选题库的标题字段名
                    "title": {"contains": title}
                }
            )
            return response.get("results", [])
        except Exception:
            return []

    def _ensure_schema(self) -> tuple[dict, dict]:
        """确保数据库包含写入所需字段，返回(字段键名映射, pages.create parent)"""
        db = self.client.databases.retrieve(database_id=self.database_id)
        properties = db.get("properties", {})

        def update_schema(missing_props: dict):
            self.client.databases.update(
                database_id=self.database_id,
                properties=missing_props,
            )

        parent = {"type": "database_id", "database_id": self.database_id}

        # 标题字段必须复用现有 title 类型字段
        title_key = next(
            (k for k, v in properties.items() if v.get("type") == "title"),
            None,
        )
        if not title_key:
            raise ValueError("Notion 数据库缺少 title 类型字段，无法写入标题")

        required = {
            "file_path": ("文件路径", {"url": {}}),
            "word_count": ("字数", {"number": {"format": "number"}}),
            "quality_grade": ("质量评级", {"select": {"options": []}}),
            "quality_scores": ("质量评分", {"rich_text": {}}),
            "tags": ("标签", {"multi_select": {"options": []}}),
            "digest": ("摘要", {"rich_text": {}}),
            "status": ("状态", {"select": {"options": []}}),
            "create_date": ("生成日期", {"date": {}}),
            "review_date": ("审核日期", {"date": {}}),
            "topic_relation": ("关联选题", {"relation": {"database_id": os.getenv("NOTION_TOPICS_DB_ID", "")}}),
        }

        missing = {}
        for _, (name, spec) in required.items():
            if name not in properties:
                # 跳过关联字段（如果目标数据库未配置）
                if name == "关联选题" and not os.getenv("NOTION_TOPICS_DB_ID"):
                    continue
                missing[name] = spec

        if missing:
            update_schema(missing)

        return {
            "title": title_key,
            "file_path": "文件路径",
            "word_count": "字数",
            "quality_grade": "质量评级",
            "quality_scores": "质量评分",
            "tags": "标签",
            "digest": "摘要",
            "status": "状态",
            "create_date": "生成日期",
            "review_date": "审核日期",
            "topic_relation": "关联选题",
        }, parent
