"""Hacker News 采集适配器（Algolia API）"""

from typing import List

import requests

from collector.models import CollectedItem
from collector.sources.base import BaseSource


class HackerNewsSource(BaseSource):
    """通过 HN Algolia API 获取高分故事。"""

    API_URL = "https://hn.algolia.com/api/v1/search_by_date"

    def collect(self, config: dict) -> List[CollectedItem]:
        min_points = int(config.get("min_points", 100))
        max_items = int(config.get("max_items", 20))
        tags = config.get("tags", "story")

        params = {
            "tags": tags,
            "numericFilters": f"points>{min_points}",
            "hitsPerPage": max_items,
        }
        print(f"  [HN] 拉取高分故事（points>{min_points}）...")
        resp = requests.get(self.API_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        items: List[CollectedItem] = []
        for hit in data.get("hits", []):
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            url = (hit.get("url") or hit.get("story_url") or "").strip()
            if not title or not url:
                continue

            points = hit.get("points", 0)
            comments = hit.get("num_comments", 0)
            summary = f"HN points={points}, comments={comments}"
            published_at = hit.get("created_at", "")

            items.append(
                CollectedItem(
                    title=title,
                    url=url,
                    source_name="Hacker News",
                    source_type="api",
                    category=config.get("category", "tech_ai"),
                    summary=summary,
                    published_at=published_at,
                    language="en",
                    raw_data={
                        "hn_points": points,
                        "hn_comments": comments,
                        "hn_object_id": hit.get("objectID"),
                    },
                )
            )
        return items

