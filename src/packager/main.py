"""包装层：解析草稿并生成平台发布包。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import yaml

from models import DraftPackage, PublishPackage
from publisher.models import Article

from .common import extract_images_from_cards_html, markdown_to_zhihu_html


def load_draft_package(filepath: str) -> DraftPackage:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    raw = path.read_text(encoding="utf-8")
    title = path.stem
    metadata: dict = {}
    content = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except Exception:
                metadata = {}
            content = parts[2]

    extracted_title = _extract_markdown_title(content)
    if isinstance(metadata, dict):
        title = str(metadata.get("title", extracted_title or title) or extracted_title or title)
    else:
        metadata = {}

    slug = path.stem
    cards_html = _resolve_cards_html_path(path)
    assets = {
        "cover_image": str(metadata.get("cover_image", "") or ""),
        "images": extract_images_from_cards_html(cards_html),
    }
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    enriched_metadata = dict(metadata)
    enriched_metadata.setdefault("author", "")
    enriched_metadata.setdefault("digest", "")
    enriched_metadata["source_path"] = str(path.resolve())
    enriched_metadata["tags"] = tags if isinstance(tags, list) else []

    return DraftPackage(
        title=title,
        slug=slug,
        topic=str(metadata.get("topic", title) or title),
        article_markdown=content,
        summary=str(metadata.get("digest", "") or ""),
        assets=assets,
        metadata=enriched_metadata,
    )


def build_publish_packages(draft: DraftPackage, platforms: Iterable[str]) -> list[PublishPackage]:
    packages = []
    for platform in platforms:
        packages.append(_build_publish_package(draft, platform))
    return packages


def _build_publish_package(draft: DraftPackage, platform: str) -> PublishPackage:
    format_name = "markdown"
    body = draft.article_markdown
    extra = {
        "author": str(draft.metadata.get("author", "") or ""),
        "digest": draft.summary or str(draft.metadata.get("digest", "") or ""),
        "source_path": str(draft.metadata.get("source_path", "") or ""),
        "images": list(draft.assets.get("images", [])),
        "tags": list(draft.metadata.get("tags", [])),
        "topic": draft.topic,
    }

    if platform == "zhihu":
        format_name = "html"
        body = markdown_to_zhihu_html(draft.article_markdown)

    if platform == "xiaohongshu":
        extra["body_excerpt"] = _markdown_to_plain_text(draft.article_markdown)[:1000]

    return PublishPackage(
        title=draft.title,
        platform=platform,
        body=body,
        format=format_name,
        cover_assets=[asset for asset in [draft.assets.get("cover_image", "")] if asset],
        extra=extra,
    )


def parse_article(filepath: str) -> Article:
    draft = load_draft_package(filepath)
    return draft_to_article(draft)


def draft_to_article(draft: DraftPackage) -> Article:
    return Article(
        title=draft.title,
        content=draft.article_markdown,
        author=str(draft.metadata.get("author", "") or ""),
        digest=draft.summary or str(draft.metadata.get("digest", "") or ""),
        cover_image=str(draft.assets.get("cover_image", "") or ""),
        source_path=str(draft.metadata.get("source_path", "") or ""),
        images=list(draft.assets.get("images", [])),
        tags=list(draft.metadata.get("tags", [])),
        metadata=dict(draft.metadata),
    )


def package_to_article(package: PublishPackage) -> Article:
    metadata = dict(package.extra)
    metadata["content_format"] = package.format
    return Article(
        title=package.title,
        content=package.body,
        author=str(package.extra.get("author", "") or ""),
        digest=str(package.extra.get("digest", "") or ""),
        cover_image=package.cover_assets[0] if package.cover_assets else "",
        source_path=str(package.extra.get("source_path", "") or ""),
        images=list(package.extra.get("images", [])),
        tags=list(package.extra.get("tags", [])),
        metadata=metadata,
    )


def _markdown_to_plain_text(markdown_text: str) -> str:
    lines = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        lines.append(stripped)
    return "\n".join(line for line in lines if line).strip()


def _extract_markdown_title(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        match = re.match(r"^#\s+(.+)$", stripped)
        if match:
            return match.group(1).strip()
    return ""


def _resolve_cards_html_path(path: Path) -> Path:
    direct = path.with_name(path.stem + "-cards.html")
    if direct.exists():
        return direct

    # pipeline._run_write() 生成卡片时使用不带日期的 slug，这里做兼容回退。
    fallback_stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    fallback = path.with_name(fallback_stem + "-cards.html")
    return fallback
