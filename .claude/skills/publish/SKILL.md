---
description: 将 Markdown 文章发布到微信公众号及其他平台（B站/知乎/头条/小红书/懂车帝）
user-invocable: true
allowed-tools: Bash(python:*), Read
argument-hint: '<markdown文件路径> [--platforms wechat,bilibili,zhihu]'
---

# /publish — 内容发布

将 `content/drafts/` 或 `content/ready/` 中的 Markdown 文章发布到指定平台。

## 用法

```bash
/publish content/drafts/2026-02-20-xxx.md                    # 发布到所有 enabled 平台
/publish content/drafts/2026-02-20-xxx.md --platforms wechat  # 仅发布到微信
```

## 执行步骤

1. 运行发布命令：
   ```bash
   python src/publisher/main.py $ARGUMENTS
   ```

2. 检查输出，确认各平台发布结果。

## 支持平台

| 平台 | 状态 | 认证方式 |
|------|------|---------|
| wechat | 可用 | WECHAT_APP_ID + WECHAT_APP_SECRET |
| bilibili | 骨架 | BILIBILI_SESSDATA + BILIBILI_BILI_JCT |
| zhihu | 骨架 | Playwright Cookie |
| toutiao | 骨架 | Playwright Cookie |
| xiaohongshu | 骨架 | Playwright Cookie |
| dongchedi | 骨架 | Playwright Cookie |

## 配置

平台开关在 `src/config/publishers.yaml`，敏感信息在 `.env`。
