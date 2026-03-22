"""RSS + YouTube 频道采集适配器"""

import socket
from typing import List

import feedparser

from collector.models import CollectedItem
from collector.sources.base import BaseSource, clip_text

FEED_TIMEOUT = 15  # seconds per feed


class RSSSource(BaseSource):
    """通过 RSS/Atom feed 采集，同时覆盖 YouTube 频道"""

    def collect(self, config: dict, max_per_feed: int = 5) -> List[CollectedItem]:
        items = []
        # 合并 tech_ai + auto + youtube 三个列表
        feeds = []
        for key in ("tech_ai", "auto", "youtube"):
            feeds.extend(config.get(key, []))

        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(FEED_TIMEOUT)
        try:
            return self._collect_feeds(feeds, items, max_per_feed)
        finally:
            socket.setdefaulttimeout(old_timeout)

    def _collect_feeds(self, feeds, items, max_per_feed):
        for feed_cfg in feeds:
            name = feed_cfg["name"]
            url = feed_cfg["url"]
            category = feed_cfg.get("category", "tech_ai")
            language = feed_cfg.get("language", "en")
            is_youtube = "youtube.com/feeds" in url

            print(f"  [RSS] {name}...")
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:max_per_feed]:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    summary_raw = getattr(entry, "summary", "")
                    content_blocks = entry.get("content", []) or []
                    content_raw = ""
                    if content_blocks:
                        content_raw = " ".join(block.get("value", "") for block in content_blocks)
                    if not content_raw:
                        content_raw = entry.get("description", "") or summary_raw
                    summary = clip_text(summary_raw or content_raw, 300)
                    content = clip_text(content_raw or summary_raw, 4000)
                    published = entry.get("published", "")

                    items.append(CollectedItem(
                        title=title,
                        url=link,
                        source_name=name,
                        source_type="youtube" if is_youtube else "rss",
                        category=category,
                        summary=summary,
                        content=content,
                        published_at=published,
                        language=language,
                    ))
            except Exception as e:
                print(f"  [RSS] {name} 采集失败: {e}")

        return items
