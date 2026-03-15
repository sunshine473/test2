---
description: 分析视频内容的短视频优化潜力，生成八维评分报告和优化建议
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
argument-hint: <视频路径或URL>
---

# video-optimize

分析视频的短视频优化潜力，输出包含八维评分、关键帧时间轴和优化建议的可视化报告。

## 使用方法

```bash
/video-optimize <视频路径或URL>
```

## 支持的输入

- 本地视频文件（MP4, MOV, AVI 等）
- YouTube URL
- B站 URL
- 小红书视频 URL
- 抖音视频 URL

## 输出

生成归档报告到 `./outputs/reports/<timestamp>/`：
- `report.html` - 完整报告（内嵌视频，可离线查看）
- `report-lite.html` - 轻量报告（引用 video.mp4）
- `video.mp4` - 原始视频
- `frames/` - 关键帧截图
- `analysis.json` - 原始分析数据

## 执行协议

1. 调用 `video_analyzer.py --archive-dir ./outputs/reports`
2. 如果退出码为 2（需要浏览器下载），读取 `FALLBACK.md` 并展示给用户
3. 如果成功（退出码 0），读取生成的 `report.html` 并作为文件附件输出
4. 提供报告路径和关键发现摘要

## 示例

```bash
# 分析本地视频
/video-optimize ./videos/demo.mp4

# 分析 YouTube 视频
/video-optimize https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 分析 B站视频
/video-optimize https://www.bilibili.com/video/BV1xx411c7mD
```

## 报告内容

- **八维评分雷达图**：视觉冲击力、信息密度、节奏把控、情绪调动、记忆点设计、完播驱动力、互动引导、平台适配度
- **关键帧时间轴**：可点击跳转的场景缩略图
- **综合评价**：AI 生成的整体分析
- **优化建议**：针对性的改进方案

## 技术栈

- yt-dlp：视频下载（B站/YouTube）
- ffmpeg：视频压缩和帧提取
- 豆包 API (doubao-seed-2-0-pro-260215)：原生视频理解和分析
- Chart.js：数据可视化
- WebVTT：场景同步标记
