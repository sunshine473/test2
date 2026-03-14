"""test_collector_dedup.py — dedup.py 单元测试"""

from collector.dedup import Deduplicator, _canonical_url, _normalize_title


class TestNormalizeAndCanonical:
    def test_normalize_title(self):
        """标题规范化：小写、压缩空格、去除标点。"""
        assert _normalize_title("  GPT-5!!!   发布  ") == "gpt5 发布"

    def test_canonical_url_special_sites(self):
        """百度/微博/YouTube URL 归一化。"""
        assert _canonical_url("https://www.baidu.com/s?wd=新能源车") == "baidu:新能源车"
        assert _canonical_url("https://s.weibo.com/weibo?q=%E6%99%BA%E9%A9%BE") == "weibo:智驾"
        assert _canonical_url("https://www.youtube.com/watch?v=abc123&t=1s") == "youtube:abc123"
        assert _canonical_url("https://youtu.be/xyz789") == "youtube:xyz789"


class TestDeduplicator:
    def test_dedup_by_url_keep_richer_item(self, make_item):
        """同 URL 去重时保留主要内容更完整的一条。"""
        short = make_item(
            title="Same",
            url="https://example.com/a",
            summary="short",
            content="tiny",
        )
        rich = make_item(
            title="Same richer title",
            url="https://example.com/a/",
            summary="short",
            content="this content is much longer than the existing item",
        )
        dedup = Deduplicator()
        unique = dedup._dedup_by_url([short, rich])
        assert len(unique) == 1
        assert unique[0].title == "Same richer title"

    def test_cluster_and_process_metadata(self, make_item):
        """相似标题聚类并注入 cluster_id/cluster_size。"""
        item1 = make_item(title="OpenAI releases GPT-5 for coding", url="https://example.com/1")
        item2 = make_item(title="OpenAI released GPT5 for coding", url="https://example.com/2")
        item3 = make_item(title="Tesla launches new EV battery", url="https://example.com/3")

        dedup = Deduplicator(title_similarity_threshold=0.75)
        ranked, clusters = dedup.process([item1, item2, item3])

        assert len(clusters) == 2
        assert clusters[0].cluster_id == "C001"
        assert len(clusters[0].items) == 2
        assert len(ranked) == 2
        assert ranked[0].raw_data["cluster_id"] == "C001"
        assert ranked[0].raw_data["cluster_size"] == 2

    def test_summarize_clusters(self, make_item):
        """聚类摘要统计返回簇数、最大簇和来源分布。"""
        dedup = Deduplicator()
        _, clusters = dedup.process(
            [
                make_item(title="A1", source_name="Hacker News", url="https://example.com/a1"),
                make_item(title="A2", source_name="Hacker News", url="https://example.com/a2"),
                make_item(title="B1", source_name="微博热搜", url="https://example.com/b1"),
            ]
        )
        summary = dedup.summarize_clusters(clusters)
        assert summary["cluster_count"] == 3
        assert summary["max_cluster_size"] == 1
        assert summary["source_distribution"] == {"Hacker News": 2, "微博热搜": 1}
