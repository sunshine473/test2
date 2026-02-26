"""test_publisher_registry.py — publisher/registry.py 单元测试"""

import pytest

from publisher.base import BasePublisher
from publisher.registry import _REGISTRY, register, get_publisher, list_publishers


class TestRegistry:
    def setup_method(self):
        """每个测试前保存并清空注册表。"""
        self._backup = dict(_REGISTRY)
        _REGISTRY.clear()

    def teardown_method(self):
        """每个测试后恢复注册表。"""
        _REGISTRY.clear()
        _REGISTRY.update(self._backup)

    def test_register_and_get(self):
        """注册后能获取实例。"""
        @register("test_platform")
        class TestPublisher(BasePublisher):
            def publish(self, article, config):
                pass

        pub = get_publisher("test_platform")
        assert isinstance(pub, TestPublisher)

    def test_get_unknown_publisher(self):
        """未注册平台抛 ValueError。"""
        with pytest.raises(ValueError, match="未知的发布平台"):
            get_publisher("nonexistent")

    def test_list_publishers(self):
        """列出所有已注册平台。"""
        @register("platform_a")
        class PubA(BasePublisher):
            def publish(self, article, config):
                pass

        @register("platform_b")
        class PubB(BasePublisher):
            def publish(self, article, config):
                pass

        names = list_publishers()
        assert "platform_a" in names
        assert "platform_b" in names
        assert len(names) == 2
