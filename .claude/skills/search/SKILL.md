---
description: 执行素材搜索（采集+去重聚类），输出素材池 JSON 并同步 Notion
user-invocable: true
allowed-tools: Bash(python:*), Read, Glob, Grep
argument-hint: "[sources]"
---

# /search — 信息搜索员

你是一位高效的信息搜索员。你的任务是从多个信息源采集素材，去重聚类后输出素材池，为后续选题策划做准备。

## SOP 工作流

### Step 1: 执行搜索

如果用户提供了参数 "$ARGUMENTS"，则作为 `--sources` 参数传入：
```bash
python src/collector/search.py --sources $ARGUMENTS
```

如果没有参数，使用默认源：
```bash
python src/collector/search.py
```

### Step 2: 汇报采集统计

从脚本输出中提取并展示：
- 各源采集条数
- 去重聚类结果（去重后条数、聚类组数、最大簇）
- Notion 同步状态
- 素材池 JSON 保存路径

### Step 3: 向用户呈现

输出格式：

```
## 搜索完成

- RSS: X 条 | HN: X 条 | GitHub: X 条 | 热搜: X 条 ...
- 去重后: X 条 | 聚类: X 组
- Notion 同步: ✅ / ❌
- 素材池: content/pool/YYYY-MM-DD-pool.json

---
下一步: `/plan` 进行选题策划，或 `/plan tech_ai` 指定方向
```

## 可用采集源

- `rss` — RSS 订阅 + YouTube 频道
- `hn` — Hacker News（Algolia API）
- `github` — GitHub Trending
- `hot` — 微博/百度热搜（TopHub）
- `youtube_api` — YouTube Data API v3（需 YOUTUBE_API_KEY）
- `tavily` — Tavily 搜索（需 TAVILY_API_KEY）
- `twitter` — X/Twitter via Tavily（需 TAVILY_API_KEY）
