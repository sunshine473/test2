"""test_generator_writer.py — writer.py 单元测试"""

import importlib
import shutil
import sys
import types
from pathlib import Path

from freezegun import freeze_time


def _import_writer_with_stub(monkeypatch):
    fake_gemini = types.ModuleType("generator.gemini_client")
    fake_gemini.generate_text = lambda prompt, task="article": f"mock:{task}:{prompt[:20]}"
    monkeypatch.setitem(sys.modules, "generator.gemini_client", fake_gemini)
    sys.modules.pop("generator.writer", None)
    return importlib.import_module("generator.writer")


class TestWriter:
    def test_make_slug(self, monkeypatch):
        """slug 生成：保留中文/字母数字，空格转连字符。"""
        writer = _import_writer_with_stub(monkeypatch)
        slug = writer._make_slug("  GPT-5 发布：多模态 + Agent!  ")
        assert slug == "GPT-5-发布多模态-Agent"

    @freeze_time("2026-02-26 12:00:00")
    def test_generate_article_with_mock_gemini(self, monkeypatch):
        """mock Gemini API，验证 prompt 组装与文件落盘。"""
        writer = _import_writer_with_stub(monkeypatch)
        test_tmp = Path(__file__).parent / ".tmp_writer"
        shutil.rmtree(test_tmp, ignore_errors=True)
        (test_tmp / "drafts").mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(writer, "DRAFTS_DIR", test_tmp / "drafts")
        monkeypatch.setattr(writer, "_load_template", lambda _: "题目:{topic}\n素材:\n{sources}")

        captured = {}

        def fake_generate_text(prompt, task="article"):
            captured["prompt"] = prompt
            captured["task"] = task
            return "# 标题\n\n正文"

        monkeypatch.setattr(writer, "generate_text", fake_generate_text)
        content, output_path = writer.generate_article(
            "测试选题",
            sources=["来源1", "来源2"],
        )

        assert content == "# 标题\n\n正文"
        assert output_path.name == "2026-02-26-测试选题.md"
        assert output_path.exists()
        assert "题目:测试选题" in captured["prompt"]
        assert "- 来源1" in captured["prompt"]
        assert captured["task"] == "article"

        shutil.rmtree(test_tmp, ignore_errors=True)
