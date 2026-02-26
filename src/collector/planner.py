"""策划阶段入口 — 从素材池 JSON 加载素材，按方向筛选并打分排序。

用法:
    python -m collector.planner --pool content/pool/2026-02-23-pool.json
    python -m collector.planner --pool content/pool/2026-02-23-pool.json --direction tech_ai
    python -m collector.planner --pool content/pool/2026-02-23-pool.json --direction auto
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from collector.models import CollectedItem
from collector.scorer import ItemScorer
from collector.directions import DIRECTIONS, TRENDING_KEYWORDS, get_direction, Direction
from collector.main import ensure_utf8

POOL_DIR = PROJECT_ROOT / "content" / "pool"


def load_pool(pool_path: str) -> list[CollectedItem]:
    """从素材池 JSON 反序列化回 CollectedItem 列表。"""
    with open(pool_path, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for d in data.get("items", []):
        raw = d.pop("raw_data", None)
        item = CollectedItem(**d)
        item.raw_data = raw
        items.append(item)
    return items


def filter_by_direction(items: list[CollectedItem], direction: Direction) -> list[CollectedItem]:
    """按方向筛选素材：category 匹配或 trending 关键词匹配。"""
    keywords = TRENDING_KEYWORDS.get(direction.name, set())
    result = []
    for item in items:
        if item.category in direction.categories and item.category != "trending":
            result.append(item)
        elif item.category == "trending":
            # trending 类素材用关键词二次筛选
            text = f"{item.title} {item.summary}".lower()
            if any(kw in text for kw in keywords):
                result.append(item)
    return result


def plan_direction(items: list[CollectedItem], direction: Direction) -> dict:
    """对单个方向执行筛选 + 打分排序，返回结果 dict。"""
    filtered = filter_by_direction(items, direction)
    scorer = ItemScorer(direction=direction)
    ranked = scorer.score_and_rank(filtered)
    score_summary = scorer.summarize_scores(ranked)

    print(f"\n--- {direction.label} ({direction.name}) ---")
    print(f"筛选: {len(items)} → {len(filtered)} 条")
    print(f"打分: max={score_summary['max']}, avg={score_summary['avg']}, min={score_summary['min']}")

    if ranked:
        print(f"Top-5:")
        for i, item in enumerate(ranked[:5], 1):
            s = (item.raw_data or {}).get("score", 0)
            print(f"  {i}. [{s}] {item.title[:60]}")

    return {
        "direction": direction.name,
        "label": direction.label,
        "input_count": len(items),
        "filtered_count": len(filtered),
        "score_summary": score_summary,
        "items": [item.to_dict() for item in ranked],
    }


def plan(pool_path: str, direction_name: str | None = None) -> dict:
    """策划入口：加载素材池，按方向筛选打分。不传 direction 时两个方向都跑。"""
    ensure_utf8()
    items = load_pool(pool_path)
    print(f"=== 选题策划开始，素材池 {len(items)} 条 ===")

    results = {}
    if direction_name:
        d = get_direction(direction_name)
        results[d.name] = plan_direction(items, d)
    else:
        for name, d in DIRECTIONS.items():
            results[name] = plan_direction(items, d)

    print(f"\n=== 策划完成 ===")
    return results


def find_latest_pool() -> str | None:
    """查找 content/pool/ 下最新的素材池 JSON。"""
    if not POOL_DIR.exists():
        return None
    pools = sorted(POOL_DIR.glob("*-pool.json"), reverse=True)
    return str(pools[0]) if pools else None


def main():
    parser = argparse.ArgumentParser(description="选题策划（从素材池筛选+打分）")
    parser.add_argument("--pool", default=None, help="素材池 JSON 路径（默认取最新）")
    parser.add_argument("--direction", choices=["tech_ai", "auto"], default=None,
                        help="指定方向（默认两个方向都跑）")
    args = parser.parse_args()

    pool_path = args.pool or find_latest_pool()
    if not pool_path:
        print("错误: 未找到素材池 JSON，请先运行 search 或指定 --pool 路径")
        sys.exit(1)

    print(f"素材池: {pool_path}")
    results = plan(pool_path, args.direction)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
