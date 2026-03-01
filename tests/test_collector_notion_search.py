"""test_collector_notion_search.py — notion_search 查询范围测试"""

import sys
import types

from collector.notion_search import search_notion


def test_search_notion_uses_database_query_in_non_data_sources_mode(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "test-key")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db")

    calls = {"databases_query": 0, "search": 0}

    class FakeDatabases:
        @staticmethod
        def retrieve(database_id):
            return {
                "properties": {
                    "标题": {"type": "title"},
                    "URL": {"type": "url"},
                    "摘要": {"type": "rich_text"},
                }
            }

        @staticmethod
        def query(database_id, filter, page_size):
            calls["databases_query"] += 1
            return {
                "results": [
                    {
                        "properties": {
                            "标题": {"title": [{"plain_text": "AI 新闻"}]},
                            "URL": {"url": "https://example.com"},
                            "摘要": {"rich_text": [{"plain_text": "摘要"}]},
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, auth):
            self.databases = FakeDatabases()
            self.data_sources = None

        def search(self, **kwargs):
            calls["search"] += 1
            return {"results": []}

    fake_notion = types.ModuleType("notion_client")
    fake_notion.Client = FakeClient
    monkeypatch.setitem(sys.modules, "notion_client", fake_notion)

    results = search_notion(["AI"], limit=5)
    assert len(results) == 1
    assert calls["databases_query"] == 1
    assert calls["search"] == 0
