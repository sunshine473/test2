"""Gemini API 客户端 — 根据任务类型自动选择模型"""

import os
import time
import base64
from pathlib import Path

import yaml
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# 优先使用 CI/文档中的 GEMINI_API_KEY，兼容 Google Cloud 通用变量名和旧回退。
_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("YOUTUBE_API_KEY")
if not _API_KEY:
    raise RuntimeError("未找到 API Key，请在 .env 中设置 GEMINI_API_KEY / GOOGLE_API_KEY / YOUTUBE_API_KEY")

_client = genai.Client(api_key=_API_KEY)

# 加载模型配置
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "models.yaml"
with open(_CONFIG_PATH, encoding="utf-8") as f:
    _CONFIG = yaml.safe_load(f)


def get_text_config(task: str = "article") -> dict:
    """获取文本任务的模型配置"""
    return _CONFIG["text"].get(task, _CONFIG["text"]["article"])


def get_image_config(task: str = "card") -> dict:
    """获取图像任务的模型配置"""
    return _CONFIG["image"].get(task, _CONFIG["image"]["card"])


def get_rate_limit_config() -> dict:
    """获取速率限制配置"""
    return _CONFIG["rate_limit"]


def generate_text(prompt: str, *, task: str = "article",
                  temperature: float = None, max_tokens: int = None) -> str:
    """调用 Gemini 生成文本，根据 task 自动选模型，含网络重试"""
    cfg = get_text_config(task)
    for attempt in range(3):
        try:
            response = _client.models.generate_content(
                model=cfg["model"],
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature if temperature is not None else cfg["temperature"],
                    max_output_tokens=max_tokens if max_tokens is not None else cfg["max_tokens"],
                ),
            )
            return response.text
        except Exception as e:
            if attempt < 2:
                wait = 10 * (attempt + 1)
                print(f"    ⚠ 请求失败，{wait}s 后重试: {str(e)[:80]}")
                time.sleep(wait)
            else:
                raise


def generate_image(prompt: str, *, task: str = "card",
                   aspect_ratio: str = None) -> str:
    """生成图像，根据配置自动选择 Gemini 原生生图或 Imagen，返回 base64 PNG"""
    cfg = get_image_config(task)
    model_type = cfg.get("type", "imagen")

    if model_type == "gemini_native":
        return _generate_image_gemini(prompt, cfg)
    else:
        return _generate_image_imagen(prompt, cfg, aspect_ratio)


def _generate_image_gemini(prompt: str, cfg: dict) -> str:
    """Gemini 原生图文生成（gemini-2.5-flash-image / gemini-3-pro-image-preview）"""
    response = _client.models.generate_content(
        model=cfg["model"],
        contents=f"Generate an illustration image for the following description. Output only the image, no text.\n\n{prompt}",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    # 从 response parts 中提取图像
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return base64.b64encode(part.inline_data.data).decode("utf-8")
    raise RuntimeError(f"Gemini 未返回图像，model: {cfg['model']}, prompt: {prompt[:80]}")


def _generate_image_imagen(prompt: str, cfg: dict, aspect_ratio: str = None) -> str:
    """Imagen 生图"""
    response = _client.models.generate_images(
        model=cfg["model"],
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio or cfg.get("aspect_ratio", "3:4"),
        ),
    )
    if not response.generated_images:
        raise RuntimeError(f"Imagen 未返回图像，prompt: {prompt[:80]}")
    img = response.generated_images[0]
    return base64.b64encode(img.image.image_bytes).decode("utf-8")
