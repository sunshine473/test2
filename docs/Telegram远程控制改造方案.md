# Telegram 远程控制改造方案

改造时间：2026-03-07

---

## 改造目标

将 Telegram 从单向通知升级为**双向交互控制端**，在关键环节加入人工确认，实现远程控制整个内容生产流程。

---

## 核心改造点

### 1. 流程改造：全自动 → 分阶段 + 人工确认

#### 改造前（全自动）
```
GitHub Actions 每日 10:00 自动执行
  ↓
采集 → 策划 → 自动选题 → 生成草稿 → 自动审核 → 发布
  ↓
Telegram 被动接收通知
```

**问题**：
- 无人工介入，质量难以保证
- 只采集 AI 科技方向，缺少汽车内容
- Telegram 只能看，不能控制

#### 改造后（分阶段 + 交互）
```
GitHub Actions 每日 10:00 自动采集（两方向）
  ↓
Telegram 发送交互式通知（带按钮）
  ↓
用户通过 Telegram 远程控制：
  - 查看各方向 Top10
  - 选择方向和选题
  - 触发写作
  - 审核草稿
  - 确认发布
```

**优势**：
- ✅ 人工确认关键环节
- ✅ 两个方向都采集（AI 科技 + 汽车）
- ✅ Telegram 成为远程控制中心
- ✅ 随时随地通过手机操作

---

## 详细改造内容

### 1. GitHub Actions 改造

#### 新增：`daily-collect.yml`（替代 `collect.yml`）
```yaml
name: 每日素材采集（两方向）

on:
  schedule:
    - cron: '0 2 * * *'  # UTC 2:00 = 北京时间 10:00

jobs:
  collect:
    steps:
      - name: Run collector (两方向都采集)
        run: |
          # 不指定 --direction，默认跑 tech_ai 和 auto 两个方向
          python -m collector.main --sources hn,github,hot,youtube_api
```

**改动**：
- ✅ 移除 `--direction tech_ai` 限制
- ✅ 两个方向都采集和策划
- ✅ 采集完成后自动发送交互式 Telegram 通知

#### 修改：`daily-pipeline.yml`
**建议**：删除或改为手动触发，不再自动执行全流程

---

### 2. Telegram 通知改造

#### 新增：`telegram_notifier_interactive.py`

**核心功能**：
1. 发送带按钮的通知消息
2. 支持查看各方向详情
3. 支持快速操作（开始写作、查看素材池等）

**消息格式**：
```
📊 素材采集完成 — 2026-03-07

🧠 今日总结
- 采集 150 条，去重后 80 条，共 45 个话题簇

📌 分方向推荐

🎯 AI 科技: 候选 45 条，24h 新鲜 12 条，均分 72.5
  1. OpenAI 发布 GPT-5 预览版 ⭐95.2
  2. Claude 3.5 Sonnet 新增代码执行 ⭐88.3
  3. Anthropic 拒绝被列为供应链风险 ⭐85.1

🚗 汽车: 候选 35 条，24h 新鲜 8 条，均分 68.2
  1. 比亚迪 2 月销量突破 30 万辆 ⭐82.5
  2. 特斯拉 FSD 进入中国市场 ⭐79.8
  3. 小米汽车交付量破万 ⭐75.3

👇 点击下方按钮进行操作

[🎯 查看 AI 科技 Top10] [🚗 查看汽车 Top10]
[✍️ 开始写作]           [📦 查看素材池]
```

**按钮功能**：
- `查看 AI 科技 Top10`：展开显示 AI 科技方向的详细 Top10 列表（含 URL、摘要）
- `查看汽车 Top10`：展开显示汽车方向的详细 Top10 列表
- `开始写作`：进入写作流程，选择方向和选题
- `查看素材池`：查看素材池概况

---

### 3. Bot 回调处理

#### 新增：`callback_handler.py`

**支持的回调操作**：

| 回调 | 功能 | 说明 |
|------|------|------|
| `view_tech_ai` | 查看 AI 科技 Top10 | 展开显示详细列表（标题、评分、来源、时间、摘要、URL） |
| `view_auto` | 查看汽车 Top10 | 同上 |
| `start_write` | 开始写作 | 让用户选择方向（AI 科技 / 汽车） |
| `write_tech_ai` | 选择 AI 科技方向 | 显示该方向 Top5 供选择 |
| `write_auto` | 选择汽车方向 | 显示该方向 Top5 供选择 |
| `check_pool` | 查看素材池 | 显示素材池日期、条数、路径 |
| `back_to_summary` | 返回总结 | 返回采集通知消息 |

**交互流程示例**：
```
1. 用户点击 [开始写作]
   ↓
2. Bot 回复：请选择要写作的方向
   [🎯 AI 科技] [🚗 汽车]
   ↓
3. 用户点击 [🎯 AI 科技]
   ↓
4. Bot 回复：📝 AI 科技 Top5 选题
   请回复选题编号（1-5）或直接输入选题标题：
   1. OpenAI 发布 GPT-5 预览版 ⭐95.2
   2. Claude 3.5 Sonnet 新增代码执行 ⭐88.3
   ...
   ↓
5. 用户回复：1
   ↓
6. Bot 调用 write 工具生成草稿
   ↓
7. Bot 回复：草稿已生成，请审核...
```

---

### 4. Bot 主循环改造

#### 修改：`bot/main.py`

**新增功能**：
- ✅ 支持处理回调查询（callback_query）
- ✅ 区分普通消息和按钮点击
- ✅ 统一的授权检查

**代码逻辑**：
```python
for update in updates:
    # 处理普通消息
    if "message" in update:
        handle_text_message(update["message"])

    # 处理回调查询（按钮点击）
    if "callback_query" in update:
        handle_callback_query(update["callback_query"])
```

---

## 使用流程

### 每日自动采集
1. GitHub Actions 每天 10:00 自动执行采集
2. 采集完成后，Telegram 收到交互式通知
3. 通知包含两个方向的 Top3 摘要 + 操作按钮

### 远程查看详情
1. 点击 `[查看 AI 科技 Top10]` 或 `[查看汽车 Top10]`
2. Bot 展开显示该方向的详细 Top10 列表
3. 每条包含：标题、评分、来源、时间、摘要、URL

### 远程触发写作
1. 点击 `[开始写作]`
2. 选择方向（AI 科技 / 汽车）
3. Bot 显示该方向 Top5 选题
4. 回复选题编号（1-5）或直接输入选题标题
5. Bot 调用 Claude 生成草稿
6. 草稿生成完成后，Bot 发送通知

### 远程审核发布
1. 收到草稿生成通知后，点击查看草稿
2. 通过 Telegram 发送命令：`发布 <文件名>`
3. Bot 调用发布工具，发布到各平台
4. 发布完成后，Bot 发送结果通知

---

## 技术实现

### 1. 内联键盘（Inline Keyboard）
```python
buttons = [
    [
        {"text": "🎯 查看 AI 科技 Top10", "callback_data": "view_tech_ai"},
        {"text": "🚗 查看汽车 Top10", "callback_data": "view_auto"},
    ],
    [
        {"text": "✍️ 开始写作", "callback_data": "start_write"},
        {"text": "📦 查看素材池", "callback_data": "check_pool"},
    ]
]

payload = {
    "chat_id": chat_id,
    "text": message_text,
    "reply_markup": {"inline_keyboard": buttons}
}
```

### 2. 回调查询处理
```python
def handle_callback(callback_query: dict):
    callback_id = callback_query["id"]
    data = callback_query["data"]  # 例如 "view_tech_ai"

    # 先应答回调（避免 Telegram 显示加载中）
    answer_callback_query(callback_id)

    # 根据 data 执行不同操作
    if data == "view_tech_ai":
        send_tech_ai_detail()
    elif data == "start_write":
        send_write_options()
    ...
```

### 3. 新鲜度筛选优化
```python
def _is_fresh(published_at: str, hours: int = 24) -> bool:
    if not published_at:
        # GitHub Trending 等没有 published_at 的内容视为新鲜
        return True
    # ... 时间判断逻辑
```

**改进**：
- ✅ 没有 `published_at` 的内容（如 GitHub Trending）视为新鲜
- ✅ 解析失败也视为新鲜（宽松策略）
- ✅ 避免过度过滤

---

## 文件清单

### 新增文件
- `.github/workflows/daily-collect.yml` — 每日采集工作流（两方向）
- `src/collector/telegram_notifier_interactive.py` — 交互式通知器
- `src/bot/callback_handler.py` — 回调查询处理器

### 修改文件
- `src/bot/main.py` — 支持回调查询处理
- `src/collector/main.py` — 使用交互式通知器

### 待删除/废弃文件
- `.github/workflows/daily-pipeline.yml` — 全自动流水线（建议删除或改为手动触发）
- `.github/workflows/collect.yml` — 旧版采集工作流（被 `daily-collect.yml` 替代）

---

## 配置要求

### 环境变量（无需新增）
所有环境变量保持不变，无需额外配置：
- `TELEGRAM_BOT_TOKEN` — Telegram Bot Token
- `TELEGRAM_CHAT_ID` — 接收消息的 Chat ID
- `CLAUDE_API_KEY` / `GEMINI_API_KEY` — AI API Key
- `TAVILY_API_KEY` / `YOUTUBE_API_KEY` 等 — 采集源 API Key

### GitHub Secrets
确保以下 Secrets 已配置：
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CLAUDE_API_KEY` 或 `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `YOUTUBE_API_KEY`
- `NOTION_API_KEY` / `NOTION_DATABASE_ID`（可选）

---

## 测试验证

### 1. 测试采集通知
```bash
# 本地测试
cd src
python -m collector.main --sources hn,github
```

**预期结果**：
- ✅ 采集两个方向的素材
- ✅ Telegram 收到带按钮的通知
- ✅ 通知包含两个方向的 Top3 摘要

### 2. 测试按钮交互
1. 点击 `[查看 AI 科技 Top10]`
   - ✅ 展开显示详细 Top10 列表
   - ✅ 包含 URL、摘要等完整信息
2. 点击 `[开始写作]`
   - ✅ 显示方向选择按钮
3. 点击 `[🎯 AI 科技]`
   - ✅ 显示该方向 Top5 选题

### 3. 测试写作流程
1. 回复选题编号：`1`
2. Bot 调用 write 工具
3. 草稿生成完成后收到通知

---

## 后续优化建议

### 1. 草稿审核交互
在草稿生成后，发送带按钮的通知：
```
✅ 草稿已生成

标题：OpenAI 发布 GPT-5 预览版
路径：content/drafts/2026-03-07-openai-gpt5.md

[📖 查看草稿] [✅ 通过审核] [❌ 重新生成]
```

### 2. 发布确认交互
在发布前，发送确认消息：
```
📤 准备发布

标题：OpenAI 发布 GPT-5 预览版
平台：微信公众号、知乎、B站

[✅ 确认发布] [❌ 取消]
```

### 3. 定时提醒
如果采集完成后 2 小时内没有操作，发送提醒：
```
⏰ 提醒：今日素材已采集完成，还未选题

[查看素材] [开始写作]
```

### 4. 多人协作
支持多个 Chat ID，实现团队协作：
- 采集通知发送给所有人
- 任何人都可以触发写作
- 草稿审核需要指定审核人确认

---

## 总结

本次改造实现了：
- ✅ Telegram 从单向通知升级为双向交互控制端
- ✅ 两个方向都采集（AI 科技 + 汽车）
- ✅ 关键环节加入人工确认
- ✅ 支持远程查看详情、选题、写作、审核、发布
- ✅ 新鲜度筛选优化，避免过度过滤

用户现在可以通过 Telegram 随时随地远程控制整个内容生产流程，实现真正的移动办公。
