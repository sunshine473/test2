"""素材采集主入口

用法:
    python -m collector.main                                 # 采集并写入 Notion
    python -m collector.main --sources hn,github,hot                 # 只采集 HN/GitHub/热搜
    python -m collector.main --sources youtube_api,hn,github,hot     # 含 YouTube API 采集
    python -m collector.main --sources rss,hn,github,tavily          # 自定义采集源
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import yaml
from dotenv import load_dotenv

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

load_dotenv()

from collector.models import CollectedItem
from collector.dedup import Deduplicator
from collector.scorer import ItemScorer
from collector.sources.hacker_news import HackerNewsSource
from collector.sources.github_trending import GitHubTrendingSource
from collector.sources.hot_search import HotSearchSource
from collector.sources.rss import RSSSource
from collector.sources.youtube_api import YouTubeAPISource


def load_config() -> dict:
    config_path = PROJECT_ROOT / "src" / "config" / "sources.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_utf8():
    """Windows 控制台 UTF-8 兼容"""
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)


def collect_all(config: dict, sources: List[str]) -> List[CollectedItem]:
    items = []

    # RSS + YouTube
    if "rss" in sources:
        print("[1/6] 采集 RSS + YouTube...")
        rss = RSSSource()
        items.extend(rss.collect(config.get("rss", {})))

    # Hacker News
    if "hn" in sources:
        print("[2/6] 采集 Hacker News...")
        hn = HackerNewsSource()
        items.extend(hn.collect(config.get("hacker_news", {})))

    # GitHub Trending
    if "github" in sources:
        print("[3/6] 采集 GitHub Trending...")
        gh = GitHubTrendingSource()
        items.extend(gh.collect(config.get("scraper", [])))

    # 微博/百度热搜
    if "hot" in sources:
        print("[4/7] 采集 微博/百度热搜...")
        hot = HotSearchSource()
        items.extend(hot.collect(config.get("hot_search", {})))

    # YouTube Data API
    if "youtube_api" in sources:
        print("[5/7] 采集 YouTube API...")
        try:
            yt = YouTubeAPISource()
            items.extend(yt.collect(config.get("youtube_api", {})))
        except ValueError as e:
            print(f"  跳过 YouTube API: {e}")

    # Tavily 搜索
    if "tavily" in sources:
        print("[6/7] 采集 Tavily 搜索...")
        try:
            from collector.sources.tavily_search import TavilySearchSource
            tavily = TavilySearchSource()
            items.extend(tavily.collect(config.get("tavily", {})))
        except ValueError as e:
            print(f"  跳过 Tavily: {e}")

    # X/Twitter
    if "twitter" in sources:
        print("[7/7] 采集 X/Twitter...")
        try:
            from collector.sources.twitter import TwitterSource
            twitter = TwitterSource()
            items.extend(twitter.collect(config.get("twitter", {})))
        except ValueError as e:
            print(f"  跳过 Twitter: {e}")

    return items


def main():
    parser = argparse.ArgumentParser(description="素材采集器")
    parser.add_argument(
        "--sources",
        default="rss,hn,github,hot,tavily,youtube_api",
        help="要采集的信息源，逗号分隔 (rss,hn,github,hot,youtube_api,tavily,twitter)",
    )
    args = parser.parse_args()

    ensure_utf8()
    source_list = [s.strip() for s in args.sources.split(",")]
    slow_sources = {"tavily", "twitter"}
    if any(source in slow_sources for source in source_list):
        print("提示: Tavily/Twitter 属于慢速采集源，首次运行建议先用 --sources rss,github")

    print(f"=== 素材采集开始 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    print(f"采集源: {', '.join(source_list)}\n")

    config = load_config()
    raw_items = collect_all(config, source_list)
    print(f"\n=== 原始采集 {len(raw_items)} 条，开始去重聚类 ===")
    deduplicator = Deduplicator()
    dedup_items, clusters = deduplicator.process(raw_items)
    dedup_summary = deduplicator.summarize_clusters(clusters)
    print(
        f"去重后 {len(dedup_items)} 条，聚类 {dedup_summary['cluster_count']} 组，"
        f"最大簇 {dedup_summary['max_cluster_size']} 条"
    )

    print("=== 开始打分排序 ===")
    scorer = ItemScorer()
    items = scorer.score_and_rank(dedup_items)
    score_summary = scorer.summarize_scores(items)
    print(
        f"打分完成: max={score_summary['max']}, "
        f"avg={score_summary['avg']}, min={score_summary['min']}"
    )

    print(f"\n=== 采集完成，共 {len(items)} 条素材 ===\n")

    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "raw_total": len(raw_items),
        "cluster_total": len(clusters),
        "total": len(items),
        "score_summary": score_summary,
        "cluster_summary": dedup_summary,
        "items": [item.to_dict() for item in items],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 强制同步 Notion：未配置凭据或写入失败时直接退出
    if not (os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID")):
        raise SystemExit(
            "Notion 同步为必选项，但缺少环境变量: NOTION_API_KEY / NOTION_DATABASE_ID"
        )

    if not items:
        raise SystemExit("本次采集结果为空，未写入 Notion。")

    print(f"\n[Notion] 正在写入 {len(items)} 条素材...")
    try:
        from collector.notion_output import NotionOutput

        notion = NotionOutput()
        saved = notion.save(items)
        print(f"[Notion] 成功写入 {saved}/{len(items)} 条")
        if saved == 0:
            raise SystemExit("Notion 同步失败：0 条写入成功。")
    except Exception as e:
        raise SystemExit(f"[Notion] 写入失败: {e}") from e


if __name__ == "__main__":
    main()
