"""流水线调度入口 — 串联 collect/normalize → plan → select → create → review → package/distribute。

用法:
    python src/pipeline/main.py                          # 默认跑到 select 暂停
    python src/pipeline/main.py --auto                   # 全自动
    python src/pipeline/main.py --until plan             # 跑到指定阶段
    python src/pipeline/main.py --resume latest --topic "选题"
    python src/pipeline/main.py --resume latest --approve
    python src/pipeline/main.py --from write --topic "选题"
    python src/pipeline/main.py --status
    python src/pipeline/main.py --list
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from pipeline.models import PIPELINE_DIR, PipelineState


class Pipeline:
    STAGE_ORDER = ["search", "plan", "select", "write", "review", "publish"]

    def __init__(self, state: PipelineState):
        self.state = state

    @classmethod
    def create(
        cls,
        sources: str = "",
        direction: str = "",
        platforms: str = "",
        no_cards: bool = False,
    ) -> "Pipeline":
        state = PipelineState()
        if sources:
            state.sources = sources
        if direction:
            state.direction = direction
        if platforms:
            state.platforms = platforms
        state.no_cards = no_cards
        return cls(state)

    @classmethod
    def load(cls, pipeline_id: str) -> "Pipeline":
        if pipeline_id == "latest":
            state = PipelineState.find_latest()
            if not state:
                raise FileNotFoundError("没有找到任何流水线记录")
        else:
            state = PipelineState.load(pipeline_id)
        return cls(state)

    @classmethod
    def list_runs(cls, limit: int = 20) -> list[PipelineState]:
        return PipelineState.list_recent(limit=limit)

    @staticmethod
    def _next_stage(stage: str) -> str | None:
        idx = Pipeline.STAGE_ORDER.index(stage)
        if idx + 1 >= len(Pipeline.STAGE_ORDER):
            return None
        return Pipeline.STAGE_ORDER[idx + 1]

    def run(self, until: str | None = None, auto: bool = False) -> PipelineState:
        """从 current_stage 顺序执行，遇到人工节点或 until 停止。"""
        self.state.status = "running"
        start_idx = self.STAGE_ORDER.index(self.state.current_stage)

        for stage in self.STAGE_ORDER[start_idx:]:
            self.state.current_stage = stage
            self.state.save()

            print(f"\n{'=' * 50}")
            print(f"  阶段: {stage}")
            print(f"{'=' * 50}")

            try:
                handler = getattr(self, f"_run_{stage}")
                handler(auto=auto)
            except Exception as e:
                self.state.status = "failed"
                self.state.error = f"{stage}: {e}\n{traceback.format_exc()}"
                self.state.log(stage, f"失败: {e}")
                self.state.save()
                print(f"\n阶段 {stage} 失败: {e}")
                return self.state

            if self.state.status == "paused":
                self.state.save()
                return self.state

            self.state.log(stage, "完成")
            self.state.save()

            if until and stage == until:
                print(f"\n已执行到指定阶段: {until}")
                next_stage = self._next_stage(stage)
                if next_stage:
                    self.state.current_stage = next_stage
                    self.state.status = "paused"
                else:
                    self.state.status = "completed"
                self.state.save()
                return self.state

        self.state.status = "completed"
        self.state.save()
        print(f"\n流水线完成! ID: {self.state.pipeline_id}")
        return self.state

    def _run_search(self, auto: bool = False):
        from collector.search import search

        source_list = [s.strip() for s in self.state.sources.split(",") if s.strip()]
        pool = search(source_list)
        self.state.pool_path = pool.get("_output_path", "")
        if not self.state.pool_path:
            from collector.planner import find_latest_pool

            self.state.pool_path = find_latest_pool() or ""
        self.state.log("search", f"素材池 {pool.get('dedup_total', 0)} 条: {self.state.pool_path}")

    def _run_plan(self, auto: bool = False):
        from collector.planner import find_latest_pool, plan

        pool_path = self.state.pool_path or find_latest_pool()
        if not pool_path:
            raise RuntimeError("未找到素材池，请先执行 search 阶段")
        result = plan(pool_path, self.state.direction or None)
        self.state.plan_result = result

        for dname, ddata in result.items():
            items = ddata.get("items", [])
            if items:
                print(f"\n  [{ddata.get('label', dname)}] Top-5 推荐:")
                for i, item in enumerate(items[:5], 1):
                    score = (item.get("raw_data") or {}).get("score", 0)
                    print(f"    {i}. [{score}] {item.get('title', '')[:60]}")

    def _run_select(self, auto: bool = False):
        if auto:
            for ddata in self.state.plan_result.values():
                items = ddata.get("items", [])
                if items:
                    top = items[0]
                    self.state.selected_topic = top.get("title", "")
                    self.state.selected_sources = [top.get("url", "")]
                    print(f"  自动选题: {self.state.selected_topic}")
                    return
            raise RuntimeError("plan_result 中没有可选素材")

        if self.state.selected_topic:
            print(f"  已选题: {self.state.selected_topic}")
            return

        print("\n  流水线已暂停，等待人工选题。")
        print('  恢复命令: python src/pipeline/main.py --resume latest --topic "选题标题"')
        self.state.status = "paused"

    def _run_write(self, auto: bool = False):
        if not self.state.selected_topic:
            raise RuntimeError("未选择选题，请先完成 select 阶段")

        from generator.writer import DRAFTS_DIR, _make_slug, generate_article

        sources = self.state.selected_sources or None
        article, draft_path = generate_article(self.state.selected_topic, sources)
        self.state.draft_path = str(draft_path)
        print(f"  草稿已生成: {draft_path}")

        if not self.state.no_cards:
            try:
                from generator.card_generator import generate_cards

                slug = _make_slug(self.state.selected_topic)
                cards_path = generate_cards(article, slug, DRAFTS_DIR)
                self.state.cards_path = str(cards_path)
                print(f"  卡片已生成: {cards_path}")
            except Exception as e:
                print(f"  卡片生成失败（跳过）: {e}")

    def _run_review(self, auto: bool = False):
        if auto:
            print("  自动审核通过")
            return
        if not self.state.draft_path:
            raise RuntimeError("未找到草稿，请先完成 write 阶段")

        print(f"\n  草稿路径: {self.state.draft_path}")
        print("  流水线已暂停，等待人工审核。")
        print("  审核通过: python src/pipeline/main.py --resume latest --approve")
        self.state.status = "paused"

    def _run_publish(self, auto: bool = False):
        if not self.state.draft_path:
            raise RuntimeError("未找到草稿，请先完成 write 阶段")

        from packager.main import build_publish_packages, load_draft_package, package_to_article
        from publisher.main import load_config
        from publisher.registry import get_publisher

        import publisher.platforms.bilibili  # noqa: F401
        import publisher.platforms.dongchedi  # noqa: F401
        import publisher.platforms.toutiao  # noqa: F401
        import publisher.platforms.wechat  # noqa: F401
        import publisher.platforms.xiaohongshu  # noqa: F401
        import publisher.platforms.zhihu  # noqa: F401

        config = load_config()
        draft = load_draft_package(self.state.draft_path)

        if self.state.platforms:
            targets = [p.strip() for p in self.state.platforms.split(",") if p.strip()]
        else:
            targets = [n for n, c in config.items() if isinstance(c, dict) and c.get("enabled")]

        if not targets:
            print("  没有启用的发布平台，跳过发布")
            return

        print(f"  发布平台: {', '.join(targets)}")
        packages = build_publish_packages(draft, targets)
        results = []
        for package in packages:
            name = package.platform
            print(f"  [{name}] 发布中...")
            try:
                pub = get_publisher(name)
                result = pub.publish(package_to_article(package), config.get(name, {}))
                results.append(
                    {"platform": name, "status": result.status.value, "message": result.message}
                )
                print(f"  [{name}] {result.status.value}: {result.message}")
            except Exception as e:
                results.append({"platform": name, "status": "failed", "message": str(e)})
                print(f"  [{name}] 错误: {e}")
        self.state.publish_results = results

    def apply_resume_inputs(self, topic: str = "", approve: bool = False):
        stage = self.state.current_stage
        if stage == "select" and topic:
            self.state.selected_topic = topic
            self.state.selected_sources = []
            self.state.status = "running"
            self.state.save()
            return
        if stage == "review" and approve:
            self.state.status = "running"
            self.state.save()
            return

        if stage == "select":
            raise RuntimeError('当前停在 select，需传 --topic "选题标题"')
        if stage == "review":
            raise RuntimeError("当前停在 review，需传 --approve")

    def print_summary(self):
        print(f"pipeline_id : {self.state.pipeline_id}")
        print(f"status      : {self.state.status}")
        print(f"stage       : {self.state.current_stage}")
        if self.state.selected_topic:
            print(f"topic       : {self.state.selected_topic}")
        if self.state.draft_path:
            print(f"draft       : {self.state.draft_path}")
        if self.state.publish_results:
            print(f"publish     : {len(self.state.publish_results)} 平台")
        if self.state.error:
            print(f"error       : {self.state.error.splitlines()[0]}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="流水线调度器")
    parser.add_argument("--sources", default="", help="采集源，逗号分隔")
    parser.add_argument("--direction", default="", choices=["", "tech_ai", "auto"], help="内容方向")
    parser.add_argument("--platforms", default="", help="发布平台，逗号分隔")
    parser.add_argument("--no-cards", action="store_true", help="写作阶段不生成卡片")
    parser.add_argument("--auto", action="store_true", help="自动通过 select/review 人工节点")
    parser.add_argument("--until", choices=Pipeline.STAGE_ORDER, default=None, help="执行到指定阶段")
    parser.add_argument("--resume", default="", help="恢复指定流水线 ID 或 latest")
    parser.add_argument("--from", dest="from_stage", choices=Pipeline.STAGE_ORDER, default="", help="从某阶段启动")
    parser.add_argument("--topic", default="", help="恢复/启动时设置选题")
    parser.add_argument("--approve", action="store_true", help="恢复 review 阶段时表示审核通过")
    parser.add_argument("--status", action="store_true", help="查看最新流水线状态")
    parser.add_argument("--list", action="store_true", help="列出最近流水线")
    parser.add_argument("--json", action="store_true", help="状态输出为 JSON")
    return parser.parse_args()


def _print_list(limit: int = 20):
    runs = Pipeline.list_runs(limit=limit)
    if not runs:
        print("暂无流水线记录")
        return
    print("最近流水线:")
    for state in runs:
        print(f"- {state.pipeline_id} | {state.status:9s} | {state.current_stage}")


def _print_status(as_json: bool = False):
    latest = PipelineState.find_latest()
    if not latest:
        print("暂无流水线记录")
        return
    if as_json:
        print(json.dumps(latest.to_dict(), ensure_ascii=False, indent=2))
        return
    Pipeline(latest).print_summary()


def main():
    args = _parse_args()

    if args.list:
        _print_list()
        return
    if args.status:
        _print_status(as_json=args.json)
        return

    try:
        if args.resume:
            pipeline = Pipeline.load(args.resume)
            pipeline.apply_resume_inputs(topic=args.topic, approve=args.approve)
        else:
            pipeline = Pipeline.create(
                sources=args.sources,
                direction=args.direction,
                platforms=args.platforms,
                no_cards=args.no_cards,
            )
            if args.from_stage:
                pipeline.state.current_stage = args.from_stage
                if args.topic:
                    pipeline.state.selected_topic = args.topic
                pipeline.state.status = "running"
                pipeline.state.save()

        until = args.until
        if not args.auto and not until and not args.resume and not args.from_stage:
            until = "select"

        state = pipeline.run(until=until, auto=args.auto)
        if args.json:
            print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
