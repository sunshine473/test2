"""GitHub Trending 采集适配器"""

from typing import List

import requests
from bs4 import BeautifulSoup

from collector.models import CollectedItem
from collector.sources.base import BaseSource


class GitHubTrendingSource(BaseSource):
    """通过 HTML 抓取 GitHub Trending 页面"""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def collect(self, config: dict) -> List[CollectedItem]:
        items = []
        # config 是 scraper 列表中的单个条目
        sources = config if isinstance(config, list) else [config]

        for src in sources:
            url = src.get("url", "https://github.com/trending?since=daily")
            max_items = src.get("max_items", 10)
            category = src.get("category", "tech_ai")

            print(f"  [GitHub] Trending...")
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for article in soup.select("article.Box-row")[:max_items]:
                    title_tag = article.select_one("h2 a") or article.select_one("h1 a")
                    if not title_tag:
                        continue

                    title = title_tag.text.strip().replace("\n", "").replace(" ", "")
                    link = "https://github.com" + title_tag["href"]

                    desc_tag = article.select_one("p")
                    desc = desc_tag.text.strip() if desc_tag else ""

                    items.append(CollectedItem(
                        title=title,
                        url=link,
                        source_name="GitHub Trending",
                        source_type="scraper",
                        category=category,
                        summary=desc,
                        language="en",
                    ))
            except Exception as e:
                print(f"  [GitHub] 采集失败: {e}")

        return items
