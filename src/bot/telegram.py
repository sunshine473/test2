"""Telegram Bot API 客户端 — getUpdates 轮询 + sendMessage 回复。

复用 telegram_notifier.py 的 HTTP 模式（requests 库），无额外依赖。
"""

import os
from typing import Any

import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Telegram 单条消息最大 4096 字符
MAX_MESSAGE_LENGTH = 4096


def _check_token():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 未配置，无法调用 Telegram API")


def get_updates(offset: int | None = None, timeout: int = 30) -> list[dict[str, Any]]:
    """长轮询获取新消息。返回 Update 对象列表。"""
    _check_token()
    params: dict[str, Any] = {
        "timeout": timeout,
        "allowed_updates": ["message"],
    }
    if offset is not None:
        params["offset"] = offset

    resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=timeout + 10)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok"):
        print(f"[Telegram] getUpdates 失败: {data}")
        return []

    return data.get("result", [])


def send_message(chat_id: str | int, text: str) -> bool:
    """发送消息到指定 chat，自动分段处理超长文本。返回是否全部成功。"""
    _check_token()
    if not text.strip():
        return True

    chunks = _split_text(text)
    success = True
    for chunk in chunks:
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Telegram] 发送失败: {e}")
            success = False

    return success


def _split_text(text: str) -> list[str]:
    """将超长文本按段落边界分割为 ≤4096 字符的块。"""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = current + "\n" + line if current else line
        if len(candidate) > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current)
            # 单行超长时强制截断
            while len(line) > MAX_MESSAGE_LENGTH:
                chunks.append(line[:MAX_MESSAGE_LENGTH])
                line = line[MAX_MESSAGE_LENGTH:]
            current = line
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks
