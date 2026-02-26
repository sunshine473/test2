"""共享 fixtures — 为所有测试模块提供工厂函数和临时资源。"""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def make_item():
    """CollectedItem 工厂函数，快速创建测试用素材条目。"""
    from collector.models import CollectedItem

    def _factory(**overrides):
        defaults = {
            "title": "测试标题",
            "url": "https://example.com/test",
            "source_name": "Hacker News",
            "source_type": "scraper",
            "category": "tech_ai",
            "summary": "测试摘要",
            "published_at": "2026-02-26T08:00:00Z",
            "language": "zh",
        }
        defaults.update(overrides)
        return CollectedItem(**defaults)

    return _factory


@pytest.fixture()
def sample_pool_path(tmp_path):
    """将 sample_pool.json 复制到临时目录并返回路径。"""
    src = FIXTURES_DIR / "sample_pool.json"
    dst = tmp_path / "2026-02-26-pool.json"
    shutil.copy(src, dst)
    return dst


@pytest.fixture()
def sample_article_path(tmp_path):
    """将 sample_article.md 复制到临时目录并返回路径。"""
    src = FIXTURES_DIR / "sample_article.md"
    dst = tmp_path / "2026-02-26-test-article.md"
    shutil.copy(src, dst)
    return dst


@pytest.fixture()
def tmp_content_dir(tmp_path):
    """创建临时 content/ 目录结构。"""
    pool_dir = tmp_path / "content" / "pool"
    drafts_dir = tmp_path / "content" / "drafts"
    ready_dir = tmp_path / "content" / "ready"
    published_dir = tmp_path / "content" / "published"
    for d in [pool_dir, drafts_dir, ready_dir, published_dir]:
        d.mkdir(parents=True)
    return tmp_path / "content"
