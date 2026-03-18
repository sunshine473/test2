"""批量内容生产流水线 — 自动生成多篇文章并发布到指定平台。

用法:
    python src/pipeline/batch_pipeline.py --count 4 --platforms xiaohongshu,zhihu
    python src/pipeline/batch_pipeline.py --count 2 --direction tech_ai --platforms xiaohongshu
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from pipeline.main import Pipeline
from pipeline.ai_selector import select_best_topic


class BatchPipeline:
    """批量内容生产流水线"""

    def __init__(
        self,
        count_per_direction: int = 2,
        platforms: str = "xiaohongshu,zhihu",
        sources: str = "",
        no_cards: bool = False,
    ):
        self.count_per_direction = count_per_direction
        self.platforms = platforms
        self.sources = sources
        self.no_cards = no_cards
        self.results = []

    def run(self) -> list[dict]:
        """执行批量生产流水线

        Returns:
            结果列表，每个元素包含 direction, topic, draft_path, publish_results
        """
        print(f"\n{'=' * 60}")
        print(f"  批量内容生产流水线")
        print(f"  每个方向生成: {self.count_per_direction} 篇")
        print(f"  发布平台: {self.platforms}")
        print(f"{'=' * 60}\n")

        # 阶段 1: 素材搜索（只执行一次）
        print("\n[阶段 1/4] 素材搜索")
        pipeline = Pipeline.create(
            sources=self.sources,
            platforms=self.platforms,
            no_cards=self.no_cards,
        )
        pipeline.run(until="plan", auto=True)
        pool_path = pipeline.state.pool_path

        # 阶段 2: 选题策划（两个方向）
        print("\n[阶段 2/4] 选题策划")
        pipeline.run(until="select", auto=True)
        recommended_topics = pipeline.state.recommended_topics

        if not recommended_topics:
            print("  ⚠ 未找到推荐选题，流水线终止")
            return []

        # 阶段 3: 批量生成内容
        print(f"\n[阶段 3/4] 批量生成内容（每个方向 {self.count_per_direction} 篇）")

        for direction_name, topics in recommended_topics.items():
            direction_label = "AI 科技" if direction_name == "tech_ai" else "汽车"
            print(f"\n  === {direction_label} 方向 ===")

            # 选择 Top N 个选题
            selected_topics = topics[:self.count_per_direction]

            for i, topic_data in enumerate(selected_topics, 1):
                print(f"\n  [{i}/{self.count_per_direction}] 生成: {topic_data['title']}")

                try:
                    # 创建新的流水线实例
                    article_pipeline = Pipeline.create(
                        direction=direction_name,
                        platforms=self.platforms,
                        no_cards=self.no_cards,
                    )

                    # 设置选题
                    article_pipeline.state.pool_path = pool_path
                    article_pipeline.state.plan_result = pipeline.state.plan_result
                    article_pipeline.state.recommended_topics = recommended_topics
                    article_pipeline.state.selected_topic = topic_data["title"]
                    article_pipeline.state.selected_sources = topic_data.get("source_urls", [])
                    article_pipeline.state.current_stage = "write"

                    # 执行 write → review → publish
                    article_pipeline.run(auto=True)

                    # 记录结果
                    result = {
                        "direction": direction_name,
                        "direction_label": direction_label,
                        "topic": topic_data["title"],
                        "score": topic_data.get("score", 0),
                        "draft_path": article_pipeline.state.draft_path,
                        "review_score": article_pipeline.state.review_score,
                        "review_passed": article_pipeline.state.review_passed,
                        "publish_results": article_pipeline.state.publish_results,
                        "pipeline_id": article_pipeline.state.pipeline_id,
                    }
                    self.results.append(result)

                    print(f"    ✅ 完成: {article_pipeline.state.draft_path}")
                    print(f"    📊 审核评分: {article_pipeline.state.review_score}/100")

                except Exception as e:
                    print(f"    ❌ 失败: {e}")
                    self.results.append({
                        "direction": direction_name,
                        "direction_label": direction_label,
                        "topic": topic_data["title"],
                        "error": str(e),
                    })

        # 阶段 4: 汇总报告
        print(f"\n[阶段 4/4] 批量生产完成")
        self._print_summary()

        return self.results

    def _print_summary(self):
        """打印汇总报告"""
        print(f"\n{'=' * 60}")
        print(f"  批量生产汇总报告")
        print(f"{'=' * 60}\n")

        # 按方向统计
        tech_ai_count = sum(1 for r in self.results if r.get("direction") == "tech_ai" and not r.get("error"))
        auto_count = sum(1 for r in self.results if r.get("direction") == "auto" and not r.get("error"))
        failed_count = sum(1 for r in self.results if r.get("error"))

        print(f"  AI 科技方向: {tech_ai_count} 篇")
        print(f"  汽车方向: {auto_count} 篇")
        print(f"  失败: {failed_count} 篇")
        print(f"  总计: {len(self.results)} 篇\n")

        # 按平台统计发布结果
        platforms = self.platforms.split(",")
        print("  发布结果:")
        for platform in platforms:
            success = 0
            failed = 0
            for result in self.results:
                if result.get("error"):
                    continue
                for pub_result in result.get("publish_results", []):
                    if pub_result.get("platform") == platform:
                        if pub_result.get("status") == "success":
                            success += 1
                        else:
                            failed += 1
            print(f"    {platform}: {success} 成功, {failed} 失败")

        # 详细列表
        print(f"\n  详细列表:")
        for i, result in enumerate(self.results, 1):
            direction_label = result.get("direction_label", "未知")
            topic = result.get("topic", "未知")
            if result.get("error"):
                print(f"    {i}. [{direction_label}] {topic} - ❌ {result['error']}")
            else:
                score = result.get("review_score", 0)
                passed = "✅" if result.get("review_passed") else "❌"
                print(f"    {i}. [{direction_label}] {topic} - {passed} {score}/100")

        print(f"\n{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="批量内容生产流水线")
    parser.add_argument(
        "--count",
        type=int,
        default=2,
        help="每个方向生成的文章数量（默认 2）"
    )
    parser.add_argument(
        "--platforms",
        default="xiaohongshu,zhihu",
        help="发布平台（逗号分隔，默认 xiaohongshu,zhihu）"
    )
    parser.add_argument(
        "--sources",
        default="",
        help="素材来源（逗号分隔，默认全部）"
    )
    parser.add_argument(
        "--no-cards",
        action="store_true",
        help="不生成视觉卡片"
    )

    args = parser.parse_args()

    batch = BatchPipeline(
        count_per_direction=args.count,
        platforms=args.platforms,
        sources=args.sources,
        no_cards=args.no_cards,
    )

    results = batch.run()

    # 保存结果到 JSON
    import json
    from datetime import datetime
    output_path = PROJECT_ROOT / "content" / "batch" / f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-batch.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  结果已保存: {output_path}")


if __name__ == "__main__":
    main()
