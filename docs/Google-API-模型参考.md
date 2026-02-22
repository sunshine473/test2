# Google API 可用模型参考

> 更新时间：2026-02-18 | API Key：YOUTUBE_API_KEY / GOOGLE_API_KEY

## 文本模型

| 模型 | 输入 / 1M tokens | 输出 / 1M tokens | 特点 |
|------|-----------------|-----------------|------|
| `gemini-3-pro-preview` | $2.00 (≤200K) / $4.00 | $12.00 / $18.00 | 最强旗舰，复杂推理 |
| `gemini-3-flash-preview` | $0.50 | $3.00 | 新一代 Flash，快速 |
| `gemini-2.5-pro` | $1.25 (≤200K) / $2.50 | $10.00 / $15.00 | 强推理，长上下文，**当前文章写作用** |
| `gemini-2.5-flash` | $0.30 | $2.50 | 性价比之王，**当前卡片拆分/打分用** |
| `gemini-2.5-flash-lite` | $0.10 | $0.40 | 最便宜，**当前翻译用** |
| `gemini-2.0-flash` | 免费 | 免费 | 免费层可用，质量一般 |

## 图像生成（Gemini 原生）

| 模型 | 每张价格 | 特点 |
|------|---------|------|
| `gemini-3-pro-image-preview` | ~$0.134 (1K/2K) / $0.24 (4K) | 高质量，**当前封面图用** |
| `gemini-2.5-flash-image` | ~$0.039 | 速度快，**当前卡片插图用** |

## 图像生成（Imagen）

| 模型 | 每张价格 | 特点 |
|------|---------|------|
| `imagen-4.0-ultra-generate-001` | ~$0.06 | 最高质量，细节丰富 |
| `imagen-4.0-generate-001` | ~$0.04 | 标准质量，平衡之选 |
| `imagen-4.0-fast-generate-001` | ~$0.02 | 最便宜，速率限制较严 |

## 视频生成（Veo）

| 模型 | 特点 |
|------|------|
| `veo-3.0-generate-001` | 视频生成，支持音效 |
| `veo-3.0-fast-generate-001` | 快速版视频生成 |
| `veo-3.1-generate-preview` | 最新预览版 |

## 其他模型

| 模型 | 用途 |
|------|------|
| `gemini-2.5-flash-preview-tts` | 文本转语音 |
| `gemini-2.5-pro-preview-tts` | 高质量文本转语音 |
| `deep-research-pro-preview-12-2025` | 深度研究 |
| `gemini-embedding-001` | 文本向量化 |
| `nano-banana-pro-preview` | Nano Banana 图文生成 |

## 速率限制

### 文本模型

| 层级 | Gemini 2.5 Pro | Gemini 2.5 Flash | Flash-Lite |
|------|---------------|-----------------|------------|
| 免费 | 5 RPM / 100 RPD | 10 RPM / 250 RPD | 15 RPM / 1000 RPD |
| Tier 1 | 150 RPM / 1000 RPD | 300 RPM / 1500 RPD | 300 RPM / 1500 RPD |
| Tier 2 | 1000 RPM / 10000 RPD | 2000 RPM / 10000 RPD | 2000 RPM / 10000 RPD |

### 图像生成

Gemini 原生生图模型速率限制比 Imagen 宽松，推荐优先使用。

## 当前项目模型分配

配置文件：`src/config/models.yaml`

| 任务 | 模型 | 单次成本 |
|------|------|---------|
| 文章写作 | `gemini-3-pro-preview` | ~$0.10 |
| 卡片拆分 | `gemini-2.5-flash` | ~$0.01 |
| Prompt 翻译 | `gemini-2.5-flash-lite` | ~$0.001 |
| 卡片插图 | `gemini-2.5-flash-image` | ~$0.039/张 |
| 封面图 | `gemini-3-pro-image-preview` | ~$0.134/张 |

单篇总成本（文章 + 7 张卡片）：~$0.35
$300 额度可生成约 850 篇
