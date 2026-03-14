"""测试 Notion 数据中枢完整流程"""

import io
import os
import sys
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()


def test_material_pool():
    """测试素材池写入"""
    print("\n=== 1. 测试素材池数据库 ===")

    from collector.notion_output import NotionOutput
    from collector.models import CollectedItem

    try:
        notion = NotionOutput()

        # 测试数据
        test_item = CollectedItem(
            title="测试素材 - Notion 数据中枢集成",
            url="https://example.com/test",
            source_name="测试源",
            source_type="API",
            category="tech_ai",
            summary="这是一条测试素材，用于验证 Notion 数据中枢功能",
            language="zh-CN",
        )

        saved = notion.save([test_item])

        if saved > 0:
            print(f"OK 素材池写入成功 ({saved} 条)")
            return True
        else:
            print("X 素材池写入失败")
            return False

    except Exception as e:
        print(f"X 素材池测试失败: {e}")
        return False


def test_topics_db():
    """测试选题库写入"""
    print("\n=== 2. 测试选题库数据库 ===")

    from collector.notion_topics import NotionTopics

    try:
        notion = NotionTopics()

        # 测试数据
        test_topics = [
            {
                "title": "测试选题 - AI 大模型最新进展",
                "score": 92,
                "reason": "这是一个测试选题，用于验证选题库功能。涵盖 AI 领域热点话题。",
                "source_urls": [
                    "https://example.com/source1",
                    "https://example.com/source2"
                ]
            }
        ]

        saved = notion.save_topics(test_topics, "tech_ai")

        if saved > 0:
            print(f"OK 选题库写入成功 ({saved} 条)")
            return True
        else:
            print("X 选题库写入失败")
            return False

    except Exception as e:
        print(f"X 选题库测试失败: {e}")
        return False


def test_drafts_db():
    """测试草稿库写入"""
    print("\n=== 3. 测试草稿库数据库 ===")

    from generator.notion_drafts import NotionDrafts

    try:
        notion = NotionDrafts()

        # 测试数据
        test_draft = {
            "title": "测试草稿 - AI 大模型最新进展深度解析",
            "file_path": "file:///d:/test/draft.md",
            "word_count": 2500,
            "quality_grade": "A",
            "quality_scores": "信息密度: 9/10\n逻辑性: 8/10\n可读性: 9/10",
            "tags": ["AI", "大模型", "技术"],
            "digest": "本文深度解析了 AI 大模型领域的最新进展...",
            "topic_title": "测试选题 - AI 大模型最新进展"
        }

        page_id = notion.save_draft(test_draft)

        if page_id:
            print(f"OK 草稿库写入成功")
            print(f"   Page ID: {page_id}")
            return True
        else:
            print("X 草稿库写入失败")
            return False

    except Exception as e:
        print(f"X 草稿库测试失败: {e}")
        return False


def test_publish_records():
    """测试发布记录写入"""
    print("\n=== 4. 测试发布记录数据库 ===")

    from publisher.notion_records import NotionRecords

    try:
        notion = NotionRecords()

        # 测试数据
        test_results = [
            {
                "platform": "wechat",
                "status": "success",
                "url": "https://mp.weixin.qq.com/s/test123",
                "message": "发布成功"
            },
            {
                "platform": "zhihu",
                "status": "draft",
                "url": "",
                "message": "已保存为草稿"
            }
        ]

        saved = notion.save_batch_results(
            title="测试草稿 - AI 大模型最新进展深度解析",
            results=test_results,
            draft_title="测试草稿 - AI 大模型最新进展深度解析"
        )

        if saved > 0:
            print(f"OK 发布记录写入成功 ({saved} 条)")
            return True
        else:
            print("X 发布记录写入失败")
            return False

    except Exception as e:
        print(f"X 发布记录测试失败: {e}")
        return False


def main():
    print("=" * 50)
    print("Notion 数据中枢完整流程测试")
    print("=" * 50)

    results = []

    # 测试 4 个数据库
    results.append(("素材池", test_material_pool()))
    results.append(("选题库", test_topics_db()))
    results.append(("草稿库", test_drafts_db()))
    results.append(("发布记录", test_publish_records()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    for name, success in results:
        status = "OK" if success else "X"
        print(f"{status} {name}: {'通过' if success else '失败'}")

    success_count = sum(1 for _, s in results if s)
    total_count = len(results)

    print(f"\n总计: {success_count}/{total_count} 通过")

    if success_count == total_count:
        print("\nOK 所有测试通过！Notion 数据中枢已就绪。")
    else:
        print("\n! 部分测试失败，请检查配置和权限。")


if __name__ == "__main__":
    main()
