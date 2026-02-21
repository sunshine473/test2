"""发布模块数据模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PublishStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Article:
    """待发布的文章"""
    title: str
    content: str              # Markdown 原文
    author: str = ""
    digest: str = ""
    cover_image: str = ""     # 封面图路径
    source_path: str = ""     # 原始 Markdown 文件路径
    images: list[str] = field(default_factory=list)   # 配图路径列表（小红书等需要）
    tags: list[str] = field(default_factory=list)      # 话题标签
    metadata: dict = field(default_factory=dict)


@dataclass
class PublishResult:
    """单平台发布结果"""
    platform: str
    status: PublishStatus
    message: str = ""
    url: str = ""
    platform_id: str = ""
