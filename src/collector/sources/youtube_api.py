"""YouTube Data API v3 采集适配器。"""

from typing import Dict, List, Optional

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from collector.models import CollectedItem
from collector.sources.base import BaseSource, clip_text


class YouTubeAPISource(BaseSource):
    """通过 channels.list + playlistItems.list 拉取频道最新视频。"""

    API_BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        import os

        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY 未设置，请在 .env 中配置")

    def collect(self, config: dict) -> List[CollectedItem]:
        channels = config.get("channels", [])
        max_items = int(config.get("max_items_per_channel", 3))
        default_category = config.get("category", "tech_ai")
        default_language = config.get("language", "en")

        items: List[CollectedItem] = []
        for ch in channels:
            display_name = ch.get("name", "YouTube")
            category = ch.get("category", default_category)
            language = ch.get("language", default_language)
            print(f"  [YouTube API] {display_name}...")

            channel = self._resolve_channel(ch)
            if not channel:
                print(f"  [YouTube API] 跳过 {display_name}: 无法解析频道")
                continue

            uploads_id = (
                channel.get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads", "")
            )
            channel_id = channel.get("id", "")
            channel_title = channel.get("snippet", {}).get("title", display_name)
            if not uploads_id:
                print(f"  [YouTube API] 跳过 {display_name}: uploads playlist 缺失")
                continue

            videos = self._list_videos(uploads_id, max_items=max_items)
            for v in videos:
                snippet = v.get("snippet", {})
                title = snippet.get("title", "").strip()
                video_id = (
                    snippet.get("resourceId", {}).get("videoId")
                    or snippet.get("videoId", "")
                )
                if not title or not video_id:
                    continue
                url = f"https://www.youtube.com/watch?v={video_id}"
                desc = (snippet.get("description", "") or "").strip()
                transcript = self._get_transcript(video_id, language)
                content = clip_text(transcript or desc, 4000)
                summary = clip_text(desc or transcript, 300)
                published_at = snippet.get("publishedAt", "")

                items.append(
                    CollectedItem(
                        title=title,
                        url=url,
                        source_name=channel_title,
                        source_type="youtube_api",
                        category=category,
                        summary=summary,
                        content=content,
                        published_at=published_at,
                        language=language,
                        raw_data={
                            "channel_id": channel_id,
                            "video_id": video_id,
                        },
                    )
                )
        return items

    def _resolve_channel(self, channel_cfg: Dict) -> Optional[dict]:
        channel_id = (channel_cfg.get("channel_id") or "").strip()
        handle = (channel_cfg.get("handle") or "").strip().lstrip("@")

        if channel_id:
            return self._get_channel_by_id(channel_id)
        if handle:
            return self._get_channel_by_handle(handle)
        return None

    def _get_channel_by_id(self, channel_id: str) -> Optional[dict]:
        params = {
            "part": "snippet,contentDetails",
            "id": channel_id,
            "key": self.api_key,
        }
        resp = requests.get(f"{self.API_BASE}/channels", params=params, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return items[0] if items else None

    def _get_channel_by_handle(self, handle: str) -> Optional[dict]:
        params = {
            "part": "snippet,contentDetails",
            "forHandle": handle,
            "key": self.api_key,
        }
        resp = requests.get(f"{self.API_BASE}/channels", params=params, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return items[0] if items else None

    def _list_videos(self, uploads_playlist_id: str, max_items: int) -> List[dict]:
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": max(1, min(50, max_items)),
            "key": self.api_key,
        }
        resp = requests.get(f"{self.API_BASE}/playlistItems", params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("items", [])

    @staticmethod
    def _get_transcript(video_id: str, language: str) -> str:
        """尽量抓取字幕，失败时静默回退到 description。"""
        preferred_languages = []
        lang = (language or "").lower()
        if lang.startswith("zh"):
            preferred_languages.extend(["zh-Hans", "zh-CN", "zh", "en"])
        else:
            preferred_languages.extend(["en", "en-US", "en-GB", "zh-Hans", "zh"])

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_languages)
        except Exception:
            return ""

        text = " ".join(
            part.get("text", "").replace("\n", " ").strip()
            for part in transcript
            if part.get("text")
        )
        return clip_text(text, 4000)
