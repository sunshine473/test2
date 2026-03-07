# CLAUDE.md

本文件为 Claude Code 提供项目上下文与工作指引。

## 项目定位

半自动化内容工厂 — 从素材采集、选题推荐、内容生成到多平台分发的全流程系统。

**当前状态**: M1/M2/M3 已完成 ✅ 全链路可用

## 协作模式

本工作区由 Claude Code 和 Codex 协同开发：
- 接任务前先读 `docs/开发计划.md`，认领"待认领"任务
- 架构设计和 SOP 详见 `docs/需求说明.md`
- 协作规范详见 `AGENTS.md`

## 项目结构

```
├── src/
│   ├── collector/              # 素材采集（✅ 已完成）
│   │   ├── sources/            # 各信息源适配器
│   │   ├── directions.py       # 方向配置（AI科技/汽车）
│   │   ├── search.py           # 搜索阶段入口
│   │   ├── planner.py          # 策划阶段入口
│   │   ├── dedup.py            # 去重 + 聚类
│   │   └── scorer.py           # 打分排序（支持按方向）
│   ├── generator/              # 内容生成（✅ 已完成）
│   ├── publisher/              # 统一发布框架（✅ 已完成，4 平台可用）
│   │   ├── platforms/          # 各平台适配器
│   │   ├── base.py             # 发布适配器基类
│   │   ├── registry.py         # 注册表
│   │   └── main.py             # CLI 入口
│   ├── pipeline/               # 流水线调度（✅ 已完成）
│   ├── bot/                    # Telegram Bot 双向交互（✅ 已完成）
│   ├── config/                 # 统一配置
│   ├── inspiration_bot/        # 旧版灵感采集（待替换）
│   └── wechat_publisher/       # 微信发布（旧版，已迁移到 publisher/）
├── .claude/skills/
│   ├── collect/                # /collect 素材采集（✅ 已完成）
│   ├── write/                  # /write 内容生成（✅ 已完成）
│   ├── publish/                # /publish 一键发布（✅ 已完成）
│   ├── get-inspiration/        # 旧版（待替换）
│   └── publish-to-wechat/      # 旧版（待替换）
├── content/                    # 内容仓库
│   ├── pool/                   # 素材池 JSON（搜索阶段输出）
│   ├── drafts/                 # 草稿
│   ├── ready/                  # 待发布
│   └── published/              # 已发布归档
├── MultiPost-Extension/        # 多平台分发浏览器扩展
├── docs/                       # 需求文档与开发计划
├── 参考/                       # 外部参考资料
├── AGENTS.md                   # 协作规范（Claude Code + Codex）
└── CLAUDE.md                   # 本文件
```

## 核心 SOP

```
素材搜索（自动）→ 选题策划（按方向）→ 人工选题 → 内容生成（自动）→ 人工审核 → 发布分发（一键）
```

对应 Skill：
1. `/search` — 采集素材 + 去重聚类，输出素材池 JSON
2. `/plan` — 从素材池按方向（AI科技/汽车）筛选打分，推荐选题
3. `/collect` — 一键串联搜索 + 策划
4. `/write "选题"` — 基于选题生成 Markdown 草稿到 `content/drafts/`
5. `/publish` — 统一发布到微信公众号 + B站/知乎/头条/小红书/懂车帝

## 常用命令

- **一键采集**: `python src/collector/main.py`（搜索 + 两方向策划）
- **指定采集源**: `python src/collector/main.py --sources hn,github,hot`
- **汽车增强采集**: `python src/collector/main.py --sources rss,tavily,hot`
- **全量默认采集**: `python src/collector/main.py --sources rss,hn,github,hot,tavily,youtube_api`
- **仅搜索**: `python src/collector/main.py --search-only`（或 `python src/collector/search.py`）
- **仅策划**: `python src/collector/main.py --plan-only --pool <path>`（或 `python src/collector/planner.py --pool <path>`）
- **指定方向**: `python src/collector/main.py --direction tech_ai`
- **素材搜索**: `python src/collector/search.py [--sources hn,github]`
- **选题策划**: `python src/collector/planner.py --pool content/pool/<date>-pool.json [--direction tech_ai|auto]`
- **内容生成**: `python src/generator/main.py "选题标题"`（生成文章+卡片到 `content/drafts/`）
- **仅生成文章**: `python src/generator/main.py "选题标题" --no-cards`
- **统一发布**: `python src/publisher/main.py <markdown文件路径>`（发布到所有 enabled 平台）
- **指定平台发布**: `python src/publisher/main.py <markdown文件路径> --platforms wechat,bilibili`
- **流水线（默认到 select 暂停）**: `python src/pipeline/main.py`
- **流水线全自动**: `python src/pipeline/main.py --auto`
- **恢复流水线**: `python src/pipeline/main.py --resume latest --topic "选题标题"` / `python src/pipeline/main.py --resume latest --approve`
- **流水线状态**: `python src/pipeline/main.py --list` / `python src/pipeline/main.py --status --json`
- **微信发布（旧）**: `python src/wechat_publisher/main.py <markdown文件路径>`
- **查找待办**: `rg "TODO|FIXME|待办" .`

## 代码风格

- Python: `snake_case`，类名 `PascalCase`，使用 `ruff` 格式化
- TypeScript: `camelCase` 函数/变量，`PascalCase` 组件/接口，`SNAKE_CASE` 常量
- 文档文件: `kebab-case` 或中文语义化命名
- 缩进: 4 空格（除非语言规范另有要求）

## 开发工作流

**每次完成代码变更后，必须按顺序执行以下步骤：**

### 1. 提交代码
```bash
git add <修改的文件>
git commit -m "类型: 简短描述

详细说明（可选）

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

提交类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构（不改变功能）
- `docs`: 文档更新
- `chore`: 构建/工具/依赖更新

### 2. 更新文档

根据变更类型更新对应文档：

| 变更类型 | 需要更新的文档 |
|---------|--------------|
| 新增/修改 Skill | `.claude/skills/<name>/SKILL.md` |
| 新增/修改命令 | `CLAUDE.md` 的"常用命令"章节 |
| 架构变更 | `CLAUDE.md` 的"项目结构"章节 |
| 新增功能 | `docs/需求说明.md` 或 `docs/开发计划.md` |
| API 变更 | 对应模块的 docstring |

### 3. 检查清单

完成变更后，确认以下事项：

- [ ] 代码已提交到 git
- [ ] 相关文档已更新
- [ ] 如有新依赖，已更新 `requirements.txt` 或 `package.json`
- [ ] 如有配置变更，已更新 `.env.example`
- [ ] 如有破坏性变更，已在 commit message 中说明

**重要**：不要跳过文档更新。过时的文档比没有文档更糟糕。

## 安全规范

- 禁止提交 API 密钥、Token、Cookie 等敏感信息
- 使用占位符: `<API_KEY>`、`<TOKEN>`、`<APP_SECRET>`
- 本地环境变量放在 `.env` 或 `.env.local`（已加入 .gitignore）
