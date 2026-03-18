"""内容流水线数据契约模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class RawMaterial:
    title: str
    url: str
    source_name: str
    source_type: str
    category: str
    summary: str = ""
    content: str = ""
    published_at: str = ""
    language: str = "en"
    raw_data: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data.get("raw_data") is None:
            data.pop("raw_data", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawMaterial":
        return cls(**data)

    @classmethod
    def from_collected_item(cls, item: Any) -> "RawMaterial":
        return cls(
            title=item.title,
            url=item.url,
            source_name=item.source_name,
            source_type=item.source_type,
            category=item.category,
            summary=getattr(item, "summary", "") or "",
            content=getattr(item, "content", "") or "",
            published_at=getattr(item, "published_at", "") or "",
            language=getattr(item, "language", "en") or "en",
            raw_data=getattr(item, "raw_data", None),
        )

    def to_collected_item(self) -> Any:
        from collector.models import CollectedItem

        return CollectedItem(
            title=self.title,
            url=self.url,
            source_name=self.source_name,
            source_type=self.source_type,
            category=self.category,
            summary=self.summary,
            content=self.content,
            published_at=self.published_at,
            language=self.language,
            raw_data=self.raw_data,
        )


@dataclass
class MaterialPool:
    date: str
    stage: str
    raw_total: int
    source_stats: dict[str, int]
    dedup_total: int
    cluster_summary: dict[str, Any]
    items: list[RawMaterial] = field(default_factory=list)
    notion_saved: Optional[int] = None
    notion_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["items"] = [item.to_dict() for item in self.items]
        if data.get("notion_saved") is None:
            data.pop("notion_saved", None)
        if data.get("notion_error") is None:
            data.pop("notion_error", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MaterialPool":
        payload = dict(data)
        payload.setdefault("stage", "search")
        payload.setdefault("source_stats", {})
        payload.setdefault("cluster_summary", {})
        payload["items"] = [RawMaterial.from_dict(item) for item in payload.get("items", [])]
        return cls(**payload)


@dataclass
class DraftPackage:
    title: str
    slug: str
    topic: str
    article_markdown: str
    summary: str = ""
    source_urls: list[str] = field(default_factory=list)
    assets: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DraftPackage":
        return cls(**data)


@dataclass
class PublishPackage:
    title: str
    platform: str
    body: str
    format: str
    cover_assets: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublishPackage":
        return cls(**data)


@dataclass
class PublishResultContract:
    platform: str
    status: str
    message: str = ""
    url: str = ""
    draft_id: str = ""
    published_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
