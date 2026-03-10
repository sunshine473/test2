"""Telegram Bot 回调处理器 — 处理按钮点击事件。

支持的回调：
- view_tech_ai / view_auto: 查看方向详情
- start_write: 开始写作流程
- write_tech_ai / write_auto: 选择方向写作
- check_pool: 查看素材池
- back_to_summary: 返回总结
"""

import json
import os
from pathlib import Path

import requests


class CallbackHandler:
    """处理 Telegram 回调查询。"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def handle_callback(self, callback_query: dict) -> bool:
        """处理回调查询。"""
        callback_id = callback_query.get("id")
        data = callback_query.get("data", "")
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")

        print(f"[Callback] {data}")

        # 先应答回调（避免 Telegram 显示加载中）
        self._answer_callback(callback_id)

        # 根据 callback_data 执行不同操作
        if data == "view_tech_ai":
            return self._handle_view_direction("tech_ai", chat_id)
        elif data == "view_auto":
            return self._handle_view_direction("auto", chat_id)
        elif data == "start_write":
            return self._handle_start_write(chat_id)
        elif data.startswith("write_"):
            direction = data.replace("write_", "")
            return self._handle_write_direction(direction, chat_id)
        elif data == "check_pool":
            return self._handle_check_pool(chat_id)
        elif data == "back_to_summary":
            return self._handle_back_to_summary(chat_id)
        else:
            return self._send_message(chat_id, f"未知操作: {data}")

    def _handle_view_direction(self, direction: str, chat_id: int) -> bool:
        """查看某个方向的详细 Top10。"""
        # 读取最新的素材池和策划结果
        plan_result = self._load_latest_plan()
        if not plan_result:
            return self._send_message(chat_id, "未找到最新的策划结果，请先运行采集")

        from collector.telegram_notifier_interactive import InteractiveTelegramNotifier
        notifier = InteractiveTelegramNotifier()
        return notifier.send_direction_detail(direction, plan_result)

    def _handle_start_write(self, chat_id: int) -> bool:
        """开始写作流程 - 让用户选择方向。"""
        text = "请选择要写作的方向："
        buttons = [
            [
                {"text": "🎯 AI 科技", "callback_data": "write_tech_ai"},
                {"text": "🚗 汽车", "callback_data": "write_auto"},
            ]
        ]
        return self._send_message_with_keyboard(chat_id, text, buttons)

    def _handle_write_direction(self, direction: str, chat_id: int) -> bool:
        """选择方向后，显示该方向的 Top5 供选择。"""
        plan_result = self._load_latest_plan()
        if not plan_result:
            return self._send_message(chat_id, "未找到最新的策划结果，请先运行采集")

        dir_data = plan_result.get(direction, {})
        if not dir_data:
            return self._send_message(chat_id, f"未找到 {direction} 方向的数据")

        label = dir_data.get("label", direction)
        items = dir_data.get("items", [])[:5]  # Top 5

        lines = [f"📝 {label} Top5 选题", "", "请回复选题编号（1-5）或直接输入选题标题：", ""]
        for i, item in enumerate(items, 1):
            title = item.get("title", "无标题")[:60]
            score = (item.get("raw_data") or {}).get("score", 0)
            lines.append(f"{i}. {title} ⭐{score:.1f}")

        return self._send_message(chat_id, "\n".join(lines))

    def _handle_check_pool(self, chat_id: int) -> bool:
        """查看素材池概况。"""
        from collector.planner import find_latest_pool

        pool_path = find_latest_pool()
        if not pool_path:
            return self._send_message(chat_id, "未找到素材池，请先运行采集")

        try:
            with open(pool_path, encoding="utf-8") as f:
                pool = json.load(f)

            date = pool.get("date", "未知")
            dedup_total = pool.get("dedup_total", 0)
            cluster_count = pool.get("cluster_summary", {}).get("cluster_count", 0)

            text = f"📦 最新素材池\n\n日期: {date}\n去重后: {dedup_total} 条\n话题簇: {cluster_count} 个\n\n路径: {pool_path}"
            return self._send_message(chat_id, text)
        except Exception as e:
            return self._send_message(chat_id, f"读取素材池失败: {e}")

    def _handle_back_to_summary(self, chat_id: int) -> bool:
        """返回总结（重新发送采集通知）。"""
        return self._send_message(chat_id, "请查看最新的采集通知消息")

    def _load_latest_plan(self) -> dict:
        """加载最新的策划结果。"""
        from collector.planner import find_latest_pool

        pool_path = find_latest_pool()
        if not pool_path:
            return {}

        # 尝试从 pipeline 状态中读取
        pipeline_dir = Path(__file__).parent.parent.parent / ".pipeline"
        if pipeline_dir.exists():
            json_files = sorted(pipeline_dir.glob("*.json"), reverse=True)
            for json_file in json_files:
                try:
                    with open(json_file, encoding="utf-8") as f:
                        state = json.load(f)
                        plan_result = state.get("plan_result")
                        if plan_result:
                            return plan_result
                except Exception:
                    continue

        # 如果没有 pipeline 状态，重新策划
        try:
            from collector.planner import plan
            return plan(pool_path, direction_name=None)
        except Exception as e:
            print(f"[Callback] 策划失败: {e}")
            return {}

    def _answer_callback(self, callback_id: str) -> bool:
        """应答回调查询（避免 Telegram 显示加载中）。"""
        if not callback_id:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        try:
            resp = requests.post(url, json={"callback_query_id": callback_id}, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            # 应答失败不影响功能，只是会显示加载中
            print(f"[Callback] 应答失败（不影响功能）: {e}")
            return False

    def _send_message(self, chat_id: int, text: str) -> bool:
        """发送简单文本消息。"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Callback] 发送消息失败: {e}")
            return False

    def _send_message_with_keyboard(self, chat_id: int, text: str, buttons: list) -> bool:
        """发送带内联键盘的消息。"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
            "reply_markup": {"inline_keyboard": buttons},
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Callback] 发送消息失败: {e}")
            return False
