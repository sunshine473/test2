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
python src/collector/main.py --sources youtube_api,hn,github,hot

# 仅搜索（输出素材池 JSON）
python src/collector/main.py --search-only
# 或
python src/collector/search.py

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

- Python 3 + 各模块 `requirements.txt` 依赖
- Node.js + pnpm（MultiPost 扩展开发）
- LLM API 密钥（Claude / Gemini / OpenAI）
- Notion 配置（素材采集为必选）：`NOTION_API_KEY`、`NOTION_DATABASE_ID`
- YouTube API 配置（启用 `youtube_api` 时）：`YOUTUBE_API_KEY`
- `.env` 文件配置敏感信息（不要提交到仓库）

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
