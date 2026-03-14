# Notion 数据中枢配置指南

本项目使用 Notion 作为数据中枢，管理从素材采集到发布的全流程数据。

## 架构概览

```
素材池数据库 (Material Pool)
    ↓
选题库数据库 (Topic Library)
    ↓
草稿库数据库 (Draft Library)
    ↓
发布记录数据库 (Publish Records)
```

## 配置步骤

### 1. 创建 Notion Integration

1. 访问 https://www.notion.so/my-integrations
2. 点击 "New integration"
3. 填写信息：
   - Name: `Content Factory` (或任意名称)
   - Associated workspace: 选择你的工作区
   - Capabilities: 勾选 "Read content", "Update content", "Insert content"
4. 点击 "Submit"
5. 复制 "Internal Integration Token"（格式：`secret_xxx` 或 `ntn_xxx`）

### 2. 创建 4 个 Notion 数据库

#### 2.1 素材池数据库 (Material Pool)

1. 在 Notion 中创建新数据库（Database - Full page）
2. 命名为 "素材池" 或 "Material Pool"
3. 点击右上角 "..." → "Add connections" → 选择你的 Integration
4. 复制数据库 ID（URL 中的 32 位字符串）
   - 示例 URL: `https://notion.so/workspace/b1edb28f8f5a45d984c6bc2aee14ad11`
   - 数据库 ID: `b1edb28f8f5a45d984c6bc2aee14ad11`

**字段说明**（系统会自动创建）：
- 名称（Title）：标题
- URL（URL）：素材链接
- 来源（Select）：信息源
- 采集方式（Select）：RSS/API/Search
- 分类（Select）：AI/汽车/科技等
- 摘要（Rich Text）：内容摘要
- 语言（Select）：zh-CN/en
- 采集日期（Date）：采集时间
- 文章发布时间（Date）：原文发布时间
- 评分（Number）：AI 打分（0-100）
- 方向（Multi-select）：AI科技/汽车
- 状态（Select）：待筛选/已推荐/已选用/已忽略

#### 2.2 选题库数据库 (Topic Library)

1. 创建新数据库，命名为 "选题库" 或 "Topic Library"
2. 添加 Integration 连接
3. 复制数据库 ID

**字段说明**（系统会自动创建）：
- 选题标题（Title）：选题名称
- 方向（Select）：AI科技/汽车
- 评分（Number）：AI 推荐分数
- 推荐理由（Rich Text）：AI 生成的推荐理由
- 关联素材（Rich Text）：素材 URL 列表
- 状态（Select）：待选择/已选中/已生成/已发布/已放弃
- 推荐日期（Date）：策划时间
- 选中日期（Date）：人工选题时间
- 关联草稿（Relation）：关联到草稿库

#### 2.3 草稿库数据库 (Draft Library)

1. 创建新数据库，命名为 "草稿库" 或 "Draft Library"
2. 添加 Integration 连接
3. 复制数据库 ID

**字段说明**（系统会自动创建）：
- 文章标题（Title）：草稿标题
- 文件路径（URL）：本地 Markdown 文件路径
- 字数（Number）：文章字数
- 质量评级（Select）：A/B/C
- 质量评分（Rich Text）：各维度评分详情
- 标签（Multi-select）：文章标签
- 摘要（Rich Text）：文章摘要
- 状态（Select）：待审核/审核通过/需修改/已发布
- 生成日期（Date）：创建时间
- 审核日期（Date）：审核时间
- 关联选题（Relation）：关联到选题库

#### 2.4 发布记录数据库 (Publish Records)

1. 创建新数据库，命名为 "发布记录" 或 "Publish Records"
2. 添加 Integration 连接
3. 复制数据库 ID

**字段说明**（系统会自动创建）：
- 标题（Title）：发布标题
- 平台（Select）：微信/知乎/B站/小红书/懂车帝/头条
- 状态（Select）：成功/失败/草稿
- 发布链接（URL）：发布后的链接
- 发布消息（Rich Text）：发布结果详情
- 发布日期（Date）：发布时间
- 关联草稿（Relation）：关联到草稿库

### 3. 配置环境变量

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# Notion API
NOTION_API_KEY=ntn_xxx  # 你的 Integration Token

# 素材池数据库（已有）
NOTION_DATABASE_ID=b1edb28f8f5a45d984c6bc2aee14ad11

# 选题库数据库
NOTION_TOPICS_DB_ID=你的选题库数据库ID

# 草稿库数据库
NOTION_DRAFTS_DB_ID=你的草稿库数据库ID

# 发布记录数据库
NOTION_PUBLISH_DB_ID=你的发布记录数据库ID
```

### 4. 验证配置

运行以下命令测试 Notion 连接：

```bash
# 测试素材池写入（已有功能）
python src/collector/search.py --sources hn

# 测试选题库写入
python src/collector/planner.py --recommend

# 测试草稿库写入
python src/generator/main.py "测试选题"

# 测试发布记录写入
python src/publisher/main.py content/drafts/xxx.md --platforms wechat
```

## 数据流说明

### 采集阶段
- 脚本：`src/collector/search.py`
- 写入：素材池数据库
- 状态：待筛选

### 策划阶段
- 脚本：`src/collector/planner.py --recommend`
- 写入：选题库数据库
- 更新：素材池状态 → 已推荐

### 生成阶段
- 脚本：`src/generator/main.py`
- 写入：草稿库数据库
- 更新：选题库状态 → 已生成

### 发布阶段
- 脚本：`src/publisher/main.py`
- 写入：发布记录数据库
- 更新：草稿库状态 → 已发布

## 常见问题

### Q: 如何获取数据库 ID？
A: 打开数据库页面，URL 中 `?v=` 之前的 32 位字符串就是数据库 ID。

### Q: 提示 "NOTION_TOPICS_DB_ID 未设置" 怎么办？
A: 确保在 `.env` 文件中配置了对应的数据库 ID，并重启脚本。

### Q: 字段会自动创建吗？
A: 是的，首次运行时系统会自动创建缺失的字段。但标题字段（Title 类型）必须手动创建。

### Q: 可以使用现有的数据库吗？
A: 可以，但需要确保数据库中有一个 Title 类型的字段，其他字段会自动补充。

### Q: 如何查看 Notion 中的数据？
A: 直接在 Notion 中打开对应的数据库页面，可以看到所有同步的数据。

## 进阶配置

### 自定义字段映射
如果你的 Notion 数据库使用了不同的字段名，可以修改对应模块中的 `_ensure_schema()` 方法。

### 关联关系
选题库、草稿库、发布记录之间通过 Relation 字段关联，可以在 Notion 中追踪完整的内容生产链路。

### 视图和筛选
在 Notion 中可以创建多个视图：
- 按状态筛选（待处理/进行中/已完成）
- 按方向分组（AI科技/汽车）
- 按日期排序（最新优先）
- 看板视图（Kanban）追踪流程
