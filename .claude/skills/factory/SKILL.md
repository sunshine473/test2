---
description: >
  全自动内容工厂：从素材采集到多平台发布的完整流水线。AI 自动评估和选择最佳选题，
  自动生成内容，自动质量审核（6 维度 70 分通过），自动发布到多平台。支持全自动模式
  和半自动模式（在选题和审核阶段暂停）。集成 Notion 数据管理。
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '[--auto] [--until <stage>] [--direction tech_ai|auto] [--sources <list>] [--platforms <list>]'
---

# /factory — 全链路内容工厂

串联完整的内容生产流水线，从素材采集到多平台发布。

## 工作流

```
素材搜索 → 选题策划 → AI选题评估 → 内容生成 → AI质量审核 → 发布分发
(自动)    (按方向)    (AI自动)      (自动)      (自动打分)    (一键)
```

**全自动模式** (`--auto`)：AI 自动评估推荐选题并选择最佳选题，审核不通过自动重写。

**半自动模式** (默认)：在选题和审核阶段暂停，等待人工确认。

**AI 选题评估**：Claude 分析推荐选题的时效性、话题热度、内容深度、差异化、读者价值，自动选择最佳选题。

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

### 1. search — 素材采集

**输入**：
- `sources` 参数：采集源列表（如 `["rss", "hn", "github", "hot", "tavily", "youtube_api"]`）
- `src/config/sources.yaml`：各源的配置（RSS 订阅地址、Tavily 查询词等）

**执行脚本**：
```bash
python src/collector/search.py --sources rss,hn,github,hot,tavily,youtube_api
```

**处理流程**：
1. 从各信息源采集原始素材（RSS、HN、GitHub Trending、热榜、Tavily 搜索、YouTube）
2. 调用 `normalizer` 进行数据清洗、去重、聚类
3. 生成素材池 JSON
4. 同步到 Notion 素材池数据库（状态：待筛选）

**输出**：
- 文件：`content/pool/2026-03-15-pool.json`
- 数据结构：
```json
{
  "date": "2026-03-15",
  "stage": "search",
  "dedup_total": 150,
  "cluster_summary": {
    "cluster_count": 12,
    "max_cluster_size": 8
  },
  "items": [
    {
      "title": "GPT-5 发布，性能提升 10 倍",
      "url": "https://example.com/gpt5",
      "source_name": "Hacker News",
      "category": "AI",
      "summary": "OpenAI 发布 GPT-5...",
      "published_at": "2026-03-15T10:00:00Z",
      "cluster_id": 1,
      "cluster_size": 3
    }
  ],
  "_output_path": "content/pool/2026-03-15-pool.json",
  "notion_saved": 150
}
```

---

### 2. plan — 选题策划

**输入**：
- 素材池 JSON：`content/pool/2026-03-15-pool.json`
- `direction` 参数：内容方向（`tech_ai` / `auto` / `null`）

**执行脚本**：
```bash
python src/collector/planner.py --pool content/pool/2026-03-15-pool.json --direction tech_ai --recommend
```

**处理流程**：
1. 按方向筛选素材（匹配 category 或关键词）
2. 调用 `ItemScorer` 对素材打分（时效性、热度、质量等维度）
3. 按分数排序
4. AI 分析 Top 10 素材，推荐 3-5 个选题
5. 同步推荐选题到 Notion 选题库（状态：待选择）

**输出**：
- 数据结构（保存在 `state.plan_result`）：
```json
{
  "tech_ai": {
    "direction": "tech_ai",
    "label": "AI 科技",
    "input_count": 150,
    "filtered_count": 45,
    "score_summary": {
      "max": 95,
      "avg": 72,
      "min": 50
    },
    "items": [
      {
        "title": "GPT-5 发布，性能提升 10 倍",
        "url": "https://example.com/gpt5",
        "category": "AI",
        "summary": "...",
        "raw_data": {
          "score": 95
        }
      }
    ]
  }
}
```

- AI 推荐选题（同步到 Notion）：
```json
[
  {
    "title": "GPT-5 来了：AI 大模型进入新纪元",
    "score": 92.5,
    "reason": "推荐理由: GPT-5 是行业重大事件，时效性强，话题热度高\n建议角度: 从技术突破、应用场景、行业影响三个维度展开",
    "source_urls": ["https://example.com/gpt5", "https://example.com/gpt5-analysis"]
  }
]
```

---

### 3. select — AI 选题评估

**输入**：
- `state.recommended_topics`：AI 推荐的选题列表
- `state.plan_result`：策划阶段的排序结果（备用）
- `auto` 参数：是否自动选题

**执行脚本**：
```bash
# 半自动模式：暂停等待人工输入
python src/pipeline/main.py --resume latest --topic "GPT-5 来了：AI 大模型进入新纪元"

# 全自动模式：AI 自动评估选择
python src/pipeline/main.py --auto
```

**处理流程（全自动模式）**：
1. 从 `recommended_topics` 获取 AI 推荐的选题列表
2. 调用 `ai_selector.select_best_topic()` 让 Claude 评估选题
3. Claude 分析 5 个维度：时效性、话题热度、内容深度、差异化、读者价值
4. 自动选择最佳选题
5. 输出选择理由和评分

**处理流程（半自动模式）**：
- 暂停流水线，等待用户通过 `--topic` 参数指定选题

**输出**：
- 保存到 `state`：
```json
{
  "selected_topic": "GPT-5 来了：AI 大模型进入新纪元",
  "selected_sources": ["https://example.com/gpt5"]
}
```

**AI 选题评估示例**：
```
🤖 AI 正在评估推荐选题...
✅ AI 选题: GPT-5 来了：AI 大模型进入新纪元
📊 评分: 92.5
💡 选择理由: 时效性强，话题热度高，有足够素材支撑深度分析
```

---

### 4. write — 内容生成

**输入**：
- `selected_topic`：选中的选题标题
- `selected_sources`：关联的素材 URL（可选）
- `no_cards` 参数：是否生成视觉卡片

**执行脚本**：
```bash
python src/generator/main.py "GPT-5 来了：AI 大模型进入新纪元"
```

**处理流程**：
1. 调用 `generator.writer.generate_article()` 生成文章
2. 自动补全 frontmatter（标题、日期、标签、摘要等）
3. 如果 `no_cards=False`，调用 `card_generator.generate_cards()` 生成视觉卡片 HTML

**输出**：
- 文章文件：`content/drafts/gpt-5-来了-ai-大模型进入新纪元.md`
```markdown
---
title: GPT-5 来了：AI 大模型进入新纪元
date: 2026-03-15
tags: [AI, GPT, 大模型]
summary: OpenAI 发布 GPT-5，性能提升 10 倍，标志着 AI 大模型进入新纪元...
---

# GPT-5 来了：AI 大模型进入新纪元

OpenAI 今天正式发布了 GPT-5...

## 技术突破

GPT-5 在以下方面实现了重大突破：
1. 推理能力提升 10 倍
2. 上下文窗口扩展到 1M tokens
...
```

- 卡片文件：`content/drafts/gpt-5-来了-ai-大模型进入新纪元-cards.html`
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .card { width: 800px; padding: 40px; background: linear-gradient(...); }
  </style>
</head>
<body>
  <div class="card">
    <h1>GPT-5 来了</h1>
    <p>AI 大模型进入新纪元</p>
  </div>
</body>
</html>
```

- 保存到 `state`：
```json
{
  "draft_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元.md",
  "cards_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元-cards.html"
}
```

- 同步到 Notion 草稿库（状态：待审核）

---

### 5. review — AI 质量审核

**输入**：
- `draft_path`：草稿文件路径
- `auto` 参数：是否自动重写

**执行脚本**：
```bash
python src/reviewer/quality_checker.py content/drafts/gpt-5-来了-ai-大模型进入新纪元.md
```

**处理流程**：
1. 读取草稿内容
2. AI 从 6 个维度评分（总分 100）
3. 判断是否通过（>= 70 分）
4. 如果不通过：
   - 半自动模式：暂停，等待 `--approve` 或 `--rewrite`
   - 全自动模式：自动调用 `_run_write()` 重新生成

**输出**：
- 评分结果（保存到 `state`）：
```json
{
  "review_score": 85,
  "review_passed": true,
  "review_feedback": "✅ 审核通过\n\n标题吸引力: 18/20 - 标题有数字和具体场景\n开头钩子: 14/15 - 开头抓住注意力\n内容结构: 19/20 - 结构清晰\n逻辑连贯性: 14/15 - 论证充分\n可读性: 13/15 - 语言流畅\n信息密度: 7/15 - 信息密度偏低"
}
```

- 如果不通过（< 70 分）：
```json
{
  "review_score": 65,
  "review_passed": false,
  "review_feedback": "❌ 审核不通过\n\n标题吸引力: 12/20 - 标题过于平淡\n开头钩子: 10/15 - 开头缺乏吸引力\n..."
}
```

---

### 6. publish — 多平台发布

**输入**：
- `draft_path`：草稿文件路径
- `platforms` 参数：指定发布平台（逗号分隔）
- `src/config/publishers.yaml`：平台配置和开关

**执行脚本**：
```bash
python src/publisher/main.py content/drafts/gpt-5-来了-ai-大模型进入新纪元.md --platforms wechat,zhihu
```

**处理流程**：
1. 加载草稿为 `DraftPackage`
2. 调用 `packager` 为每个平台生成 `PublishPackage`（处理图片、格式转换）
3. 调用各平台 publisher 执行发布
4. 记录发布结果到 Notion 发布记录数据库

**输出**：
- 发布结果（保存到 `state.publish_results`）：
```json
[
  {
    "platform": "wechat",
    "status": "success",
    "message": "草稿已创建，ID: 123456"
  },
  {
    "platform": "zhihu",
    "status": "success",
    "message": "文章已发布: https://zhuanlan.zhihu.com/p/123456"
  },
  {
    "platform": "bilibili",
    "status": "failed",
    "message": "登录失败：Cookie 已过期"
  }
]
```

- Notion 发布记录：
```json
{
  "title": "GPT-5 来了：AI 大模型进入新纪元",
  "platforms": ["微信公众号", "知乎"],
  "status": "部分成功",
  "publish_date": "2026-03-15T15:30:00Z",
  "links": {
    "wechat": "草稿箱",
    "zhihu": "https://zhuanlan.zhihu.com/p/123456"
  }
}
```

---

## 流水线状态文件

**文件路径**：`content/pipeline/2026-03-15-143022.json`

**完整数据结构**：
```json
{
  "pipeline_id": "2026-03-15-143022",
  "created_at": "2026-03-15T14:30:22.123456",
  "current_stage": "publish",
  "status": "completed",

  "pool_path": "content/pool/2026-03-15-pool.json",
  "plan_result": { /* 策划结果 */ },
  "selected_topic": "GPT-5 来了：AI 大模型进入新纪元",
  "selected_sources": ["https://example.com/gpt5"],
  "draft_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元.md",
  "cards_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元-cards.html",
  "review_score": 85,
  "review_passed": true,
  "review_feedback": "✅ 审核通过...",
  "publish_results": [ /* 发布结果 */ ],

  "sources": "rss,hn,github,hot,tavily,youtube_api",
  "direction": "tech_ai",
  "platforms": "",
  "no_cards": false,

  "error": "",
  "history": [
    {
      "stage": "search",
      "message": "素材池 150 条: content/pool/2026-03-15-pool.json",
      "time": "2026-03-15T14:30:25.123456"
    },
    {
      "stage": "plan",
      "message": "完成",
      "time": "2026-03-15T14:32:10.123456"
    }
  ]
}
```

## 使用示例

### 标准流程（全自动）
```bash
# 一键跑完全流程（AI 自动选题、自动审核、不通过自动重写）
/factory --auto --direction tech_ai
```

### 标准流程（半自动）
```bash
# 1. 启动流水线（执行到选题暂停）
/factory --direction tech_ai

# 2. 查看 AI 推荐选题
/factory --status

# 3. 选择选题并继续
/factory --resume latest --topic "GPT-5 发布解读"

# 4. AI 审核通过后继续发布（如果审核不通过会自动暂停）
/factory --resume latest --approve

# 5. 如果审核不通过，可以重新生成
/factory --resume latest --rewrite
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
