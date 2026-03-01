"""测试 Telegram 通知消息格式"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Windows 控制台 UTF-8 兼容
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

from collector.telegram_notifier import TelegramNotifier


def test_message_format():
    """测试通知消息格式（包含 Top10 + URL + 新鲜度筛选）"""
    notifier = TelegramNotifier()

    # 模拟搜索结果
    search_result = {
        "date": "2026-03-01",
        "raw_total": 127,
        "dedup_total": 95,
        "cluster_summary": {"cluster_count": 23},
    }

    # 模拟策划结果（包含新旧内容混合）
    now = datetime.now(timezone.utc)
    fresh_time = (now - timedelta(hours=2)).isoformat()  # 2 小时前
    old_time = (now - timedelta(hours=48)).isoformat()  # 48 小时前

    plan_result = {
        "tech_ai": {
            "label": "AI 科技",
            "filtered_count": 45,
            "score_summary": {"avg": 72},
            "items": [
                {
                    "title": "OpenAI 发布 GPT-5 预览版，性能提升 3 倍",
                    "url": "https://openai.com/blog/gpt-5-preview",
                    "summary": "OpenAI 今日发布 GPT-5 预览版，在推理、编程和多模态能力上均有显著提升，性能较 GPT-4 提升约 3 倍。",
                    "source_name": "OpenAI Blog",
                    "published_at": fresh_time,
                    "raw_data": {"score": 95},
                },
                {
                    "title": "Claude 3.5 Sonnet 新增代码执行功能",
                    "url": "https://anthropic.com/news/claude-code-execution",
                    "summary": "Anthropic 为 Claude 3.5 Sonnet 新增代码执行功能，可直接运行 Python 代码并返回结果。",
                    "source_name": "Anthropic",
                    "published_at": fresh_time,
                    "raw_data": {"score": 88},
                },
                {
                    "title": "旧新闻：AI 芯片市场分析报告",
                    "url": "https://example.com/old-news",
                    "summary": "这是一条 48 小时前的旧新闻，应该被过滤掉。",
                    "source_name": "Tech News",
                    "published_at": old_time,
                    "raw_data": {"score": 75},
                },
            ] + [
                {
                    "title": f"AI 技术新闻 #{i}",
                    "url": f"https://example.com/news-{i}",
                    "summary": f"这是第 {i} 条 AI 技术新闻的摘要内容。",
                    "source_name": "Tech Source",
                    "published_at": fresh_time,
                    "raw_data": {"score": 70 - i},
                }
                for i in range(3, 13)  # 生成 10 条新闻（总共 12 条新鲜内容）
            ],
        },
        "auto": {
            "label": "汽车",
            "filtered_count": 28,
            "score_summary": {"avg": 68},
            "items": [
                {
                    "title": "特斯拉 FSD V13 正式推送，城市道路表现大幅提升",
                    "url": "https://tesla.com/fsd-v13",
                    "summary": "特斯拉今日向用户推送 FSD V13 版本，在城市道路场景下的表现大幅提升，接管率降低 40%。",
                    "source_name": "Tesla",
                    "published_at": fresh_time,
                    "raw_data": {"score": 92},
                },
            ],
        },
    }

    # 生成消息
    message = notifier._build_message(search_result, plan_result)

    print("=" * 60)
    print("Telegram 通知消息预览：")
    print("=" * 60)
    print(message)
    print("=" * 60)

    # 验证关键内容
    assert "Top10 新鲜内容" in message
    assert "24h 新鲜" in message
    assert "🔗 https://openai.com/blog/gpt-5-preview" in message
    assert "🔗 https://anthropic.com/news/claude-code-execution" in message
    assert "旧新闻" not in message  # 48 小时前的内容应该被过滤
    assert "OpenAI 发布 GPT-5 预览版" in message
    assert "Claude 3.5 Sonnet 新增代码执行功能" in message

    print("\n✅ 测试通过！")
    print(f"- 消息长度: {len(message)} 字符")
    print(f"- 包含 URL: {message.count('🔗')} 个")
    print(f"- AI 科技新鲜内容: 12 条（应显示前 10 条）")
    print(f"- 汽车新鲜内容: 1 条")


if __name__ == "__main__":
    test_message_format()
