"""素材去重与聚类。"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Tuple
from urllib.parse import urlparse, parse_qs

from collector.models import CollectedItem


def _normalize_title(title: str) -> str:
    title = (title or "").strip().lower()
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[^\w\u4e00-\u9fff ]+", "", title)
    return title


def _canonical_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    # 对百度/微博搜索 URL 保留主要 query 参数，避免完全丢语义
    if "baidu.com" in parsed.netloc:
        q = parse_qs(parsed.query).get("wd", [""])[0]
        return f"baidu:{q}"
    if "weibo.com" in parsed.netloc:
        q = parse_qs(parsed.query).get("q", [""])[0]
        return f"weibo:{q}"
    if "youtube.com" in parsed.netloc:
        q = parse_qs(parsed.query)
        video_id = q.get("v", [""])[0]
        if video_id:
            return f"youtube:{video_id}"
    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.strip("/")
        if video_id:
            return f"youtube:{video_id}"
    return f"{parsed.netloc.lower()}{path}"


@dataclass
class Cluster:
    cluster_id: str
    items: List[CollectedItem]


class Deduplicator:
    """先按 URL 去重，再按标题相似度聚类。"""

    def __init__(self, title_similarity_threshold: float = 0.84):
        self.title_similarity_threshold = title_similarity_threshold

    def process(self, items: List[CollectedItem]) -> Tuple[List[CollectedItem], List[Cluster]]:
        unique = self._dedup_by_url(items)
        clusters = self._cluster_by_title(unique)

        ranked = []
        for cluster in clusters:
            lead = cluster.items[0]
            lead.raw_data = lead.raw_data or {}
            lead.raw_data["cluster_id"] = cluster.cluster_id
            lead.raw_data["cluster_size"] = len(cluster.items)
            ranked.append(lead)
        return ranked, clusters

    def _dedup_by_url(self, items: List[CollectedItem]) -> List[CollectedItem]:
        grouped: Dict[str, CollectedItem] = {}
        for item in items:
            key = _canonical_url(item.url) or _normalize_title(item.title)
            existing = grouped.get(key)
            if not existing:
                grouped[key] = item
                continue
            # 保留摘要更完整、标题更长的一条
            if len(item.summary or "") + len(item.title or "") > len(existing.summary or "") + len(existing.title or ""):
                grouped[key] = item
        return list(grouped.values())

    def _cluster_by_title(self, items: List[CollectedItem]) -> List[Cluster]:
        clusters: List[Cluster] = []
        for item in items:
            title_norm = _normalize_title(item.title)
            assigned = False
            for cluster in clusters:
                anchor = _normalize_title(cluster.items[0].title)
                sim = SequenceMatcher(None, title_norm, anchor).ratio()
                if sim >= self.title_similarity_threshold:
                    cluster.items.append(item)
                    assigned = True
                    break
            if not assigned:
                cluster_id = f"C{len(clusters) + 1:03d}"
                clusters.append(Cluster(cluster_id=cluster_id, items=[item]))

        # 大簇优先，其次按标题排序，便于可读
        clusters.sort(key=lambda c: (-len(c.items), _normalize_title(c.items[0].title)))
        # 重新编号，避免排序后 ID 跳变
        for idx, cluster in enumerate(clusters, start=1):
            cluster.cluster_id = f"C{idx:03d}"
        return clusters

    @staticmethod
    def summarize_clusters(clusters: List[Cluster]) -> dict:
        by_source = defaultdict(int)
        for cluster in clusters:
            for item in cluster.items:
                by_source[item.source_name] += 1
        return {
            "cluster_count": len(clusters),
            "max_cluster_size": max((len(c.items) for c in clusters), default=0),
            "source_distribution": dict(sorted(by_source.items(), key=lambda x: x[0])),
        }
