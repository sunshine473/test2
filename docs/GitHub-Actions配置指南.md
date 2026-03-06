# GitHub Actions 配置指南

## 概述

本项目配置了 3 个 GitHub Actions 工作流：

1. **collect.yml** - 每日 8:00 素材采集（仅采集+通知）
2. **telegram-bot.yml** - 每 2 分钟轮询 Telegram Bot
3. **daily-pipeline.yml** - 每日 10:00 全自动流水线（采集→生成→发布）✨ 新增

## 工作流详情

### 1. 定时素材采集（collect.yml）

**执行时间**: 每天北京时间 8:00（UTC 0:00）

**功能**:
- 采集多源素材（RSS、HN、GitHub、热搜、YouTube）
- 去重聚类
- 按方向（AI 科技/汽车）打分排序
- 发送 Telegram 通知（Top 10 新鲜内容）

**用途**: 早上提供素材推荐，供人工选题

---

### 2. Telegram Bot 轮询（telegram-bot.yml）

**执行时间**: 每 2 分钟

**功能**:
- 接收 Telegram 用户消息
- 调用 Claude API 处理
- 返回响应

**用途**: 支持 Telegram 双向交互

---

### 3. 每日全自动流水线（daily-pipeline.yml）✨ 新增

**执行时间**: 每天北京时间 10:00（UTC 2:00）

**功能**:
- 素材搜索（HN + GitHub + 热搜 + YouTube）
- 选题策划（AI 科技方向）
- 自动选择 Top 1 选题
- 生成文章（Markdown）
- 自动审核通过
- 发布到微信公众号草稿箱

**用途**: 全自动生成并发布内容，无需人工干预

**执行流程**:
```
8:00  → 素材采集（collect.yml）→ Telegram 通知
10:00 → 全自动流水线（daily-pipeline.yml）→ 生成+发布
```

---

## 必需的 GitHub Secrets

在 GitHub 仓库设置中配置以下 Secrets（Settings → Secrets and variables → Actions）：

### 采集器相关
```
NOTION_API_KEY          # Notion API 密钥
NOTION_DATABASE_ID      # Notion 数据库 ID
TAVILY_API_KEY          # Tavily 搜索 API
YOUTUBE_API_KEY         # YouTube Data API（同时也是 Google Cloud API Key）
TELEGRAM_BOT_TOKEN      # Telegram Bot Token
TELEGRAM_CHAT_ID        # Telegram 聊天 ID
```

### 生成器相关
```
ANTHROPIC_API_KEY       # Claude API 密钥
CLAUDE_MODEL            # Claude 模型名称（可选，默认 claude-sonnet-4-6）
GEMINI_API_KEY          # Gemini API 密钥（备用）
```

### 发布器相关
```
WECHAT_APPID            # 微信公众号 AppID
WECHAT_SECRET           # 微信公众号 Secret
BILIBILI_COOKIE         # B站 Cookie（可选）
ZHIHU_COOKIE            # 知乎 Cookie（可选）
TOUTIAO_COOKIE          # 头条 Cookie（可选）
XIAOHONGSHU_COOKIE      # 小红书 Cookie（可选）
DONGCHEDI_COOKIE        # 懂车帝 Cookie（可选）
```

---

## 配置步骤

### 1. 获取 API 密钥

#### Notion
1. 访问 https://www.notion.so/my-integrations
2. 创建新集成，获取 API Key
3. 在 Notion 数据库中添加集成权限

#### Tavily
1. 访问 https://tavily.com
2. 注册并获取 API Key

#### YouTube/Google Cloud
1. 访问 https://console.cloud.google.com
2. 启用 YouTube Data API v3
3. 创建 API 密钥

#### Telegram
1. 与 @BotFather 对话创建 Bot
2. 获取 Bot Token
3. 与 @userinfobot 对话获取 Chat ID

#### Claude API
1. 访问 https://console.anthropic.com
2. 创建 API Key

#### 微信公众号
1. 登录微信公众平台
2. 开发 → 基本配置 → 获取 AppID 和 AppSecret

### 2. 配置 GitHub Secrets

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 逐个添加上述 Secrets

### 3. 启用 GitHub Actions

1. 进入仓库 Actions 标签
2. 如果提示启用 Workflows，点击 "I understand my workflows, go ahead and enable them"

### 4. 手动测试

在 Actions 标签中，选择对应的 Workflow，点击 "Run workflow" 手动触发测试。

---

## 时间线规划

```
每天 8:00  → collect.yml 执行
           → 采集素材 + Telegram 通知（Top 10）
           → 用户可在 Telegram 中查看推荐

每天 10:00 → daily-pipeline.yml 执行
           → 自动选择 Top 1 选题
           → 生成文章
           → 发布到微信公众号草稿箱
           → 用户可在公众号后台审核发布
```

---

## 自定义配置

### 修改执行时间

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # UTC 2:00 = 北京时间 10:00
```

Cron 表达式格式：`分 时 日 月 周`

示例：
- `0 2 * * *` - 每天 UTC 2:00（北京时间 10:00）
- `0 6 * * *` - 每天 UTC 6:00（北京时间 14:00）
- `0 2 * * 1-5` - 每周一到周五 UTC 2:00

### 修改采集源

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
run: |
  python -m pipeline.main \
    --auto \
    --sources hn,github,hot,youtube \  # 修改这里
    --direction tech_ai \
    --platforms wechat
```

可选采集源：
- `hn` - Hacker News
- `github` - GitHub Trending
- `hot` - 热搜（微博/知乎/百度）
- `youtube` - YouTube 热门
- `rss` - RSS 订阅源

### 修改发布平台

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
--platforms wechat  # 修改为 wechat,bilibili,zhihu 等
```

可选平台：
- `wechat` - 微信公众号
- `bilibili` - B站
- `zhihu` - 知乎
- `toutiao` - 今日头条
- `xiaohongshu` - 小红书
- `dongchedi` - 懂车帝

### 禁用卡片生成

如果不需要生成视觉卡片（HTML），可以添加 `--no-cards` 参数：

```yaml
run: |
  python -m pipeline.main \
    --auto \
    --no-cards \  # 添加这行
    --sources hn,github,hot,youtube \
    --direction tech_ai \
    --platforms wechat
```

---

## 监控与调试

### 查看执行日志

1. 进入 Actions 标签
2. 选择对应的 Workflow Run
3. 查看详细日志

### 下载产物

每次执行会上传以下产物（保留 7 天）：
- 素材池 JSON（`content/pool/*.json`）
- 生成的草稿（`content/drafts/*.md`）
- 视觉卡片（`content/drafts/*.html`）
- 流水线状态（`.pipeline/*.json`）

### 失败通知

如果流水线执行失败，会自动发送 Telegram 通知。

---

## 常见问题

### Q: 为什么 Actions 没有执行？

A: 检查以下几点：
1. GitHub Actions 是否已启用
2. Secrets 是否配置完整
3. 仓库是否为 Public（Private 仓库需要付费）
4. Cron 时间是否正确（注意时区）

### Q: 如何暂停自动执行？

A: 进入 Actions 标签，选择对应的 Workflow，点击右上角的 "..." → "Disable workflow"

### Q: 如何修改自动选题逻辑？

A: 当前默认选择 Top 1 选题。如需修改，编辑 `src/pipeline/main.py` 中的 `_run_select()` 方法。

### Q: 如何查看流水线状态？

A: 本地运行：
```bash
python src/pipeline/main.py --status
python src/pipeline/main.py --list
```

---

## 成本估算

### API 调用成本（每日）

- **Tavily API**: 约 10 次搜索 = $0.10
- **Claude API**: 1 篇文章生成 = $0.50
- **YouTube API**: 约 50 次查询 = $0（免费额度内）
- **微信公众号 API**: 免费

**总计**: 约 $0.60/天 = $18/月

### GitHub Actions 成本

- Public 仓库：免费
- Private 仓库：每月 2000 分钟免费，超出部分 $0.008/分钟

---

## 下一步优化

1. **多选题支持**: 每天生成 3 篇文章而不是 1 篇
2. **智能选题**: 基于历史数据和用户反馈优化选题算法
3. **A/B 测试**: 同时生成多个版本，选择最佳版本发布
4. **定时发布**: 不仅生成草稿，还自动定时发布
5. **数据分析**: 收集阅读量、点赞数等数据，反馈到选题系统

---

## 总结

通过 GitHub Actions，你已经实现了：
- ✅ 每日 8:00 自动采集素材并推送 Telegram 通知
- ✅ 每日 10:00 全自动生成并发布内容
- ✅ 全流程无需人工干预（可选人工审核）
- ✅ 失败自动通知
- ✅ 产物自动归档

现在你的内容工厂已经实现了真正的自动化！🎉
