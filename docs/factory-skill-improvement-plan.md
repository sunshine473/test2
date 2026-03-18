# Factory Skill 改进方案

## 问题总结

当前 factory skill 存在以下问题：

1. **结构问题**：492 行全部内联，违反渐进式披露原则
2. **描述不清**：frontmatter description 过于简单，未说明触发时机
3. **缺少入口**：没有"何时使用"章节，用户不知道何时调用
4. **文档过载**：所有阶段细节、数据结构、JSON 示例全部堆在 SKILL.md
5. **缺少资源**：没有利用 references/ 目录做渐进式加载

## 改进目标

将 factory skill 从 **参考手册** 改造为 **高效技能**：
- SKILL.md 压缩到 150-180 行（当前 492 行）
- 添加清晰的"何时使用"章节
- 采用渐进式披露：核心流程在 SKILL.md，细节在 references/
- 提供快速入门路径（3 分钟上手）

## 新文件结构

```
.claude/skills/factory/
├── SKILL.md (150-180 行)
│   ├── Frontmatter（改进 description）
│   ├── When to Use This Skill（新增）
│   ├── Quick Overview（简化）
│   ├── Workflow Diagram（保留）
│   ├── Quick Start（新增 3 个常见场景）
│   ├── Parameters（简化，链接到详细文档）
│   └── Learn More（链接到 references）
├── references/
│   ├── pipeline-stages.md（6 阶段详细文档）
│   ├── data-structures.md（JSON schemas）
│   ├── quality-scoring.md（6 维度评分标准）
│   ├── notion-integration.md（Notion 配置指南）
│   ├── state-machine.md（状态机图 + 转换逻辑）
│   ├── parameter-matrix.md（参数组合指南）
│   └── troubleshooting.md（FAQ + 错误恢复）
└── evals/
    └── evals.json（已存在）
```

## 改进后的 SKILL.md 结构

### 1. Frontmatter（改进）

```yaml
---
description: >
  Orchestrates the complete content production pipeline from material collection
  through multi-platform distribution. Use this skill when running the full content
  factory workflow with semi-automatic pauses at topic selection and quality review
  stages. Supports both semi-automatic (paused) and fully automatic modes, with AI
  quality scoring (6 dimensions, 70-point threshold). Integrates with Notion for
  data management.
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '[--auto] [--until <stage>] [--direction tech_ai|auto] [--sources <list>] [--platforms <list>]'
keywords: content-factory, pipeline, automation, publishing, notion, quality-review
---
```

### 2. When to Use This Skill（新增）

```markdown
## When to Use This Skill

Use the factory skill when you need to:

- **Run the complete content pipeline**: From material collection to multi-platform publishing
- **Semi-automatic workflow**: Execute with human checkpoints at topic selection and quality review
- **Fully automatic workflow**: Run end-to-end without manual intervention
- **Resume interrupted pipelines**: Continue from where you left off after topic selection or review
- **Batch content production**: Generate multiple articles from collected materials
- **Quality-controlled publishing**: Ensure content meets 70-point AI review threshold before publishing

**Don't use this skill for:**
- Single-stage operations (use `/search`, `/plan`, `/write`, `/publish` instead)
- Manual content writing (use `/write` directly)
- Quick material collection (use `/search` or `/collect`)
```

### 3. Quick Overview（简化）

```markdown
## Quick Overview

The factory skill orchestrates a 6-stage content production pipeline:

```
素材搜索 → 选题策划 → 人工选题 → 内容生成 → AI质量审核 → 发布分发
(自动)    (按方向)    (★卡点)    (自动)      (自动打分)    (一键)
```

**Default behavior**: Executes to **select** stage and pauses for human topic selection.

**AI Review**: 6-dimension scoring (title, hook, structure, logic, readability, density)
with 70-point pass threshold.

**Notion Integration**: Syncs materials, topics, drafts, and publish records to 4 databases.
```

### 4. Quick Start（新增）

```markdown
## Quick Start

### Scenario 1: Standard Semi-Automatic Workflow

```bash
# 1. Start pipeline (pauses at topic selection)
/factory --direction tech_ai

# 2. Review recommended topics in output
# 3. Select topic and continue
/factory --resume latest --topic "Your Selected Topic"

# 4. If review passes, approve and publish
/factory --resume latest --approve
```

### Scenario 2: Fully Automatic Mode

```bash
# One-command end-to-end (auto-selects top topic, auto-retries if review fails)
/factory --auto --direction tech_ai
```

### Scenario 3: Partial Execution

```bash
# Only collect and plan (stop before topic selection)
/factory --until plan

# Only publish existing draft
python src/publisher/main.py content/drafts/your-article.md
```

**See [references/pipeline-stages.md](references/pipeline-stages.md) for detailed stage documentation.**
```

### 5. Parameters（简化）

```markdown
## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--auto` | Fully automatic mode (skip manual checkpoints) | `/factory --auto` |
| `--until <stage>` | Execute until specified stage | `--until plan` |
| `--direction <dir>` | Content direction (tech_ai/auto) | `--direction tech_ai` |
| `--sources <list>` | Specify collection sources | `--sources hn,github` |
| `--platforms <list>` | Specify publish platforms | `--platforms wechat,zhihu` |
| `--resume latest` | Resume latest pipeline | `--resume latest --topic "X"` |
| `--approve` | Approve review and continue | `--resume latest --approve` |
| `--rewrite` | Regenerate after failed review | `--resume latest --rewrite` |

**For parameter combinations and advanced usage, see [references/parameter-matrix.md](references/parameter-matrix.md).**
```

### 6. Learn More（新增）

```markdown
## Learn More

- **[Pipeline Stages](references/pipeline-stages.md)**: Detailed documentation for all 6 stages
- **[Data Structures](references/data-structures.md)**: JSON schemas and state file format
- **[Quality Scoring](references/quality-scoring.md)**: 6-dimension AI review criteria
- **[Notion Integration](references/notion-integration.md)**: Setup and sync guide
- **[State Machine](references/state-machine.md)**: Pipeline transitions and resume logic
- **[Parameter Matrix](references/parameter-matrix.md)**: Parameter combinations guide
- **[Troubleshooting](references/troubleshooting.md)**: FAQ and error recovery

**Total SKILL.md length**: ~150-180 lines (vs. current 492 lines)
```

## References 文件内容分配

### references/pipeline-stages.md
- 当前 SKILL.md 的 lines 74-375（6 个阶段的详细文档）
- 每个阶段的输入、脚本、流程、输出、数据结构

### references/data-structures.md
- 素材池 JSON schema
- 选题结果 JSON schema
- 流水线状态文件 schema
- Notion 数据库字段定义

### references/quality-scoring.md
- 6 维度评分标准（标题 20 + 开头 15 + 结构 20 + 逻辑 15 + 可读性 15 + 信息密度 15）
- 每个维度的评分细则
- 通过标准（>= 70 分）
- 示例评分报告

### references/notion-integration.md
- 4 个数据库的创建步骤
- 字段配置
- 关联关系设置
- 同步逻辑说明

### references/state-machine.md
- ASCII 状态机图
- 正常流程：search → plan → select → write → review → publish
- 暂停点：select（等待 --topic）、review（等待 --approve 或 --rewrite）
- 恢复逻辑：--resume latest 的行为

### references/parameter-matrix.md
- 参数组合表
- 常见场景映射
- 冲突参数说明

### references/troubleshooting.md
- 当前 SKILL.md 的 FAQ 章节（lines 474-492）
- 扩展错误恢复指南
- 日志检查技巧

## 实施步骤

### Phase 1: 创建 references/ 目录结构
1. 创建 `.claude/skills/factory/references/` 目录
2. 从当前 SKILL.md 提取内容到 7 个 reference 文件
3. 验证链接和引用正确

### Phase 2: 重写 SKILL.md
1. 更新 frontmatter description
2. 添加 "When to Use This Skill" 章节
3. 简化 Quick Overview
4. 添加 Quick Start（3 个场景）
5. 简化 Parameters 表格
6. 添加 Learn More 链接章节

### Phase 3: 验证和测试
1. 运行 `/factory` 验证 skill 加载
2. 测试 references 文件是否能被 Claude 正确读取
3. 检查文档链接完整性
4. 确认总行数 < 200

### Phase 4: 更新相关文档
1. 更新 CLAUDE.md 中的 factory skill 说明
2. 更新 docs/开发计划.md
3. 提交 git commit

## 预期效果

**改进前**：
- SKILL.md: 492 行
- 用户体验：需要阅读全部内容才能理解如何使用
- 加载成本：所有细节一次性加载到 context

**改进后**：
- SKILL.md: 150-180 行
- 用户体验：3 分钟快速上手，需要时查阅 references
- 加载成本：核心流程在 context，细节按需加载

## 参考资料

- awesome-claude-skills/skill-creator/SKILL.md
- awesome-claude-skills/content-research-writer/SKILL.md
- awesome-claude-skills/changelog-generator/SKILL.md
- awesome-claude-skills/skill-creator/scripts/init_skill.py
