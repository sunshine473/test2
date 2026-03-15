---
description: 全链路半自动化内容工厂（采集→策划→选题→生成→AI审核→发布）
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '[--auto] [--until <stage>] [--direction tech_ai|auto] [--sources <list>] [--platforms <list>]'
---

# /factory — 全链路内容工厂

串联完整的内容生产流水线，从素材采集到多平台发布。

## 工作流

```
素材搜索 → 选题策划 → 人工选题 → 内容生成 → AI质量审核 → 发布分发
(自动)    (按方向)    (★卡点)    (自动)      (自动打分)    (一键)
```

默认执行到 **select** 阶段暂停，等待人工选题。

**AI 审核标准**（总分 >= 70 分通过）：
- 标题吸引力 (20分)：悬念、数字、具体场景
- 开头钩子 (15分)：前3句抓住注意力
- 内容结构 (20分)：清晰框架、短段落、排版元素
- 逻辑连贯性 (15分)：论点清晰、论据充分
- 可读性 (15分)：简洁流畅、案例丰富
- 信息密度 (15分)：新信息、数据支撑

## 基础用法

### 启动流水线（默认到选题暂停）
```bash
python src/pipeline/main.py $ARGS
```

### 恢复流水线（选题后继续）
```bash
python src/pipeline/main.py --resume latest --topic "$TOPIC"
```

### 恢复流水线（审核通过后继续）
```bash
python src/pipeline/main.py --resume latest --approve
```

### 恢复流水线（审核不通过，重新生成）
```bash
python src/pipeline/main.py --resume latest --rewrite
```

### 查看状态
```bash
python src/pipeline/main.py --status
```

### 查看历史
```bash
python src/pipeline/main.py --list
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--auto` | 全自动模式（跳过人工卡点） | `/factory --auto` |
| `--until <stage>` | 执行到指定阶段 | `--until plan` |
| `--direction <dir>` | 内容方向（tech_ai/auto） | `--direction tech_ai` |
| `--sources <list>` | 指定采集源（逗号分隔） | `--sources hn,github` |
| `--platforms <list>` | 指定发布平台（逗号分隔） | `--platforms wechat,zhihu` |
| `--no-cards` | 生成时不创建视觉卡片 | `--no-cards` |

## 阶段说明

1. **search** — 多源采集，输出素材池到 `content/pool/`
2. **plan** — 按方向筛选打分，推荐 Top-5 选题
3. **select** — ⏸️ 人工选题（默认暂停点）
4. **write** — 生成文章 + 卡片，输出到 `content/drafts/`
5. **review** — 🤖 AI 质量审核（6 维度评分，< 70 分自动打回重写）
6. **publish** — 多平台发布

## 使用示例

### 标准流程（半自动）
```bash
# 1. 启动流水线（执行到选题暂停）
/factory --direction tech_ai

# 2. 查看推荐选题
/factory --status

# 3. 选择选题并继续
/factory --resume latest --topic "GPT-5 发布解读"

# 4. AI 审核通过后继续发布（如果审核不通过会自动暂停）
/factory --resume latest --approve

# 5. 如果审核不通过，可以重新生成
/factory --resume latest --rewrite
```

### 全自动模式
```bash
# 一键跑完全流程（自动选 Top-1，AI 自动审核，不通过自动重写）
/factory --auto --direction tech_ai
```

### 部分执行
```bash
# 只执行采集和策划
/factory --until plan

# 从写作阶段开始（需指定选题）
python src/pipeline/main.py --from write --topic "选题标题"
```

### 指定源和平台
```bash
# 只采集 HN 和 GitHub，只发布到微信
/factory --sources hn,github --platforms wechat
```

## 输出说明

流水线状态保存在 `content/pipeline/<timestamp>.json`，包含：
- 当前阶段和状态（running/paused/completed/failed）
- 素材池路径
- 选题信息
- 草稿路径
- 发布结果

使用 `--status` 查看最新状态，`--list` 查看历史记录。

## 常见问题

**Q: 流水线卡在 select 怎么办？**
A: 这是正常的人工卡点，使用 `--resume latest --topic "选题"` 继续

**Q: AI 审核不通过怎么办？**
A: 使用 `--resume latest --rewrite` 重新生成，或手动修改草稿后 `--approve`

**Q: AI 审核标准是什么？**
A: 6 个维度总分 >= 70 分通过（标题 20 + 开头 15 + 结构 20 + 逻辑 15 + 可读性 15 + 信息密度 15）

**Q: 如何跳过 AI 审核？**
A: 使用 `--auto` 参数启动流水线（审核不通过会自动重写）

**Q: 如何只执行部分阶段？**
A: 使用 `--until <stage>` 或 `--from <stage>` 参数

**Q: 发布失败怎么办？**
A: 检查 `src/config/publishers.yaml` 中的平台配置和 `.env` 中的凭证
