---
description: 采集多源素材（RSS/HN/GitHub/热搜/YouTube），执行去重聚类与打分排序，强制同步到 Notion
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: "[sources]"
---

# 素材采集

根据用户指定的采集源（默认 rss,hn,github,hot,tavily,youtube_api）执行素材采集流程。

## 步骤

1. 进入项目根目录
2. 执行采集命令：

如果用户提供了参数 "$ARGUMENTS"，则作为 `--sources` 参数传入：
```bash
python src/collector/main.py --sources $ARGUMENTS
```

如果没有参数，使用默认源：
```bash
python src/collector/main.py
```

3. 等待采集完成，向用户汇报：
   - 各源采集条数
   - 去重聚类结果
   - 打分排序摘要（最高分/平均分/最低分）
   - Notion 同步状态

## 可用采集源

- `rss` — RSS 订阅 + YouTube 频道
- `hn` — Hacker News（Algolia API）
- `github` — GitHub Trending
- `hot` — 微博/百度热搜（TopHub）
- `youtube_api` — YouTube Data API v3（需 YOUTUBE_API_KEY）
- `tavily` — Tavily 搜索（需 TAVILY_API_KEY）
- `twitter` — X/Twitter via Tavily（需 TAVILY_API_KEY）

## 使用示例

- `/collect` — 默认采集（rss,hn,github,hot,tavily,youtube_api）
- `/collect hn,github` — 仅采集 HN 和 GitHub
- `/collect rss,hn,github,youtube_api` — 包含 YouTube API
