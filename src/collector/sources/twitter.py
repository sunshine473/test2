"""X/Twitter 采集适配器（通过 Tavily 间接搜索）"""

import os
from typing import List
from urllib.parse import urlparse

from tavily import TavilyClient

from collector.models import CollectedItem
from collector.sources.base import BaseSource, clip_text

# 高优先级分组：只采集这些分组以控制 API 用量
HIGH_PRIORITY_GROUPS = ("aggregators", "official")


class TwitterSource(BaseSource):
    """通过 Tavily 搜索 from:handle 间接采集 X/Twitter 内容"""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            raise ValueError("TAVILY_API_KEY 未设置，请在 .env 中配置")
        self.client = TavilyClient(api_key=api_key)

    def collect(self, config: dict, max_per_handle: int = 3) -> List[CollectedItem]:
        items = []
        # 收集要采集的 handle 列表
        handles = []
        for group_key, accounts in config.items():
            if not isinstance(accounts, list):
                continue
            priority = group_key in HIGH_PRIORITY_GROUPS
            for acc in accounts:
                handles.append({
                    "handle": acc["handle"],
                    "name": acc.get("name", acc["handle"]),
                    "note": acc.get("note", ""),
                    "priority": priority,
                })

        # 只采集高优先级账号
        targets = [h for h in handles if h["priority"]]
        print(f"  [Twitter] 采集 {len(targets)} 个高优先级账号...")

        for target in targets:
            handle = target["handle"]
            query = f"site:x.com/{handle}/status OR site:twitter.com/{handle}/status"

            print(f"  [Twitter] @{handle}...")
            try:
                resp = self.client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_per_handle,
                )
                for r in resp.get("results", []):
                    url = r.get("url", "")
                    if not self._is_twitter_url(url, handle):
                        continue
                    raw_content = r.get("content", "")
                    items.append(CollectedItem(
                        title=r.get("title", ""),
                        url=url,
                        source_name=f"X/@{handle}",
                        source_type="twitter",
                        category="tech_ai",
                        summary=clip_text(raw_content, 300),
                        content=clip_text(raw_content, 4000),
                        language="en",
                    ))
            except Exception as e:
                print(f"  [Twitter] @{handle} 采集失败: {e}")

        return items

    @staticmethod
    def _is_twitter_url(url: str, handle: str) -> bool:
        """过滤掉 Tavily 返回的站外噪声链接。"""
        if not url:
            return False
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
        handle_path = f"/{handle.lower()}"
        if not ("x.com" in host or "twitter.com" in host):
            return False
        return path.startswith(handle_path)
