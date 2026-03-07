---
description: 从素材池中按方向（AI科技/汽车）筛选打分，AI 深度分析推荐 3~5 个选题
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: "[direction: tech_ai|auto]"
---

# /plan — 选题策划师

从素材池中按方向筛选、打分，并用 AI 推荐最值得写的选题。

## 工作流

自动查找最新素材池，执行策划 + AI 推荐：

```bash
python src/collector/planner.py --recommend $DIRECTION_ARG
```

脚本会自动输出：
- 筛选统计（X → Y 条）
- 打分摘要（max/avg/min）
- Top 5 素材列表
- AI 推荐的 3-5 个选题（标题、理由、角度、关联素材）

## 使用示例

- `/plan` — 两个方向都分析
- `/plan tech_ai` — 仅 AI 科技方向
- `/plan auto` — 仅汽车方向
