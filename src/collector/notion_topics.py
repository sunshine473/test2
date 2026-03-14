"""Notion 选题库模块 — 管理策划推荐的选题"""

import os
from datetime import datetime
from typing import Any

from notion_client import Client


class NotionTopics:
    """管理 Notion 选题库数据库"""

    def __init__(self):
        api_key = os.getenv("NOTION_API_KEY", "")
        if not api_key:
            raise ValueError("NOTION_API_KEY 未设置，请在 .env 中配置")
        self.client = Client(auth=api_key)
        self.database_id = os.getenv("NOTION_TOPICS_DB_ID", "")
        if not self.database_id:
            raise ValueError("NOTION_TOPICS_DB_ID 未设置，请在 .env 中配置")
        self.property_keys, self.parent = self._ensure_schema()

    def save_topics(self, topics: list[dict[str, Any]], direction: str) -> int:
        """将策划推荐的选题写入 Notion，返回成功写入的条数

        Args:
            topics: 选题列表，每个选题包含 title, score, reason, source_urls 等字段
            direction: 内容方向（tech_ai / auto）
        """
        saved = 0
        today = datetime.now().strftime("%Y-%m-%d")

        for topic in topics:
            try:
                self._create_topic_page(topic, direction, today)
                saved += 1
            except Exception as e:
                print(f"  [Notion Topics] 写入失败: {topic.get('title', '')[:30]}... - {e}")

        return saved

    def update_topic_status(self, topic_title: str, status: str, **kwargs):
        """更新选题状态

        Args:
            topic_title: 选题标题
            status: 新状态（待选择 / 已选中 / 已生成 / 已发布 / 已放弃）
            **kwargs: 其他要更新的字段（如 selected_date, draft_id）
        """
        # 查询选题页面
        pages = self._query_by_title(topic_title)
        if not pages:
            print(f"  [Notion Topics] 未找到选题: {topic_title}")
            return

        page_id = pages[0]["id"]
        keys = self.property_keys
        properties = {
            keys["status"]: {"select": {"name": status}}
        }

        # 更新选中日期
        if "selected_date" in kwargs:
            properties[keys["selected_date"]] = {
                "date": {"start": kwargs["selected_date"]}
            }

        # 更新关联草稿（如果提供了 draft_id）
        if "draft_id" in kwargs:
            properties[keys["draft_relation"]] = {
                "relation": [{"id": kwargs["draft_id"]}]
            }

        self.client.pages.update(page_id=page_id, properties=properties)

    def _create_topic_page(self, topic: dict[str, Any], direction: str, date: str):
        """创建单条选题页面"""
        keys = self.property_keys
        properties = {
            keys["title"]: {"title": [{"text": {"content": topic.get("title", "")[:2000]}}]},
            keys["direction"]: {"select": {"name": self._map_direction(direction)}},
            keys["score"]: {"number": topic.get("score", 0)},
            keys["reason"]: {"rich_text": [{"text": {"content": topic.get("reason", "")[:2000]}}]},
            keys["status"]: {"select": {"name": "待选择"}},
            keys["recommend_date"]: {"date": {"start": date}},
        }

        # 关联素材（如果提供了素材 URL）
        source_urls = topic.get("source_urls", [])
        if source_urls and isinstance(source_urls, list):
            # 将 URL 列表转为文本存储（Notion Relation 需要 page_id，这里简化处理）
            urls_text = "\n".join(source_urls[:5])  # 最多 5 个
            properties[keys["source_urls"]] = {
                "rich_text": [{"text": {"content": urls_text[:2000]}}]
            }

        self.client.pages.create(
            parent=self.parent,
            properties=properties,
        )

    def _query_by_title(self, title: str) -> list[dict]:
        """根据标题查询选题页面"""
        keys = self.property_keys
        response = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": keys["title"],
                "title": {"equals": title}
            }
        )
        return response.get("results", [])

    @staticmethod
    def _map_direction(direction: str) -> str:
        """映射方向名称"""
        mapping = {
            "tech_ai": "AI科技",
            "auto": "汽车",
        }
        return mapping.get(direction, direction)

    def _ensure_schema(self) -> tuple[dict, dict]:
        """确保数据库包含写入所需字段，返回(字段键名映射, pages.create parent)"""
        db = self.client.databases.retrieve(database_id=self.database_id)
        data_sources = db.get("data_sources", []) or []

        if data_sources:
            data_source_id = data_sources[0]["id"]
            schema_obj = self.client.data_sources.retrieve(data_source_id=data_source_id)
            properties = schema_obj.get("properties", {})

            def update_schema(missing_props: dict):
                self.client.data_sources.update(
                    data_source_id=data_source_id,
                    properties=missing_props,
                )

            parent = {"type": "data_source_id", "data_source_id": data_source_id}
        else:
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
            "direction": ("方向", {"select": {"options": []}}),
            "score": ("评分", {"number": {"format": "number"}}),
            "reason": ("推荐理由", {"rich_text": {}}),
            "source_urls": ("关联素材", {"rich_text": {}}),
            "status": ("状态", {"select": {"options": []}}),
            "recommend_date": ("推荐日期", {"date": {}}),
            "selected_date": ("选中日期", {"date": {}}),
            # 关联字段需要在 Notion UI 中手动创建，这里不自动创建
            # "draft_relation": ("关联草稿", {"relation": {...}}),
        }

        missing = {}
        for _, (name, spec) in required.items():
            if name not in properties:
                missing[name] = spec

        if missing:
            update_schema(missing)

        return {
            "title": title_key,
            "direction": "方向",
            "score": "评分",
            "reason": "推荐理由",
            "source_urls": "关联素材",
            "status": "状态",
            "recommend_date": "推荐日期",
            "selected_date": "选中日期",
            "draft_relation": "关联草稿",
        }, parent
