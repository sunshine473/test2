---
description: 根据选题生成公众号长文 + 视觉卡片 HTML，输出到 content/drafts/
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '"选题标题" [--sources url1,url2] [--no-cards] [--cards-only]'
---

# /write — 内容生成器

根据选题生成文章和卡片，自动审核质量并补全元数据。

## 工作流

调用生成脚本：

```bash
python src/generator/main.py "$TOPIC" $ARGS
```

脚本会自动完成：
1. 生成文章（调用 Gemini）
2. AI 质量审核（标题、结构、深度、风格）
3. 补全 frontmatter（digest、tags）
4. 生成视觉卡片（如未指定 --no-cards）

输出包含：
- 文章路径和字数
- 质量评估（A/B/C 评级 + 各维度评分）
- 补全的 frontmatter 字段

## 使用示例

- `/write "AI编程助手的未来"` — 完整流程
- `/write "GPT-5发布解读" --sources https://...` — 带素材 URL
- `/write "Rust vs Go" --no-cards` — 仅生成文章
- `/write "周报" --cards-only` — 仅生成卡片（需已有文章）
