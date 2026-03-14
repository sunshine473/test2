# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

半自动化内容工厂 — 从素材采集、选题推荐、内容生成到多平台分发的全流程系统。

**Current Status**: M1/M2/M3 完成 ✅ 全链路可用

## Architecture

### Content Pipeline (SOP)

```
素材搜索 → 选题策划 → 人工选题 → 内容生成 → 人工审核 → 发布分发
(自动)    (按方向)    (★卡点)    (自动)      (★卡点)    (一键)
```

### Notion 数据中枢

使用 Notion 作为全流程数据管理中枢，4 个核心数据库：

1. **素材池数据库** (`NOTION_DATABASE_ID`)
   - 存储采集的原始素材
   - 字段：标题、URL、来源、分类、摘要、评分、方向、状态等
   - 状态流转：待筛选 → 已推荐 → 已选用

2. **选题库数据库** (`NOTION_TOPICS_DB_ID`)
   - 存储 AI 推荐的选题
   - 字段：选题标题、方向、评分、推荐理由、关联素材、状态等
   - 状态流转：待选择 → 已选中 → 已生成 → 已发布

3. **草稿库数据库** (`NOTION_DRAFTS_DB_ID`)
   - 存储生成的文章草稿
   - 字段：文章标题、文件路径、字数、质量评级、标签、摘要、状态等
   - 状态流转：待审核 → 审核通过 → 已发布

4. **发布记录数据库** (`NOTION_PUBLISH_DB_ID`)
   - 记录多平台发布结果
   - 字段：标题、平台、状态、发布链接、发布消息、发布日期等

**数据流**：
```
采集 → 素材池 [状态: 待筛选]
策划 → 选题库 [状态: 待选择] + 更新素材池 [状态: 已推荐]
生成 → 草稿库 [状态: 待审核] + 更新选题库 [状态: 已生成]
发布 → 发布记录 + 更新草稿库 [状态: 已发布]
```

配置详见 `docs/notion-setup.md`

### Two-Phase Collection Design

**Phase 1: Search** (`src/collector/search.py`)
- 多源采集（RSS, HN, GitHub, Tavily, YouTube API）
- 去重聚类（`dedup.py`）
- 输出素材池 JSON 到 `content/pool/`

**Phase 2: Plan** (`src/collector/planner.py`)
- 按方向筛选（AI科技 / 汽车）
- LLM 打分排序（`scorer.py`）
- AI 推荐 3-5 个选题（`--recommend` 参数）

### Publisher Registry Pattern

`src/publisher/` 使用注册表模式：
- 各平台适配器继承 `base.PublisherBase`
- 用 `@register` 装饰器注册到 `registry.py`
- `main.py` 通过 `get_publisher(name)` 动态加载

新增平台：创建 `platforms/<name>.py` → 继承 `PublisherBase` → 用 `@register` 装饰

浏览器平台（知乎 / 小红书 / 懂车帝 / 头条）在 CI 中默认以 headless 运行，可通过 `<PLATFORM>_COOKIE` 环境变量注入登录态；微信公众号发布器同时兼容 `WECHAT_APP_ID/WECHAT_APP_SECRET` 与旧的 `WECHAT_APPID/WECHAT_SECRET`。

### Skills Design Principle

**Skills = 薄层调度器**，不是执行引擎：
1. 解析用户参数
2. 调用 Python 脚本
3. 格式化输出

❌ 不要在 SKILL.md 中写复杂逻辑、判断、循环
✅ 把逻辑移到 Python 脚本，Skill 只负责调度

**重要约束**：
- Skills 必须放在 `.claude/skills/<name>/SKILL.md`（不是项目根目录的 `skills/`）
- 必须包含 YAML frontmatter（description、user-invocable、allowed-tools、argument-hint）

## Key Commands

### Quick Start (推荐使用 Skills)

```bash
# 全链路工厂（推荐）
/factory                              # 半自动模式（默认在选题和审核暂停）
/factory --auto                       # 全自动模式
/factory --direction tech_ai          # 指定内容方向
/factory --resume latest --topic "选题"  # 恢复并选题
/factory --resume latest --approve    # 审核通过并继续

# 单独模块
/search                               # 素材采集
/plan                                 # 选题策划
/write "选题标题"                      # 内容生成
/publish <markdown文件>                # 多平台发布
```

### Collection
```bash
# 一键采集（搜索 + 两方向策划）
python src/collector/main.py

# 仅搜索（输出素材池）
python src/collector/search.py [--sources hn,github]

# 仅策划（从素材池推荐选题）
python src/collector/planner.py --pool <path> --recommend [--direction tech_ai|auto]
```

### Generation
```bash
# 生成文章 + 卡片（自动审核 + 补全 frontmatter）
python src/generator/main.py "选题标题"

# 仅生成文章
python src/generator/main.py "选题标题" --no-cards
```

### Publishing
```bash
# 发布到所有 enabled 平台
python src/publisher/main.py <markdown文件>

# AI 推荐平台（不执行发布）
python src/publisher/main.py <markdown文件> --suggest

# 指定平台
python src/publisher/main.py <markdown文件> --platforms wechat,zhihu
```

### Pipeline
```bash
# 流水线（默认到 select 暂停）
python src/pipeline/main.py

# 全自动
python src/pipeline/main.py --auto

# 恢复流水线
python src/pipeline/main.py --resume latest --topic "选题标题"
```

### Testing
```bash
# 运行全部测试（54 个用例）
PYTHONPATH=src pytest tests/ -v

# 运行特定模块
PYTHONPATH=src pytest tests/test_collector_*.py -v
```

## Development Workflow

**每次完成代码变更后，必须按顺序执行：**

### 1. Commit Code
```bash
git commit -m "类型: 简短描述

详细说明（可选）

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

Commit types: `feat`, `fix`, `refactor`, `docs`, `chore`

### 2. Update Documentation

| 变更类型 | 需要更新的文档 |
|---------|--------------|
| 新增/修改 Skill | `.claude/skills/<name>/SKILL.md` |
| 新增/修改命令 | `CLAUDE.md` 的 "Key Commands" 章节 |
| 架构变更 | `CLAUDE.md` 的 "Architecture" 章节 |
| 新增功能 | `docs/需求说明.md` 或 `docs/开发计划.md` |

### 3. Checklist

- [ ] 代码已提交到 git
- [ ] 相关文档已更新
- [ ] 如有新依赖，已更新 `requirements.txt`
- [ ] 如有配置变更，已更新 `.env.example`

**重要**：不要跳过文档更新。过时的文档比没有文档更糟糕。

## Multi-Agent Collaboration

本工作区由 Claude Code 和 Codex 协同开发：
- 接任务前先读 `docs/开发计划.md`，认领"待认领"任务
- 架构设计和 SOP 详见 `docs/需求说明.md`
- 协作规范详见 `AGENTS.md`

## Code Style

- Python: `snake_case`，类名 `PascalCase`，使用 `ruff` 格式化
- TypeScript: `camelCase` 函数/变量，`PascalCase` 组件/接口
- 文档: `kebab-case` 或中文语义化命名
- 缩进: 4 空格

## Security

- 禁止提交 API 密钥、Token、Cookie
- 使用占位符: `<API_KEY>`、`<TOKEN>`
- 本地环境变量放在 `.env`（已加入 .gitignore）

## Key Files

### Configuration
- `src/config/sources.yaml` — 信息源配置（RSS、Tavily query、Twitter 账号）
- `src/config/publishers.yaml` — 平台开关和配置
- `src/config/models.yaml` — Gemini 模型配置（文本/图像任务）

### Data Storage
- `content/pool/` — 素材池 JSON（搜索阶段输出）
- `content/drafts/` — 草稿（生成阶段输出）
- `content/pipeline/` — 流水线状态 JSON

### Notion Integration
- `src/collector/notion_output.py` — 素材池同步
- `src/collector/notion_topics.py` — 选题库同步
- `src/generator/notion_drafts.py` — 草稿库同步
- `src/publisher/notion_records.py` — 发布记录同步
- `docs/notion-setup.md` — Notion 配置指南

### Skills
- `.claude/skills/` — Claude Skills 定义
