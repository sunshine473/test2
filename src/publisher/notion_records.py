"""Notion 发布记录模块 — 记录多平台发布结果"""

import os
from datetime import datetime
from typing import Any

from notion_client import Client


class NotionRecords:
    """管理 Notion 发布记录数据库"""

    def __init__(self):
        api_key = os.getenv("NOTION_API_KEY", "")
        if not api_key:
            raise ValueError("NOTION_API_KEY 未设置，请在 .env 中配置")
        self.client = Client(auth=api_key)
        self.database_id = os.getenv("NOTION_PUBLISH_DB_ID", "")
        if not self.database_id:
            raise ValueError("NOTION_PUBLISH_DB_ID 未设置，请在 .env 中配置")
        self.property_keys, self.parent = self._ensure_schema()

    def save_publish_result(self, result_data: dict[str, Any]) -> str | None:
        """记录单个平台的发布结果，返回创建的页面 ID

        Args:
            result_data: 发布结果数据，包含：
                - title: 文章标题
                - platform: 平台名称（wechat/zhihu/bilibili等）
                - status: 发布状态（成功/失败/草稿）
                - publish_url: 发布链接（可选）
                - message: 发布消息/错误信息
                - draft_title: 关联的草稿标题（可选）
        """
        try:
            page = self._create_record_page(result_data)
            page_id = page.get("id")
            print(f"  [Notion Records] 发布记录已写入: {result_data.get('platform')} - {result_data.get('title', '')[:30]}...")
            return page_id
        except Exception as e:
            print(f"  [Notion Records] 写入失败: {result_data.get('platform')} - {e}")
            return None

    def save_batch_results(self, title: str, results: list[dict[str, Any]], draft_title: str = "") -> int:
        """批量记录多个平台的发布结果

        Args:
            title: 文章标题
            results: 发布结果列表，每个包含 platform, status, message, url 等
            draft_title: 关联的草稿标题

        Returns:
            成功写入的记录数
        """
        saved = 0
        for result in results:
            result_data = {
                "title": title,
                "platform": result.get("platform", ""),
                "status": result.get("status", ""),
                "publish_url": result.get("url", ""),
                "message": result.get("message", ""),
                "draft_title": draft_title,
            }
            if self.save_publish_result(result_data):
                saved += 1
        return saved

    def _create_record_page(self, result_data: dict[str, Any]) -> dict:
        """创建单条发布记录页面"""
        keys = self.property_keys
        today = datetime.now().strftime("%Y-%m-%d")

        properties = {
            keys["title"]: {"title": [{"text": {"content": result_data.get("title", "")[:2000]}}]},
            keys["platform"]: {"select": {"name": self._map_platform(result_data.get("platform", ""))}},
            keys["status"]: {"select": {"name": self._map_status(result_data.get("status", ""))}},
            keys["publish_date"]: {"date": {"start": today}},
        }

        # 发布链接
        publish_url = result_data.get("publish_url", "")
        if publish_url:
            properties[keys["publish_url"]] = {"url": publish_url}

        # 发布消息
        message = result_data.get("message", "")
        if message:
            properties[keys["message"]] = {
                "rich_text": [{"text": {"content": str(message)[:2000]}}]
            }

        # 关联草稿（通过标题查询）
        draft_title = result_data.get("draft_title")
        if draft_title:
            draft_pages = self._query_draft_by_title(draft_title)
            if draft_pages:
                properties[keys["draft_relation"]] = {
                    "relation": [{"id": draft_pages[0]["id"]}]
                }

        return self.client.pages.create(
            parent=self.parent,
            properties=properties,
        )

    def _query_draft_by_title(self, title: str) -> list[dict]:
        """根据标题查询草稿页面（用于关联）"""
        drafts_db_id = os.getenv("NOTION_DRAFTS_DB_ID", "")
        if not drafts_db_id:
            return []

        try:
            response = self.client.databases.query(
                database_id=drafts_db_id,
                filter={
                    "property": "文章标题",  # 假设草稿库的标题字段名
                    "title": {"contains": title}
                }
            )
            return response.get("results", [])
        except Exception:
            return []

    @staticmethod
    def _map_platform(platform: str) -> str:
        """映射平台名称"""
        mapping = {
            "wechat": "微信公众号",
            "zhihu": "知乎",
            "bilibili": "B站",
            "xiaohongshu": "小红书",
            "dongchedi": "懂车帝",
            "toutiao": "头条",
        }
        return mapping.get(platform.lower(), platform)

    @staticmethod
    def _map_status(status: str) -> str:
        """映射发布状态"""
        mapping = {
            "success": "成功",
            "failed": "失败",
            "draft": "草稿",
            "error": "失败",
        }
        return mapping.get(status.lower(), status)

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
            "platform": ("平台", {"select": {"options": []}}),
            "status": ("状态", {"select": {"options": []}}),
            "publish_url": ("发布链接", {"url": {}}),
            "message": ("发布消息", {"rich_text": {}}),
            "publish_date": ("发布日期", {"date": {}}),
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
            "platform": "平台",
            "status": "状态",
            "publish_url": "发布链接",
            "message": "发布消息",
            "publish_date": "发布日期",
            "draft_relation": "关联草稿",
        }, parent
