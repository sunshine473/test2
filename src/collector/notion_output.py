"""Notion 输出模块 — 将采集结果写入 Notion 数据库"""

import os
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List

import requests
from notion_client import Client

from collector.models import CollectedItem


class NotionOutput:
    """将 CollectedItem 列表写入 Notion 数据库"""

    def __init__(self):
        api_key = os.getenv("NOTION_API_KEY", "")
        if not api_key:
            raise ValueError("NOTION_API_KEY 未设置，请在 .env 中配置")
        self.client = Client(auth=api_key)
        self.database_id = os.getenv("NOTION_DATABASE_ID", "")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID 未设置，请在 .env 中配置")
        self.property_keys, self.parent = self._ensure_schema()
        self._translation_cache = {}

    def save(self, items: List[CollectedItem]) -> int:
        """将素材列表写入 Notion，返回成功写入的条数"""
        saved = 0
        today = datetime.now().strftime("%Y-%m-%d")

        for item in items:
            try:
                self._create_page(item, today)
                saved += 1
            except Exception as e:
                print(f"  [Notion] 写入失败: {item.title[:30]}... - {e}")

        return saved

    def _create_page(self, item: CollectedItem, date: str):
        """创建单条 Notion 页面"""
        bilingual_title = self._build_bilingual_title(item.title, item.language)
        summary = self._build_bilingual_summary(item.summary or "", item.language)

        keys = self.property_keys
        properties = {
            keys["title"]: {"title": [{"text": {"content": bilingual_title}}]},
            keys["url"]: {"url": item.url if item.url else None},
            keys["source"]: {"select": {"name": self._map_source(item.source_name)}},
            keys["method"]: {"select": {"name": item.source_type}},
            keys["category"]: {"select": {"name": item.category}},
            keys["summary"]: {"rich_text": [{"text": {"content": summary}}]},
            keys["language"]: {"select": {"name": item.language}},
            keys["date"]: {"date": {"start": date}},
        }
        published_at = self._normalize_datetime(item.published_at)
        if published_at:
            properties[keys["published_at"]] = {"date": {"start": published_at}}

        self.client.pages.create(
            parent=self.parent,
            properties=properties,
        )

    def _map_source(self, source_name: str) -> str:
        """将 source_name 映射到 Notion Select 选项"""
        name_lower = source_name.lower()
        if "hacker" in name_lower or "hn" in name_lower:
            return "Hacker News"
        if "openai" in name_lower:
            return "OpenAI Blog"
        if "anthropic" in name_lower:
            return "Anthropic Blog"
        if "deepmind" in name_lower:
            return "DeepMind Blog"
        if "36kr" in name_lower:
            return "36kr"
        if "github" in name_lower:
            return "GitHub Trending"
        if "youtube" in name_lower or "two minute" in name_lower or \
           "fireship" in name_lower or "matt wolfe" in name_lower or \
           "ai explained" in name_lower or "david shapiro" in name_lower or \
           "ai advantage" in name_lower or "lex fridman" in name_lower:
            return "YouTube"
        # 其他来源直接用原名，Notion 会自动创建新选项
        return source_name[:100]

    def _build_bilingual_summary(self, summary: str, language: str) -> str:
        """摘要统一为中英双语，中文在前，英文在后。"""
        text = summary.strip()
        if not text:
            return ""

        lang = (language or "").lower()
        if lang.startswith("zh") or self._contains_chinese(text):
            zh_text = text
            en_text = self._translate(text, source="zh-CN", target="en")
        else:
            en_text = text
            zh_text = self._translate(text, source="en", target="zh-CN")

        # 控制单段长度，避免触发 Notion rich_text 上限
        zh_text = zh_text[:900]
        en_text = en_text[:900]
        bilingual = f"中文：{zh_text}\n\nEnglish: {en_text}"
        return bilingual[:2000]

    def _build_bilingual_title(self, title: str, language: str) -> str:
        """名称（标题字段）统一为中英双语，中文在前，英文在后。"""
        text = (title or "").strip()
        if not text:
            return "中文：未命名 | English: Untitled"

        lang = (language or "").lower()
        if lang.startswith("zh") or self._contains_chinese(text):
            zh_text = text
            en_text = self._translate(text, source="zh-CN", target="en")
        else:
            en_text = text
            zh_text = self._translate(text, source="en", target="zh-CN")

        zh_text = zh_text[:120]
        en_text = en_text[:120]
        return f"中文：{zh_text} | English: {en_text}"

    @staticmethod
    def _contains_chinese(text: str) -> bool:
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def _translate(self, text: str, source: str, target: str) -> str:
        """使用 Google Translate 无密钥接口翻译，失败时回退原文。"""
        cache_key = (text, source, target)
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]

        try:
            resp = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": source,
                    "tl": target,
                    "dt": "t",
                    "q": text,
                },
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()
            translated = "".join(part[0] for part in data[0] if part and part[0]).strip()
            if translated:
                self._translation_cache[cache_key] = translated
                return translated
        except Exception:
            pass

        self._translation_cache[cache_key] = text
        return text

    @staticmethod
    def _normalize_datetime(value: str) -> str:
        """将发布时间归一化为 Notion date 可接受的 ISO8601 字符串。"""
        text = (value or "").strip()
        if not text:
            return ""

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass

        try:
            return parsedate_to_datetime(text).isoformat()
        except (TypeError, ValueError):
            return ""

    def _ensure_schema(self) -> tuple[dict, dict]:
        """确保数据库包含写入所需字段，返回(字段键名映射, pages.create parent)。"""
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

        # 标题字段必须复用现有 title 类型字段（Notion 限制只能有一个）
        title_key = next(
            (k for k, v in properties.items() if v.get("type") == "title"),
            None,
        )
        if not title_key:
            raise ValueError("Notion 数据库缺少 title 类型字段，无法写入标题")

        required = {
            "url": ("URL", {"url": {}}),
            "source": ("来源", {"select": {"options": []}}),
            "method": ("采集方式", {"select": {"options": []}}),
            "category": ("分类", {"select": {"options": []}}),
            "summary": ("摘要", {"rich_text": {}}),
            "language": ("语言", {"select": {"options": []}}),
            "date": ("采集日期", {"date": {}}),
            "published_at": ("文章发布时间", {"date": {}}),
        }

        missing = {}
        for _, (name, spec) in required.items():
            if name not in properties:
                missing[name] = spec

        if missing:
            update_schema(missing)

        return {
            "title": title_key,
            "url": "URL",
            "source": "来源",
            "method": "采集方式",
            "category": "分类",
            "summary": "摘要",
            "language": "语言",
            "date": "采集日期",
            "published_at": "文章发布时间",
        }, parent
