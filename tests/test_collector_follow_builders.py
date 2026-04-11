"""Follow Builders 采集适配器测试。"""

import json

from collector.sources.follow_builders import FollowBuildersSource


def test_follow_builders_collects_x_podcast_and_blog(tmp_path):
    (tmp_path / "feed-x.json").write_text(json.dumps({
        "x": [{
            "name": "Builder One",
            "handle": "builderone",
            "bio": "AI builder",
            "tweets": [{
                "id": "1",
                "text": "We are shipping a useful agent workflow today.",
                "createdAt": "2026-04-05T01:00:00.000Z",
                "url": "https://x.com/builderone/status/1",
                "likes": 10,
                "retweets": 2,
                "replies": 1,
            }],
        }],
    }), encoding="utf-8")
    (tmp_path / "feed-podcasts.json").write_text(json.dumps({
        "podcasts": [{
            "name": "No Priors",
            "title": "Agents in production",
            "guid": "episode-1",
            "url": "https://example.com/podcast",
            "publishedAt": "2026-04-05T02:00:00.000Z",
            "transcript": "Speaker 1 | Agents are moving from demos to production systems.",
        }],
    }), encoding="utf-8")
    (tmp_path / "feed-blogs.json").write_text(json.dumps({
        "blogs": [{
            "name": "Claude Blog",
            "title": "New model update",
            "url": "https://example.com/blog",
            "publishedAt": "2026-04-05T03:00:00.000Z",
            "description": "A model update.",
            "content": "Claude received a practical coding and agent reliability update.",
        }],
    }), encoding="utf-8")

    items = FollowBuildersSource().collect({"local_dir": str(tmp_path)})

    assert [item.source_type for item in items] == [
        "follow_builders_x",
        "follow_builders_podcast",
        "follow_builders_blog",
    ]
    assert items[0].source_name == "Follow Builders X"
    assert items[0].raw_data["handle"] == "builderone"
    assert "production systems" in items[1].content
    assert items[2].source_name == "Follow Builders Blog"
