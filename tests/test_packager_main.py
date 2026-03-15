"""test_packager_main.py — 包装层测试"""

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
