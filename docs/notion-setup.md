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

## 快速开始

### 1. 创建 Notion Integration

1. 访问 https://www.notion.so/my-integrations
2. 点击 "New integration"
3. 填写信息：
   - Name: `Content Factory` (或任意名称)
   - Associated workspace: 选择你的工作区
   - Capabilities: 勾选 "Read content", "Update content", "Insert content"
4. 点击 "Submit"
5. 复制 "Internal Integration Token"（格式：`secret_xxx` 或 `ntn_xxx`）

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# Notion API
NOTION_API_KEY=ntn_xxx  # 你的 Integration Token

# 素材池数据库（如已配置可跳过）
NOTION_DATABASE_ID=你的素材池数据库ID

# 可选：指定父页面 ID（用于自动创建数据库）
NOTION_PARENT_PAGE_ID=你的Notion页面ID
```

### 3. 自动创建数据库

运行以下脚本自动创建 3 个数据库（选题库、草稿库、发布记录）：

```bash
python scripts/create_notion_databases.py
```

脚本会：
- 自动创建 3 个数据库并配置基础字段
- 将数据库 ID 写入 `.env` 文件
- 尝试创建关联字段（可能需要手动补充）

### 4. 配置数据库字段

运行以下脚本确保所有字段完整：

```bash
python scripts/setup_notion_databases.py
```

输出示例：
```
OK 选题库已配置 7 个字段
OK 草稿库已配置 9 个字段
OK 发布记录已配置 5 个字段
成功: 3/3
```

### 5. 创建关联字段

运行以下脚本自动创建关联字段：

```bash
python scripts/create_relations_final.py
```

输出示例：
```
✅ 选题库 '关联草稿' 字段已创建
✅ 草稿库 '关联选题' 字段已创建
✅ 发布记录 '关联草稿' 字段已创建
总计: 3/3 成功
```

**技术说明**：
- Notion API 2025-09-03 版本使用 `data_sources` 架构
- 创建 Relation 字段需要使用 `data_source_id`（不是 `database_id`）
- 正确配置：`type: "single_property"` + `single_property: {}`
   - 选择 "Relation"，命名为 "关联草稿"
   - 关联到草稿库数据库

2. **草稿库 → 选题库**
   - 打开草稿库数据库
   - 添加 Relation 属性，命名为 "关联选题"
   - 关联到选题库数据库

3. **发布记录 → 草稿库**
   - 打开发布记录数据库
   - 添加 Relation 属性，命名为 "关联草稿"
   - 关联到草稿库数据库

### 6. 验证配置

运行以下命令测试 Notion 连接：

```bash
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
A: 是的，首次运行时系统会自动创建缺失的字段（除了关联字段）。但标题字段（Title 类型）必须在数据库创建时就存在。

### Q: 为什么关联字段需要手动创建？
A: Notion API 2025-09-03 版本对关联字段（Relation）的创建有复杂的验证要求（需要 `data_source_id` 和 `single_property`/`dual_property` 配置），手动在 UI 中创建更可靠。

### Q: 可以使用现有的数据库吗？
A: 可以，但需要确保数据库中有一个 Title 类型的字段，其他字段会自动补充。

### Q: 如何查看 Notion 中的数据？
A: 直接在 Notion 中打开对应的数据库页面，可以看到所有同步的数据。

### Q: 脚本提示 "data_sources" 相关错误怎么办？
A: 这是正常的。新版 Notion API 使用 data_sources 架构，脚本会自动适配。如果数据库是旧版创建的，会使用传统的 `databases.update()` 方法。

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
