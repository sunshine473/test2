---
description: 手动发送消息到 Telegram（用于测试或临时通知）
user-invocable: true
allowed-tools: Bash(python:*), Read
argument-hint: '"消息内容" [--parse-mode markdown|html]'
---

# /telegram — Telegram 消息发送器

手动发送消息到 Telegram，用于测试通知或发送临时消息。

## 前置条件

- `.env` 中配置 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`

## SOP 工作流

### Step 1: 解析消息内容

从用户参数中提取消息内容和格式选项。

### Step 2: 发送消息

使用 Python 脚本发送消息到 Telegram：

```bash
python -c "
import os, sys, requests
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

if not bot_token or not chat_id:
    print('错误: 未配置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID', file=sys.stderr)
    sys.exit(1)

message = '''$MESSAGE'''
parse_mode = '$PARSE_MODE'  # 'markdown', 'html', 或空字符串

url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
payload = {
    'chat_id': chat_id,
    'text': message,
    'disable_web_page_preview': False,
}

if parse_mode in ['markdown', 'html', 'MarkdownV2']:
    payload['parse_mode'] = parse_mode

try:
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    if result.get('ok'):
        print('✅ 消息发送成功')
        print(f'消息 ID: {result[\"result\"][\"message_id\"]}')
    else:
        print(f'❌ 发送失败: {result.get(\"description\")}', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'❌ 发送失败: {e}', file=sys.stderr)
    sys.exit(1)
"
```

将 `$MESSAGE` 替换为用户提供的消息内容，`$PARSE_MODE` 替换为格式选项（默认为空）。

### Step 3: 向用户反馈

输出格式：

```
✅ 消息已发送到 Telegram
- 消息长度: X 字符
- 格式: [纯文本/Markdown/HTML]
- 消息 ID: 12345
```

## 使用示例

### 纯文本消息
```
/telegram "测试消息：素材采集已完成"
```

### Markdown 格式
```
/telegram "*加粗文本* 和 _斜体文本_" --parse-mode markdown
```

### HTML 格式
```
/telegram "<b>加粗</b> 和 <a href='https://example.com'>链接</a>" --parse-mode html
```

### 多行消息
```
/telegram "第一行
第二行
第三行"
```

## 格式说明

### Markdown 格式
- `*加粗*` → **加粗**
- `_斜体_` → *斜体*
- `[链接](url)` → 超链接
- `` `代码` `` → `代码`

### HTML 格式
- `<b>加粗</b>` → **加粗**
- `<i>斜体</i>` → *斜体*
- `<a href="url">链接</a>` → 超链接
- `<code>代码</code>` → `代码`

## 注意事项

- Telegram 单条消息最多 4096 字符
- 如果消息过长，会被截断或发送失败
- Markdown/HTML 格式错误会导致发送失败
- 默认禁用网页预览，如需启用可修改 `disable_web_page_preview: False`

## 常见用途

1. **测试通知**：验证 Telegram Bot 配置是否正确
2. **临时通知**：手动发送重要消息（如部署完成、任务失败）
3. **调试消息格式**：测试 Markdown/HTML 格式是否正确
4. **发送采集摘要**：手动触发素材采集通知
