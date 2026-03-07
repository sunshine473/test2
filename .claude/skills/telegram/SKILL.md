---
description: 手动发送消息到 Telegram（用于测试或临时通知）
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '"消息内容" [--parse-mode markdown|html]'
---

# /telegram — Telegram 消息发送器

手动发送消息到 Telegram，用于测试通知或发送临时消息。

## 工作流

调用发送脚本：

```bash
python src/bot/send_message.py "$MESSAGE" $PARSE_MODE_ARG
```

脚本会自动输出发送结果。

## 使用示例

- `/telegram "测试消息：素材采集已完成"`
- `/telegram "*加粗文本* 和 _斜体文本_" --parse-mode markdown`
- `/telegram "<b>加粗</b> 和 <a href='https://example.com'>链接</a>" --parse-mode html`
