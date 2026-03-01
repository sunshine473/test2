---
description: 根据选题生成公众号长文 + 视觉卡片 HTML，输出到 content/drafts/
user-invocable: true
allowed-tools: Bash(python:*), Read, Write, Edit, WebFetch, WebSearch, Glob, Grep
argument-hint: '"选题标题" [--sources url1,url2] [--no-cards] [--cards-only]'
---

# /write — 内容生成器

你的任务是调用 Gemini 生成文章和卡片，并对生成结果进行质量检查和元数据补全。

## 账号定位

AI/编程/科技方向公众号，目标读者是开发者和科技爱好者。文风要求：专业但不晦涩，有观点有深度，适当口语化。

## SOP 工作流

### Step 1: 选题分析（可选）

如果选题不够明确，先做简要分析：
- 目标读者是谁？他们关心什么？
- 文章核心论点是什么？
- 建议的文章框架（如：现象引入→技术解析→实践建议→趋势展望）

### Step 2: 素材采集（可选）

如果需要补充素材，可以：

#### 2a. 查询 Notion 素材库

提取选题中的 3-5 个关键词，查询 Notion 已有素材：

```bash
python src/collector/notion_search.py --keywords "关键词1,关键词2,关键词3" --limit 10
```

如果 Notion 未配置或查询失败，跳过此步。

#### 2b. 网络搜索

用关键词通过 WebSearch 工具搜索最新相关信息，筛选 5-8 条高价值结果。

#### 2c. 用户指定 URL

如果用户提供了 `--sources url1,url2`，用 WebFetch 抓取内容。

#### 2d. 素材整合

将素材整理为纯文本列表，写入临时文件 `content/drafts/.sources-temp.txt`：

```
标题1
URL: https://...
要点: ...

标题2
URL: https://...
要点: ...
```

### Step 3: 内容生成

执行生成脚本：

```bash
python src/generator/main.py "$TOPIC" --sources content/drafts/.sources-temp.txt $OTHER_ARGS
```

如果素材较少（<3 条）或用户明确不需要素材，可以不带 `--sources` 运行。

等待 Gemini 生成完成，记录输出文件路径。生成完成后删除临时素材文件。

### Step 4: 质量审核

读取生成的 Markdown 文件，进行 AI 自评：

**检查清单：**
- **标题吸引力**：是否能引发点击欲望？给出改进建议（如有）
- **结构完整性**：是否有清晰的 开头引入→正文论述→结尾总结？
- **内容深度**：是否有干货和独特观点，而非泛泛而谈？
- **事实准确性**：是否有明显的事实性错误或过时信息？
- **字数评估**：公众号最佳阅读长度 2000-4000 字，当前字数是否合适？
- **风格一致性**：是否符合账号定位（专业但不晦涩）？

给出整体质量评分（A/B/C）和具体修改建议。

### Step 5: Frontmatter 补全

读取生成的 Markdown 文件，检查 frontmatter 字段。如果以下字段缺失或为空，自动生成并写入：

- **digest**：100 字以内的文章摘要，用于公众号分享描述
- **tags**：3-5 个话题标签，如 `AI, 编程, GPT`
- **author**：如果为空，写入默认值 `AI技术前沿`

使用 Edit 工具直接修改文件中的 frontmatter 部分。

### Step 6: 向用户呈现

输出格式：

```
## ✍️ 生成完成

**文件路径**: content/drafts/2026-xx-xx-xxx.md
**卡片路径**: content/drafts/2026-xx-xx-xxx-cards.html（如有）
**字数**: X 字
**素材来源**: Notion X 条 / 网搜 X 条 / 用户指定 X 条（如有）

## 📋 质量评估: [A/B/C]

| 维度 | 评分 | 说明 |
|------|------|------|
| 标题吸引力 | ⭐⭐⭐⭐ | ... |
| 结构完整性 | ⭐⭐⭐⭐⭐ | ... |
| 内容深度 | ⭐⭐⭐⭐ | ... |
| 素材引用 | ⭐⭐⭐⭐ | ... |
| 风格一致性 | ⭐⭐⭐⭐ | ... |

## 📝 修改建议
- ...（如有）

## 📄 Frontmatter
- digest: [已补全的摘要]
- tags: [已补全的标签]

---
💡 满意的话，直接 `/publish content/drafts/xxx.md` 发布
```

## 使用示例

- `/write "AI编程助手的未来"` — 完整流程：生成→审核→补全
- `/write "GPT-5发布解读" --sources https://...` — 带素材 URL
- `/write "Rust vs Go" --no-cards` — 仅生成文章，不生成卡片
- `/write "周报" --cards-only` — 仅生成卡片（需已有文章）

## 注意事项

- Step 1 和 Step 2 是可选的，如果用户说"直接写"或选题已经很明确，可以跳过
- Notion 查询失败不应阻塞流程，跳过即可
- 素材采集应该快速完成（<2 分钟），不要过度搜索
