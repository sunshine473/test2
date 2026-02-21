# 自动化内容工厂

半自动化内容生产系统 — 素材采集、选题推荐、LLM 写作、多平台一键分发。

## 项目结构

```
├── src/
│   ├── collector/              # 素材采集 + LLM 打分（建设中）
│   ├── generator/              # LLM 内容生成（建设中）
│   ├── publisher/              # 发布模块（待迁移）
│   ├── pipeline/               # 流水线调度（建设中）
│   ├── config/                 # 信息源配置 + prompt 模板（建设中）
│   ├── inspiration_bot/        # 旧版灵感采集
│   └── wechat_publisher/       # 微信公众号发布（已有）
├── skills/                     # Claude Skills 定义
├── content/                    # 内容仓库：drafts → ready → published
├── MultiPost-Extension/        # 多平台分发浏览器扩展（30+ 平台）
├── docs/                       # 需求说明 + 开发计划
└── 参考/                       # 外部参考资料
```

## 核心 SOP

```
素材采集（自动）→ 选题推荐（自动）→ 人工选题 → 内容生成（自动）→ 人工审核 → 发布分发（一键）
```

| Skill | 作用 |
|-------|------|
| `/collect` | 采集多源素材，LLM 打分排序，输出选题清单 |
| `/write "选题"` | 基于选题 + 素材生成 Markdown 草稿 |
| `/publish` | 推送微信公众号 + MultiPost 多平台分发 |

## 快速开始

```bash
# 素材采集（默认 rss + hn + github + hot；自动去重聚类、打分并写入 Notion）
python src/collector/main.py

# 指定采集源（示例）
python src/collector/main.py --sources hn,github,hot
python src/collector/main.py --sources youtube_api,hn,github,hot

# 微信公众号发布（已有）
python src/wechat_publisher/main.py <markdown文件路径>

# MultiPost 扩展开发
cd MultiPost-Extension && pnpm dev
```

## 环境配置

- Python 3 + 各模块 `requirements.txt` 依赖
- Node.js + pnpm（MultiPost 扩展开发）
- LLM API 密钥（Claude / OpenAI / 国内模型）
- Notion 配置（素材采集为必选）：`NOTION_API_KEY`、`NOTION_DATABASE_ID`
- YouTube API 配置（启用 `youtube_api` 时）：`YOUTUBE_API_KEY`
- `.env` 文件配置敏感信息（不要提交到仓库）

## 协作

本项目由 Claude Code 和 Codex 协同开发，详见：
- [docs/需求说明.md](docs/需求说明.md) — 架构设计与 SOP
- [docs/开发计划.md](docs/开发计划.md) — 里程碑与任务认领
- [AGENTS.md](AGENTS.md) — 协作规范
- [CLAUDE.md](CLAUDE.md) — Claude Code 工作指引
