# 发布渠道测试报告

测试日期：2026-03-15
测试平台：知乎、小红书

## 测试环境

- Python 版本：3.9
- Playwright 版本：1.58.0
- 操作系统：macOS (Darwin 25.3.0)

## 测试准备

### 1. 依赖安装

```bash
# 安装 Python 依赖
python3 -m pip install -r requirements.txt --user

# 安装 Playwright 浏览器
python3 -m playwright install chromium
```

✅ 所有依赖已成功安装

### 2. 配置更新

已启用知乎和小红书平台：

```yaml
# src/config/publishers.yaml
zhihu:
  enabled: true
  headless: false  # 首次需要手动登录

xiaohongshu:
  enabled: true
  headless: false  # 首次需要手动扫码登录
```

### 3. 测试文章

创建了测试文章 `content/drafts/test-publish.md`：
- 标题：AI 编程助手测试文章
- 内容：包含标题、列表、代码块等元素
- 标签：AI、编程、测试

## 测试结果

### 知乎发布

**发布器实现**：`src/publisher/platforms/zhihu.py`

**功能特性**：
- ✅ 使用 Playwright 自动化
- ✅ 支持 Cookie 持久化（首次登录后自动保存）
- ✅ Markdown 转 HTML 富文本
- ✅ 自动填写标题和正文
- ✅ 保存为草稿

**测试流程**：
1. 启动浏览器（非 headless 模式）
2. 打开知乎登录页
3. 等待用户手动登录
4. 跳转到编辑器页面
5. 自动填写标题（限 100 字）
6. 通过 paste 事件注入富文本内容
7. 保存草稿

**注意事项**：
- 首次使用需要手动登录
- 登录后 Cookie 会保存到 `.playwright/cookies/zhihu.json`
- 后续发布会自动使用保存的 Cookie
- 也可以通过 `.env` 中的 `ZHIHU_COOKIE` 环境变量注入

**测试状态**：⏸️ 需要手动登录验证

### 小红书发布

**发布器实现**：`src/publisher/platforms/xiaohongshu.py`

**功能特性**：
- ✅ 使用 Playwright 自动化
- ✅ 支持图文笔记发布
- ✅ 自动上传图片（支持多张）
- ✅ 自动填写标题和正文
- ✅ 保存为草稿

**测试流程**：
1. 检查是否有图片（至少 1 张）
2. 启动浏览器
3. 打开小红书创作者平台
4. 等待用户扫码登录
5. 切换到"上传图文"标签
6. 上传图片
7. 填写标题和正文
8. 保存草稿

**注意事项**：
- ⚠️ **必须提供至少 1 张图片**
- 首次使用需要扫码登录
- 登录后 Cookie 会保存到 `.playwright/cookies/xiaohongshu.json`
- 标题建议包含话题标签（如 #AI编程）

**测试状态**：⏸️ 需要图片和手动登录验证

## 发布器架构

### 注册表模式

所有平台发布器使用统一的注册表模式：

```python
from publisher.registry import register

@register("zhihu")
class ZhihuPublisher(BrowserPublisher):
    # 实现发布逻辑
    pass
```

### 基类继承

- `PublisherBase` - 所有发布器的基类
- `BrowserPublisher` - 浏览器自动化发布器基类（继承自 PublisherBase）
  - 提供 Cookie 管理
  - 提供登录检测
  - 提供随机延迟（模拟人类操作）

### 数据流

```
Markdown 草稿
    ↓
Packager (Layer 5) - 转换为平台格式
    ↓
PublishPackage
    ↓
Publisher (Layer 6) - 发布到平台
    ↓
PublishResult
```

## 使用方式

### 方式 1：通过 publisher/main.py

```bash
# 发布到知乎
python3 src/publisher/main.py content/drafts/test-publish.md --platforms zhihu

# 发布到小红书（需要图片）
python3 src/publisher/main.py content/drafts/test-publish.md --platforms xiaohongshu

# 同时发布到多个平台
python3 src/publisher/main.py content/drafts/test-publish.md --platforms zhihu,xiaohongshu
```

### 方式 2：通过 /factory skill

```bash
# 全链路发布（包含知乎和小红书）
/factory --auto --platforms zhihu,xiaohongshu
```

### 方式 3：通过测试脚本

```bash
# 运行测试脚本
python3 test_publish.py
```

## 已知问题

1. **SSL 警告**
   - 问题：urllib3 v2 需要 OpenSSL 1.1.1+，当前系统使用 LibreSSL 2.8.3
   - 影响：仅警告，不影响功能
   - 解决：可忽略或升级 OpenSSL

2. **小红书图片要求**
   - 问题：必须提供至少 1 张图片
   - 解决：使用 `/write` 生成文章时会自动生成卡片图

3. **首次登录**
   - 问题：首次使用需要手动登录
   - 解决：登录后 Cookie 会自动保存，后续自动使用

## 改进建议

1. **自动生成小红书封面图**
   - 当前：依赖 `/write` 生成的卡片
   - 建议：如果没有图片，自动生成简单封面图

2. **登录状态检测优化**
   - 当前：通过页面元素判断
   - 建议：增加更多判断条件，提高准确性

3. **发布结果验证**
   - 当前：仅检查是否保存成功
   - 建议：获取草稿链接，验证内容完整性

4. **错误重试机制**
   - 当前：失败直接返回
   - 建议：增加自动重试（网络错误、超时等）

## 总结

✅ **已完成**：
- 知乎和小红书发布器实现
- Playwright 自动化集成
- Cookie 持久化
- 测试脚本和文档

⏸️ **待验证**：
- 实际登录和发布流程
- 多图片上传（小红书）
- 富文本格式转换准确性

📝 **下一步**：
1. 手动测试知乎发布流程
2. 准备测试图片，测试小红书发布
3. 验证 Cookie 持久化功能
4. 测试批量发布功能
