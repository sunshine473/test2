# 自动化内容工厂

半自动化内容生产系统 — 素材采集、选题推荐、LLM 写作、多平台一键分发。

**当前状态**: M1/M2/M3 已完成 ✅ 全链路可用

## 项目结构

```
├── src/
│   ├── collector/              # 素材采集 + 打分排序（✅ 已完成）
│   ├── generator/              # LLM 内容生成（✅ 已完成）
│   ├── publisher/              # 统一发布框架（✅ 已完成，4 平台可用）
│   ├── pipeline/               # 流水线调度（✅ 已完成）
│   ├── bot/                    # Telegram Bot 双向交互（✅ 已完成）
│   ├── config/                 # 信息源配置 + prompt 模板
│   ├── inspiration_bot/        # 旧版灵感采集（待替换）
│   └── wechat_publisher/       # 微信公众号发布（已迁移到 publisher/）
├── .claude/skills/             # Claude Skills 定义
├── content/                    # 内容仓库：pool → drafts → ready → published
├── MultiPost-Extension/        # 多平台分发浏览器扩展（30+ 平台）
├── docs/                       # 需求说明 + 开发计划
└── 参考/                       # 外部参考资料
```

## 核心 SOP

```
素材搜索（自动）→ 选题策划（按方向）→ 人工选题 → 内容生成（自动）→ 人工审核 → 发布分发（一键）
```

| Skill | 作用 |
|-------|------|
| `/search` | 采集素材 + 去重聚类，输出素材池 JSON |
| `/plan` | 从素材池按方向（AI科技/汽车）筛选打分，推荐选题 |
| `/collect` | 一键串联搜索 + 策划 |
| `/write "选题"` | 基于选题生成 Markdown 草稿 + 视觉卡片 |
| `/publish` | 统一发布到微信公众号 + B站/知乎/头条/小红书/懂车帝 |

## 快速开始

```bash
# 一键采集（搜索 + 两方向策划）
python src/collector/main.py

# 指定采集源
python src/collector/main.py --sources hn,github,hot
python src/collector/main.py --sources rss,tavily,hot
python src/collector/main.py --sources rss,hn,github,hot,tavily,youtube_api

# 仅搜索（输出素材池 JSON）
python src/collector/main.py --search-only
# 或
python src/collector/search.py

# 素材池 JSON 字段说明：每条 item 同时包含短摘要 `summary` 和主要内容摘录 `content`
# Pool JSON schema: each item includes both short summary `summary` and main-content excerpt `content`

# 仅策划（从素材池推荐选题）
python src/collector/main.py --plan-only --pool content/pool/<date>-pool.json
# 或
python src/collector/planner.py --pool content/pool/<date>-pool.json --direction tech_ai

# 内容生成（生成文章 + 卡片到 content/drafts/）
python src/generator/main.py "选题标题"

# 统一发布（发布到所有 enabled 平台）
python src/publisher/main.py content/drafts/<markdown文件>

# 指定平台发布
python src/publisher/main.py content/drafts/<markdown文件> --platforms wechat,bilibili

# 流水线调度（默认到 select 暂停）
python src/pipeline/main.py

# 全自动跑完
python src/pipeline/main.py --auto

# 恢复流水线
python src/pipeline/main.py --resume latest --topic "选题标题"
python src/pipeline/main.py --resume latest --approve

# 查看流水线状态
python src/pipeline/main.py --list
python src/pipeline/main.py --status --json

# MultiPost 扩展开发
cd MultiPost-Extension && pnpm dev
```

## 发布平台状态

| 平台 | 状态 | 实现方式 |
|------|------|----------|
| 微信公众号 | ✅ 生产可用 | API（access_token + 草稿箱接口） |
| 小红书 | ✅ 生产可用 | Playwright 自动化 |
| 知乎专栏 | ✅ 生产可用 | Playwright 自动化 |
| 懂车帝 | ✅ 生产可用 | Playwright 自动化（走头条号后台） |
| B站专栏 | ⚠️ 骨架实现 | bilibili-api-python 库 |
| 今日头条 | ⚠️ 骨架实现 | Playwright 自动化 |

## 环境配置

### 基础依赖
- Python 3 + 各模块 `requirements.txt` 依赖
- Node.js + pnpm（MultiPost 扩展开发）
- LLM API 密钥（Claude / Gemini / OpenAI）

### Notion 配置（数据中枢）

本项目使用 Notion 作为全流程数据管理中枢，需要配置 4 个数据库：

```bash
# 必需配置
NOTION_API_KEY=ntn_xxx                    # Notion Integration Token
NOTION_DATABASE_ID=xxx                    # 素材池数据库 ID

# 可选配置（启用完整数据中枢）
NOTION_TOPICS_DB_ID=xxx                   # 选题库数据库 ID
NOTION_DRAFTS_DB_ID=xxx                   # 草稿库数据库 ID
NOTION_PUBLISH_DB_ID=xxx                  # 发布记录数据库 ID
```

**配置指南**: 详见 [docs/notion-setup.md](docs/notion-setup.md)

**数据流**:
- 采集阶段 → 素材池数据库
- 策划阶段 → 选题库数据库
- 生成阶段 → 草稿库数据库
- 发布阶段 → 发布记录数据库

### 其他配置
- YouTube API 配置（启用 `youtube_api` 时）：`YOUTUBE_API_KEY`
- `.env` 文件配置敏感信息（不要提交到仓库）

## GitHub Actions 自动化

本项目支持 GitHub Actions 定时任务，实现全自动内容生产：

| 工作流 | 执行时间 | 功能 |
|--------|----------|------|
| `collect.yml` | 每天 8:00 | 素材采集 + Telegram 通知（Top 10） |
| `daily-collect.yml` | 每天 10:00 | 双方向素材采集（含 RSS/Tavily 汽车源） |
| `daily-pipeline.yml` | 每天 10:00 | 全自动流水线（采集→生成→发布） |
| `telegram-bot.yml` | 每 2 分钟 | Telegram Bot 轮询 |

`daily-pipeline.yml` 当前会尝试发布到 `wechat`、`zhihu`、`xiaohongshu`。微信公众号优先读取 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`，同时兼容旧的 `WECHAT_APPID` / `WECHAT_SECRET`；知乎和小红书依赖对应的 `ZHIHU_COOKIE` / `XIAOHONGSHU_COOKIE` Secrets，并在 GitHub Actions 中默认以 headless 模式运行。

**配置指南**: 详见 [docs/GitHub-Actions配置指南.md](docs/GitHub-Actions配置指南.md)

**快速测试**:
```bash
# Linux/Mac
./test-pipeline.sh

# Windows
test-pipeline.bat
```

## 测试

```bash
# 安装测试依赖
pip install -r tests/requirements.txt

# 运行全部测试（54 个用例）
PYTHONPATH=src pytest tests/ -v

# 运行特定模块测试
PYTHONPATH=src pytest tests/test_collector_*.py -v
PYTHONPATH=src pytest tests/test_bot_*.py -v
PYTHONPATH=src pytest tests/test_publisher_*.py -v

# 测试覆盖率
PYTHONPATH=src pytest tests/ --cov=src --cov-report=term-missing
```

## 协作

本项目由 Claude Code 和 Codex 协同开发，详见：
- [docs/需求说明.md](docs/需求说明.md) — 架构设计与 SOP
- [docs/开发计划.md](docs/开发计划.md) — 里程碑与任务认领
- [AGENTS.md](AGENTS.md) — 协作规范
- [CLAUDE.md](CLAUDE.md) — Claude Code 工作指引
