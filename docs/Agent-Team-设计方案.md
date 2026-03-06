# Agent Team 设计方案

## 1. 架构概览

```
Coordinator Agent (协调者)
    ├── Collector Agent (采集专家)
    ├── Selector Agent (选题专家) ← 新增
    ├── Writer Agent (写作专家)
    ├── Reviewer Agent (审核专家) ← 新增
    └── Publisher Agent (发布专家)
```

## 2. Agent 职责

### 2.1 Coordinator Agent（协调者）
**职责**：流程编排、任务分发、状态监控

**能力**：
- 定时触发采集任务
- 根据素材池状态决定是否生成内容
- 监控各 Agent 状态
- 处理异常和重试

**实现**：`src/agents/coordinator.py`

### 2.2 Collector Agent（采集专家）
**职责**：素材采集、去重、打分

**能力**：
- 多源并行采集
- 智能去重聚类
- 按方向打分排序
- 同步 Notion

**实现**：已有 `src/collector/`，封装为 Agent

### 2.3 Selector Agent（选题专家）← 新增
**职责**：自动选题决策

**能力**：
- 分析素材池质量
- 根据策略自动选题
- 考虑因素：
  - 评分（权重 40%）
  - 新鲜度（权重 30%）
  - 多样性（权重 20%）
  - 用户偏好（权重 10%）

**选题策略**：
```python
# 策略 1：保守型（只选 Top1）
strategy = "conservative"
# 每天只选最高分的 1 篇

# 策略 2：激进型（多篇并行）
strategy = "aggressive"
# 每天选 Top3，并行生成

# 策略 3：多样化（跨方向）
strategy = "diverse"
# AI 科技 1 篇 + 汽车 1 篇
```

**实现**：`src/agents/selector.py`

### 2.4 Writer Agent（写作专家）
**职责**：内容生成

**能力**：
- 根据选题生成文章
- 生成视觉卡片
- 自动优化标题和摘要

**实现**：已有 `src/generator/`，封装为 Agent

### 2.5 Reviewer Agent（审核专家）← 新增
**职责**：自动质量审核

**能力**：
- 结构检查（标题、摘要、正文、结论）
- 字数检查（2000+ 字）
- 关键词覆盖（与选题相关）
- 可读性评分（Flesch Reading Ease）
- 原创性检查（与素材对比）

**审核标准**：
```python
quality_score = {
    "structure": 0-25,      # 结构完整性
    "length": 0-25,         # 字数达标
    "keyword": 0-25,        # 关键词覆盖
    "readability": 0-25,    # 可读性
}
# 总分 >= 70 通过，< 70 重写
```

**实现**：`src/agents/reviewer.py`

### 2.6 Publisher Agent（发布专家）
**职责**：多平台发布

**能力**：
- 统一发布接口
- 平台适配
- 发布状态追踪

**实现**：已有 `src/publisher/`，封装为 Agent

## 3. 工作流程

### 3.1 全自动模式（推荐）

```
每天 8:00 (北京时间)
    ↓
Coordinator 触发 Collector
    ↓
Collector 采集素材 → 素材池
    ↓
Coordinator 触发 Selector
    ↓
Selector 自动选题（根据策略）
    ↓
Coordinator 触发 Writer（可并行）
    ↓
Writer 生成文章 → 草稿
    ↓
Coordinator 触发 Reviewer
    ↓
Reviewer 审核
    ├─ 通过 → 发布
    └─ 不通过 → 重写（最多 3 次）
    ↓
Coordinator 触发 Publisher
    ↓
Publisher 发布到各平台
    ↓
Telegram 通知用户
```

### 3.2 半自动模式（保留人工介入）

```
每天 8:00
    ↓
Collector 采集 → Telegram 推送 Top10
    ↓
用户在 Telegram 选择（或不选，自动选 Top1）
    ↓
Writer 生成 → Telegram 推送预览
    ↓
用户审核（或 24h 后自动通过）
    ↓
Publisher 发布
```

## 4. 配置文件

### 4.1 Agent Team 配置
`src/config/agent_team.yaml`

```yaml
# Agent Team 配置
mode: auto  # auto | semi-auto | manual

# 协调者配置
coordinator:
  schedule: "0 8 * * *"  # 每天 8:00
  timezone: "Asia/Shanghai"
  max_retries: 3
  retry_delay: 300  # 5 分钟

# 选题策略
selector:
  strategy: conservative  # conservative | aggressive | diverse
  min_score: 70  # 最低评分
  max_age_hours: 24  # 最大时效（小时）

  # 保守型：每天 1 篇
  conservative:
    daily_limit: 1
    direction: tech_ai  # 优先方向

  # 激进型：每天 3 篇
  aggressive:
    daily_limit: 3
    direction: null  # 不限方向

  # 多样化：每天 2 篇（跨方向）
  diverse:
    daily_limit: 2
    direction_balance: true  # 平衡方向

# 审核标准
reviewer:
  enabled: true
  min_quality_score: 70
  max_rewrite_attempts: 3
  checks:
    structure: true
    length: true
    keyword: true
    readability: true

# 发布配置
publisher:
  auto_publish: true  # 审核通过后自动发布
  platforms:
    - wechat
    - xiaohongshu
    - zhihu
    - dongchedi

# 通知配置
notification:
  telegram:
    enabled: true
    events:
      - collection_complete
      - topic_selected
      - article_generated
      - review_failed
      - publish_complete
```

## 5. 实现步骤

### Phase 1: 核心 Agent 封装（1-2 天）
- [ ] 创建 `src/agents/` 目录
- [ ] 实现 `base_agent.py`（Agent 基类）
- [ ] 封装 Collector Agent
- [ ] 封装 Writer Agent
- [ ] 封装 Publisher Agent

### Phase 2: 新增智能 Agent（2-3 天）
- [ ] 实现 Selector Agent（自动选题）
- [ ] 实现 Reviewer Agent（自动审核）
- [ ] 实现质量评分算法

### Phase 3: Coordinator 实现（2-3 天）
- [ ] 实现 Coordinator Agent
- [ ] 实现任务调度
- [ ] 实现状态管理
- [ ] 实现异常处理和重试

### Phase 4: 配置和测试（1-2 天）
- [ ] 创建配置文件
- [ ] 编写单元测试
- [ ] 端到端测试
- [ ] 文档更新

## 6. 关键技术点

### 6.1 Agent 通信
使用消息队列（内存队列或 Redis）

```python
# 示例
from queue import Queue

task_queue = Queue()
result_queue = Queue()

# Coordinator 发布任务
task_queue.put({
    "agent": "collector",
    "action": "collect",
    "params": {"sources": "hn,github"}
})

# Agent 返回结果
result_queue.put({
    "agent": "collector",
    "status": "success",
    "data": {...}
})
```

### 6.2 状态持久化
使用 JSON 文件或 SQLite

```python
# 状态文件：content/agent_state.json
{
    "last_collection": "2026-03-01T08:00:00",
    "pending_topics": [...],
    "in_progress": [...],
    "completed": [...]
}
```

### 6.3 并行处理
使用 `concurrent.futures` 或 `asyncio`

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(writer.generate, topic1),
        executor.submit(writer.generate, topic2),
        executor.submit(writer.generate, topic3),
    ]
```

## 7. 优势对比

| 维度 | 当前模式 | Agent Team 模式 |
|------|----------|----------------|
| 选题 | 人工选择 | 自动选择（可配置策略） |
| 审核 | 人工审核 | 自动审核（质量评分） |
| 效率 | 顺序执行 | 并行处理 |
| 人工介入 | 2 次 | 0 次（可选 Telegram 确认） |
| 每日产出 | 1 篇 | 1-3 篇（可配置） |
| 容错 | 手动重试 | 自动重试 |

## 8. 风险和缓解

### 8.1 自动选题质量
**风险**：选题不符合预期
**缓解**：
- 保留 Telegram 推送，用户可手动干预
- 记录选题历史，持续优化策略
- 支持黑名单（排除某些关键词）

### 8.2 自动审核误判
**风险**：好文章被拒，差文章通过
**缓解**：
- 审核标准可配置
- 保留人工复审入口
- 记录审核日志，持续优化

### 8.3 API 成本
**风险**：自动化导致 API 调用增加
**缓解**：
- 设置每日限额
- 使用更便宜的模型（Gemini Flash）
- 缓存重复请求

## 9. 后续优化

### 9.1 学习用户偏好
- 记录用户手动选择的选题
- 训练选题模型
- 个性化推荐

### 9.2 A/B 测试
- 同一选题生成多个版本
- 自动选择最优版本
- 或发布到不同平台测试

### 9.3 多语言支持
- 自动翻译为英文
- 发布到国际平台

## 10. 总结

Agent Team 方案将人工介入从 2 次降为 0 次，同时保留灵活性：
- **全自动模式**：完全无人值守
- **半自动模式**：Telegram 确认关键节点
- **手动模式**：保留当前流程

建议先实现 Phase 1-2，验证效果后再推进 Phase 3-4。
