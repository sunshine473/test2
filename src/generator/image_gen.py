"""图像生成封装 — 中文描述翻译 + Imagen 生成（含速率限制重试）"""

import time
from generator.gemini_client import generate_text, generate_image, get_rate_limit_config

_TRANSLATE_PROMPT = """将以下中文图像描述翻译为简洁的英文 Imagen prompt（不超过 120 词）。
要求：描述视觉元素、风格、色调，适合作为 AI 生图 prompt。只输出英文 prompt，不要其他内容。

中文描述：{description}"""

_RATE_CFG = get_rate_limit_config()


def create_illustration(description: str, *, image_task: str = "card",
                        aspect_ratio: str = None) -> str:
    """根据中文描述生成插图，返回 base64 PNG

    流程：中文描述 → Gemini 翻译为英文 prompt → Imagen 生图
    遇到 429 速率限制时自动等待重试。
    """
    en_prompt = generate_text(
        _TRANSLATE_PROMPT.format(description=description),
        task="translate",
    ).strip()

    max_retries = _RATE_CFG["image_max_retries"]
    retry_delay = _RATE_CFG["image_retry_delay"]

    for attempt in range(max_retries):
        try:
            return generate_image(en_prompt, task=image_task, aspect_ratio=aspect_ratio)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait = retry_delay * (attempt + 1)
                print(f"      速率限制，等待 {wait}s 后重试...")
                time.sleep(wait)
            else:
                raise
