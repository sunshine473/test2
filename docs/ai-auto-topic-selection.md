# AI 自动选题功能实现总结

## 实现内容

### 1. 新增 AI 选题评估器
**文件**: `src/pipeline/ai_selector.py`

**核心功能**:
- `select_best_topic(topics, direction)` - Claude 分析推荐选题并选择最佳选题
- `select_best_topic_from_plan_result(plan_result, direction)` - 从策划结果中提取并选择

**评估标准**（5 个维度）:
1. **时效性** - 是否是当下热点，时效性强的优先
2. **话题热度** - 是否有足够的讨论度和关注度
3. **内容深度** - 是否有足够的素材支撑深度内容
4. **差异化** - 是否有独特角度，避免同质化
5. **读者价值** - 是否能给读者带来实际价值

**工作流程**:
```
AI 推荐选题列表 → Claude 分析评估 → 选择最佳选题 → 输出选择理由
```

### 2. 更新流水线主逻辑
**文件**: `src/pipeline/main.py`

**改动点**:
1. `_run_plan()` - 保存 AI 推荐选题到 `state.recommended_topics`
2. `_run_select()` - 集成 AI 选题评估器
   - 全自动模式：调用 `select_best_topic()` 让 Claude 评估
   - 半自动模式：保持原有暂停逻辑

**输出示例**:
```
🤖 AI 正在评估推荐选题...
✅ AI 选题: GPT-5 来了：AI 大模型进入新纪元
📊 评分: 92.5
💡 选择理由: 时效性强，话题热度高，有足够素材支撑深度分析
```

### 3. 更新数据模型
**文件**: `src/pipeline/models.py`

**新增字段**:
```python
recommended_topics: Dict = field(default_factory=dict)  # AI 推荐的选题 {direction: [topics]}
```

**数据结构**:
```json
{
  "recommended_topics": {
    "tech_ai": [
      {
        "title": "GPT-5 来了：AI 大模型进入新纪元",
        "score": 92.5,
        "reason": "推荐理由...",
        "source_urls": ["https://..."],
        "ai_selection_reason": "时效性强，话题热度高..."
      }
    ]
  }
}
```

### 4. 更新 Factory Skill
**文件**: `.claude/skills/factory/SKILL.md`

**改动点**:
1. **Description** - 改为"全自动内容工厂"，强调 AI 自动选题
2. **工作流图** - 更新为"AI 选题评估"
3. **使用示例** - 调整顺序，全自动模式优先
4. **阶段说明** - 更新 select 阶段文档

**新描述**:
```yaml
description: >
  全自动内容工厂：从素材采集到多平台发布的完整流水线。AI 自动评估和选择最佳选题，
  自动生成内容，自动质量审核（6 维度 70 分通过），自动发布到多平台。支持全自动模式
  和半自动模式（在选题和审核阶段暂停）。集成 Notion 数据管理。
```

## 使用方式

### 全自动模式（推荐）
```bash
/factory --auto --direction tech_ai
```

**流程**:
1. 素材搜索（自动）
2. 选题策划（自动，AI 推荐 3-5 个选题）
3. AI 选题评估（自动，Claude 选择最佳选题）
4. 内容生成（自动）
5. AI 质量审核（自动，不通过自动重写）
6. 发布分发（自动）

### 半自动模式
```bash
# 1. 启动流水线（执行到选题暂停）
/factory --direction tech_ai

# 2. 查看 AI 推荐选题
/factory --status

# 3. 人工选择选题并继续
/factory --resume latest --topic "选题标题"
```

## 技术细节

### AI 选题评估 Prompt
```python
prompt = f"""你是一位资深内容策划师。以下是 {direction_label} 方向的 {len(topics)} 个推荐选题：

{topics_summary}

请分析这些选题，选择**最值得写**的一个。评估标准：
1. **时效性**：是否是当下热点，时效性强的优先
2. **话题热度**：是否有足够的讨论度和关注度
3. **内容深度**：是否有足够的素材支撑深度内容
4. **差异化**：是否有独特角度，避免同质化
5. **读者价值**：是否能给读者带来实际价值

请直接输出你选择的选题序号（1-{len(topics)}），并简要说明理由（1-2 句话）。

输出格式：
选择: N
理由: [简要说明]
"""
```

### 回退机制
如果 AI 选题失败，自动回退到评分最高的选题：
```python
except Exception as e:
    print(f"  ⚠ AI 选题失败: {e}，使用评分最高的选题")
    return max(topics, key=lambda t: t.get("score", 0))
```

## 优势

### 1. 真正的全自动
- 无需人工干预，从采集到发布一键完成
- AI 自动评估选题质量，选择最佳选题
- 审核不通过自动重写，确保内容质量

### 2. 智能决策
- 5 个维度综合评估，不只看评分
- Claude 理解内容语义，判断更准确
- 输出选择理由，决策过程透明

### 3. 灵活性
- 支持全自动和半自动两种模式
- 可随时切换到人工选题
- 保留人工审核选项

### 4. 可扩展性
- AI 选题评估器独立模块，易于复用
- 评估标准可配置
- 支持多方向选题

## 测试建议

### 1. 单元测试
```bash
# 测试 AI 选题评估器
python -c "
from pipeline.ai_selector import select_best_topic

topics = [
    {'title': '选题1', 'score': 85, 'reason': '...', 'source_urls': []},
    {'title': '选题2', 'score': 90, 'reason': '...', 'source_urls': []},
]

selected = select_best_topic(topics, 'tech_ai')
print(selected)
"
```

### 2. 集成测试
```bash
# 测试全自动流水线
/factory --auto --direction tech_ai --until select

# 检查选题结果
/factory --status
```

### 3. 对比测试
- 运行 10 次全自动流水线
- 对比 AI 选题 vs 评分最高选题
- 评估选题质量差异

## 后续优化

### 1. 多轮对话选题
- Claude 可以提问澄清需求
- 用户可以给出偏好反馈
- 迭代优化选题选择

### 2. 历史数据学习
- 记录历史选题的阅读量、互动数据
- 分析哪些选题更受欢迎
- 优化选题评估标准

### 3. A/B 测试
- 同时生成多个选题的文章
- 对比发布效果
- 自动选择最佳选题策略

### 4. 用户画像
- 分析目标读者偏好
- 个性化选题推荐
- 提高内容匹配度

## Git 提交

```bash
git commit -m "feat: 添加 AI 自动选题功能

核心改进：
- 新增 src/pipeline/ai_selector.py - Claude 评估推荐选题
- 更新 pipeline/main.py - 集成 AI 选题评估器
- 更新 pipeline/models.py - 添加 recommended_topics 字段
- 更新 factory SKILL.md - 改为全自动内容工厂

AI 选题评估标准：
- 时效性：是否是当下热点
- 话题热度：讨论度和关注度
- 内容深度：素材支撑深度
- 差异化：独特角度
- 读者价值：实际价值

使用方式：
- 全自动：/factory --auto --direction tech_ai
- 半自动：/factory --direction tech_ai（在选题暂停）
"
```

## 总结

成功将 factory skill 从"半自动内容工厂"升级为"全自动内容工厂"：

✅ AI 自动评估和选择最佳选题
✅ 5 个维度综合评估（时效性、热度、深度、差异化、价值）
✅ 决策过程透明（输出选择理由）
✅ 保持灵活性（支持全自动和半自动模式）
✅ 回退机制（AI 失败时使用评分最高选题）

现在用户只需一条命令 `/factory --auto --direction tech_ai`，即可完成从素材采集到多平台发布的全流程，真正实现"全自动内容工厂"！
