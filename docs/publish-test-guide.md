# 知乎和小红书发布测试指南

## 当前状态

✅ 测试脚本已启动
✅ 浏览器已打开（Chromium）
⏳ 等待手动登录知乎

## 操作步骤

### 1. 查看浏览器窗口

测试脚本已经启动了 Chromium 浏览器，应该可以看到一个浏览器窗口。

### 2. 登录知乎

在浏览器中：
1. 输入手机号/邮箱
2. 输入密码或验证码
3. 点击登录

### 3. 等待自动填写

登录成功后，脚本会自动：
1. 跳转到知乎编辑器页面
2. 填写文章标题
3. 填写文章内容
4. 保存为草稿

### 4. 查看结果

终端会显示：
```
发布结果:
  状态: success/failed
  消息: 具体信息
  链接: 草稿链接（如果有）
```

## 如果看不到浏览器窗口

可能原因：
1. 浏览器在后台运行
2. 窗口被其他应用遮挡

解决方法：
```bash
# 查看所有 Chrome 窗口
ps aux | grep "Google Chrome for Testing"

# 如果需要停止测试
# 按 Ctrl+C 或在另一个终端运行：
pkill -f "Google Chrome for Testing"
```

## 测试完成后

### 验证知乎发布

1. 登录知乎网页版
2. 进入创作中心
3. 查看草稿箱
4. 确认文章标题和内容是否正确

### Cookie 持久化

首次登录成功后，Cookie 会保存到：
```
.playwright/cookies/zhihu.json
```

下次发布时会自动使用这个 Cookie，无需再次登录。

## 小红书测试

小红书测试需要：
1. 至少 1 张图片
2. 手动扫码登录

建议先完成知乎测试，再测试小红书。

## 故障排除

### 问题 1：浏览器无法启动

```bash
# 重新安装 Playwright 浏览器
python3 -m playwright install chromium
```

### 问题 2：登录后没有自动填写

可能原因：
- 页面加载慢
- 元素选择器变化

查看终端输出的错误信息。

### 问题 3：脚本卡住不动

```bash
# 停止测试
Ctrl+C

# 或在另一个终端
pkill -f test_publish.py
```

## 手动测试（备选方案）

如果自动化测试有问题，可以手动测试：

```bash
# 1. 启动发布脚本
PYTHONPATH=src python3 src/publisher/main.py content/drafts/test-publish.md --platforms zhihu

# 2. 在浏览器中手动登录

# 3. 观察脚本是否自动填写内容
```

## 下一步

完成知乎测试后：
1. 检查 `.playwright/cookies/zhihu.json` 是否生成
2. 再次运行测试，验证 Cookie 是否有效
3. 准备带图片的文章，测试小红书发布
