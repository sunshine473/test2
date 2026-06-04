# 全自动化内容工厂

全自动化内容生产系统 — AI 自动选题、智能生成、质量审核、多平台一键分发。

**当前状态**: ✅ 全自动模式已验证成功（2026-03-18）
- AI 自动选题（Claude 5 维度评估）
- AI 自动生成（Gemini 8,578 字长文）
- AI 自动审核（6 维度评分 90/100）
- 全链路可用，支持批量生产

**验证报告**: [docs/全自动内容工厂验证报告.md](docs/全自动内容工厂验证报告.md)

## 项目结构

```
├── src/
│   ├── collector/              # 素材采集 + 打分排序（✅ 已完成）
│   ├── normalizer/             # 整理层：清洗、去重聚类、素材池建模（✅ 新增骨架）
│   ├── generator/              # LLM 内容生成（✅ 已完成）
│   ├── packager/               # 包装层：草稿解析、平台发布包生成（✅ 新增骨架）
│   ├── publisher/              # 统一发布框架（✅ 已完成，4 平台可用）
│   ├── pipeline/               # 流水线调度（✅ 已完成）
│   ├── bot/                    # Telegram Bot 双向交互（✅ 已完成）
│   ├── models/                 # 六层数据契约 dataclass（✅ 新增）
│   ├── schemas/                # 契约对应 JSON Schema（✅ 新增）
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

**全自动模式**（`--auto`）：
```
采集/整理（自动）→ 选题策划（按方向）→ AI选题（自动）→ 内容生成（自动）→ AI审核（自动）→ 包装/发布（一键）
```

**半自动模式**（默认）：
```
采集/整理（自动）→ 选题策划（按方向）→ 人工选题 → 内容生成（自动）→ 人工审核 → 包装/发布（一键）
```

| Skill | 作用 |
|-------|------|
| `/factory --auto` | 全自动流水线（AI 选题 + AI 审核） |
| `/batch-factory` | 批量生产（默认 4 篇：2 篇 AI + 2 篇汽车） |
| `/search` | 采集素材 + 去重聚类，输出素材池 JSON |
| `/plan` | 从素材池按方向（AI科技/汽车）筛选打分，推荐选题 |
| `/collect` | 一键串联搜索 + 策划 |
| `/write "选题"` | 基于选题生成 Markdown 草稿 + 视觉卡片 |
| `/publish` | 统一发布到微信公众号 + B站/知乎/头条/小红书/懂车帝 |

## 快速开始

### 全自动模式（推荐）

```bash
# 单篇文章全自动生产（AI 选题 + AI 审核）
python src/pipeline/main.py --auto --direction tech_ai

# 批量生产（默认 4 篇：2 篇 AI + 2 篇汽车）
python src/pipeline/batch_pipeline.py

# 指定数量和平台
python src/pipeline/batch_pipeline.py --count 2 --platforms dongchedi
```

### 半自动模式

```bash
# 一键采集（搜索 + 两方向策划）
python src/collector/main.py

# 指定采集源
python src/collector/main.py --sources follow_builders,github,hot,tavily
python src/collector/main.py --sources hn,github,hot
python src/collector/main.py --sources rss,tavily,hot
python src/collector/main.py --sources follow_builders,rss,github,hot,tavily,youtube_api

# 仅搜索（输出素材池 JSON）
python src/collector/main.py --search-only
# 或
python src/collector/search.py

# 整理层由 search 内部调用，也可单独复用 `src/normalizer/`
# Packaging is now handled by `src/packager/` before publisher adapters run

# 素材池 JSON 字段说明：每条 item 同时包含短摘要 `summary` 和主要内容摘录 `content`
# Pool JSON schema: each item includes both short summary `summary` and main-content excerpt `content`
# 汽车方向会硬过滤无发布时间或 7 天外素材，避免旧销量/旧政策进入文章主线

# 仅策划（从素材池推荐选题）
python src/collector/main.py --plan-only --pool content/pool/<date>-pool.json
# 或
python src/collector/planner.py --pool content/pool/<date>-pool.json --direction tech_ai --recommend

# 内容生成（生成文章 + 卡片到 content/drafts/）
python src/generator/main.py "选题标题"
python src/generator/main.py "汽车选题标题" --direction auto

# AI 质量审核（6 维度评分，≥70 分通过）
python src/reviewer/quality_checker.py content/drafts/<markdown文件>

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
python src/pipeline/main.py --resume latest --rewrite

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
| 懂车帝 | ✅ 生产可用 | Playwright 自动化（走懂车号后台） |
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
- 每日 AI 素材默认使用 `follow_builders`，优先读取 `follow-builders/feed-*.json`，本地缺失时回退到远端 feed
- YouTube API 配置（启用 `youtube_api` 时）：`YOUTUBE_API_KEY`
- `.env` 文件配置敏感信息（不要提交到仓库）

## GitHub Actions 自动化

本项目当前仅保留一条 GitHub Actions 工作流，对应批量工厂完整流程：

| 工作流 | 执行时间 | 功能 |
|--------|----------|------|
| `batch-factory.yml` | 每天 10:00 | 批量工厂（一次采集 → 双方向选题 → 批量生成 → 多平台发布） |

`batch-factory.yml` 直接执行 `python src/pipeline/batch_pipeline.py`，默认每个方向生成 2 篇，发布到 `dongchedi`，默认采集源为 `follow_builders,github,hot,tavily`。手动触发时可覆盖 `count`、`platforms`、`sources`、`no_cards` 四个输入参数。

默认云端发布只需要配置 `DONGCHEDI_COOKIE`；如果手动把平台切到 `wechat`、`bilibili`、`toutiao`、`zhihu`、`xiaohongshu`，需要提前配置对应 Secrets。浏览器平台在 GitHub Actions 中默认以 headless 模式运行。

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
- [docs/内容流水线数据契约.md](docs/内容流水线数据契约.md) — 各阶段输入输出契约
- [docs/六层架构映射说明.md](docs/六层架构映射说明.md) — 六层架构与当前仓库映射
- [docs/6层改造草案.md](docs/6层改造草案.md) — 六层重构顺序与落地建议
- [AGENTS.md](AGENTS.md) — 协作规范
- [CLAUDE.md](CLAUDE.md) — Claude Code 工作指引
