"""test_collector_scorer.py — scorer.py 单元测试"""

from freezegun import freeze_time

from collector.scorer import ItemScorer


class TestRecencyAndKeyword:
    @freeze_time("2026-02-26 12:00:00+00:00")
    def test_recency_bonus_buckets(self):
        """时效性加分分段。"""
        scorer = ItemScorer()
        assert scorer._recency_bonus("2026-02-26T10:00:00Z") == 10
        assert scorer._recency_bonus("2026-02-26T00:30:00Z") == 8
        assert scorer._recency_bonus("2026-02-24T12:00:00Z") == 6
        assert scorer._recency_bonus("2026-02-20T12:00:00Z") == 4
        assert scorer._recency_bonus("2026-02-10T12:00:00Z") == 1

    def test_keyword_bonus_and_cap(self, make_item):
        """关键词匹配累计并受上限约束。"""
        scorer = ItemScorer()
        item = make_item(
            title="OpenAI agent 模型",
            summary="llm deepmind anthropic 自动驾驶 机器人",
        )
        bonus = scorer._keyword_bonus(item)
        assert bonus == 15


class TestScoreAndRank:
    @freeze_time("2026-02-26 12:00:00+00:00")
    def test_score_and_rank(self, make_item):
        """打分后按 score、cluster_size、title 排序。"""
        scorer = ItemScorer()
        top = make_item(
            title="OpenAI agent update",
            source_name="Hacker News",
            category="tech_ai",
            published_at="2026-02-26T11:30:00Z",
            raw_data={"cluster_size": 3, "hn_points": 200},
        )
        mid = make_item(
            title="中等热度新闻",
            source_name="百度热搜",
            category="trending",
            published_at="2026-02-25T20:00:00Z",
            raw_data={"cluster_size": 1},
        )
        low = make_item(
            title="旧闻",
            source_name="Unknown",
            category="unknown",
            published_at="2026-02-01T08:00:00Z",
            raw_data={"cluster_size": 1},
        )

        ranked = scorer.score_and_rank([mid, low, top])
        assert ranked[0].title == "OpenAI agent update"
        assert ranked[1].title == "中等热度新闻"
        assert ranked[2].title == "旧闻"
        assert (ranked[0].raw_data or {})["score"] > (ranked[1].raw_data or {})["score"]
        assert any(r.startswith("recency:") for r in (ranked[0].raw_data or {})["score_reasons"])

    def test_summarize_scores(self, make_item):
        """分数摘要计算 max/min/avg。"""
        item1 = make_item(raw_data={"score": 10})
        item2 = make_item(raw_data={"score": 20})
        item3 = make_item(raw_data={"score": 30})
        summary = ItemScorer.summarize_scores([item1, item2, item3])
        assert summary == {"max": 30, "min": 10, "avg": 20}
