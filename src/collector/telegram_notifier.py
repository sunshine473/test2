"""Telegram 通知模块 — 采集完成后推送选题摘要到 Telegram。

未配置 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 时静默跳过，不阻塞流程。
使用 Telegram Bot API sendMessage 接口，纯 HTTP 调用，无需额外依赖。
"""

import os
from datetime import datetime

import requests


class TelegramNotifier:
    """将采集+策划结果推送到 Telegram。"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)

    def notify(self, search_result: dict, plan_result: dict) -> bool:
        """发送选题摘要通知。返回是否发送成功。"""
        if not self.enabled:
            print("[Telegram] 未配置凭据，跳过通知")
            return False

        text = self._build_message(search_result, plan_result)
        return self._send(text)

    def _build_message(self, search_result: dict, plan_result: dict) -> str:
        """构建 Telegram MarkdownV2 消息。"""
        date = search_result.get("date", datetime.now().strftime("%Y-%m-%d"))
        raw_total = search_result.get("raw_total", 0)
        dedup_total = search_result.get("dedup_total", 0)
        cluster_count = search_result.get("cluster_summary", {}).get("cluster_count", 0)

        lines = [
            f"📊 素材采集完成 — {date}",
            "",
            f"采集: {raw_total} 条 → 去重: {dedup_total} 条 → 聚类: {cluster_count} 组",
        ]
        # 各方向 Top 选题
        direction_emojis = {"tech_ai": "🎯 AI 科技", "auto": "🚗 汽车"}
        for dir_name, dir_data in plan_result.items():
            label = direction_emojis.get(dir_name, dir_data.get("label", dir_name))
            items = dir_data.get("items", [])
            top_items = items[:5]

            lines.append("")
            lines.append(f"{label} Top {len(top_items)}")

            for i, item in enumerate(top_items, 1):
                title = item.get("title", "无标题")[:60]
                url = item.get("url", "")
                score = (item.get("raw_data") or {}).get("score", 0)
                if url:
                    lines.append(f"{i}. {title} ⭐{score}")
                    lines.append(f"   {url}")
                else:
                    lines.append(f"{i}. {title} ⭐{score}")

        lines.append("")
        lines.append(f"素材池: content/pool/{date}-pool.json")

        return "\n".join(lines)

    def _send(self, text: str) -> bool:
        """调用 Telegram Bot API 发送消息。"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
            print("[Telegram] 通知发送成功")
            return True
        except Exception as e:
            print(f"[Telegram] 发送失败: {e}")
            return False
