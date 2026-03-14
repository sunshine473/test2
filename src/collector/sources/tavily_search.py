"""Tavily 搜索采集适配器"""

import os
from typing import List

from tavily import TavilyClient

from collector.models import CollectedItem
from collector.sources.base import BaseSource, clip_text


class TavilySearchSource(BaseSource):
    """通过 Tavily API 搜索采集素材"""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            raise ValueError("TAVILY_API_KEY 未设置，请在 .env 中配置")
        self.client = TavilyClient(api_key=api_key)

    def collect(self, config: dict) -> List[CollectedItem]:
        items = []
        # config 包含 tech_ai / auto / trending 三个子列表
        for group_key in ("tech_ai", "auto", "trending"):
            queries = config.get(group_key, [])
            for q in queries:
                name = q["name"]
                query = q["query"]
                category = q.get("category", group_key)
                depth = q.get("search_depth", "basic")
                max_results = q.get("max_results", 5)

                days = q.get("days", 3)

                print(f"  [Tavily] {name}...")
                try:
                    resp = self.client.search(
                        query=query,
                        search_depth=depth,
                        max_results=max_results,
                        days=days,
                    )
                    for r in resp.get("results", []):
                        raw_content = r.get("content", "")
                        items.append(CollectedItem(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            source_name=name,
                            source_type="tavily",
                            category=category,
                            summary=clip_text(raw_content, 300),
                            content=clip_text(raw_content, 4000),
                            language="zh" if any(
                                c > '\u4e00' for c in query
                            ) else "en",
                        ))
                except Exception as e:
                    print(f"  [Tavily] {name} 采集失败: {e}")

        return items
