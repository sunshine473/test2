---
description: 将 Markdown 文章发布到微信公众号及其他平台（B站/知乎/头条/小红书/懂车帝）
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '<markdown文件路径> [--platforms wechat,bilibili,zhihu]'
---

# /publish — 分发运营官

将文章发布到多个平台，支持 AI 推荐平台组合。

## 工作流

### 1. AI 推荐平台（可选）

如果用户未指定平台，先用 AI 分析推荐：

```bash
python src/publisher/main.py "$FILEPATH" --suggest
```

展示推荐结果，等用户确认。

### 2. 执行发布

```bash
python src/publisher/main.py "$FILEPATH" $PLATFORMS_ARG
```

脚本会自动：
- 解析 frontmatter（title、digest、tags、cover_image）
- 提取配套卡片图（从 -cards.html）
- 逐平台发布并报告结果

### 3. 结果汇总

展示发布结果表格：

```
| 平台 | 状态 | 说明 |
|------|------|------|
| wechat | ✅ 成功 | 已推送到草稿箱 |
| zhihu | ✅ 成功 | 已发布为草稿 |
| xiaohongshu | ❌ 失败 | Cookie 过期 |
```

失败平台给出排查建议。

## 支持平台

| 平台 | 状态 | 认证方式 |
|------|------|---------|
| wechat | ✅ 可用 | WECHAT_APP_ID + WECHAT_APP_SECRET |
| bilibili | 🔧 骨架 | BILIBILI_SESSDATA + BILIBILI_BILI_JCT |
| zhihu | ✅ 可用 | Playwright Cookie |
| toutiao | 🔧 骨架 | Playwright Cookie |
| xiaohongshu | ✅ 可用 | Playwright Cookie |
| dongchedi | ✅ 可用 | Playwright Cookie |

## 使用示例

- `/publish content/drafts/2026-02-20-xxx.md` — AI 推荐平台
- `/publish content/drafts/2026-02-20-xxx.md --platforms wechat` — 仅微信
- `/publish content/drafts/2026-02-20-xxx.md --platforms wechat,zhihu,xiaohongshu` — 指定多平台
