"""test_publisher_main.py — publisher/main.py 单元测试"""

import base64
from types import SimpleNamespace
from pathlib import Path

import pytest

import publisher.main as publisher_main
from publisher.main import parse_article, extract_images_from_cards_html


class TestParseArticle:
    def test_with_frontmatter(self, sample_article_path):
        """完整 frontmatter 解析。"""
        article = parse_article(str(sample_article_path))
        assert article.title == "测试文章标题"
        assert article.author == "测试作者"
        assert article.digest == "这是一篇测试文章的摘要"
        assert "AI" in article.tags
        assert "测试" in article.tags
        assert "# 测试文章标题" in article.content

    def test_no_frontmatter(self, tmp_path):
        """无 frontmatter 用文件名做标题。"""
        md = tmp_path / "my-cool-article.md"
        md.write_text("# Just content\n\nSome text here.", encoding="utf-8")
        article = parse_article(str(md))
        assert article.title == "my-cool-article"
        assert article.author == ""
        assert article.tags == []
        assert "Just content" in article.content

    def test_missing_file_raises(self, tmp_path):
        """文件不存在时抛 FileNotFoundError。"""
        missing = tmp_path / "missing.md"
        with pytest.raises(FileNotFoundError, match="missing.md"):
            parse_article(str(missing))

    def test_yaml_frontmatter_with_list_tags(self, tmp_path):
        """frontmatter 支持 YAML 列表 tags 和包含冒号的字符串。"""
        md = tmp_path / "yaml-frontmatter.md"
        md.write_text(
            "---\n"
            "title: \"含冒号: 标题\"\n"
            "author: 作者A\n"
            "digest: \"摘要: 支持冒号\"\n"
            "tags:\n"
            "  - AI\n"
            "  - 测试\n"
            "---\n"
            "# 内容\n",
            encoding="utf-8",
        )
        article = parse_article(str(md))
        assert article.title == "含冒号: 标题"
        assert article.digest == "摘要: 支持冒号"
        assert article.tags == ["AI", "测试"]


class TestExtractImages:
    def test_no_html(self, tmp_path):
        """无卡片 HTML 文件返回空列表。"""
        fake_path = tmp_path / "nonexistent-cards.html"
        result = extract_images_from_cards_html(fake_path)
        assert result == []

    def test_no_base64_in_html(self, tmp_path):
        """HTML 中无 base64 图片返回空列表。"""
        html_path = tmp_path / "test-cards.html"
        html_path.write_text("<html><body><p>No images</p></body></html>", encoding="utf-8")
        result = extract_images_from_cards_html(html_path)
        assert result == []

    def test_with_base64(self, tmp_path):
        """提取 base64 图片并保存为临时文件。"""
        # 创建一个 1x1 白色 PNG 的 base64
        png_1x1 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "nGP4z8BQDwAEgAF/pooBPQAAAABJRU5ErkJggg=="
        )
        html_content = f'<img src="data:image/png;base64,{png_1x1}" />'
        html_path = tmp_path / "test-cards.html"
        html_path.write_text(html_content, encoding="utf-8")

        result = extract_images_from_cards_html(html_path)
        assert len(result) == 1
        # 验证文件确实存在且是有效的 PNG
        img_path = Path(result[0])
        assert img_path.exists()
        assert img_path.read_bytes()[:4] == b"\x89PNG"


class TestMainFlow:
    def test_continue_on_platform_error(self, monkeypatch, tmp_path, capsys):
        """单平台异常不应中断后续平台发布。"""
        md = tmp_path / "article.md"
        md.write_text("---\ntitle: 测试\n---\n内容", encoding="utf-8")

        monkeypatch.setattr(
            "publisher.main.argparse.ArgumentParser.parse_args",
            lambda self: SimpleNamespace(filepath=str(md), platforms=None),
        )
        monkeypatch.setattr(
            "publisher.main.load_config",
            lambda: {"wechat": {"enabled": True}, "zhihu": {"enabled": True}},
        )

        class FailPublisher:
            def publish(self, article, config):
                raise RuntimeError("boom")

        class OkPublisher:
            def publish(self, article, config):
                from publisher.models import PublishResult, PublishStatus
                return PublishResult(platform="zhihu", status=PublishStatus.SUCCESS, message="ok")

        def fake_get_publisher(name):
            return FailPublisher() if name == "wechat" else OkPublisher()

        monkeypatch.setattr("publisher.main.get_publisher", fake_get_publisher)

        publisher_main.main()
        out = capsys.readouterr().out
        assert "[wechat] 错误: boom" in out
        assert "[zhihu] success: ok" in out
