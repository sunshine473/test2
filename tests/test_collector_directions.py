"""test_collector_directions.py — directions.py 单元测试"""

import pytest

from collector.directions import DIRECTIONS, TRENDING_KEYWORDS, get_direction


class TestDirectionsConfig:
    def test_direction_fields_complete(self):
        """每个方向应具备完整配置字段。"""
        for name, direction in DIRECTIONS.items():
            assert direction.name == name
            assert direction.label
            assert direction.categories
            assert direction.source_weight
            assert direction.category_weight
            assert direction.keyword_bonus
            assert isinstance(direction.preferred_source_bonus, int)

    def test_trending_keywords_mapping_complete(self):
        """每个方向都应配置 trending 二次筛选关键词。"""
        for name in DIRECTIONS:
            assert name in TRENDING_KEYWORDS
            assert len(TRENDING_KEYWORDS[name]) > 0

    def test_get_direction(self):
        """按名称获取方向，不存在则抛 KeyError。"""
        assert get_direction("tech_ai").name == "tech_ai"
        assert get_direction("auto").name == "auto"
        with pytest.raises(KeyError):
            get_direction("unknown")
