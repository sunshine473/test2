"""发布适配器注册表"""

from typing import Dict, Type

from publisher.base import BasePublisher

_REGISTRY: Dict[str, Type[BasePublisher]] = {}


def register(name: str):
    """装饰器：注册发布适配器

    用法:
        @register("wechat")
        class WeChatPublisher(BasePublisher):
            ...
    """
    def decorator(cls: Type[BasePublisher]):
        cls.name = name
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_publisher(name: str) -> BasePublisher:
    """根据名称获取发布适配器实例"""
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys()) or "无"
        raise ValueError(f"未知的发布平台: {name}（可用: {available}）")
    return _REGISTRY[name]()


def list_publishers() -> list[str]:
    """列出所有已注册的发布平台"""
    return list(_REGISTRY.keys())
