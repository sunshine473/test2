# 全链路测试与 GitHub Actions 配置总结

## 测试结果 ✅

### 本地流水线测试

**执行命令**:
```bash
python src/pipeline/main.py --auto --sources hn,github --direction tech_ai --no-cards
```

**执行结果**:
- ✅ 流水线 ID: `2026-03-01-111322`
- ✅ 状态: `completed`
- ✅ 阶段: `publish`
- ✅ 选题: "We do not think Anthropic should be designated as a supply chain risk"
- ✅ 草稿: `content/drafts/2026-03-01-We-do-not-think-Anthropic-should-be-designated-as-a-supply-c.md`
- ✅ 发布: 1 个平台（微信公众号）

**流程验证**:
1. ✅ 素材搜索（HN + GitHub）
2. ✅ 选题策划（AI 科技方向）
3. ✅ 自动选题（Top 1）
4. ✅ 内容生成（Markdown 文章）
5. ✅ 自动审核通过
6. ✅ 发布到微信公众号

**结论**: 完整链路已跑通，所有阶段正常工作！

---

## GitHub Actions 配置 ✅

### 新增文件

1. **`.github/workflows/daily-pipeline.yml`** - 每日 10 点全自动流水线
2. **`docs/GitHub-Actions配置指南.md`** - 详细配置文档
3. **`test-pipeline.sh`** - Linux/Mac 本地测试脚本
4. **`test-pipeline.bat`** - Windows 本地测试脚本

### 工作流配置

#### 1. 每日全自动流水线（daily-pipeline.yml）

**执行时间**: 每天北京时间 10:00（UTC 2:00）

**功能**:
- 素材搜索（HN + GitHub + 热搜 + YouTube）
- 选题策划（AI 科技方向）
- 自动选择 Top 1 选题
- 生成文章（Markdown）
- 自动审核通过
- 发布到微信公众号草稿箱

**特性**:
- ✅ 全自动执行，无需人工干预
- ✅ 失败自动发送 Telegram 通知
- ✅ 产物自动上传（保留 7 天）
- ✅ 支持手动触发（workflow_dispatch）

#### 2. 定时素材采集（collect.yml）

**执行时间**: 每天北京时间 8:00（UTC 0:00）

**功能**:
- 采集多源素材
- 去重聚类
- 按方向打分排序
- 发送 Telegram 通知（Top 10 新鲜内容）

#### 3. Telegram Bot 轮询（telegram-bot.yml）

**执行时间**: 每 2 分钟

**功能**:
- 接收 Telegram 用户消息
- 调用 Claude API 处理
- 返回响应

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

## 必需的 GitHub Secrets

在 GitHub 仓库设置中配置以下 Secrets（Settings → Secrets and variables → Actions）：

### 采集器相关
```
NOTION_API_KEY          # Notion API 密钥
NOTION_DATABASE_ID      # Notion 数据库 ID
TAVILY_API_KEY          # Tavily 搜索 API
YOUTUBE_API_KEY         # YouTube Data API
TELEGRAM_BOT_TOKEN      # Telegram Bot Token
TELEGRAM_CHAT_ID        # Telegram 聊天 ID
```

### 生成器相关
```
ANTHROPIC_API_KEY       # Claude API 密钥
CLAUDE_MODEL            # Claude 模型名称（可选）
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

## 下一步操作

### 1. 配置 GitHub Secrets

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 逐个添加上述 Secrets

### 2. 启用 GitHub Actions

1. 进入仓库 Actions 标签
2. 如果提示启用 Workflows，点击 "I understand my workflows, go ahead and enable them"

### 3. 手动测试

在 Actions 标签中，选择 "每日全自动内容流水线"，点击 "Run workflow" 手动触发测试。

### 4. 监控执行

- 查看执行日志：Actions → 选择 Workflow Run → 查看详细日志
- 下载产物：Actions → 选择 Workflow Run → Artifacts
- 失败通知：自动发送到 Telegram

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

## 自定义配置

### 修改执行时间

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # UTC 2:00 = 北京时间 10:00
```

Cron 表达式示例：
- `0 2 * * *` - 每天 UTC 2:00（北京时间 10:00）
- `0 6 * * *` - 每天 UTC 6:00（北京时间 14:00）
- `0 2 * * 1-5` - 每周一到周五 UTC 2:00

### 修改采集源

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
--sources hn,github,hot,youtube  # 修改这里
```

可选采集源：`hn`, `github`, `hot`, `youtube`, `rss`

### 修改发布平台

编辑 `.github/workflows/daily-pipeline.yml`：

```yaml
--platforms wechat  # 修改为 wechat,bilibili,zhihu 等
```

可选平台：`wechat`, `bilibili`, `zhihu`, `toutiao`, `xiaohongshu`, `dongchedi`

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

### Q: 如何查看流水线状态？

A: 本地运行：
```bash
python src/pipeline/main.py --status
python src/pipeline/main.py --list
```

---

## 总结

通过本次配置，你已经实现了：

- ✅ 完整链路测试通过（采集→生成→发布）
- ✅ GitHub Actions 每日 10 点自动执行
- ✅ 全流程无需人工干预（可选人工审核）
- ✅ 失败自动通知
- ✅ 产物自动归档
- ✅ 本地测试脚本（test-pipeline.sh / test-pipeline.bat）
- ✅ 详细配置文档（GitHub-Actions配置指南.md）

现在你的内容工厂已经实现了真正的自动化！🎉

**下一步**: 将代码推送到 GitHub，配置 Secrets，启用 Actions，等待明天 10 点自动执行。
