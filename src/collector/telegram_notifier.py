"""Telegram 通知模块 — 采集完成后推送选题摘要到 Telegram。

未配置 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 时静默跳过，不阻塞流程。
使用 Telegram Bot API sendMessage 接口，纯 HTTP 调用，无需额外依赖。
"""

import os
from datetime import datetime, timezone

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
        """构建 Telegram 通知消息（总结优先）。"""
        date = search_result.get("date", datetime.now().strftime("%Y-%m-%d"))
        raw_total = search_result.get("raw_total", 0)
        dedup_total = search_result.get("dedup_total", 0)
        cluster_count = search_result.get("cluster_summary", {}).get("cluster_count", 0)
        best = self._pick_global_best(plan_result)

        lines = [
            f"📊 素材采集完成 — {date}",
            "",
            "🧠 今日总结",
            f"- 采集 {raw_total} 条，去重后 {dedup_total} 条，共 {cluster_count} 个话题簇",
        ]

        if best:
            lines.append(
                f"- 建议优先写：《{best['title']}》"
                f"（{best['direction_label']}，评分 {best['score']}）"
            )
        else:
            lines.append("- 今日暂无可直接推荐的高潜选题")

        lines.append("")
        lines.append("📌 分方向推荐（Top10 新鲜内容）")

        # 各方向 Top 10 选题（仅显示 24 小时内的新内容）
        direction_emojis = {"tech_ai": "🎯 AI 科技", "auto": "🚗 汽车"}
        for dir_name, dir_data in plan_result.items():
            label = direction_emojis.get(dir_name, dir_data.get("label", dir_name))
            items = dir_data.get("items", [])

            # 筛选 24 小时内的新内容
            fresh_items = []
            for item in items:
                published_at = item.get("published_at", "")
                if self._is_fresh(published_at, hours=24):
                    fresh_items.append(item)

            top_items = fresh_items[:10]  # 取前 10 条
            filtered_count = dir_data.get("filtered_count", 0)
            avg_score = (dir_data.get("score_summary") or {}).get("avg", 0)

            lines.append("")
            lines.append(f"{label}: 候选 {filtered_count} 条，24h 新鲜 {len(fresh_items)} 条，均分 {avg_score}")

            if not top_items:
                lines.append("  暂无 24 小时内新内容")
                continue

            for i, item in enumerate(top_items, 1):
                title = item.get("title", "无标题")[:60]
                score = (item.get("raw_data") or {}).get("score", 0)
                source = item.get("source_name", "")
                url = item.get("url", "")
                time_label = self._format_time(item.get("published_at", ""))
                summary = (item.get("summary") or "")[:150].replace("\n", " ")

                # 标题 + 评分
                lines.append(f"  {i}) {title} ⭐{score}")

                # 元信息（来源 + 时间）
                meta_parts = []
                if source:
                    meta_parts.append(source)
                meta_parts.append(time_label)
                lines.append(f"     [{' · '.join(meta_parts)}]")

                # 摘要
                if summary:
                    lines.append(f"     {summary}")

                # URL 链接
                if url:
                    lines.append(f"     🔗 {url}")

        lines.append("")
        lines.append(f"素材池: content/pool/{date}-pool.json")

        return "\n".join(lines)

    @staticmethod
    def _is_fresh(published_at: str, hours: int = 24) -> bool:
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

    @staticmethod
    def _format_time(published_at: str) -> str:
        """将 published_at 转为相对时间标签。"""
        if not published_at:
            return "时间未知"
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(published_at, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                return "时间未知"
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

    @staticmethod
    def _pick_global_best(plan_result: dict) -> dict | None:
        """从所有方向候选中选出评分最高的选题。"""
        best = None
        for dir_name, dir_data in plan_result.items():
            label = dir_data.get("label") or dir_name
            for item in dir_data.get("items", []):
                score = (item.get("raw_data") or {}).get("score", 0)
                if best is None or score > best["score"]:
                    best = {
                        "direction": dir_name,
                        "direction_label": label,
                        "title": item.get("title", "无标题"),
                        "score": score,
                    }
        return best

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
