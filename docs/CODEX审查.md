# CODEX 审查报告（代码质量 + Skill 质量）

审查时间：2026-02-26  
审查范围：`src/`、`.claude/skills/`、`README.md`、`CLAUDE.md`

## 结论概览

- 整体架构已成型，模块边界基本清晰，可运行性较好（`compileall` 通过）。
- 存在若干高优先级质量风险，主要集中在发布链路“成功判定”与 Skill 文档和代码行为不一致。
- 测试覆盖缺失，当前质量保障主要依赖人工回归，后续迭代风险较高。

## 主要问题（按严重级别）

### P0

1. 浏览器平台发布存在“误报成功”风险  
   - 文件：
     - `src/publisher/platforms/zhihu.py`
     - `src/publisher/platforms/xiaohongshu.py`
     - `src/publisher/platforms/dongchedi.py`
   - 问题：流程执行后直接返回 `SUCCESS`，缺少对“草稿保存成功/发布成功”明确 UI 信号的断言校验。  
   - 风险：流水线会把失败当成功，导致运营误判。

### P1

2. `/publish` Skill 排障指令与实现不一致  
   - 文件：`.claude/skills/publish/SKILL.md`  
   - 问题：文档提示 `python src/publisher/platforms/xiaohongshu.py --login`，但对应脚本没有该 CLI 能力。  
   - 风险：用户按文档操作会直接失败，影响可用性与信任。

3. Markdown frontmatter 解析过于脆弱  
   - 文件：
     - `src/publisher/main.py`
     - `src/wechat_publisher/processor.py`
   - 问题：使用手写按行 `key:value` 解析，复杂 YAML（多行、数组、冒号、引号）易误解析。  
   - 风险：发布字段丢失或错误，造成稿件信息不完整。

4. `/collect` Skill 期望与脚本输出不完全对齐  
   - 文件：
     - `.claude/skills/collect/SKILL.md`
     - `src/collector/main.py`
   - 问题：Skill 要求输出“各源采集条数”，但脚本未提供结构化分源统计。  
   - 风险：执行时容易出现“估算式汇报”。

### P2

5. `toutiao` 仍为骨架实现  
   - 文件：`src/publisher/platforms/toutiao.py`  
   - 问题：当前固定返回 `SKIPPED`。  
   - 风险：若配置启用会造成预期落差。

6. 生成模块 import 阶段强依赖 API Key  
   - 文件：`src/generator/gemini_client.py`  
   - 问题：模块导入即读取并校验 Key，影响本地测试与工具复用。  
   - 风险：无密钥环境下难以做单测/静态验证。

7. 文档路径表述有历史残留  
   - 文件：`README.md`、`CLAUDE.md`  
   - 问题：仍强调 `skills/`，而当前实际可用 Skill 在 `.claude/skills/`。  
   - 风险：维护者认知不一致。

8. 测试覆盖为空  
   - 目录：`tests/`  
   - 问题：缺少关键链路自动化测试。  
   - 风险：回归风险高，改动信心不足。

## 已执行验证

- 语法检查：`python -m compileall -q src`（通过）
- 未执行：真实外部集成验证（Notion/微信/Playwright 平台发布），因依赖外部凭据与登录态

## 建议修复优先级

1. 先修 P0：发布成功判定增加可观测断言（草稿列表可见、成功 toast、URL 状态等）。
2. 再修 P1：统一 frontmatter 解析到 `yaml.safe_load`；修正 `/publish` Skill 错误命令；给 `collect` 增加分源统计输出。
3. 最后补 P2：清理文档路径、降低 import 期强依赖、补最小回归测试（collector/publisher 核心路径）。

---

## 第二轮复审（新增需求：Telegram 双向 Bot）

审查范围新增：
- `src/bot/`
- `.github/workflows/telegram-bot.yml`
- `src/collector/telegram_notifier.py`

### 新增主要问题（按严重级别）

### P0

1. Bot offset 持久化在“未处理消息”路径会写入非法值，下一轮启动可能直接崩溃  
   - 文件：`src/bot/main.py`
   - 问题：`offset` 初始可为 `None`，当本轮消息都未通过授权或无文本时，`offset` 不会被更新，最终 `save_offset(offset)` 可能写入 `"None"`；下次 `load_offset()` 执行 `int("None")` 会抛异常。  
   - 影响：Bot 轮询中断，无法继续服务。

2. offset 只在“授权且成功处理”后推进，可能导致重复拉取同一批消息  
   - 文件：`src/bot/main.py`
   - 问题：未授权消息、非文本消息不会推进 offset。  
   - 影响：同一更新反复处理，产生噪声和潜在死循环。

### P1

3. Telegram Bot workflow 未安装 `generator/publisher` 依赖，导致部分工具名义可用但运行失败  
   - 文件：`.github/workflows/telegram-bot.yml`
   - 问题：当前仅安装 `src/collector/requirements.txt` 与 `src/bot/requirements.txt`，但 bot 的 `write/publish` 工具会调用 `generator`、`publisher` 模块。  
   - 影响：用户在 Telegram 中触发写作/发布会报错，能力与宣称不一致。

4. 缺少 `TELEGRAM_BOT_TOKEN` 空值防护  
   - 文件：`src/bot/telegram.py`
   - 问题：token 为空时仍构造请求 URL 并直接请求。  
   - 影响：错误表现不清晰，排障成本高。

5. `tool_publish` 状态值格式不一致  
   - 文件：`src/bot/tools.py`
   - 问题：异常分支写入 `"FAILED"`（大写），正常分支来自枚举是小写 `failed/success/skipped`。  
   - 影响：上层展示/统计逻辑可能出现分支漏判。

### P2

6. `telegram-bot` workflow 轮询频率与超时窗口较紧，配合 `cancel-in-progress` 存在中断执行风险  
   - 文件：`.github/workflows/telegram-bot.yml`
   - 问题：每 2 分钟触发、任务超时 5 分钟、并发取消策略会导致长请求或工具调用时被中断。  
   - 影响：消息处理不稳定，offset 持久化可靠性下降。

7. Bot 相关目录暂无自动化测试  
   - 目录：`src/bot/`, `tests/`
   - 影响：回归风险高，特别是 offset 状态机和工具编排路径。

### 复审验证记录

- 语法检查：`python -m compileall -q src/bot`（通过）
- 静态扫描：已检查 `TODO/except/请求调用/工具边界`
- 未做：真实 Telegram/Claude API 联调（依赖线上凭据与网络）
