# 知乎和小红书发布测试 - 当前状态

## 测试进行中 ⏳

### 当前状态
- ✅ 测试脚本已启动
- ✅ Chromium 浏览器已打开
- ⏳ 等待手动登录知乎（最多 10 分钟）

### 浏览器窗口操作指南

**应该能看到一个 Chromium 浏览器窗口，显示知乎登录页面。**

请在浏览器中完成以下操作：

1. **输入账号**
   - 手机号或邮箱

2. **输入密码或验证码**
   - 如果选择密码登录，输入密码
   - 如果选择验证码登录，输入收到的验证码

3. **点击登录按钮**

4. **等待自动操作**
   - 登录成功后，脚本会自动：
     - 保存 Cookie 到 `.browser_state/zhihu_state.json`
     - 跳转到知乎编辑器页面
     - 填写测试标题
     - 填写测试内容

5. **查看结果**
   - 终端会显示操作结果
   - 可以在浏览器中查看填写的内容

### 如果看不到浏览器窗口

可能原因：
- 窗口在后台
- 被其他应用遮挡
- 在其他桌面空间

解决方法：
```bash
# 查看 Chrome 进程
ps aux | grep "Google Chrome for Testing" | head -3

# 使用 Mission Control (F3) 查找窗口
# 或使用 Cmd+Tab 切换应用
```

### 测试超时

如果 10 分钟内未完成登录，脚本会自动退出。可以重新运行：

```bash
PYTHONPATH=src python3 test_zhihu_login.py
```

### 停止测试

如果需要停止测试：

```bash
# 方法 1：在终端按 Ctrl+C

# 方法 2：关闭浏览器窗口

# 方法 3：杀死进程
pkill -f test_zhihu_login
pkill -f "Google Chrome for Testing"
```

## 测试成功后

### 验证 Cookie 保存

```bash
# 检查 Cookie 文件
ls -lh .browser_state/zhihu_state.json

# 查看 Cookie 内容（JSON 格式）
cat .browser_state/zhihu_state.json | head -20
```

### 验证知乎草稿

1. 打开知乎网页版
2. 进入创作中心
3. 查看草稿箱
4. 确认是否有"测试文章标题"

### 下次测试

有了保存的 Cookie 后，下次测试会自动登录：

```bash
# 使用完整的发布脚本
PYTHONPATH=src python3 src/publisher/main.py content/drafts/test-publish.md --platforms zhihu

# 或使用 factory skill
/factory --platforms zhihu
```

## 小红书测试

完成知乎测试后，可以测试小红书：

### 准备工作

1. **生成带图片的文章**
   ```bash
   /write "AI 编程助手测试"
   ```
   这会生成文章和卡片图

2. **运行小红书测试**
   ```bash
   PYTHONPATH=src python3 src/publisher/main.py content/drafts/<文章路径> --platforms xiaohongshu
   ```

3. **扫码登录**
   - 小红书需要扫码登录
   - 使用小红书 App 扫描浏览器中的二维码

## 故障排除

### 问题 1：浏览器启动失败

```bash
# 重新安装 Playwright 浏览器
python3 -m playwright install chromium
```

### 问题 2：登录后没有自动填写

可能原因：
- 知乎页面结构变化
- 元素选择器失效

查看终端输出的错误信息，或手动检查页面元素。

### 问题 3：Cookie 保存失败

检查目录权限：
```bash
mkdir -p .browser_state
chmod 755 .browser_state
```

## 技术细节

### 登录检测逻辑

脚本通过以下方式检测是否在登录页：
1. 检查 URL 是否包含 "signin" 或 "login"
2. 每 2 秒检查一次
3. 最多等待 600 秒（10 分钟）

### Cookie 持久化

登录成功后，Playwright 会保存：
- Cookies
- LocalStorage
- SessionStorage
- IndexedDB

保存位置：`.browser_state/zhihu_state.json`

### 自动填写流程

1. 跳转到编辑器页面
2. 定位标题输入框（textarea）
3. 填写标题
4. 定位内容编辑器（contenteditable）
5. 填写内容
6. 等待自动保存

## 当前任务 ID

后台任务 ID: `bqi32ffr7`

查看任务输出：
```bash
# 在 Claude Code 中
/tasks
```
