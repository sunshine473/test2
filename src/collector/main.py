"""素材采集主入口 — 串联搜索 + 策划的一键入口。

用法:
    python -m collector.main                                    # 搜索 + 两方向策划
    python -m collector.main --sources hn,github,hot            # 指定源
    python -m collector.main --search-only                      # 仅搜索
    python -m collector.main --plan-only --pool <path>          # 仅策划
    python -m collector.main --direction tech_ai                # 指定方向
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

ALLOWED_SOURCES = {"rss", "hn", "github", "hot", "youtube_api", "tavily", "twitter"}


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


def collect_all(config: dict, sources: List[str]) -> tuple[List[CollectedItem], dict]:
    """采集所有信息源，返回素材列表和分源统计"""
    items = []
    stats = {}

    def safe_collect(source_key: str, label: str, fn):
        try:
            collected = fn()
            stats[source_key] = len(collected)
            items.extend(collected)
        except Exception as e:
            print(f"  跳过 {label}: {e}")
            stats[source_key] = 0

    # RSS + YouTube
    if "rss" in sources:
        print("[1/7] 采集 RSS + YouTube...")
        safe_collect("rss", "RSS", lambda: RSSSource().collect(config.get("rss", {})))

    # Hacker News
    if "hn" in sources:
        print("[2/7] 采集 Hacker News...")
        safe_collect("hn", "Hacker News", lambda: HackerNewsSource().collect(config.get("hacker_news", {})))

    # GitHub Trending
    if "github" in sources:
        print("[3/7] 采集 GitHub Trending...")
        safe_collect("github", "GitHub Trending", lambda: GitHubTrendingSource().collect(config.get("scraper", [])))

    # 微博/百度热搜
    if "hot" in sources:
        print("[4/7] 采集 微博/百度热搜...")
        safe_collect("hot", "微博/百度热搜", lambda: HotSearchSource().collect(config.get("hot_search", {})))

    # YouTube Data API
    if "youtube_api" in sources:
        print("[5/7] 采集 YouTube API...")
        safe_collect("youtube_api", "YouTube API", lambda: YouTubeAPISource().collect(config.get("youtube_api", {})))

    # Tavily 搜索
    if "tavily" in sources:
        print("[6/7] 采集 Tavily 搜索...")
        def collect_tavily():
            from collector.sources.tavily_search import TavilySearchSource
            return TavilySearchSource().collect(config.get("tavily", {}))
        safe_collect("tavily", "Tavily", collect_tavily)

    # X/Twitter
    if "twitter" in sources:
        print("[7/7] 采集 X/Twitter...")
        def collect_twitter():
            from collector.sources.twitter import TwitterSource
            return TwitterSource().collect(config.get("twitter", {}))
        safe_collect("twitter", "Twitter", collect_twitter)

    return items, stats


def parse_sources_arg(raw_sources: str) -> List[str]:
    """解析并校验 sources 参数，返回去重后的源列表。"""
    source_list: List[str] = []
    seen = set()
    for source in (s.strip() for s in (raw_sources or "").split(",")):
        if not source:
            continue
        if source not in ALLOWED_SOURCES:
            allowed = ",".join(sorted(ALLOWED_SOURCES))
            raise ValueError(f"未知 source: {source}（可用: {allowed}）")
        if source not in seen:
            seen.add(source)
            source_list.append(source)

    if not source_list:
        raise ValueError("sources 不能为空")
    return source_list


def main():
    parser = argparse.ArgumentParser(description="素材采集器（搜索 + 策划）")
    parser.add_argument(
        "--sources",
        default="rss,hn,github,hot,tavily,youtube_api",
        help="要采集的信息源，逗号分隔 (rss,hn,github,hot,youtube_api,tavily,twitter)",
    )
    parser.add_argument("--search-only", action="store_true", help="仅执行搜索阶段")
    parser.add_argument("--plan-only", action="store_true", help="仅执行策划阶段")
    parser.add_argument("--pool", default=None, help="素材池 JSON 路径（--plan-only 时使用）")
    parser.add_argument("--direction", choices=["tech_ai", "auto"], default=None,
                        help="指定方向（默认两个方向都跑）")
    args = parser.parse_args()

    ensure_utf8()

    # 仅策划模式
    if args.plan_only:
        from collector.planner import plan, find_latest_pool
        pool_path = args.pool or find_latest_pool()
        if not pool_path:
            raise SystemExit("错误: 未找到素材池 JSON，请先运行搜索或指定 --pool 路径")
        results = plan(pool_path, args.direction)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # 搜索阶段
    from collector.search import search
    try:
        source_list = parse_sources_arg(args.sources)
    except ValueError as e:
        raise SystemExit(f"错误: {e}")
    slow_sources = {"tavily", "twitter"}
    if any(source in slow_sources for source in source_list):
        print("提示: Tavily/Twitter 属于慢速采集源，首次运行建议先用 --sources rss,github")

    pool = search(source_list)

    if args.search_only:
        print(json.dumps(pool, indent=2, ensure_ascii=False))
        return

    # 策划阶段
    from collector.planner import plan
    from collector.search import POOL_DIR
    pool_path = str(POOL_DIR / f"{pool['date']}-pool.json")
    results = plan(pool_path, args.direction)

    # Telegram 通知（交互式）
    try:
        from collector.telegram_notifier_interactive import InteractiveTelegramNotifier
        InteractiveTelegramNotifier().notify_with_buttons(pool, results)
    except Exception as e:
        print(f"[Telegram] 通知异常: {e}")

    output = {"search": pool, "plan": results}
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
