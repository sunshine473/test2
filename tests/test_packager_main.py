"""test_packager_main.py — 包装层测试"""

from pathlib import Path

from packager.main import build_publish_packages, load_draft_package, package_to_article


def test_load_draft_package_extracts_frontmatter(sample_article_path):
    draft = load_draft_package(str(sample_article_path))

    assert draft.title == "测试文章标题"
    assert draft.summary == "这是一篇测试文章的摘要"
    assert "AI" in draft.metadata["tags"]
    assert draft.metadata["source_path"].endswith(sample_article_path.name)


def test_build_publish_packages_for_zhihu_outputs_html(sample_article_path):
    draft = load_draft_package(str(sample_article_path))

    packages = build_publish_packages(draft, ["zhihu", "xiaohongshu"])

    zhihu_package = next(item for item in packages if item.platform == "zhihu")
    xhs_package = next(item for item in packages if item.platform == "xiaohongshu")
    article = package_to_article(zhihu_package)

    assert zhihu_package.format == "html"
    assert "<h1>" in zhihu_package.body
    assert article.metadata["content_format"] == "html"
    assert "body_excerpt" in xhs_package.extra


def test_load_draft_package_uses_markdown_h1_as_title_when_frontmatter_missing(tmp_path: Path):
    article_path = tmp_path / "2026-03-15-english-slug.md"
    article_path.write_text(
        "# 为什么说 Linux 才是数字世界真正的“不老”系统？\n\n正文内容。",
        encoding="utf-8",
    )

    draft = load_draft_package(str(article_path))

    assert draft.title == "为什么说 Linux 才是数字世界真正的“不老”系统？"


def test_load_draft_package_finds_cards_without_date_prefix(tmp_path: Path):
    article_path = tmp_path / "2026-03-15-sample-article.md"
    cards_path = tmp_path / "sample-article-cards.html"
    article_path.write_text("# 示例标题\n\n正文内容。", encoding="utf-8")
    cards_path.write_text(
        '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a8XcAAAAASUVORK5CYII=">',
        encoding="utf-8",
    )

    draft = load_draft_package(str(article_path))

    assert len(draft.assets["images"]) == 1
