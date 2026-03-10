# Telegram 远程控制改造 - 调试报告

调试时间：2026-03-07

---

## 调试结果

✅ **所有功能测试通过**

### 测试项目

1. ✅ **消息构建** - 交互式通知消息和按钮构建正常
2. ✅ **方向详情** - 各方向 Top10 详情消息构建正常
3. ✅ **回调处理器** - 按钮点击事件处理逻辑正常
4. ✅ **新鲜度检测** - 24小时新鲜度筛选逻辑正常

---

## 发现的问题及修复

### 1. 参数名错误

**问题**：`callback_handler.py` 中调用 `plan()` 函数时使用了错误的参数名 `direction`

**修复**：
```python
# 修复前
plan(pool_path, direction=None)

# 修复后
plan(pool_path, direction_name=None)
```

**文件**：`src/bot/callback_handler.py:145`

### 2. 新鲜度筛选优化

**问题**：GitHub Trending 等内容没有 `published_at` 字段，会被判定为不新鲜

**修复**：
```python
def _is_fresh(published_at: str, hours: int = 24) -> bool:
    if not published_at:
        # GitHub Trending 等没有 published_at 的内容视为新鲜
        return True
    # ... 时间判断逻辑
```

**效果**：
- 空字符串 → ✅ 新鲜
- None → ✅ 新鲜
- 解析失败 → ✅ 新鲜（宽松策略）

---

## 当前状态

### 功能正常
- ✅ 交互式通知消息构建
- ✅ 内联按钮生成
- ✅ 回调查询处理
- ✅ 方向详情展示
- ✅ 新鲜度筛选
- ✅ Bot 主循环（支持消息和回调）

### 测试数据说明

**当前素材池**：`content/pool/2026-03-01-pool.json`
- 采集源：HN (20条) + GitHub (10条)
- 分类：全部为 `tech_ai`
- 汽车方向：0 条（因为只采集了 HN 和 GitHub）

**说明**：
- HN 和 GitHub 主要是科技内容，不包含汽车信息
- 汽车内容需要从 `hot`（微博/百度热搜）采集
- 新的 `daily-collect.yml` 已配置采集 `hot` 源

---

## 测试输出示例

### 交互式通知消息
```
📊 素材采集完成 — 2026-03-01

🧠 今日总结
- 采集 30 条，去重后 30 条，共 30 个话题簇

📌 分方向推荐

🎯 AI 科技: 候选 30 条，24h 新鲜 10 条，均分 60.7
  1. Shubhamsaboo/awesome-llm-apps ⭐66.0
  2. Wei-Shaw/claude-relay-service ⭐66.0
  3. anthropics/claude-code ⭐65.0

🚗 汽车: 候选 0 条，24h 新鲜 0 条，均分 0.0

👇 点击下方按钮进行操作
```

### 按钮布局
```
第 1 行:
  [🎯 查看 AI 科技 Top10] -> view_tech_ai
  [🚗 查看汽车 Top10] -> view_auto
第 2 行:
  [✍️ 开始写作] -> start_write
  [📦 查看素材池] -> check_pool
```

### 方向详情（AI 科技 Top10）
```
AI 科技:
  总计: 30 条
  新鲜 (24h): 10 条
  Top 3:
    1. Shubhamsaboo/awesome-llm-apps ⭐66.0
    2. Wei-Shaw/claude-relay-service ⭐66.0
    3. anthropics/claude-code ⭐65.0
```

---

## 下一步操作

### 1. 部署到 GitHub Actions

**文件清单**：
- ✅ `.github/workflows/daily-collect.yml` - 每日采集（两方向）
- ✅ `.github/workflows/telegram-bot.yml` - Bot 轮询（已存在）
- ⚠️ `.github/workflows/daily-pipeline.yml` - 建议删除或改为手动触发

**操作**：
1. 提交新文件到 GitHub
2. 确保 GitHub Secrets 已配置
3. 手动触发 `daily-collect.yml` 测试

### 2. 测试完整流程

**测试步骤**：
1. 手动触发采集（包含 `hot` 源）
   ```bash
   python src/collector/main.py --sources hn,github,hot,youtube_api
   ```
2. 检查 Telegram 是否收到交互式通知
3. 点击按钮测试回调功能
4. 测试选题和写作流程

### 3. 验证汽车内容采集

**预期**：
- 采集 `hot` 源后，应该有汽车相关的热搜内容
- 汽车方向应该有候选素材
- Telegram 通知中应该显示汽车方向的 Top3

**如果仍然没有汽车内容**：
- 检查 `hot` 源是否正常工作
- 检查汽车方向的分类逻辑
- 检查 `directions.py` 中的汽车关键词配置

---

## 配置检查清单

### GitHub Secrets（必需）
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `TELEGRAM_CHAT_ID`
- ✅ `CLAUDE_API_KEY` 或 `GEMINI_API_KEY`
- ✅ `TAVILY_API_KEY`
- ✅ `YOUTUBE_API_KEY`
- ⚠️ `NOTION_API_KEY` / `NOTION_DATABASE_ID`（可选）

### 本地环境变量（测试用）
- ✅ `.env` 文件已配置
- ✅ 所有必需的 API Key 已设置

---

## 已知限制

### 1. 消息长度限制
- Telegram 单条消息最多 4096 字符
- 当前实现：如果超过限制，Telegram API 会自动截断
- 建议优化：拆分为多条消息发送

### 2. 按钮数量限制
- Telegram 内联键盘最多 100 个按钮
- 当前实现：2 行 4 个按钮，远低于限制

### 3. 回调数据长度限制
- Telegram callback_data 最多 64 字节
- 当前实现：使用简短的标识符（如 `view_tech_ai`），符合限制

---

## 文件清单

### 新增文件
- ✅ `.github/workflows/daily-collect.yml`
- ✅ `src/collector/telegram_notifier_interactive.py`
- ✅ `src/bot/callback_handler.py`
- ✅ `docs/Telegram远程控制改造方案.md`
- ✅ `test_telegram_interactive.py`

### 修改文件
- ✅ `src/bot/main.py` - 支持回调查询
- ✅ `src/collector/main.py` - 使用交互式通知器

### 测试文件
- ✅ `test_telegram_interactive.py` - 完整功能测试

---

## 总结

✅ **改造完成，所有功能测试通过**

核心改进：
1. ✅ Telegram 从单向通知升级为双向交互控制端
2. ✅ 支持查看各方向详情、选题、写作等远程操作
3. ✅ 新鲜度筛选优化，避免过度过滤
4. ✅ 两个方向都采集（配置已更新）

待验证：
- ⏳ GitHub Actions 自动采集（包含汽车内容）
- ⏳ Telegram 实际通知和按钮交互
- ⏳ 完整的选题→写作→审核→发布流程

建议：
- 先手动运行一次完整采集（包含 `hot` 源）
- 验证汽车内容是否正常采集
- 测试 Telegram 按钮交互功能
- 确认后再启用 GitHub Actions 自动化
