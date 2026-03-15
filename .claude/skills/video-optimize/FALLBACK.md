# 浏览器下载指南

由于平台限制，以下视频需要通过浏览器手动下载：

## B站视频

1. 安装浏览器扩展：
   - Chrome/Edge: [Bilibili Evolved](https://github.com/the1812/Bilibili-Evolved)
   - Firefox: [Bilibili Helper](https://addons.mozilla.org/zh-CN/firefox/addon/bilibili-helper/)

2. 打开视频页面，点击扩展图标
3. 选择"下载视频" → 选择清晰度 → 下载
4. 将下载的视频保存到本地路径
5. 重新运行：`/video-optimize <本地路径>`

## YouTube视频

1. 使用在线工具：
   - [y2mate.com](https://www.y2mate.com/)
   - [savefrom.net](https://savefrom.net/)

2. 粘贴视频URL，选择MP4格式
3. 下载到本地
4. 重新运行：`/video-optimize <本地路径>`

## 小红书视频

1. 打开视频页面
2. 按 F12 打开开发者工具
3. 切换到 Network 标签，筛选 Media
4. 刷新页面，找到 `.mp4` 文件
5. 右键 → Open in new tab → 另存为
6. 重新运行：`/video-optimize <本地路径>`

## 抖音视频

1. 使用第三方工具：
   - [douyin.wtf](https://douyin.wtf/)
   - [snaptik.app](https://snaptik.app/)

2. 复制视频分享链接
3. 粘贴到工具，下载无水印版本
4. 重新运行：`/video-optimize <本地路径>`

---

**提示**：下载后的视频文件建议保存到 `./videos/` 目录，便于管理。

**隐私提醒**：请确保下载的视频符合平台使用条款和版权规定。
