---
description: 将 Markdown 文件发布到微信公众号草稿箱，自动处理图片上传和格式转换
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: "<markdown文件路径>"
---

# 微信发布

将本地 Markdown 文件发布到微信公众号草稿箱。

## 前置条件
- `.env` 中配置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
- 已安装 `src/wechat_publisher/requirements.txt` 依赖

## 执行

```bash
python src/wechat_publisher/main.py $ARGUMENTS
```

## Markdown Frontmatter 格式

文件需包含 YAML frontmatter：
```yaml
---
title: 文章标题
author: 作者名
digest: 摘要
cover_image: path/to/cover.jpg
---
```

## 处理流程
1. 解析 Markdown frontmatter（标题、作者、封面图）
2. 上传本地图片到微信服务器
3. 替换图片路径为微信 URL
4. Markdown 转 HTML
5. 上传文章到微信草稿箱
