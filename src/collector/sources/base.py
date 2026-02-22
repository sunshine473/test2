"""信息源适配器抽象基类"""

from abc import ABC, abstractmethod
from typing import List

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
