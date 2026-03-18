# Batch Factory Output Format

This document describes the output file formats and data schemas for the batch-factory skill.

## Batch Results JSON

**Location:** `content/batch/YYYY-MM-DD-HHMMSS-batch.json`

**Schema:**

```json
[
  {
    "direction": "tech_ai",
    "direction_label": "AI 科技",
    "topic": "GPT-5 来了：AI 大模型进入新纪元",
    "score": 92.5,
    "draft_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元.md",
    "review_score": 85,
    "review_passed": true,
    "publish_results": [
      {
        "platform": "xiaohongshu",
        "status": "success",
        "message": "发布成功"
      },
      {
        "platform": "zhihu",
        "status": "success",
        "message": "文章已发布: https://zhuanlan.zhihu.com/p/123456"
      }
    ],
    "pipeline_id": "2026-03-18-143022"
  },
  {
    "direction": "tech_ai",
    "direction_label": "AI 科技",
    "topic": "Claude 3.5 发布：多模态能力全面升级",
    "score": 89.0,
    "draft_path": "content/drafts/claude-3-5-发布-多模态能力全面升级.md",
    "review_score": 82,
    "review_passed": true,
    "publish_results": [
      {
        "platform": "xiaohongshu",
        "status": "success",
        "message": "发布成功"
      },
      {
        "platform": "zhihu",
        "status": "success",
        "message": "文章已发布: https://zhuanlan.zhihu.com/p/123457"
      }
    ],
    "pipeline_id": "2026-03-18-143045"
  },
  {
    "direction": "auto",
    "direction_label": "汽车",
    "topic": "特斯拉 FSD V12 体验：完全自动驾驶真的来了？",
    "score": 91.0,
    "draft_path": "content/drafts/特斯拉-fsd-v12-体验.md",
    "review_score": 88,
    "review_passed": true,
    "publish_results": [
      {
        "platform": "xiaohongshu",
        "status": "success",
        "message": "发布成功"
      },
      {
        "platform": "zhihu",
        "status": "success",
        "message": "文章已发布: https://zhuanlan.zhihu.com/p/123458"
      }
    ],
    "pipeline_id": "2026-03-18-143108"
  },
  {
    "direction": "auto",
    "direction_label": "汽车",
    "topic": "比亚迪秦 PLUS DM-i 深度评测",
    "score": 87.5,
    "draft_path": "content/drafts/比亚迪秦-plus-dm-i-深度评测.md",
    "review_score": 80,
    "review_passed": true,
    "publish_results": [
      {
        "platform": "xiaohongshu",
        "status": "success",
        "message": "发布成功"
      },
      {
        "platform": "zhihu",
        "status": "success",
        "message": "文章已发布: https://zhuanlan.zhihu.com/p/123459"
      }
    ],
    "pipeline_id": "2026-03-18-143131"
  }
]
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `direction` | string | Content direction: "tech_ai" or "auto" |
| `direction_label` | string | Human-readable direction label |
| `topic` | string | Article topic/title |
| `score` | number | Topic recommendation score (0-100) |
| `draft_path` | string | Path to generated draft file |
| `review_score` | number | AI quality review score (0-100) |
| `review_passed` | boolean | Whether review passed (≥70) |
| `publish_results` | array | Publication results per platform |
| `pipeline_id` | string | Unique pipeline execution ID |
| `error` | string | Error message (if failed) |

**Publish Result Schema:**

```json
{
  "platform": "xiaohongshu",
  "status": "success",
  "message": "发布成功"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `platform` | string | Platform name |
| `status` | string | "success" or "failed" |
| `message` | string | Success message or error details |

## Pipeline State JSON

**Location:** `content/pipeline/<pipeline_id>.json`

**Schema:**

```json
{
  "pipeline_id": "2026-03-18-143022",
  "created_at": "2026-03-18T14:30:22.123456",
  "current_stage": "publish",
  "status": "completed",

  "pool_path": "content/pool/2026-03-18-pool.json",
  "plan_result": {
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
      "items": [...]
    },
    "auto": {...}
  },
  "recommended_topics": {
    "tech_ai": [
      {
        "title": "GPT-5 来了：AI 大模型进入新纪元",
        "score": 92.5,
        "reason": "推荐理由...",
        "source_urls": ["https://..."]
      }
    ],
    "auto": [...]
  },
  "selected_topic": "GPT-5 来了：AI 大模型进入新纪元",
  "selected_sources": ["https://example.com/gpt5"],
  "draft_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元.md",
  "cards_path": "content/drafts/gpt-5-来了-ai-大模型进入新纪元-cards.html",
  "review_score": 85,
  "review_passed": true,
  "review_feedback": "✅ 审核通过\n\n标题吸引力: 18/20...",
  "publish_results": [
    {
      "platform": "xiaohongshu",
      "status": "success",
      "message": "发布成功"
    },
    {
      "platform": "zhihu",
      "status": "success",
      "message": "文章已发布: https://zhuanlan.zhihu.com/p/123456"
    }
  ],

  "sources": "rss,hn,github,hot,tavily,youtube_api",
  "direction": "tech_ai",
  "platforms": "xiaohongshu,zhihu",
  "no_cards": false,

  "error": "",
  "history": [
    {
      "stage": "search",
      "message": "素材池 150 条: content/pool/2026-03-18-pool.json",
      "time": "2026-03-18T14:30:25.123456"
    },
    {
      "stage": "plan",
      "message": "完成",
      "time": "2026-03-18T14:32:10.123456"
    },
    {
      "stage": "select",
      "message": "完成",
      "time": "2026-03-18T14:32:15.123456"
    },
    {
      "stage": "write",
      "message": "完成",
      "time": "2026-03-18T14:35:20.123456"
    },
    {
      "stage": "review",
      "message": "完成",
      "time": "2026-03-18T14:36:10.123456"
    },
    {
      "stage": "publish",
      "message": "完成",
      "time": "2026-03-18T14:38:30.123456"
    }
  ]
}
```

## Draft File Format

**Location:** `content/drafts/<slug>.md`

**Format:** Markdown with YAML frontmatter

**Example:**

```markdown
---
title: GPT-5 来了：AI 大模型进入新纪元
date: 2026-03-18
tags: [AI, GPT, 大模型]
summary: OpenAI 发布 GPT-5，性能提升 10 倍，标志着 AI 大模型进入新纪元...
category: tech_ai
author: AI Content Factory
---

# GPT-5 来了：AI 大模型进入新纪元

OpenAI 今天正式发布了 GPT-5，这是继 GPT-4 之后的又一次重大突破...

## 技术突破

GPT-5 在以下方面实现了重大突破：

1. **推理能力提升 10 倍** - 在复杂推理任务上的表现显著提升
2. **上下文窗口扩展到 1M tokens** - 可以处理更长的文档
3. **多模态能力增强** - 支持图像、音频、视频的理解和生成

## 应用场景

GPT-5 的发布将带来以下应用场景的革新：

- **代码生成** - 更准确的代码理解和生成
- **内容创作** - 更高质量的文章和创意内容
- **数据分析** - 更深入的数据洞察和分析

## 行业影响

GPT-5 的发布将对 AI 行业产生深远影响...

## 总结

GPT-5 的发布标志着 AI 大模型进入新纪元...
```

## Visual Cards HTML Format

**Location:** `content/drafts/<slug>-cards.html`

**Format:** Standalone HTML file with embedded CSS

**Example:**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT-5 来了：AI 大模型进入新纪元</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .card {
            width: 800px;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            margin: 20px auto;
        }
        .card h1 {
            font-size: 48px;
            margin: 0 0 20px 0;
        }
        .card p {
            font-size: 24px;
            opacity: 0.9;
        }
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

## Material Pool JSON Format

**Location:** `content/pool/YYYY-MM-DD-pool.json`

**Schema:**

```json
{
  "date": "2026-03-18",
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
      "published_at": "2026-03-18T10:00:00Z",
      "cluster_id": 1,
      "cluster_size": 3
    }
  ],
  "_output_path": "content/pool/2026-03-18-pool.json",
  "notion_saved": 150
}
```

## Summary Report Format

**Console Output:**

```
============================================================
  批量生产汇总报告
============================================================

  AI 科技方向: 2 篇
  汽车方向: 2 篇
  失败: 0 篇
  总计: 4 篇

  发布结果:
    xiaohongshu: 4 成功, 0 失败
    zhihu: 4 成功, 0 失败

  详细列表:
    1. [AI 科技] GPT-5 来了：AI 大模型进入新纪元 - ✅ 85/100
    2. [AI 科技] Claude 3.5 发布：多模态能力全面升级 - ✅ 82/100
    3. [汽车] 特斯拉 FSD V12 体验：完全自动驾驶真的来了？ - ✅ 88/100
    4. [汽车] 比亚迪秦 PLUS DM-i 深度评测 - ✅ 80/100

============================================================

  结果已保存: content/batch/2026-03-18-143022-batch.json
```
