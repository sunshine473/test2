"""Telegram 交互式通知模块 — 带按钮的通知，支持远程控制。

在原有通知基础上增加：
1. 内联按钮（Inline Keyboard）支持
2. 快速选题按钮
3. 查看详情按钮
4. 开始写作按钮
"""

import os
from datetime import datetime, timezone

import requests


class InteractiveTelegramNotifier:
    """交互式 Telegram 通知器，支持按钮和回调。"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)

    def notify_with_buttons(self, search_result: dict, plan_result: dict) -> bool:
        """发送带交互按钮的通知。"""
        if not self.enabled:
            print("[Telegram] 未配置凭据，跳过通知")
            return False

        # 构建消息文本
        text = self._build_message(search_result, plan_result)

        # 构建按钮
        buttons = self._build_buttons(plan_result)

        return self._send_with_keyboard(text, buttons)

    def _build_message(self, search_result: dict, plan_result: dict) -> str:
        """构建通知消息（简化版，重点是总结）。"""
        date = search_result.get("date", datetime.now().strftime("%Y-%m-%d"))
        raw_total = search_result.get("raw_total", 0)
        dedup_total = search_result.get("dedup_total", 0)
        cluster_count = search_result.get("cluster_summary", {}).get("cluster_count", 0)

        lines = [
            f"📊 素材采集完成 — {date}",
            "",
            "🧠 今日总结",
            f"- 采集 {raw_total} 条，去重后 {dedup_total} 条，共 {cluster_count} 个话题簇",
            "",
            "📌 分方向推荐",
        ]

        # 各方向统计
        direction_emojis = {"tech_ai": "🎯 AI 科技", "auto": "🚗 汽车"}
        for dir_name, dir_data in plan_result.items():
            label = direction_emojis.get(dir_name, dir_data.get("label", dir_name))
            items = dir_data.get("items", [])

            # 筛选 24 小时内的新内容
            fresh_items = [
                item for item in items
                if self._is_fresh(item.get("published_at", ""), hours=24)
            ]

            filtered_count = dir_data.get("filtered_count", 0)
            avg_score = (dir_data.get("score_summary") or {}).get("avg", 0)

            lines.append(f"\n{label}: 候选 {filtered_count} 条，24h 新鲜 {len(fresh_items)} 条，均分 {avg_score:.1f}")

            # 显示 Top 3
            for i, item in enumerate(fresh_items[:3], 1):
                title = item.get("title", "无标题")[:50]
                score = (item.get("raw_data") or {}).get("score", 0)
                lines.append(f"  {i}. {title} ⭐{score:.1f}")

        lines.append("")
        lines.append("👇 点击下方按钮进行操作")

        return "\n".join(lines)

    def _build_buttons(self, plan_result: dict) -> list:
        """构建内联按钮。

        按钮格式：
        [查看 AI 科技 Top10] [查看汽车 Top10]
        [开始写作]           [查看素材池]
        """
        buttons = []

        # 第一行：查看各方向详情
        row1 = []
        if "tech_ai" in plan_result:
            row1.append({
                "text": "🎯 查看 AI 科技 Top10",
                "callback_data": "view_tech_ai"
            })
        if "auto" in plan_result:
            row1.append({
                "text": "🚗 查看汽车 Top10",
                "callback_data": "view_auto"
            })
        if row1:
            buttons.append(row1)

        # 第二行：操作按钮
        row2 = [
            {"text": "✍️ 开始写作", "callback_data": "start_write"},
            {"text": "📦 查看素材池", "callback_data": "check_pool"},
        ]
        buttons.append(row2)

        return buttons

    @staticmethod
    def _is_fresh(published_at: str, hours: int = 24) -> bool:
        """判断内容是否在指定小时数内发布。"""
        if not published_at:
            # GitHub Trending 等没有 published_at 的内容视为新鲜
            return True
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return True  # 解析失败也视为新鲜
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elapsed_hours = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600
        return elapsed_hours <= hours

    def _send_with_keyboard(self, text: str, buttons: list) -> bool:
        """发送带内联键盘的消息。"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}

        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            print("[Telegram] 交互式通知发送成功")
            return True
        except Exception as e:
            print(f"[Telegram] 发送失败: {e}")
            return False

    def send_direction_detail(self, direction: str, plan_result: dict) -> bool:
        """发送某个方向的详细 Top10 列表。"""
        if not self.enabled:
            return False

        dir_data = plan_result.get(direction, {})
        if not dir_data:
            return self._send_simple(f"未找到 {direction} 方向的数据")

        label = dir_data.get("label", direction)
        items = dir_data.get("items", [])

        # 筛选新鲜内容
        fresh_items = [
            item for item in items
            if self._is_fresh(item.get("published_at", ""), hours=24)
        ]

        lines = [f"📌 {label} Top10 新鲜内容", ""]

        if not fresh_items:
            lines.append("暂无 24 小时内新内容")
        else:
            for i, item in enumerate(fresh_items[:10], 1):
                title = item.get("title", "无标题")[:60]
                score = (item.get("raw_data") or {}).get("score", 0)
                url = item.get("url", "")
                source = item.get("source_name", "")
                time_label = self._format_time(item.get("published_at", ""))
                summary = (item.get("summary") or "")[:150].replace("\n", " ")

                lines.append(f"{i}. {title} ⭐{score:.1f}")
                lines.append(f"   [{source} · {time_label}]")
                if summary:
                    lines.append(f"   {summary}")
                if url:
                    lines.append(f"   🔗 {url}")
                lines.append("")

        text = "\n".join(lines)

        # 添加操作按钮
        buttons = [[
            {"text": "✍️ 选择这个方向写作", "callback_data": f"write_{direction}"},
            {"text": "🔙 返回", "callback_data": "back_to_summary"},
        ]]

        return self._send_with_keyboard(text, buttons)

    @staticmethod
    def _format_time(published_at: str) -> str:
        """将 published_at 转为相对时间标签。"""
        if not published_at:
            return "最近"
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return "最近"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600
        if hours < 1:
            return "刚刚"
        if hours < 24:
            return f"{int(hours)}小时前"
        days = int(hours / 24)
        if days <= 30:
            return f"{days}天前"
        return f"{days // 30}个月前"

    def _send_simple(self, text: str) -> bool:
        """发送简单文本消息。"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Telegram] 发送失败: {e}")
            return False
