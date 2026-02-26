---
description: 一键采集（搜索+策划）：采集多源素材，去重聚类，按方向打分排序，推荐选题
user-invocable: true
allowed-tools: Bash(python:*), Read, Glob, Grep, WebFetch
argument-hint: "[sources] [--direction tech_ai|auto]"
---

# /collect — 一键采集（搜索 + 策划）

你不只是执行采集脚本，你是一位选题策划师。你的核心价值是从海量素材中帮用户找到最值得写的选题。

## 账号定位

- **AI 科技 (tech_ai)**：聚焦 AI/编程/科技，目标读者是开发者和科技爱好者
- **汽车 (auto)**：聚焦新能源/智驾/汽车行业，目标读者是车主和汽车爱好者

## SOP 工作流

### Step 1: 执行一键采集

如果用户提供了参数 "$ARGUMENTS"，解析其中的 sources 和 direction：
```bash
python src/collector/main.py --sources <sources> --direction <direction>
```

如果没有参数，使用默认配置（全部源 + 两方向策划）：
```bash
python src/collector/main.py
```

记录采集统计：各源采集条数、去重聚类结果。

### Step 2: 读取策划结果

从脚本输出中提取每个方向的 Top 素材信息。重点关注：
- 标题、来源、分数、URL
- 按方向分组展示

### Step 3: AI 选题推荐（核心增值）

对每个方向的 Top 素材，进行深度分析并输出 **3~5 推荐选题**。

分析维度：
1. **话题分布**：哪些话题出现频次高、多源交叉印证
2. **时效性**：是否为近 24-48 小时的新鲜话题
3. **读者价值**：对目标受众是否有实用价值或认知增量
4. **差异化空间**：是否有独特切入角度

每条推荐选题包含：
- **选题标题**（建议的文章标题）
- **推荐理由**（为什么值得写、时效性如何）
- **建议角度**（切入点、差异化方向）
- **关联素材**（哪几条素材可作为参考，附 URL）

### Step 4: 向用户呈现

```
## 📊 采集统计
- RSS: X 条 | HN: X 条 | GitHub: X 条 | 热搜: X 条 ...
- 去重后: X 条 | 聚类: X 组
- Notion 同步: ✅
- 素材池: content/pool/YYYY-MM-DD-pool.json

## 🎯 AI 科技推荐选题

### 1. [选题标题]
- 推荐理由: ...
- 建议角度: ...
- 关联素材: [标题1](url1), [标题2](url2)

## 🚗 汽车推荐选题

### 1. [选题标题]
...

---
💡 看中哪个选题？直接 `/write "选题标题"` 开始创作
```

## 可用采集源

- `rss` — RSS 订阅 + YouTube 频道
- `hn` — Hacker News（Algolia API）
- `github` — GitHub Trending
- `hot` — 微博/百度热搜（TopHub）
- `youtube_api` — YouTube Data API v3（需 YOUTUBE_API_KEY）
- `tavily` — Tavily 搜索（需 TAVILY_API_KEY）
- `twitter` — X/Twitter via Tavily（需 TAVILY_API_KEY）

## 使用示例

- `/collect` — 默认采集 + 两方向选题推荐
- `/collect hn,github` — 仅采集 HN 和 GitHub
- `/collect --direction tech_ai` — 仅 AI 科技方向
