"""统一数据模型"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class CollectedItem:
    """采集到的单条素材"""
    title: str
    url: str
    source_name: str        # 信息源名称（如 "Hacker News"）
    source_type: str        # 采集方式：rss / scraper / tavily / twitter
    category: str           # tech_ai / auto / trending
    summary: str = ""
    published_at: str = ""
    language: str = "en"
    raw_data: Optional[dict] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        if d.get("raw_data") is None:
            del d["raw_data"]
        return d
