"""微博/百度热搜采集适配器（通过 TopHub）"""

from typing import List

import requests
from bs4 import BeautifulSoup

from collector.models import CollectedItem
from collector.sources.base import BaseSource


class HotSearchSource(BaseSource):
    """从 TopHub 聚合页提取微博热搜与百度热搜。"""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    def collect(self, config: dict) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        max_items = int(config.get("max_items", 20))
        feeds = config.get("feeds", [])

        for feed in feeds:
            name = feed.get("name", "热搜")
            url = feed.get("url", "")
            category = feed.get("category", "trending")
            domain_hint = feed.get("domain_hint", "")
            if not url:
                continue

            print(f"  [HotSearch] {name}...")
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            count = 0
            seen_titles = set()
            for link in soup.select("a[href]"):
                href = (link.get("href") or "").strip()
                title = " ".join(link.get_text(" ", strip=True).split())
                if not href or not title:
                    continue
                if href.startswith("/"):
                    href = f"https://tophub.today{href}"

                if domain_hint and domain_hint not in href:
                    continue
                if title in seen_titles:
                    continue
                # TopHub 噪声过滤
                if title in {"", "创建追踪器", "成为赞助商"}:
                    continue
                if "最新" in title and "更新" in title:
                    continue
                if len(title) < 4:
                    continue

                seen_titles.add(title)
                items.append(
                    CollectedItem(
                        title=title,
                        url=href,
                        source_name=name,
                        source_type="scraper",
                        category=category,
                        summary=f"{name}实时热搜词条",
                        content=f"{name}热搜词条：{title}",
                        language="zh",
                    )
                )
                count += 1
                if count >= max_items:
                    break

        return items
