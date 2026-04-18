"""test_collector_planner.py — planner.py 单元测试"""

import importlib
import sys
import types
from pathlib import Path

from freezegun import freeze_time


def _import_planner_with_stub(monkeypatch):
    fake_main = types.ModuleType("collector.main")
    fake_main.ensure_utf8 = lambda: None
    monkeypatch.setitem(sys.modules, "collector.main", fake_main)
    sys.modules.pop("collector.planner", None)
    return importlib.import_module("collector.planner")


class TestPlanner:
    def test_load_pool(self, monkeypatch):
        """从 JSON 正确反序列化素材条目。"""
        planner = _import_planner_with_stub(monkeypatch)
        sample_pool = Path(__file__).parent / "fixtures" / "sample_pool.json"
        items = planner.load_pool(str(sample_pool))
        assert len(items) == 3
        assert items[0].title == "GPT-5 发布：多模态能力大幅提升"
        assert items[0].raw_data is None

    def test_filter_by_direction(self, monkeypatch, make_item):
        """方向筛选应包含匹配 category 和命中关键词的 trending 条目。"""
        planner = _import_planner_with_stub(monkeypatch)
        d = planner.get_direction("tech_ai")
        items = [
            make_item(category="tech_ai", title="常规 AI 新闻"),
            make_item(category="trending", title="今日 AI 热点", summary="openai 发布新模型"),
            make_item(category="trending", title="体育热点", summary="足球赛事"),
            make_item(category="auto", title="汽车新闻"),
        ]
        filtered = planner.filter_by_direction(items, d)
        titles = [it.title for it in filtered]
        assert "常规 AI 新闻" in titles
        assert "今日 AI 热点" in titles
        assert "体育热点" not in titles
        assert "汽车新闻" not in titles

    @freeze_time("2026-02-26 12:00:00+00:00")
    def test_auto_direction_requires_recent_published_at(self, monkeypatch, make_item):
        """汽车方向必须过滤掉 7 天外或缺少发布时间的素材。"""
        planner = _import_planner_with_stub(monkeypatch)
        d = planner.get_direction("auto")
        items = [
            make_item(category="auto", title="本周新能源新闻", published_at="2026-02-25T12:00:00Z"),
            make_item(category="auto", title="2025 年旧销量榜", published_at="2025-12-31T12:00:00Z"),
            make_item(category="auto", title="无日期汽车新闻", published_at=""),
            make_item(
                category="trending",
                title="小米汽车热搜",
                summary="小米汽车智驾",
                published_at="2026-02-26T08:00:00Z",
            ),
        ]
        filtered = planner.filter_by_direction(items, d)
        titles = [it.title for it in filtered]
        assert titles == ["本周新能源新闻", "小米汽车热搜"]

    def test_plan_direction_and_plan(self, monkeypatch):
        """plan_direction 与 plan 返回结构完整。"""
        planner = _import_planner_with_stub(monkeypatch)
        sample_pool = Path(__file__).parent / "fixtures" / "sample_pool.json"
        items = planner.load_pool(str(sample_pool))
        direction = planner.get_direction("tech_ai")

        one = planner.plan_direction(items, direction)
        assert one["direction"] == "tech_ai"
        assert "score_summary" in one
        assert isinstance(one["items"], list)

        all_results = planner.plan(str(sample_pool))
        assert "tech_ai" in all_results
        assert "auto" in all_results

        only_auto = planner.plan(str(sample_pool), direction_name="auto")
        assert list(only_auto.keys()) == ["auto"]

    def test_recommend_topics_skips_empty_items(self, monkeypatch):
        """无可用素材时不应继续调用 AI 脑补选题。"""
        planner = _import_planner_with_stub(monkeypatch)
        text, topics = planner.recommend_topics([], planner.get_direction("auto"))
        assert "没有符合时效要求的素材" in text
        assert topics == []
