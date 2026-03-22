"""Coordinator Agent — 流程协调者。

负责编排整个内容生产流程，协调各个专业 Agent。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.base_agent import AgentResult, AgentStatus, BaseAgent


class CoordinatorAgent(BaseAgent):
    """协调者 Agent。"""

    def __init__(self, config: Optional[dict] = None):
        super().__init__("coordinator")
        self.config = config or self._default_config()
        self.state_file = Path("content/agent_state.json")

    @staticmethod
    def _default_config() -> dict:
        """默认配置。"""
        return {
            "mode": "auto",  # auto | semi-auto | manual
            "max_retries": 3,
            "retry_delay": 300,  # 5 分钟
        }

    def execute(self, **kwargs) -> AgentResult:
        """执行协调任务。"""
        self.status = AgentStatus.RUNNING

        try:
            mode = self.config.get("mode", "auto")

            if mode == "auto":
                result = self._run_auto_pipeline()
            elif mode == "semi-auto":
                result = self._run_semi_auto_pipeline()
            else:
                result = self._run_manual_pipeline()

            return self._success(data=result)

        except Exception as e:
            return self._failed(f"协调失败: {e}")

    def _run_auto_pipeline(self) -> dict:
        """全自动流程。"""
        print("=== 全自动流程启动 ===")

        # 1. 采集素材
        print("\n[1/5] 采集素材...")
        collector_result = self._run_collector()
        if collector_result.status != AgentStatus.SUCCESS:
            raise RuntimeError(f"采集失败: {collector_result.error}")

        pool_path = collector_result.data.get("pool_path")
        print(f"  ✓ 素材池: {pool_path}")

        # 2. 策划选题
        print("\n[2/5] 策划选题...")
        planner_result = self._run_planner(pool_path)
        if planner_result.status != AgentStatus.SUCCESS:
            raise RuntimeError(f"策划失败: {planner_result.error}")

        plan_result = planner_result.data
        print(f"  ✓ 策划完成")

        # 3. 自动选题
        print("\n[3/5] 自动选题...")
        selector_result = self._run_selector(plan_result)
        if selector_result.status != AgentStatus.SUCCESS:
            raise RuntimeError(f"选题失败: {selector_result.error}")

        selected_topics = selector_result.data
        print(f"  ✓ 选中 {len(selected_topics)} 篇")

        # 4. 生成文章
        print("\n[4/5] 生成文章...")
        writer_results = self._run_writer_batch(selected_topics)
        print(f"  ✓ 生成 {len(writer_results)} 篇")

        # 5. 发布文章
        print("\n[5/5] 发布文章...")
        publish_results = self._run_publisher_batch(writer_results)
        print(f"  ✓ 发布完成")

        return {
            "pool_path": pool_path,
            "selected_count": len(selected_topics),
            "generated_count": len(writer_results),
            "published_count": len(publish_results),
        }

    def _run_semi_auto_pipeline(self) -> dict:
        """半自动流程（保留 Telegram 确认）。"""
        print("=== 半自动流程启动 ===")

        # 1. 采集素材
        print("\n[1/5] 采集素材...")
        collector_result = self._run_collector()
        if collector_result.status != AgentStatus.SUCCESS:
            raise RuntimeError(f"采集失败: {collector_result.error}")

        pool_path = collector_result.data.get("pool_path")

        # 2. 策划选题
        print("\n[2/5] 策划选题...")
        planner_result = self._run_planner(pool_path)
        plan_result = planner_result.data

        # 3. 发送 Telegram 通知，等待用户选择
        print("\n[3/5] 等待用户选题...")
        self._send_telegram_notification(plan_result)
        print("  → 已发送 Telegram 通知，等待用户选择")

        # 保存状态，等待用户输入
        self._save_state({
            "stage": "waiting_for_selection",
            "pool_path": pool_path,
            "plan_result": plan_result,
        })

        return {"status": "waiting_for_user"}

    def _run_manual_pipeline(self) -> dict:
        """手动流程（保留当前模式）。"""
        print("=== 手动流程（使用 pipeline/main.py）===")
        return {"status": "manual_mode"}

    def _run_collector(self) -> AgentResult:
        """运行 Collector Agent。"""
        from collector.search import search

        try:
            pool = search([])  # 使用默认采集源
            return AgentResult(
                agent_name="collector",
                status=AgentStatus.SUCCESS,
                data=pool,
            )
        except Exception as e:
            return AgentResult(
                agent_name="collector",
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def _run_planner(self, pool_path: str) -> AgentResult:
        """运行 Planner。"""
        from collector.planner import plan

        try:
            result = plan(pool_path)
            return AgentResult(
                agent_name="planner",
                status=AgentStatus.SUCCESS,
                data=result,
            )
        except Exception as e:
            return AgentResult(
                agent_name="planner",
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def _run_selector(self, plan_result: dict) -> AgentResult:
        """运行 Selector Agent。"""
        from agents.selector import SelectorAgent

        agent = SelectorAgent(config=self.config.get("selector", {}))
        return agent.execute(plan_result=plan_result)

    def _run_writer_batch(self, topics: list[dict]) -> list[dict]:
        """批量生成文章。"""
        from generator.writer import generate_article

        results = []
        for topic in topics:
            try:
                title = topic.get("title", "")
                sources = [topic.get("url", "")]
                article, draft_path = generate_article(title, sources)
                results.append({
                    "title": title,
                    "draft_path": str(draft_path),
                    "status": "success",
                })
            except Exception as e:
                results.append({
                    "title": title,
                    "status": "failed",
                    "error": str(e),
                })
        return results

    def _run_publisher_batch(self, drafts: list[dict]) -> list[dict]:
        """批量发布文章。"""
        from publisher.main import load_config, parse_article
        from publisher.registry import get_publisher

        # 导入所有平台
        import publisher.platforms.wechat  # noqa: F401
        import publisher.platforms.xiaohongshu  # noqa: F401
        import publisher.platforms.zhihu  # noqa: F401
        import publisher.platforms.dongchedi  # noqa: F401

        config = load_config()
        targets = [n for n, c in config.items() if isinstance(c, dict) and c.get("enabled")]

        results = []
        for draft in drafts:
            if draft.get("status") != "success":
                continue

            draft_path = draft.get("draft_path")
            try:
                article = parse_article(draft_path)
                for platform in targets:
                    pub = get_publisher(platform)
                    result = pub.publish(article, config.get(platform, {}))
                    results.append({
                        "title": draft.get("title"),
                        "platform": platform,
                        "status": result.status.value,
                    })
            except Exception as e:
                results.append({
                    "title": draft.get("title"),
                    "status": "failed",
                    "error": str(e),
                })
        return results

    def _send_telegram_notification(self, plan_result: dict):
        """发送 Telegram 通知。"""
        from bot.telegram import send_message
        import os

        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not chat_id:
            return

        # 构造消息
        message = "📌 选题推荐\n\n"
        for direction, data in plan_result.items():
            items = data.get("items", [])[:5]
            if items:
                message += f"🎯 {data.get('label', direction)}\n"
                for i, item in enumerate(items, 1):
                    score = (item.get("raw_data") or {}).get("score", 0)
                    message += f"  {i}. [{score}] {item.get('title', '')[:50]}\n"
                message += "\n"

        message += "回复选题标题即可生成文章"
        send_message(chat_id, message)

    def _save_state(self, state: dict):
        """保存状态。"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        state["timestamp"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _load_state(self) -> Optional[dict]:
        """加载状态。"""
        if not self.state_file.exists():
            return None
        with open(self.state_file, encoding="utf-8") as f:
            return json.load(f)


def main():
    """测试 Coordinator Agent。"""
    import argparse

    parser = argparse.ArgumentParser(description="Coordinator Agent")
    parser.add_argument("--mode", choices=["auto", "semi-auto", "manual"], default="auto")
    args = parser.parse_args()

    config = {
        "mode": args.mode,
        "selector": {
            "strategy": "conservative",
            "min_score": 70,
            "max_age_hours": 24,
        },
    }

    agent = CoordinatorAgent(config=config)
    result = agent.execute()

    if result.status == AgentStatus.SUCCESS:
        print(f"\n✓ 协调完成: {result.data}")
    else:
        print(f"\n✗ 协调失败: {result.error}")


if __name__ == "__main__":
    main()
