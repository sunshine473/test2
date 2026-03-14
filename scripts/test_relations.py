"""测试关联字段功能"""

import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()


def test_relations():
    """测试关联字段是否正常工作"""
    print("=== 测试 Notion 关联字段功能 ===\n")

    from collector.notion_topics import NotionTopics
    from generator.notion_drafts import NotionDrafts
    from publisher.notion_records import NotionRecords

    # 1. 创建选题
    print("1. 创建测试选题...")
    topics = NotionTopics()
    test_topic = [{
        "title": "关联测试选题 - AI 技术突破",
        "score": 95,
        "reason": "测试关联字段功能",
        "source_urls": ["https://example.com/test"]
    }]
    topics.save_topics(test_topic, "tech_ai")
    print("   ✅ 选题已创建\n")

    # 2. 创建草稿（关联到选题）
    print("2. 创建测试草稿（关联到选题）...")
    drafts = NotionDrafts()
    test_draft = {
        "title": "关联测试草稿 - AI 技术突破深度解析",
        "file_path": "file:///test/relation-test.md",
        "word_count": 3000,
        "quality_grade": "A",
        "quality_scores": "测试关联功能",
        "tags": ["测试", "关联"],
        "digest": "测试关联字段功能",
        "topic_title": "关联测试选题 - AI 技术突破"
    }
    draft_id = drafts.save_draft(test_draft)
    print(f"   ✅ 草稿已创建: {draft_id}\n")

    # 3. 创建发布记录（关联到草稿）
    print("3. 创建测试发布记录（关联到草稿）...")
    records = NotionRecords()
    test_results = [{
        "platform": "wechat",
        "status": "success",
        "url": "https://mp.weixin.qq.com/test-relation",
        "message": "测试关联功能"
    }]
    saved = records.save_batch_results(
        title="关联测试草稿 - AI 技术突破深度解析",
        results=test_results,
        draft_title="关联测试草稿 - AI 技术突破深度解析"
    )
    print(f"   ✅ 发布记录已创建: {saved} 条\n")

    print("=== 测试完成 ===")
    print("\n请在 Notion 中检查：")
    print("1. 选题库中的 '关联测试选题' 是否有 '关联草稿' 字段显示关联的草稿")
    print("2. 草稿库中的 '关联测试草稿' 是否有 '关联选题' 字段显示关联的选题")
    print("3. 发布记录中是否有 '关联草稿' 字段显示关联的草稿")
    print("\n如果能看到关联关系，说明功能正常！")


if __name__ == "__main__":
    test_relations()
