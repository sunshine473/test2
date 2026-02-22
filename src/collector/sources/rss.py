"""RSS + YouTube 频道采集适配器"""

from typing import List

import feedparser

from collector.models import CollectedItem
from collector.sources.base import BaseSource


class RSSSource(BaseSource):
    """通过 RSS/Atom feed 采集，同时覆盖 YouTube 频道"""

    def collect(self, config: dict, max_per_feed: int = 5) -> List[CollectedItem]:
        items = []
        # 合并 tech_ai + auto + youtube 三个列表
        feeds = []
        for key in ("tech_ai", "auto", "youtube"):
            feeds.extend(config.get(key, []))

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
                    summary = getattr(entry, "summary", "")
                    if summary:
                        summary = summary[:300]
                    published = entry.get("published", "")

                    items.append(CollectedItem(
                        title=title,
                        url=link,
                        source_name=name,
                        source_type="youtube" if is_youtube else "rss",
                        category=category,
                        summary=summary,
                        published_at=published,
                        language=language,
                    ))
            except Exception as e:
                print(f"  [RSS] {name} 采集失败: {e}")

        return items
