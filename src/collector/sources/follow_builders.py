"""Follow Builders feed 采集适配器。

将 `follow-builders` 的中心化 JSON feed 转换为当前仓库的 CollectedItem，
让每日 AI 素材可以复用现有 normalize / planner / writer 链路。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List
from urllib.request import urlopen

from collector.models import CollectedItem
from collector.sources.base import BaseSource, clip_text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCAL_DIR = PROJECT_ROOT / "follow-builders"
DEFAULT_REMOTE_FEEDS = {
    "x": "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json",
    "podcasts": "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-podcasts.json",
    "blogs": "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-blogs.json",
}


class FollowBuildersSource(BaseSource):
    """读取 follow-builders 的 builders / podcast / blog feed。"""

    def collect(self, config: dict) -> List[CollectedItem]:
        local_dir = Path(config.get("local_dir") or DEFAULT_LOCAL_DIR)
        if not local_dir.is_absolute():
            local_dir = PROJECT_ROOT / local_dir

        include = set(config.get("include") or ("x", "podcasts", "blogs"))
        category = config.get("category", "tech_ai")
        language = config.get("language", "en")
        remote_feeds = dict(DEFAULT_REMOTE_FEEDS)
        remote_feeds.update(config.get("remote_feeds") or {})

        items: List[CollectedItem] = []
        print(f"  [FollowBuilders] {local_dir}...")

        if "x" in include:
            feed = self._load_feed(local_dir / "feed-x.json", remote_feeds.get("x", ""))
            items.extend(self._collect_x(
                feed.get("x", []),
                category=category,
                language=language,
                max_tweets_per_builder=int(config.get("max_tweets_per_builder", 3)),
            ))

        if "podcasts" in include:
            feed = self._load_feed(local_dir / "feed-podcasts.json", remote_feeds.get("podcasts", ""))
            items.extend(self._collect_podcasts(
                feed.get("podcasts", []),
                category=category,
                language=language,
                max_podcasts=int(config.get("max_podcasts", 3)),
            ))

        if "blogs" in include:
            feed = self._load_feed(local_dir / "feed-blogs.json", remote_feeds.get("blogs", ""))
            items.extend(self._collect_blogs(
                feed.get("blogs", []),
                category=category,
                language=language,
                max_blogs=int(config.get("max_blogs", 5)),
            ))

        return items

    @staticmethod
    def _load_feed(path: Path, remote_url: str = "") -> dict:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"  [FollowBuilders] 读取失败 {path}: {exc}")

        if remote_url:
            try:
                with urlopen(remote_url, timeout=20) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                print(f"  [FollowBuilders] 远端读取失败 {remote_url}: {exc}")
        else:
            print(f"  [FollowBuilders] 缺少 feed: {path}")
        return {}

    def _collect_x(
        self,
        builders: Iterable[dict],
        *,
        category: str,
        language: str,
        max_tweets_per_builder: int,
    ) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        for builder in builders:
            name = builder.get("name") or builder.get("handle") or "Unknown Builder"
            handle = builder.get("handle", "")
            for tweet in (builder.get("tweets") or [])[:max_tweets_per_builder]:
                text = tweet.get("text", "")
                if not self._is_substantive_tweet(text):
                    continue
                title = self._tweet_title(name, text)
                items.append(CollectedItem(
                    title=title,
                    url=tweet.get("url", ""),
                    source_name="Follow Builders X",
                    source_type="follow_builders_x",
                    category=category,
                    summary=clip_text(text, 300),
                    content=clip_text(text, 4000),
                    published_at=tweet.get("createdAt", ""),
                    language=language,
                    raw_data={
                        "builder_name": name,
                        "handle": handle,
                        "tweet_id": tweet.get("id", ""),
                        "likes": tweet.get("likes", 0),
                        "retweets": tweet.get("retweets", 0),
                        "replies": tweet.get("replies", 0),
                        "bio": builder.get("bio", ""),
                    },
                ))
        return items

    @staticmethod
    def _is_substantive_tweet(text: str) -> bool:
        compact = " ".join((text or "").split())
        without_urls = re.sub(r"https?://\S+", "", compact).strip()
        letters = re.findall(r"[A-Za-z\u4e00-\u9fff]", without_urls)
        return len(letters) >= 24

    @staticmethod
    def _tweet_title(name: str, text: str) -> str:
        compact = " ".join((text or "").split())
        return f"{name}: {compact[:96]}".rstrip()

    def _collect_podcasts(
        self,
        podcasts: Iterable[dict],
        *,
        category: str,
        language: str,
        max_podcasts: int,
    ) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        for podcast in list(podcasts)[:max_podcasts]:
            transcript = podcast.get("transcript", "")
            title = podcast.get("title") or "Untitled Podcast Episode"
            if not transcript.strip() and not title.strip():
                continue
            items.append(CollectedItem(
                title=f"{podcast.get('name', 'Podcast')}: {title}",
                url=podcast.get("url", ""),
                source_name="Follow Builders Podcast",
                source_type="follow_builders_podcast",
                category=category,
                summary=clip_text(transcript or title, 500),
                content=clip_text(transcript, 12000),
                published_at=podcast.get("publishedAt", ""),
                language=language,
                raw_data={
                    "podcast_name": podcast.get("name", ""),
                    "guid": podcast.get("guid", ""),
                },
            ))
        return items

    def _collect_blogs(
        self,
        blogs: Iterable[dict],
        *,
        category: str,
        language: str,
        max_blogs: int,
    ) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        for blog in list(blogs)[:max_blogs]:
            title = blog.get("title") or "Untitled Blog Post"
            content = blog.get("content", "")
            description = blog.get("description", "")
            if not content.strip() and not description.strip():
                continue
            items.append(CollectedItem(
                title=f"{blog.get('name', 'Blog')}: {title}",
                url=blog.get("url", ""),
                source_name="Follow Builders Blog",
                source_type="follow_builders_blog",
                category=category,
                summary=clip_text(description or content, 500),
                content=clip_text(content or description, 12000),
                published_at=blog.get("publishedAt", ""),
                language=language,
                raw_data={
                    "blog_name": blog.get("name", ""),
                    "author": blog.get("author", ""),
                },
            ))
        return items
