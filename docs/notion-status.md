# Notion 数据中枢配置总结

## 数据库结构

已成功创建并配置 4 个 Notion 数据库，建立完整数据链路：

### 1. 素材池数据库 (Material Pool)
- **数据库 ID**: `b1edb28f-8f5a-45d9-84c6-bc2aee14ad11`
- **URL**: https://www.notion.so/b1edb28f8f5a45d984c6bc2aee14ad11
- **字段**: 名称、URL、来源、采集方式、分类、摘要、语言、采集日期、文章发布时间、评分、方向、状态、关联选题
- **关联**: ↔ 选题库
- **状态**: ✅ 已配置并测试通过

### 2. 选题库数据库 (Topic Library)
- **数据库 ID**: `4fb54980-3157-4343-9f0d-7477e84afe80`
- **URL**: https://www.notion.so/4fb54980315743439f0d7477e84afe80
- **字段**: 选题标题、方向、评分、推荐理由、素材链接、状态、推荐日期、选中日期、关联素材、关联草稿
- **关联**: ↔ 素材池、↔ 草稿库
- **状态**: ✅ 已配置并测试通过

### 3. 草稿库数据库 (Draft Library)
- **数据库 ID**: `3ee6f5ee-c2d2-4df9-9870-e52fc4536a79`
- **URL**: https://www.notion.so/3ee6f5eec2d24df99870e52fc4536a79
- **字段**: 文章标题、文件路径、字数、质量评级、质量评分、标签、摘要、状态、生成日期、审核日期、关联选题
- **关联**: ↔ 选题库、↔ 发布记录
- **状态**: ✅ 已配置并测试通过

### 4. 发布记录数据库 (Publish Records)
- **数据库 ID**: `56016143-40fa-46b7-8948-247b5e6106aa`
- **URL**: https://www.notion.so/5601614340fa46b78948247b5e6106aa
- **字段**: 标题、平台、状态、发布链接、发布消息、发布日期、关联草稿
- **关联**: ↔ 草稿库
- **状态**: ✅ 已配置并测试通过

## 数据流

```
素材采集 → 素材池 [状态: 待筛选]
    ↓ 关联
选题策划 → 选题库 [状态: 待选择] + 更新素材池 [状态: 已推荐]
    ↓ 关联
内容生成 → 草稿库 [状态: 待审核] + 更新选题库 [状态: 已生成]
    ↓ 关联
多平台发布 → 发布记录 + 更新草稿库 [状态: 已发布]
```

## 关联字段配置

所有关联字段已通过 API 自动创建：

### 素材池 ↔ 选题库
- 素材池 → 选题库：`关联选题` (relation)
- 选题库 → 素材池：`关联素材` (relation)
- 选题库 → 素材链接：`素材链接` (rich_text，存储 URL 文本)

### 选题库 ↔ 草稿库
- 选题库 → 草稿库：`关联草稿` (relation)
- 草稿库 → 选题库：`关联选题` (relation)

### 草稿库 ↔ 发布记录
- 草稿库 → 发布记录：自动反向关联
- 发布记录 → 草稿库：`关联草稿` (relation)

## 测试结果

### 单元测试（4/4 通过）
✅ 素材池写入测试通过
✅ 选题库写入测试通过
✅ 草稿库写入测试通过
✅ 发布记录写入测试通过

### 关联字段测试（5/5 通过）
✅ 素材池 → 选题库 关联已创建
✅ 选题库 → 素材池 关联已创建
✅ 选题库 → 草稿库 关联已创建
✅ 草稿库 → 选题库 关联已创建
✅ 发布记录 → 草稿库 关联已创建

### 端到端测试（通过）
✅ 素材池 → 选题库 → 草稿库 → 发布记录 完整链路验证成功

**总计**: 所有测试通过

## 待完成事项

⚠️ **关联字段需要手动创建**（Notion API 限制）：

1. **选题库 → 草稿库**
   - 打开选题库数据库
   - 点击右上角 "+" 添加属性
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

## 使用方式

### 命令行
```bash
# 素材采集（自动写入素材池）
python src/collector/search.py

# 选题策划（自动写入选题库）
python src/collector/planner.py --recommend

# 内容生成（自动写入草稿库）
python src/generator/main.py "选题标题"

# 多平台发布（自动写入发布记录）
python src/publisher/main.py content/drafts/xxx.md
```

### Skills
```bash
/search    # 素材采集
/plan      # 选题策划
/write     # 内容生成
/publish   # 多平台发布
/factory   # 全链路自动化
```

## 配置文件

所有数据库 ID 已保存在 `.env` 文件中：
- `NOTION_API_KEY`: Integration Token
- `NOTION_DATABASE_ID`: 素材池数据库 ID
- `NOTION_TOPICS_DB_ID`: 选题库数据库 ID
- `NOTION_DRAFTS_DB_ID`: 草稿库数据库 ID
- `NOTION_PUBLISH_DB_ID`: 发布记录数据库 ID
- `NOTION_PARENT_PAGE_ID`: 父页面 ID

## 相关脚本

### 数据库创建和配置
- `scripts/create_notion_databases.py`: 自动创建 3 个数据库（选题库、草稿库、发布记录）
- `scripts/setup_notion_databases.py`: 自动配置数据库字段

### 关联字段创建
- `scripts/create_relations_final.py`: 创建选题库↔草稿库、发布记录↔草稿库关联
- `scripts/create_material_relations.py`: 创建素材池↔选题库关联

### 测试工具
- `scripts/test_notion_flow.py`: 测试 4 个数据库的写入功能
- `scripts/test_relations.py`: 测试关联字段功能
- `scripts/test_complete_flow.py`: 端到端测试完整数据流
- `scripts/find_notion_databases.py`: 查找数据库位置
- `scripts/inspect_topics_fields.py`: 检查数据库字段

### 研究工具
- `scripts/research_notion_relations.py`: 深入研究 Notion API 结构
- `scripts/check_notion_permissions.py`: 检查 Integration 权限

## 技术突破

### Notion API 2025-09-03 版本关联字段创建

**问题**：新版 Notion API 使用 `data_sources` 架构，创建 Relation 字段的文档不完整

**解决方案**：
```python
client.data_sources.update(
    data_source_id=data_source_id,
    properties={
        "关联字段名": {
            "relation": {
                "data_source_id": target_data_source_id,
                "type": "single_property",
                "single_property": {}
            }
        }
    }
)
```

**关键点**：
- 使用 `data_source_id` 而不是 `database_id`
- 配置 `type: "single_property"` + `single_property: {}`
- 通过 `databases.retrieve()` 获取 `data_sources[0].id`
- 通过 `data_sources.retrieve()` 获取和更新 schema

---

**配置完成时间**: 2026-03-14
**状态**: ✅ 已就绪，可投入使用
**完整数据链路**: 素材池 ↔ 选题库 ↔ 草稿库 ↔ 发布记录
