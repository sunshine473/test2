---
description: >
  批量内容生产：自动生成多篇文章并发布到指定平台。默认生成 8 篇文章（AI 科技 2 篇 + 汽车 2 篇）
  并发布到小红书和知乎。支持自定义数量和平台。全自动执行：素材搜索 → 选题策划 → AI 选题 →
  批量生成 → AI 审核 → 多平台发布。
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '[--count N] [--platforms xiaohongshu,zhihu]'
---

# /batch-factory — 批量内容生产

自动生成多篇文章并发布到指定平台。

## 工作流

```
素材搜索 → 选题策划 → 批量生成 → AI审核 → 多平台发布
(一次)    (两方向)    (每方向N篇)  (自动)    (指定平台)
```

**默认配置**：
- 每个方向生成 2 篇文章
- 发布平台：小红书 + 知乎
- 总计：4 篇文章（AI 科技 2 篇 + 汽车 2 篇）× 2 平台 = 8 次发布

## 基础用法

### 默认模式（推荐）
```bash
python src/pipeline/batch_pipeline.py
```

**输出**：
- AI 科技方向：2 篇文章
- 汽车方向：2 篇文章
- 发布平台：小红书、知乎
- 总计：4 篇文章，8 次发布

### 自定义数量
```bash
# 每个方向生成 3 篇（总计 6 篇）
python src/pipeline/batch_pipeline.py --count 3
```

### 自定义平台
```bash
# 只发布到小红书
python src/pipeline/batch_pipeline.py --platforms xiaohongshu

# 发布到多个平台
python src/pipeline/batch_pipeline.py --platforms xiaohongshu,zhihu,bilibili
```

### 组合使用
```bash
# 每个方向 4 篇，发布到小红书和知乎
python src/pipeline/batch_pipeline.py --count 4 --platforms xiaohongshu,zhihu
```

## 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--count` | 每个方向生成的文章数量 | 2 | `--count 3` |
| `--platforms` | 发布平台（逗号分隔） | xiaohongshu,zhihu | `--platforms xiaohongshu` |
| `--sources` | 素材来源（逗号分隔） | 全部 | `--sources hn,github` |
| `--no-cards` | 不生成视觉卡片 | False | `--no-cards` |

## 执行流程

### 阶段 1: 素材搜索（1 次）
- 从多个信息源采集素材
- 去重聚类
- 输出素材池

### 阶段 2: 选题策划（2 个方向）
- AI 科技方向：筛选 + 打分 + AI 推荐 3-5 个选题
- 汽车方向：筛选 + 打分 + AI 推荐 3-5 个选题

### 阶段 3: 批量生成（每方向 N 篇）
对每个选题：
1. 生成文章内容
2. 生成视觉卡片（可选）
3. AI 质量审核（6 维度评分）
4. 审核不通过自动重写

### 阶段 4: 多平台发布
- 每篇文章发布到指定平台
- 记录发布结果
- 生成汇总报告

## 输出示例

```
============================================================
  批量内容生产流水线
  每个方向生成: 2 篇
  发布平台: xiaohongshu,zhihu
============================================================

[阶段 1/4] 素材搜索
  素材池 150 条: content/pool/2026-03-18-pool.json

[阶段 2/4] 选题策划
  === AI 科技 推荐选题 ===
  1. GPT-5 来了：AI 大模型进入新纪元 (92.5)
  2. Claude 3.5 发布：多模态能力全面升级 (89.0)
  3. AI 编程助手对比：GitHub Copilot vs Cursor (85.5)

  === 汽车 推荐选题 ===
  1. 特斯拉 FSD V12 体验：完全自动驾驶真的来了？ (91.0)
  2. 比亚迪秦 PLUS DM-i 深度评测 (87.5)

[阶段 3/4] 批量生成内容（每个方向 2 篇）

  === AI 科技 方向 ===

  [1/2] 生成: GPT-5 来了：AI 大模型进入新纪元
    草稿已生成: content/drafts/gpt-5-来了-ai-大模型进入新纪元.md
    正在进行 AI 质量审核...
    质量评分: 85/100
    ✅ 审核通过
    ✅ 完成: content/drafts/gpt-5-来了-ai-大模型进入新纪元.md
    📊 审核评分: 85/100

  [2/2] 生成: Claude 3.5 发布：多模态能力全面升级
    草稿已生成: content/drafts/claude-3-5-发布-多模态能力全面升级.md
    正在进行 AI 质量审核...
    质量评分: 82/100
    ✅ 审核通过
    ✅ 完成: content/drafts/claude-3-5-发布-多模态能力全面升级.md
    📊 审核评分: 82/100

  === 汽车 方向 ===

  [1/2] 生成: 特斯拉 FSD V12 体验：完全自动驾驶真的来了？
    草稿已生成: content/drafts/特斯拉-fsd-v12-体验.md
    正在进行 AI 质量审核...
    质量评分: 88/100
    ✅ 审核通过
    ✅ 完成: content/drafts/特斯拉-fsd-v12-体验.md
    📊 审核评分: 88/100

  [2/2] 生成: 比亚迪秦 PLUS DM-i 深度评测
    草稿已生成: content/drafts/比亚迪秦-plus-dm-i-深度评测.md
    正在进行 AI 质量审核...
    质量评分: 80/100
    ✅ 审核通过
    ✅ 完成: content/drafts/比亚迪秦-plus-dm-i-深度评测.md
    📊 审核评分: 80/100

[阶段 4/4] 批量生产完成

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

## 输出文件

### 草稿文件
```
content/drafts/
├── gpt-5-来了-ai-大模型进入新纪元.md
├── gpt-5-来了-ai-大模型进入新纪元-cards.html
├── claude-3-5-发布-多模态能力全面升级.md
├── claude-3-5-发布-多模态能力全面升级-cards.html
├── 特斯拉-fsd-v12-体验.md
├── 特斯拉-fsd-v12-体验-cards.html
├── 比亚迪秦-plus-dm-i-深度评测.md
└── 比亚迪秦-plus-dm-i-深度评测-cards.html
```

### 批量结果 JSON
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
  }
]
```

## 常见问题

**Q: 如何只生成不发布？**
A: 暂不支持，可以在 `publishers.yaml` 中禁用所有平台

**Q: 如何指定只生成某个方向？**
A: 暂不支持，批量模式会生成两个方向

**Q: 审核不通过会怎样？**
A: 自动重写，最多重试 3 次

**Q: 发布失败会怎样？**
A: 记录失败原因，继续处理下一篇

**Q: 如何查看详细日志？**
A: 每篇文章的流水线状态保存在 `content/pipeline/<pipeline_id>.json`

## 与单篇模式对比

| 特性 | 单篇模式 (/factory) | 批量模式 (/batch-factory) |
|------|-------------------|------------------------|
| 素材搜索 | 每次执行 | 只执行一次 |
| 选题策划 | 每次执行 | 只执行一次 |
| 生成数量 | 1 篇 | N 篇 × 2 方向 |
| 发布平台 | 可指定 | 可指定 |
| 执行时间 | 快 | 慢（N 倍） |
| 适用场景 | 单篇文章 | 批量生产 |

## 性能估算

假设每篇文章生成 + 审核 + 发布需要 5 分钟：

- 2 篇/方向（默认）：约 20 分钟（4 篇 × 5 分钟）
- 3 篇/方向：约 30 分钟（6 篇 × 5 分钟）
- 4 篇/方向：约 40 分钟（8 篇 × 5 分钟）

**建议**：首次使用建议 `--count 1` 测试流程。
