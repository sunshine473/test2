#!/usr/bin/env python3
"""
Telegram 消息发送器
用法: python src/bot/send_message.py "消息内容" [--parse-mode markdown|html]
"""
import os
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()


def send_telegram_message(message: str, parse_mode: str = "") -> dict:
    """发送消息到 Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        raise ValueError("未配置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": False,
    }

    if parse_mode in ["markdown", "html", "MarkdownV2"]:
        payload["parse_mode"] = parse_mode

    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    if not result.get("ok"):
        raise Exception(result.get("description", "未知错误"))

    return result


def main():
    parser = argparse.ArgumentParser(description="发送消息到 Telegram")
    parser.add_argument("message", help="消息内容")
    parser.add_argument("--parse-mode", choices=["markdown", "html", "MarkdownV2"], help="消息格式")
    args = parser.parse_args()

    try:
        result = send_telegram_message(args.message, args.parse_mode or "")
        message_id = result["result"]["message_id"]
        print(f"✅ 消息发送成功")
        print(f"消息 ID: {message_id}")
        print(f"消息长度: {len(args.message)} 字符")
        print(f"格式: {args.parse_mode or '纯文本'}")
    except Exception as e:
        print(f"❌ 发送失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
