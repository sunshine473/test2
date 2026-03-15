# Claude Code Plugins 安装总结

安装日期：2026-03-15

## 已安装的 Plugins

### 1. skill-creator
- **版本**: d5c15b861cd2
- **描述**: 创建新 skills、改进现有 skills、测试 skill 性能
- **用途**:
  - 从头创建 skill
  - 更新或优化现有 skill
  - 运行评估测试 skill
  - 性能基准测试
- **使用**: 当你想创建或优化 skill 时自动激活

### 2. commit-commands
- **版本**: d5c15b861cd2
- **描述**: 简化 git 工作流
- **用途**:
  - 快速 commit
  - 自动 push
  - 创建 pull request
- **使用**: 提供简单的 git 命令

### 3. code-review
- **版本**: d5c15b861cd2
- **描述**: 自动化代码审查
- **用途**:
  - 使用多个专业 agents 审查 PR
  - 基于置信度的评分
  - 全面的代码质量检查
- **使用**: 审查 pull requests 时自动激活

### 4. claude-md-management
- **版本**: 1.0.0
- **描述**: 维护和改进 CLAUDE.md 文件
- **用途**:
  - 审核 CLAUDE.md 质量
  - 捕获会话学习内容
  - 保持项目记忆最新
- **使用**: 管理项目文档时自动激活

### 5. claude-code-setup
- **版本**: 1.0.0
- **描述**: 分析代码库并推荐自动化配置
- **用途**:
  - 推荐 hooks
  - 推荐 skills
  - 推荐 MCP servers
  - 推荐 subagents
- **使用**: 项目初始化或优化时使用

### 6. code-simplifier
- **版本**: 1.0.0
- **描述**: 简化和优化代码
- **用途**:
  - 提升代码清晰度
  - 保持一致性
  - 提高可维护性
  - 保留功能
- **使用**: 重构代码时自动激活

## 如何使用

### 查看已安装的 plugins
```bash
claude plugin list
```

### 启用/禁用 plugin
```bash
# 禁用
claude plugin disable <plugin-name>

# 启用
claude plugin enable <plugin-name>
```

### 更新 plugin
```bash
claude plugin update <plugin-name>
```

### 卸载 plugin
```bash
claude plugin uninstall <plugin-name>
```

## 推荐的额外 plugins

如果需要，可以安装以下 plugins：

### 开发工具
```bash
# 完整的功能开发工作流
claude plugin install feature-dev

# 前端 UI/UX 实现
claude plugin install frontend-design

# 创建交互式 HTML playground
claude plugin install playground
```

### 安全和质量
```bash
# 安全提醒 hook
claude plugin install security-guidance

# PR 审查工具包
claude plugin install pr-review-toolkit
```

### 工作流优化
```bash
# 创建自定义 hooks
claude plugin install hookify

# 持续迭代开发循环
claude plugin install ralph-loop
```

## Plugins 的工作原理

Plugins 可以包含：
- **Commands** (斜杠命令): 如 `/commit`, `/review`
- **Agents** (代理): 专门的 AI agents 处理特定任务
- **Skills** (技能): 可重用的指令集
- **Hooks** (钩子): 在特定事件触发的自动化
- **MCP Servers**: Model Context Protocol 服务器

## 与现有 Skills 的关系

你的项目已有的 skills（在 `.claude/skills/` 目录）：
- collect
- factory
- plan
- publish
- publish-to-wechat
- search
- telegram
- video-optimize
- write

这些 skills 会继续工作，新安装的 plugins 会增强 Claude Code 的能力，但不会冲突。

## 最佳实践

1. **定期更新**: 运行 `claude plugin marketplace update` 和 `claude plugin update` 保持最新
2. **按需启用**: 如果某个 plugin 不常用，可以禁用它以减少干扰
3. **查看文档**: 每个 plugin 都有 README，可以在 marketplace 目录中查看
4. **组合使用**: 多个 plugins 可以协同工作，提升效率

## 相关资源

- 官方 Marketplace: https://github.com/anthropics/claude-plugins-official
- Claude Code 文档: https://claude.ai/code
- Skills Marketplace: https://agentskill.club/
- Plugin 开发指南: https://linuxbeast.com/blog/how-to-build-and-deploy-a-custom-claude-code-plugin/

## 下一步

1. 尝试使用新安装的 plugins
2. 根据需要安装更多 plugins
3. 使用 `skill-creator` 创建自定义 skills
4. 使用 `claude-code-setup` 分析项目并获取优化建议
