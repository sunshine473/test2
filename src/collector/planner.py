"""策划阶段入口 — 从素材池 JSON 加载素材，按方向筛选并打分排序。

用法:
    python -m collector.planner --pool content/pool/2026-02-23-pool.json
    python -m collector.planner --pool content/pool/2026-02-23-pool.json --direction tech_ai
    python -m collector.planner --pool content/pool/2026-02-23-pool.json --direction auto
    python -m collector.planner --pool content/pool/2026-02-23-pool.json --recommend  # AI 推荐选题
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


def recommend_topics(ranked_items: list[CollectedItem], direction: Direction, top_n: int = 10) -> str:
    """用 AI 分析 Top 素材，推荐 3-5 个选题"""
    try:
        from generator.gemini_client import generate_text
    except ImportError:
        return "⚠ 无法导入 gemini_client，跳过 AI 推荐"

    # 准备素材摘要
    items_summary = []
    for i, item in enumerate(ranked_items[:top_n], 1):
        score = (item.raw_data or {}).get("score", 0)
        items_summary.append(f"{i}. [{score}分] {item.title}\n   来源: {item.source} | URL: {item.url}\n   摘要: {item.summary[:150]}")

    prompt = f"""你是一位资深选题策划师。以下是 {direction.label} 方向的 Top {top_n} 素材：

{chr(10).join(items_summary)}

请分析这些素材，推荐 3-5 个最值得写的选题。每个选题包含：
1. **选题标题**（建议的文章标题，吸引人）
2. **推荐理由**（为什么值得写、时效性如何、话题热度）
3. **建议角度**（切入点、差异化方向）
4. **关联素材**（哪几条素材可作为参考，用序号标注）

输出格式：
### 1. [选题标题]
- 推荐理由: ...
- 建议角度: ...
- 关联素材: #1, #3, #5

### 2. [选题标题]
...
"""

    try:
        print(f"    🤖 AI 分析中...")
        result = generate_text(prompt, task="summary", temperature=0.7)
        return result
    except Exception as e:
        return f"⚠ AI 推荐失败: {str(e)[:100]}"


def main():
    parser = argparse.ArgumentParser(description="选题策划（从素材池筛选+打分）")
    parser.add_argument("--pool", default=None, help="素材池 JSON 路径（默认取最新）")
    parser.add_argument("--direction", choices=["tech_ai", "auto"], default=None,
                        help="指定方向（默认两个方向都跑）")
    parser.add_argument("--recommend", action="store_true", help="启用 AI 选题推荐")
    args = parser.parse_args()

    pool_path = args.pool or find_latest_pool()
    if not pool_path:
        print("错误: 未找到素材池 JSON，请先运行 search 或指定 --pool 路径")
        sys.exit(1)

    print(f"素材池: {pool_path}")
    results = plan(pool_path, args.direction)

    # AI 推荐选题
    if args.recommend:
        print("\n=== AI 选题推荐 ===")
        for direction_name, result in results.items():
            direction = get_direction(direction_name)
            items = [CollectedItem(**d) for d in result["items"]]
            print(f"\n## 🎯 {direction.label} 推荐选题\n")
            recommendation = recommend_topics(items, direction)
            print(recommendation)

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
