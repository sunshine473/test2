"""test_bot_tools.py — tools.py 单元测试"""

import json
from pathlib import Path

from bot.tools import (
    _truncate,
    execute_tool,
    tool_check_drafts,
    tool_check_pool,
    tool_check_status,
    tool_write,
    _find_latest_pool,
    MAX_RESULT_LEN,
)


class TestTruncate:
    def test_short_text(self):
        """短文本不截断。"""
        text = "hello"
        assert _truncate(text) == text

    def test_long_text(self):
        """超长文本截断并附带提示。"""
        text = "A" * 10000
        result = _truncate(text)
        assert len(result) < len(text)
        assert "已截断" in result
        assert "10000" in result

    def test_exact_boundary(self):
        """恰好 MAX_RESULT_LEN 不截断。"""
        text = "B" * MAX_RESULT_LEN
        assert _truncate(text) == text


class TestCheckPool:
    def test_no_pool(self, monkeypatch, tmp_path):
        """无素材池返回错误。"""
        monkeypatch.setattr("bot.tools.POOL_DIR", tmp_path / "nonexistent")
        result = tool_check_pool({})
        data = json.loads(result)
        assert "error" in data

    def test_with_data(self, monkeypatch, sample_pool_path):
        """有素材池返回摘要。"""
        monkeypatch.setattr("bot.tools.POOL_DIR", sample_pool_path.parent)
        result = tool_check_pool({})
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["total"] == 3


class TestCheckDrafts:
    def test_empty(self, monkeypatch, tmp_path):
        """空目录返回 0 条。"""
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        monkeypatch.setattr("bot.tools.DRAFTS_DIR", drafts)
        result = tool_check_drafts({})
        data = json.loads(result)
        assert data["total"] == 0
        assert data["files"] == []

    def test_with_files(self, monkeypatch, tmp_path):
        """有草稿文件时正确列出。"""
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "2026-02-26-test.md").write_text("# Test", encoding="utf-8")
        (drafts / "2026-02-25-old.md").write_text("# Old", encoding="utf-8")
        monkeypatch.setattr("bot.tools.DRAFTS_DIR", drafts)
        result = tool_check_drafts({})
        data = json.loads(result)
        assert data["total"] == 2
        assert len(data["files"]) == 2


class TestCheckStatus:
    def test_basic(self, monkeypatch, tmp_path):
        """mock 配置文件，验证返回结构。"""
        # 无素材池
        monkeypatch.setattr("bot.tools.POOL_DIR", tmp_path / "pool")
        # 无草稿
        monkeypatch.setattr("bot.tools.DRAFTS_DIR", tmp_path / "drafts")
        # mock PROJECT_ROOT 使 publishers.yaml 不存在
        monkeypatch.setattr("bot.tools.PROJECT_ROOT", tmp_path)

        result = tool_check_status({})
        data = json.loads(result)
        assert data["pool"] is None
        assert data["drafts"]["count"] == 0


class TestToolWrite:
    def test_no_topic(self):
        """缺少 topic 返回错误。"""
        result = tool_write({"topic": ""})
        data = json.loads(result)
        assert "error" in data
        assert "topic" in data["error"]


class TestExecuteTool:
    def test_unknown_tool(self):
        """未知工具名返回错误。"""
        result = execute_tool("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data
        assert "未知工具" in data["error"]

    def test_known_tool(self, monkeypatch, tmp_path):
        """已知工具正常执行。"""
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        monkeypatch.setattr("bot.tools.DRAFTS_DIR", drafts)
        result = execute_tool("check_drafts", {})
        data = json.loads(result)
        assert data["status"] == "ok"


class TestToolPublish:
    def test_missing_file_returns_error(self):
        """缺失文件应返回错误，而不是退出进程。"""
        result = execute_tool("publish", {"filepath": "does-not-exist.md"})
        data = json.loads(result)
        assert "error" in data
        assert "does-not-exist.md" in data["error"]

    def test_all_failed_status_failed(self, monkeypatch, tmp_path):
        """所有平台失败时，聚合状态应为 failed。"""
        md = tmp_path / "article.md"
        md.write_text("---\ntitle: t\n---\nbody", encoding="utf-8")

        monkeypatch.setattr("publisher.main.load_config", lambda: {"wechat": {"enabled": True}})
        monkeypatch.setattr("publisher.main.parse_article", lambda _: object())

        class BadPublisher:
            def publish(self, article, config):
                raise RuntimeError("boom")

        monkeypatch.setattr("publisher.registry.get_publisher", lambda _: BadPublisher())

        result = execute_tool("publish", {"filepath": str(md)})
        data = json.loads(result)
        assert data["status"] == "failed"
        assert data["results"][0]["status"] == "failed"
