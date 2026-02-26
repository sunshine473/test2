"""Telegram Bot 入口 — 轮询消息 → Claude Agent 处理 → 回复。

设计为 GitHub Actions cron 调用：每次运行拉取新消息，处理后退出。
offset 通过文件持久化（Actions cache）。
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def ensure_utf8():
    """Windows 控制台 UTF-8 兼容"""
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    if sys.stderr.encoding != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            import codecs
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)


ensure_utf8()

from bot.telegram import get_updates, send_message
from bot.agent import handle_message

AUTHORIZED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OFFSET_FILE = Path(os.getenv("BOT_STATE_DIR", "/tmp/bot_state")) / "update_offset.txt"


def load_offset() -> int | None:
    if OFFSET_FILE.exists():
        text = OFFSET_FILE.read_text().strip()
        return int(text) if text else None
    return None


def save_offset(offset: int):
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(str(offset))


def is_authorized(chat_id: int | str) -> bool:
    if not AUTHORIZED_CHAT_ID:
        return False
    return str(chat_id) == str(AUTHORIZED_CHAT_ID)


def main():
    print("=== Telegram Bot 启动 ===")

    offset = load_offset()
    print(f"当前 offset: {offset}")

    updates = get_updates(offset=offset, timeout=30)
    print(f"收到 {len(updates)} 条更新")

    if not updates:
        print("无新消息，退出")
        return

    for update in updates:
        update_id = update["update_id"]
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not text or not chat_id:
            continue

        print(f"\n[消息] chat_id={chat_id}: {text[:100]}")

        if not is_authorized(chat_id):
            print(f"  未授权的 chat_id: {chat_id}，跳过")
            continue

        # Claude Agent 处理
        print("  处理中...")
        reply = handle_message(text)
        print(f"  回复: {reply[:200]}")

        send_message(chat_id, reply)

        # 更新 offset 为最新 update_id + 1
        offset = update_id + 1

    save_offset(offset)
    print(f"\noffset 已保存: {offset}")
    print("=== Bot 运行结束 ===")


if __name__ == "__main__":
    main()
