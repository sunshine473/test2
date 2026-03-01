# SKILL 质量审查报告

审查时间：2026-03-01
审查范围：`.claude/skills/` 目录下所有 SKILL 定义及其关联脚本

## 结论概览

- SKILL 定义整体质量较高，frontmatter 格式规范，描述清晰
- 存在若干 P0/P1 问题：脚本参数不匹配、排障指令错误、Notion 查询代码复杂度过高
- 部分 SKILL 定位不清晰，与实际脚本能力不匹配

---

## 主要问题（按严重级别）

### P0 — 阻塞性问题

#### 1. `/publish` Skill 排障指令与实现不一致

**文件**: `.claude/skills/publish/SKILL.md`
**问题**:
- 第 66 行提示用户运行 `python src/publisher/platforms/xiaohongshu.py --login` 重新获取 Cookie
- 但 `xiaohongshu.py` 是一个类定义文件，不是可执行脚本，没有 CLI 入口和 `--login` 参数

**影响**: 用户按文档操作会直接报错 `ModuleNotFoundError`，无法完成排障

**建议修复**:
```markdown
## 🔧 失败排查
- xiaohongshu: Cookie 已过期，请删除 `.browser_state/xiaohongshu_state.json` 后重新运行发布命令，浏览器会自动打开引导登录
- zhihu: Cookie 已过期，请删除 `.browser_state/zhihu_state.json` 后重新运行
- dongchedi: Cookie 已过期，请删除 `.browser_state/dongchedi_state.json` 后重新运行
```

**根本原因**: 浏览器平台使用 `BrowserPublisher` 基类，Cookie 自动持久化到 `.browser_state/` 目录，首次运行或 Cookie 过期时会自动打开浏览器引导手动登录，不需要单独的 `--login` 命令。

---

#### 2. `/write` Skill 中 Notion 查询代码过于复杂且易出错

**文件**: `.claude/skills/write/SKILL.md`
**问题**:
- 第 36-101 行嵌入了 65 行 Python 代码，用于查询 Notion 数据库
- 代码逻辑复杂：需要动态获取标题字段名、判断 data_sources 模式、处理两种不同的查询 API
- 代码中使用了 `$KEYWORDS_JSON` 占位符，需要 SKILL 执行时动态替换为 Python 列表字面量
- 错误处理不完整：`client.data_sources.query` 和 `client.search` 的异常捕获只打印到 stderr，不影响主流程

**影响**:
1. SKILL 执行时需要精确替换 `$KEYWORDS_JSON`，容易出现语法错误
2. 代码复杂度高，维护成本大，与 `notion_output.py` 逻辑重复
3. 如果 Notion API 变更，需要同时修改两处代码

**建议修复**:
将 Notion 查询逻辑封装为独立脚本 `src/collector/notion_search.py`，SKILL 中只调用脚本：

```bash
python src/collector/notion_search.py --keywords "AI编程助手,Copilot,代码生成" --limit 10
```

脚本输出 JSON 格式结果，SKILL 解析后展示给用户。

---

### P1 — 高优先级问题

#### 3. `/collect` Skill 期望与脚本输出不完全对齐

**文件**: `.claude/skills/collect/SKILL.md`
**问题**:
- 第 58-62 行要求输出"各源采集条数"（如 `RSS: X 条 | HN: X 条`）
- 但 `src/collector/main.py` 脚本未提供结构化的分源统计输出
- 当前脚本只输出总条数和去重后条数，无法精确统计各源采集条数

**影响**: SKILL 执行时只能"估算式汇报"，无法给出准确的分源统计

**建议修复**:
在 `src/collector/main.py` 的 `collect_all()` 函数中，记录每个源的采集条数并返回：

```python
def collect_all(config: dict, sources: List[str]) -> tuple[List[CollectedItem], dict]:
    items = []
    stats = {}

    if "rss" in sources:
        print("[1/6] 采集 RSS + YouTube...")
        rss = RSSSource()
        rss_items = rss.collect(config.get("rss", {}))
        items.extend(rss_items)
        stats["rss"] = len(rss_items)

    # ... 其他源同理

    return items, stats
```

在主流程输出时打印分源统计：
```python
print(f"\n采集统计: {' | '.join(f'{k}: {v} 条' for k, v in stats.items())}")
```

---

#### 4. `/write` Skill 定位过于复杂，与实际脚本能力不匹配

**文件**: `.claude/skills/write/SKILL.md`
**问题**:
- SKILL 定位为"内容创作总监"，要求完成"选题分析、素材采集、内容生成、质量审核、元数据补全"全流程
- 但实际脚本 `src/generator/main.py` 只负责调用 Gemini 生成文章和卡片，不包含选题分析、素材采集、质量审核等功能
- SKILL 中大量工作（Step 1 选题分析、Step 2 素材采集、Step 4 质量审核）需要 Claude Code 自己完成，而非脚本输出

**影响**:
1. SKILL 执行时 Claude Code 需要做大量额外工作，执行时间长
2. 用户期望与实际能力不匹配：用户以为 `/write` 会自动完成全流程，但实际上很多步骤需要 Claude Code 临时处理
3. 如果 Claude Code 执行时跳过某些步骤，会导致输出质量不稳定

**建议修复**:
**方案 1（推荐）**: 简化 SKILL 定位，聚焦脚本实际能力

```markdown
# /write — 内容生成器

你的任务是调用 Gemini 生成文章和卡片，并对生成结果进行质量检查。

## SOP 工作流

### Step 1: 执行生成
python src/generator/main.py "$TOPIC" $ARGUMENTS

### Step 2: 质量检查
读取生成的 Markdown 文件，检查：
- 标题是否吸引人
- 结构是否完整（开头→正文→结尾）
- 内容是否有深度
- 字数是否合适（2000-4000 字）

给出整体评分（A/B/C）和修改建议。

### Step 3: Frontmatter 补全
检查并补全 digest、tags、author 字段。
```

**方案 2**: 将 SKILL 中的额外能力封装为独立脚本

如果确实需要"选题分析 + 素材采集 + 生成 + 审核"的全流程能力，应该：
1. 创建 `src/generator/full_pipeline.py` 脚本，封装完整流程
2. SKILL 中只调用这个脚本，而非让 Claude Code 临时处理

---

#### 5. `/search` 和 `/plan` Skill 存在但未在文档中说明

**文件**: `.claude/skills/search/SKILL.md`, `.claude/skills/plan/SKILL.md`
**问题**:
- 这两个 SKILL 在 `README.md` 和 `CLAUDE.md` 中有提及，但在 `docs/开发计划.md` 中没有对应任务
- 不清楚这两个 SKILL 是何时创建的，是否经过验收

**影响**: 协作时容易出现"代码已有但文档未更新"的不一致

**建议修复**:
在 `docs/开发计划.md` 中补充任务记录，或在 `docs/复盘记录.md` 中说明创建背景。

---

### P2 — 低优先级问题

#### 6. `/publish-to-wechat` Skill 已过时

**文件**: `.claude/skills/publish-to-wechat/SKILL.md`
**问题**:
- 这是旧版微信发布 SKILL，调用 `src/wechat_publisher/main.py`
- 新版统一发布框架已将微信迁移到 `src/publisher/platforms/wechat.py`
- 用户应该使用 `/publish --platforms wechat` 而非 `/publish-to-wechat`

**影响**: 用户可能混淆新旧版本，导致重复发布或配置冲突

**建议修复**:
在 SKILL 开头增加废弃提示：

```markdown
# 微信发布（已废弃）

⚠️ **此 SKILL 已废弃，请使用 `/publish --platforms wechat` 代替。**

新版统一发布框架支持微信公众号 + B站/知乎/头条/小红书/懂车帝多平台发布。
```

或直接删除此 SKILL。

---

#### 7. `/get-inspiration` Skill 缺失

**文件**: `.claude/skills/get-inspiration/SKILL.md`
**问题**: Glob 结果显示此文件不存在，但在文档中有提及

**影响**: 用户尝试调用 `/get-inspiration` 会失败

**建议修复**: 确认是否需要此 SKILL，如不需要则从文档中删除引用

---

## 脚本参数验证

### ✅ 参数匹配正确的 SKILL

| SKILL | 脚本 | 参数匹配 |
|-------|------|---------|
| `/collect` | `src/collector/main.py` | ✅ `--sources`, `--direction`, `--search-only`, `--plan-only` 全部匹配 |
| `/search` | `src/collector/search.py` | ✅ `--sources` 匹配 |
| `/plan` | `src/collector/planner.py` | ✅ `--pool`, `--direction` 匹配 |
| `/write` | `src/generator/main.py` | ✅ `topic`, `--sources`, `--no-cards`, `--cards-only` 全部匹配 |
| `/publish` | `src/publisher/main.py` | ✅ `filepath`, `--platforms` 匹配 |
| `/publish-to-wechat` | `src/wechat_publisher/main.py` | ✅ `filepath` 匹配（但 SKILL 已过时） |

### ❌ 参数不匹配或有问题的 SKILL

| SKILL | 问题 | 严重级别 |
|-------|------|---------|
| `/publish` | 排障指令 `--login` 不存在 | P0 |
| `/write` | Notion 查询代码过于复杂 | P0 |
| `/collect` | 分源统计输出缺失 | P1 |

---

## SKILL 质量评分

| SKILL | frontmatter | 描述清晰度 | 脚本匹配度 | 可执行性 | 综合评分 |
|-------|------------|-----------|-----------|---------|---------|
| `/collect` | ✅ 完整 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | A- |
| `/search` | ✅ 完整 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | A |
| `/plan` | ✅ 完整 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | A |
| `/write` | ✅ 完整 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | B |
| `/publish` | ✅ 完整 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | B+ |
| `/publish-to-wechat` | ✅ 完整 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | B（已过时） |

**评分说明**:
- frontmatter: 是否包含完整的 YAML 元数据
- 描述清晰度: 用户是否能理解 SKILL 的作用和使用方法
- 脚本匹配度: SKILL 描述与实际脚本能力是否匹配
- 可执行性: 用户按 SKILL 说明操作是否能成功执行
- 综合评分: A（优秀）/ B（良好）/ C（需改进）

---

## 修复优先级建议

### 立即修复（P0）
1. 修正 `/publish` Skill 中的排障指令（删除 `--login` 相关内容）
2. 将 `/write` Skill 中的 Notion 查询代码封装为独立脚本

### 近期修复（P1）
3. 在 `src/collector/main.py` 中增加分源统计输出
4. 简化 `/write` Skill 定位，或将额外能力封装为脚本
5. 补充 `/search` 和 `/plan` Skill 的任务记录

### 可选优化（P2）
6. 废弃或删除 `/publish-to-wechat` Skill
7. 确认 `/get-inspiration` Skill 是否需要

---

## 总体建议

### 1. SKILL 定位原则
- **SKILL 应该是脚本的薄封装**，而非让 Claude Code 做大量额外工作
- 如果 SKILL 需要复杂的前置处理（如选题分析、素材采集），应该封装为脚本而非写在 SKILL 中
- SKILL 的核心价值是"提供友好的交互界面"和"结果解读"，而非"替代脚本功能"

### 2. 代码复用原则
- 避免在 SKILL 中嵌入复杂的 Python 代码（如 `/write` 中的 Notion 查询）
- 如果需要查询 Notion，应该复用 `src/collector/notion_output.py` 的逻辑，或创建独立的查询脚本

### 3. 文档一致性原则
- SKILL 中的排障指令必须与实际脚本能力匹配
- 新增 SKILL 时应同步更新 `docs/开发计划.md` 和 `README.md`
- 废弃 SKILL 时应在文档中明确标注

### 4. 测试覆盖原则
- 建议为每个 SKILL 编写冒烟测试，验证脚本参数匹配和基本执行流程
- 可以在 `tests/test_skills.py` 中统一管理 SKILL 测试

---

## 附录：SKILL 执行流程建议

### 当前流程（存在问题）
```
用户调用 /write "选题"
  ↓
Claude Code 执行 SKILL
  ↓
Claude Code 做选题分析（临时处理）
  ↓
Claude Code 查询 Notion（执行 65 行 Python 代码）
  ↓
Claude Code 网络搜索（调用 WebSearch 工具）
  ↓
Claude Code 整合素材（临时处理）
  ↓
调用 src/generator/main.py 生成文章
  ↓
Claude Code 质量审核（临时处理）
  ↓
Claude Code 补全 frontmatter（临时处理）
```

### 建议流程（更清晰）
```
用户调用 /write "选题"
  ↓
Claude Code 执行 SKILL
  ↓
调用 src/generator/full_pipeline.py "选题"
  ├─ 脚本内部：选题分析
  ├─ 脚本内部：查询 Notion
  ├─ 脚本内部：网络搜索
  ├─ 脚本内部：整合素材
  ├─ 脚本内部：调用 Gemini 生成
  ├─ 脚本内部：质量审核
  └─ 脚本内部：补全 frontmatter
  ↓
Claude Code 解读脚本输出，展示给用户
```

**优势**:
- SKILL 逻辑简单，易于维护
- 脚本可以独立测试和优化
- 用户可以直接调用脚本，不依赖 Claude Code
