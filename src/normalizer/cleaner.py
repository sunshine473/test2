"""文本清洗工具。"""

from __future__ import annotations

import re

from models import RawMaterial

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text or "")
    return _WS_RE.sub(" ", text).strip()


def clean_materials(items: list[RawMaterial]) -> list[RawMaterial]:
    cleaned = []
    for item in items:
        cleaned.append(
            RawMaterial(
                title=_clean_text(item.title),
                url=item.url.strip(),
                source_name=item.source_name.strip(),
                source_type=item.source_type.strip(),
                category=item.category.strip(),
                summary=_clean_text(item.summary),
                content=_clean_text(item.content),
                published_at=(item.published_at or "").strip(),
                language=(item.language or "en").strip() or "en",
                raw_data=item.raw_data,
            )
        )
    return cleaned
