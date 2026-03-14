# Notion 数据中枢配置总结

## 数据库结构

已成功创建并配置 4 个 Notion 数据库：

### 1. 素材池数据库 (Material Pool)
- **数据库 ID**: `b1edb28f-8f5a-45d9-84c6-bc2aee14ad11`
- **URL**: https://www.notion.so/b1edb28f8f5a45d984c6bc2aee14ad11
- **字段**: 名称、URL、来源、采集方式、分类、摘要、语言、采集日期、文章发布时间、评分、方向、状态
- **状态**: ✅ 已配置并测试通过

### 2. 选题库数据库 (Topic Library)
- **数据库 ID**: `4fb54980-3157-4343-9f0d-7477e84afe80`
- **URL**: https://www.notion.so/4fb54980315743439f0d7477e84afe80
- **字段**: 选题标题、方向、评分、推荐理由、关联素材、状态、推荐日期、选中日期
- **状态**: ✅ 已配置并测试通过

### 3. 草稿库数据库 (Draft Library)
- **数据库 ID**: `3ee6f5ee-c2d2-4df9-9870-e52fc4536a79`
- **URL**: https://www.notion.so/3ee6f5eec2d24df99870e52fc4536a79
- **字段**: 文章标题、文件路径、字数、质量评级、质量评分、标签、摘要、状态、生成日期、审核日期
- **状态**: ✅ 已配置并测试通过

### 4. 发布记录数据库 (Publish Records)
- **数据库 ID**: `56016143-40fa-46b7-8948-247b5e6106aa`
- **URL**: https://www.notion.so/5601614340fa46b78948247b5e6106aa
- **字段**: 标题、平台、状态、发布链接、发布消息、发布日期
- **状态**: ✅ 已配置并测试通过

## 数据流

```
素材采集 → 素材池 [状态: 待筛选]
    ↓
选题策划 → 选题库 [状态: 待选择] + 更新素材池 [状态: 已推荐]
    ↓
内容生成 → 草稿库 [状态: 待审核] + 更新选题库 [状态: 已生成]
    ↓
多平台发布 → 发布记录 + 更新草稿库 [状态: 已发布]
```

## 测试结果

✅ 素材池写入测试通过
✅ 选题库写入测试通过
✅ 草稿库写入测试通过
✅ 发布记录写入测试通过

**总计**: 4/4 通过

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

- `scripts/create_notion_databases.py`: 自动创建数据库
- `scripts/setup_notion_databases.py`: 自动配置字段
- `scripts/find_notion_databases.py`: 查找数据库位置
- `scripts/test_notion_flow.py`: 测试完整数据流

---

**配置完成时间**: 2026-03-14
**状态**: ✅ 已就绪，可投入使用
