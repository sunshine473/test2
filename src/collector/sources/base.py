"""信息源适配器抽象基类"""

from abc import ABC, abstractmethod
from typing import List

from bs4 import BeautifulSoup

from collector.models import CollectedItem


class BaseSource(ABC):
    """所有信息源适配器的基类，子类只需实现 collect 方法"""

    @abstractmethod
    def collect(self, config: dict) -> List[CollectedItem]:
        """从信息源采集素材

        Args:
            config: sources.yaml 中对应的配置段

        Returns:
            采集到的素材列表
        """
        ...


def clean_text(value: str) -> str:
    """移除 HTML 并压缩空白，得到可读纯文本。"""
    text = (value or "").strip()
    if not text:
        return ""
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def clip_text(value: str, limit: int) -> str:
    """截断文本，避免 pool 体积失控。"""
    text = clean_text(value)
    if not text:
        return ""
    return text[:limit]
