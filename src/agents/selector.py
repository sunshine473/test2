"""Selector Agent — 自动选题专家。

根据评分、新鲜度、多样性和用户偏好自动选择最佳选题。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agents.base_agent import AgentResult, AgentStatus, BaseAgent


class SelectorAgent(BaseAgent):
    """选题专家 Agent。"""

    def __init__(self, config: Optional[dict] = None):
        super().__init__("selector")
        self.config = config or self._default_config()

    @staticmethod
    def _default_config() -> dict:
        """默认配置。"""
        return {
            "strategy": "conservative",  # conservative | aggressive | diverse
            "min_score": 70,
            "max_age_hours": 24,
            "weights": {
                "score": 0.4,       # 评分权重
                "freshness": 0.3,   # 新鲜度权重
                "diversity": 0.2,   # 多样性权重
                "preference": 0.1,  # 用户偏好权重
            },
        }

    def execute(self, plan_result: dict, **kwargs) -> AgentResult:
        """执行选题任务。

        Args:
            plan_result: 策划结果（来自 planner.py）
            **kwargs: 其他参数

        Returns:
            AgentResult: 选题结果
        """
        self.status = AgentStatus.RUNNING

        try:
            strategy = self.config.get("strategy", "conservative")

            if strategy == "conservative":
                selected = self._select_conservative(plan_result)
            elif strategy == "aggressive":
                selected = self._select_aggressive(plan_result)
            elif strategy == "diverse":
                selected = self._select_diverse(plan_result)
            else:
                return self._failed(f"未知策略: {strategy}")

            if not selected:
                return self._failed("没有符合条件的选题")

            return self._success(data=selected)

        except Exception as e:
            return self._failed(f"选题失败: {e}")

    def _select_conservative(self, plan_result: dict) -> list[dict]:
        """保守策略：只选最高分的 1 篇。"""
        all_items = []
        for direction_data in plan_result.values():
            items = direction_data.get("items", [])
            all_items.extend(items)

        # 过滤：评分 >= min_score，新鲜度 <= max_age_hours
        filtered = self._filter_items(all_items)
        if not filtered:
            return []

        # 按综合得分排序
        ranked = self._rank_items(filtered)
        return [ranked[0]]  # 只返回 Top1

    def _select_aggressive(self, plan_result: dict) -> list[dict]:
        """激进策略：选 Top3。"""
        all_items = []
        for direction_data in plan_result.values():
            items = direction_data.get("items", [])
            all_items.extend(items)

        filtered = self._filter_items(all_items)
        if not filtered:
            return []

        ranked = self._rank_items(filtered)
        return ranked[:3]  # 返回 Top3

    def _select_diverse(self, plan_result: dict) -> list[dict]:
        """多样化策略：每个方向选 1 篇。"""
        selected = []
        for direction_data in plan_result.values():
            items = direction_data.get("items", [])
            filtered = self._filter_items(items)
            if filtered:
                ranked = self._rank_items(filtered)
                selected.append(ranked[0])
        return selected

    def _filter_items(self, items: list[dict]) -> list[dict]:
        """过滤不符合条件的素材。"""
        min_score = self.config.get("min_score", 70)
        max_age_hours = self.config.get("max_age_hours", 24)

        filtered = []
        for item in items:
            # 检查评分
            score = (item.get("raw_data") or {}).get("score", 0)
            if score < min_score:
                continue

            # 检查新鲜度
            published_at = item.get("published_at", "")
            if not self._is_fresh(published_at, max_age_hours):
                continue

            filtered.append(item)

        return filtered

    def _rank_items(self, items: list[dict]) -> list[dict]:
        """按综合得分排序。"""
        weights = self.config.get("weights", {})

        for item in items:
            # 计算综合得分
            score_component = self._calc_score_component(item) * weights.get("score", 0.4)
            freshness_component = self._calc_freshness_component(item) * weights.get("freshness", 0.3)
            diversity_component = self._calc_diversity_component(item) * weights.get("diversity", 0.2)
            preference_component = self._calc_preference_component(item) * weights.get("preference", 0.1)

            final_score = (
                score_component +
                freshness_component +
                diversity_component +
                preference_component
            )

            # 存储到 raw_data
            if "raw_data" not in item:
                item["raw_data"] = {}
            item["raw_data"]["final_score"] = final_score

        # 按 final_score 降序排序
        return sorted(items, key=lambda x: x.get("raw_data", {}).get("final_score", 0), reverse=True)

    def _calc_score_component(self, item: dict) -> float:
        """计算评分分量（0-100）。"""
        score = (item.get("raw_data") or {}).get("score", 0)
        return min(score, 100)

    def _calc_freshness_component(self, item: dict) -> float:
        """计算新鲜度分量（0-100）。

        24 小时内：100 分
        24-48 小时：50 分
        48 小时以上：0 分
        """
        published_at = item.get("published_at", "")
        if not published_at:
            return 0

        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return 0

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        elapsed_hours = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600

        if elapsed_hours <= 24:
            return 100
        elif elapsed_hours <= 48:
            return 50
        else:
            return 0

    def _calc_diversity_component(self, item: dict) -> float:
        """计算多样性分量（0-100）。

        TODO: 实现多样性计算（如：与已选题目的相似度）
        """
        return 50  # 暂时返回中等分数

    def _calc_preference_component(self, item: dict) -> float:
        """计算用户偏好分量（0-100）。

        TODO: 根据用户历史选择计算偏好
        """
        return 50  # 暂时返回中等分数

    @staticmethod
    def _is_fresh(published_at: str, hours: int) -> bool:
        """判断内容是否在指定小时数内发布。"""
        if not published_at:
            return False
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return False
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elapsed_hours = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600
        return elapsed_hours <= hours


def main():
    """测试 Selector Agent。"""
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

    from collector.planner import plan, find_latest_pool

    # 加载最新素材池
    pool_path = find_latest_pool()
    if not pool_path:
        print("未找到素材池")
        return

    print(f"素材池: {pool_path}")

    # 执行策划
    plan_result = plan(pool_path)

    # 测试三种策略
    strategies = ["conservative", "aggressive", "diverse"]

    for strategy in strategies:
        print(f"\n{'=' * 60}")
        print(f"策略: {strategy}")
        print(f"{'=' * 60}")

        agent = SelectorAgent(config={"strategy": strategy})
        result = agent.execute(plan_result=plan_result)

        if result.status == AgentStatus.SUCCESS:
            selected = result.data
            print(f"选中 {len(selected)} 篇:")
            for i, item in enumerate(selected, 1):
                score = (item.get("raw_data") or {}).get("score", 0)
                final_score = (item.get("raw_data") or {}).get("final_score", 0)
                print(f"  {i}. [{score} → {final_score:.1f}] {item.get('title', '')[:60]}")
        else:
            print(f"失败: {result.error}")


if __name__ == "__main__":
    main()
