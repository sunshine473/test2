# Awesome Claude Skills 仓库总结

下载日期：2026-03-15
来源：https://github.com/ComposioHQ/awesome-claude-skills

## 仓库概述

这是一个精选的 Claude Skills 集合，包含 30+ 个实用的 skills，涵盖文档处理、开发工具、数据分析、商业营销、创意媒体等多个领域。

## Skills 分类

### 📄 文档处理 (Document Processing)

1. **document-skills**
   - 创建、编辑、分析 Word 文档
   - 支持跟踪更改、评论、格式化

### 💻 开发和代码工具 (Development & Code Tools)

2. **artifacts-builder** ✅
   - 创建复杂的多组件 HTML artifacts
   - 使用现代前端技术（React, Tailwind CSS, shadcn/ui）

3. **mcp-builder** ✅
   - 构建 MCP (Model Context Protocol) 服务器

4. **skill-creator** ✅
   - 创建和优化 skills
   - 与官方 plugin 类似

5. **webapp-testing** ✅
   - Web 应用测试工具

### 📊 数据和分析 (Data & Analysis)

6. **developer-growth-analysis** ✅
   - 开发者增长分析

7. **langsmith-fetch** ✅
   - 从 LangSmith 获取数据

8. **meeting-insights-analyzer** ✅
   - 会议洞察分析

### 💼 商业和营销 (Business & Marketing)

9. **brand-guidelines** ✅
   - 应用 Anthropic 官方品牌颜色和排版
   - 保持视觉一致性

10. **competitive-ads-extractor** ✅
    - 竞争对手广告提取

11. **content-research-writer** ✅
    - 内容研究和写作

12. **lead-research-assistant** ✅
    - 潜在客户研究助手

13. **twitter-algorithm-optimizer** ✅
    - Twitter 算法优化

### ✍️ 沟通和写作 (Communication & Writing)

14. **internal-comms** ✅
    - 内部沟通工具

15. **changelog-generator** ✅
    - 自动生成变更日志

16. **tailored-resume-generator** ✅
    - 定制简历生成器

### 🎨 创意和媒体 (Creative & Media)

17. **canvas-design** ✅
    - 创建美丽的视觉艺术（PNG 和 PDF）
    - 海报、设计、静态作品

18. **image-enhancer** ✅
    - 图像增强工具

19. **slack-gif-creator** ✅
    - Slack GIF 创建器

20. **theme-factory** ✅
    - 主题工厂

21. **video-downloader** ✅
    - 视频下载器

### 📁 生产力和组织 (Productivity & Organization)

22. **file-organizer** ✅
    - 智能文件和文件夹组织
    - 理解上下文、查找重复、建议更好的组织结构

23. **invoice-organizer** ✅
    - 发票组织器

24. **domain-name-brainstormer** ✅
    - 域名头脑风暴

25. **raffle-winner-picker** ✅
    - 抽奖获胜者选择器

### 🔗 应用自动化 (App Automation)

26. **connect** ✅
    - 连接 Claude 到 500+ 应用
    - 发送邮件、创建 issues、发布到 Slack

27. **connect-apps** ✅
    - 应用连接工具

28. **connect-apps-plugin** 📦
    - 应用连接插件

29. **composio-skills** 📁
    - 包含 78 个 SaaS 应用的预构建工作流 skills
    - 使用 Composio MCP

### 🛠️ 其他工具

30. **skill-share** ✅
    - 分享 skills

31. **template-skill** ✅
    - Skill 模板

## 推荐安装的 Skills

### 与你的项目相关的 Skills

基于你的内容工厂项目，推荐以下 skills：

#### 1. content-research-writer
```bash
cp -r /tmp/awesome-claude-skills/content-research-writer ~/.claude/skills/
```
**用途**：内容研究和写作，可以增强你的内容生成能力

#### 2. brand-guidelines
```bash
cp -r /tmp/awesome-claude-skills/brand-guidelines ~/.claude/skills/
```
**用途**：保持品牌视觉一致性，适合生成卡片和视觉内容

#### 3. canvas-design
```bash
cp -r /tmp/awesome-claude-skills/canvas-design ~/.claude/skills/
```
**用途**：创建视觉艺术，可以用于生成封面图和卡片

#### 4. image-enhancer
```bash
cp -r /tmp/awesome-claude-skills/image-enhancer ~/.claude/skills/
```
**用途**：增强图像质量

#### 5. twitter-algorithm-optimizer
```bash
cp -r /tmp/awesome-claude-skills/twitter-algorithm-optimizer ~/.claude/skills/
```
**用途**：优化社交媒体内容

#### 6. connect-apps
```bash
cp -r /tmp/awesome-claude-skills/connect-apps ~/.claude/skills/
```
**用途**：连接到 500+ 应用，可以自动化发布流程

#### 7. file-organizer
```bash
cp -r /tmp/awesome-claude-skills/file-organizer ~/.claude/skills/
```
**用途**：智能组织文件，管理草稿和素材

#### 8. changelog-generator
```bash
cp -r /tmp/awesome-claude-skills/changelog-generator ~/.claude/skills/
```
**用途**：自动生成变更日志

## 安装方法

### 方法 1：复制到 skills 目录

```bash
# 复制单个 skill
cp -r /tmp/awesome-claude-skills/<skill-name> ~/.claude/skills/

# 或复制到项目目录
cp -r /tmp/awesome-claude-skills/<skill-name> .claude/skills/
```

### 方法 2：使用符号链接

```bash
# 创建符号链接
ln -s /tmp/awesome-claude-skills/<skill-name> ~/.claude/skills/<skill-name>
```

### 方法 3：批量安装推荐的 skills

```bash
# 创建安装脚本
cat > /tmp/install_skills.sh << 'EOF'
#!/bin/bash

SKILLS=(
  "content-research-writer"
  "brand-guidelines"
  "canvas-design"
  "image-enhancer"
  "twitter-algorithm-optimizer"
  "connect-apps"
  "file-organizer"
  "changelog-generator"
)

for skill in "${SKILLS[@]}"; do
  echo "安装 $skill..."
  cp -r /tmp/awesome-claude-skills/$skill ~/.claude/skills/
done

echo "✅ 所有 skills 安装完成！"
EOF

chmod +x /tmp/install_skills.sh
/tmp/install_skills.sh
```

## Composio Skills

`composio-skills` 目录包含 78 个 SaaS 应用的预构建工作流：

- Gmail
- Slack
- GitHub
- Notion
- Trello
- Asana
- 等等...

每个 skill 包含：
- 工具序列
- 参数指导
- 已知陷阱
- 快速参考表

## 使用方法

### 在 Claude.ai 中使用

1. 点击聊天界面中的 skill 图标 (🧩)
2. 选择要使用的 skill

### 在 Claude Code 中使用

Skills 会自动加载，当任务匹配时自动激活。

### 查看已安装的 skills

```bash
ls ~/.claude/skills/
# 或
ls .claude/skills/
```

## 与现有 skills 的关系

你的项目已有的 skills：
- collect
- factory
- plan
- publish
- publish-to-wechat
- search
- telegram
- video-optimize
- write

新安装的 skills 会增强功能，不会冲突。

## 特别推荐：connect-apps

这个 plugin 让 Claude 可以执行真实的操作：
- 发送邮件
- 创建 issues
- 发布到 Slack
- 连接到 500+ 应用

安装方法：
```bash
claude --plugin-dir /tmp/awesome-claude-skills/connect-apps-plugin
```

然后运行设置：
```
/connect-apps:setup
```

## 相关资源

- GitHub 仓库：https://github.com/ComposioHQ/awesome-claude-skills
- Composio 平台：https://platform.composio.dev/
- 支持的应用列表：https://composio.dev/toolkits
- 贡献指南：/tmp/awesome-claude-skills/CONTRIBUTING.md

## 下一步

1. 选择与你的项目相关的 skills 并安装
2. 测试新安装的 skills
3. 根据需要自定义 skills
4. 考虑贡献你自己的 skills 到社区

## 注意事项

- 某些 skills 可能需要 API keys（如 Composio）
- 安装前建议先阅读每个 skill 的 README
- 可以根据需要修改 skills 以适应你的工作流
- 定期更新仓库以获取最新的 skills

## 本地仓库位置

```
/tmp/awesome-claude-skills/
```

可以随时访问这个目录查看和安装更多 skills。
