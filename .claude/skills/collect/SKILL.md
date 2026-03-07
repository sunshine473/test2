---
description: 一键采集（搜索+策划）：采集多源素材，去重聚类，按方向打分排序，推荐选题
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: "[sources] [--direction tech_ai|auto]"
---

# /collect — 一键采集（搜索 + 策划）

一键完成素材采集、去重聚类、打分排序、AI 选题推荐。

## 工作流

执行一键采集：

```bash
python src/collector/main.py $SOURCES_ARG $DIRECTION_ARG
```

然后调用 AI 推荐：

```bash
python src/collector/planner.py --recommend $DIRECTION_ARG
```

脚本会自动输出：
- 采集统计（各源条数、去重聚类结果）
- 每个方向的 AI 推荐选题（3-5 个）

## 使用示例

- `/collect` — 默认采集 + 两方向推荐
- `/collect hn,github` — 仅采集 HN 和 GitHub
- `/collect --direction tech_ai` — 仅 AI 科技方向
