"""test_collector_main.py — collector/main.py 参数解析测试"""

import pytest

from collector.main import parse_sources_arg


class TestParseSourcesArg:
    def test_parse_sources_success_and_dedup(self):
        sources = parse_sources_arg("follow_builders, rss, github, rss,hot")
        assert sources == ["follow_builders", "rss", "github", "hot"]

    def test_parse_sources_invalid_source(self):
        with pytest.raises(ValueError, match="未知 source"):
            parse_sources_arg("rss,unknown")

    def test_parse_sources_empty(self):
        with pytest.raises(ValueError, match="不能为空"):
            parse_sources_arg(" , ")
