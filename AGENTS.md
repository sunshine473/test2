# AGENTS.md — 协作规范与贡献指南

## 项目简介

本项目是一个半自动化内容工厂，覆盖从素材采集、内容创作到多平台分发的完整链路。详见 [docs/需求说明.md](docs/需求说明.md)。

## 多 Agent 协作须知

本工作区由 Claude Code 和 Codex 协同开发，遵守以下规则：

1. **接任务前**：先读 `docs/开发计划.md`，找到"待认领"的任务
2. **认领任务**：在任务表"负责人"列填写 `Claude` 或 `Codex`，状态改为 `进行中`
3. **完成任务**：执行以下收尾清单（缺一不可）：
   - 更新 `docs/开发计划.md` 任务状态为 `Done`，在"复盘"列写一句话结论
   - 在 `docs/复盘记录.md` 追加详细复盘条目（格式见下方）
   - 检查 `CLAUDE.md`、`README.md` 是否需要同步更新（结构、命令、SOP 有变动时必须同步）
4. **遇到阻塞**：在任务行备注原因，不要空等，可先做其他任务
5. **不要重复造轮子**：改代码前先看现有实现，优先复用和优化
6. **里程碑复盘**：每个里程碑（M1/M2/M3）全部任务完成后，在 `docs/复盘记录.md` 追加一次阶段性总结

## 任务复盘规范

### 复盘写在哪

| 位置 | 写什么 | 何时写 |
|------|--------|--------|
| `docs/开发计划.md` 任务表"复盘"列 | 一句话结论 | 每个任务完成时 |
| `docs/复盘记录.md` | 详细复盘条目 | 每个任务完成时 |
| `docs/复盘记录.md` 阶段性总结 | 里程碑回顾 | 每个里程碑完成时 |

### 详细复盘条目格式

```markdown
### T{编号} — {任务名称}
- **负责人**: Claude / Codex
- **产出**: `文件路径`
- **问题与解决**: 遇到了什么、怎么解的
- **经验**: 下次可以复用或需要注意的点
- **验收证据**: 命令输出 / 日志 / PR 链接 / 截图
- **后续**: 是否衍生新任务或需要优化的地方
```

### 里程碑总结格式

```markdown
## M{编号} 阶段性总结
- **目标达成情况**: 是否达标、偏差在哪
- **关键经验**: 整个阶段最值得记住的 2-3 条
- **流程改进**: SOP 或协作方式需要调整的地方
- **下阶段注意**: 带入下个里程碑的待办或风险
```

## 关键文档

| 文档 | 作用 |
|------|------|
| `docs/需求说明.md` | 项目目标、架构设计、SOP 流程、验收标准 |
| `docs/开发计划.md` | 里程碑、任务拆分、认领状态、复盘摘要 |
| `docs/复盘记录.md` | 任务详细复盘 + 里程碑阶段性总结 |
| `CLAUDE.md` | Claude Code 专用的项目指引 |
| `README.md` | 项目概览与快速开始 |

## 模块职责

> 以下目录为目标结构，部分模块尚未创建，按任务进度逐步建设。

| 模块 | 路径 | 说明 | 状态 |
|------|------|------|------|
| 素材采集 | `src/collector/` | 多源采集、去重聚类、LLM 打分 | 建设中 |
| 内容生成 | `src/generator/` | LLM 写作、文章模板 | 未创建 |
| 微信发布 | `src/wechat_publisher/` | Markdown → 公众号草稿箱 | 已有 |
| 多平台分发 | `MultiPost-Extension/` | 浏览器扩展，30+ 平台 | 已有 |
| 流水线调度 | `src/pipeline/` | 串联各环节 | 未创建 |
| Skills | `skills/` | Claude Code 技能定义 | 部分已有 |
| 配置 | `src/config/` | 信息源配置、prompt 模板 | 已创建 sources.yaml |
| 内容仓库 | `content/` | drafts → ready → published | 未创建 |
| 参考资料 | `参考/` | 外部文档，不作为交付内容 | 已有 |

## 开发规范

### 分支与提交
- 提交信息使用简洁前缀: `feat:`、`fix:`、`docs:`、`chore:`
- 单次提交只做一类改动，避免混合提交

### 代码风格
- Python: `snake_case`，类名 `PascalCase`
- TypeScript: `camelCase` 函数/变量，`PascalCase` 组件/接口
- 文档: `kebab-case` 或中文语义化命名
- 缩进: 4 空格（除非语言规范另有要求）

### 测试
- 测试文件放在 `tests/` 目录
- 命名: `test_<模块>_<行为>.py` 或 `<module>.test.ts`

## 安全要求

- 禁止提交密钥、令牌、Cookie、私有 URL
- 使用占位符: `<API_KEY>`、`<TOKEN>`
- 本地环境变量放在 `.env` 或 `.env.local`（已加入 .gitignore）

## 新增平台适配器

1. 在 `MultiPost-Extension/src/sync/article/` 下创建 `<platform>.ts`
2. 导出注入函数，实现 DOM 操作填充内容
3. 在 `MultiPost-Extension/src/sync/article.ts` 的 `ArticleInfoMap` 中注册
4. 在 `MultiPost-Extension/src/sync/account/` 添加登录检测（如需要）
5. 在 `MultiPost-Extension/locales/zh_CN/messages.json` 添加平台名称 i18n
