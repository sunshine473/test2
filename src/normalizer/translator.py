"""翻译适配器占位。"""

from __future__ import annotations

from models import RawMaterial


def translate_materials(items: list[RawMaterial]) -> list[RawMaterial]:
    """当前先保持透明透传，后续再替换为正式翻译服务。"""
    return items
