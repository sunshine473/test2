"""发布适配器抽象基类"""

from abc import ABC, abstractmethod

from publisher.models import Article, PublishResult


class BasePublisher(ABC):
    """所有发布适配器的基类，子类只需实现 publish 方法"""

    name: str = ""

    @abstractmethod
    def publish(self, article: Article, config: dict) -> PublishResult:
        """发布文章到目标平台

        Args:
            article: 待发布的文章
            config: publishers.yaml 中对应的配置段

        Returns:
            发布结果
        """
        ...
