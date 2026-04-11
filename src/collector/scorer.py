"""素材打分排序。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

from collector.models import CollectedItem

if TYPE_CHECKING:
    from collector.directions import Direction


# 全局默认权重（无 direction 时使用，向后兼容）
SOURCE_BASE_WEIGHT = {
    "Follow Builders Podcast": 26,
    "Follow Builders X": 24,
    "Follow Builders Blog": 23,
    "Hacker News": 25,
    "GitHub Trending": 24,
    "OpenAI Blog": 22,
    "Anthropic Blog": 22,
    "Google DeepMind Blog": 22,
    "微博热搜": 18,
    "百度热搜": 18,
}

CATEGORY_WEIGHT = {
    "tech_ai": 16,
    "auto": 12,
    "trending": 10,
}

KEYWORD_BONUS = {
    "agent": 4,
    "llm": 4,
    "模型": 4,
    "openai": 5,
    "anthropic": 4,
    "deepmind": 4,
    "自动驾驶": 4,
    "机器人": 4,
    "新能源": 3,
}


class ItemScorer:
    """对去重后的素材进行可解释打分。"""

    def __init__(self, direction: Optional[Direction] = None):
        self._direction = direction
        if direction:
            self._source_weight = direction.source_weight
            self._category_weight = direction.category_weight
            self._keyword_bonus_map = direction.keyword_bonus
            self._preferred_sources = direction.preferred_sources
            self._preferred_source_bonus = direction.preferred_source_bonus
        else:
            self._source_weight = SOURCE_BASE_WEIGHT
            self._category_weight = CATEGORY_WEIGHT
            self._keyword_bonus_map = KEYWORD_BONUS
            self._preferred_sources = set()
            self._preferred_source_bonus = 0

    def score_and_rank(self, items: List[CollectedItem]) -> List[CollectedItem]:
        for item in items:
            score, reasons = self._score_item(item)
            item.raw_data = item.raw_data or {}
            item.raw_data["score"] = score
            item.raw_data["score_reasons"] = reasons

        return sorted(
            items,
            key=lambda x: (
                -(x.raw_data or {}).get("score", 0),
                -((x.raw_data or {}).get("cluster_size", 1)),
                x.title.lower(),
            ),
        )

    def _score_item(self, item: CollectedItem) -> tuple[float, List[str]]:
        reasons: List[str] = []
        score = 0.0

        source_bonus = self._source_weight.get(item.source_name, 12)
        score += source_bonus
        reasons.append(f"source:{source_bonus}")

        cat_bonus = self._category_weight.get(item.category, 8)
        score += cat_bonus
        reasons.append(f"category:{cat_bonus}")

        if item.source_name in self._preferred_sources:
            score += self._preferred_source_bonus
            reasons.append(f"preferred:{self._preferred_source_bonus}")

        cluster_size = int((item.raw_data or {}).get("cluster_size", 1))
        cluster_bonus = min(15, cluster_size * 3)
        score += cluster_bonus
        reasons.append(f"cluster:{cluster_bonus}")

        recency_bonus = self._recency_bonus(item.published_at)
        score += recency_bonus
        reasons.append(f"recency:{recency_bonus}")

        keyword_bonus = self._keyword_bonus(item)
        score += keyword_bonus
        if keyword_bonus:
            reasons.append(f"keyword:{keyword_bonus}")

        # HN 专项加分
        hn_points = int((item.raw_data or {}).get("hn_points", 0))
        if hn_points:
            hn_bonus = min(15, hn_points / 40)
            score += hn_bonus
            reasons.append(f"hn_points:{hn_bonus:.1f}")

        return round(score, 2), reasons

    @staticmethod
    def _recency_bonus(published_at: str) -> float:
        if not published_at:
            return 3.0
        try:
            # 兼容常见格式
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return 2.0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours = (now - dt.astimezone(timezone.utc)).total_seconds() / 3600
        if hours <= 6:
            return 10
        if hours <= 24:
            return 8
        if hours <= 72:
            return 6
        if hours <= 168:
            return 4
        return 1

    def _keyword_bonus(self, item: CollectedItem) -> float:
        text = f"{item.title} {item.summary}".lower()
        bonus = 0.0
        for keyword, score in self._keyword_bonus_map.items():
            if keyword in text:
                bonus += score
        return min(15, bonus)

    @staticmethod
    def summarize_scores(items: List[CollectedItem]) -> Dict[str, float]:
        scores = [(it.raw_data or {}).get("score", 0.0) for it in items]
        if not scores:
            return {"max": 0.0, "min": 0.0, "avg": 0.0}
        return {
            "max": round(max(scores), 2),
            "min": round(min(scores), 2),
            "avg": round(sum(scores) / len(scores), 2),
        }
