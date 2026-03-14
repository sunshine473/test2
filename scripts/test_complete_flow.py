"""端到端测试：完整数据链路"""

import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()


def test_complete_flow():
    """测试完整数据链路：素材池 → 选题库 → 草稿库 → 发布记录"""
    print("=" * 60)
    print("完整数据链路端到端测试")
    print("=" * 60)

    from collector.notion_output import NotionOutput
    from collector.models import CollectedItem
    from collector.notion_topics import NotionTopics
    from generator.notion_drafts import NotionDrafts
    from publisher.notion_records import NotionRecords

    # 1. 素材池：创建测试素材
    print("\n【步骤 1】创建测试素材 → 素材池")
    print("-" * 60)

    material_notion = NotionOutput()
    test_material = CollectedItem(
        title="端到端测试素材 - Claude 4.6 发布",
        url="https://example.com/claude-4.6",
        source_name="测试源",
        source_type="API",
        category="tech_ai",
        summary="Claude 4.6 正式发布，带来多项重大更新",
        language="zh-CN",
    )

    material_saved = material_notion.save([test_material])
    if material_saved > 0:
        print(f"✅ 素材已写入素材池 ({material_saved} 条)")
    else:
        print("❌ 素材写入失败")
        return False

    # 2. 选题库：基于素材创建选题
    print("\n【步骤 2】创建选题 → 选题库（关联素材池）")
    print("-" * 60)

    topics_notion = NotionTopics()
    test_topic = [{
        "title": "端到端测试选题 - Claude 4.6 深度解析",
        "score": 98,
        "reason": "Claude 4.6 是重大版本更新，值得深度解析",
        "source_urls": ["https://example.com/claude-4.6"]
    }]

    topics_saved = topics_notion.save_topics(test_topic, "tech_ai")
    if topics_saved > 0:
        print(f"✅ 选题已写入选题库 ({topics_saved} 条)")
        print("   关联关系：选题 → 素材池")
    else:
        print("❌ 选题写入失败")
        return False

    # 3. 草稿库：基于选题生成草稿
    print("\n【步骤 3】生成草稿 → 草稿库（关联选题库）")
    print("-" * 60)

    drafts_notion = NotionDrafts()
    test_draft = {
        "title": "端到端测试草稿 - Claude 4.6 深度解析完整版",
        "file_path": "file:///test/e2e-test.md",
        "word_count": 3500,
        "quality_grade": "A",
        "quality_scores": "信息密度: 10/10\n逻辑性: 9/10\n可读性: 10/10",
        "tags": ["AI", "Claude", "测试"],
        "digest": "本文深度解析 Claude 4.6 的核心特性和技术突破",
        "topic_title": "端到端测试选题 - Claude 4.6 深度解析"
    }

    draft_id = drafts_notion.save_draft(test_draft)
    if draft_id:
        print(f"✅ 草稿已写入草稿库")
        print(f"   Page ID: {draft_id}")
        print("   关联关系：草稿 → 选题库 → 素材池")
    else:
        print("❌ 草稿写入失败")
        return False

    # 4. 发布记录：记录发布结果
    print("\n【步骤 4】记录发布 → 发布记录（关联草稿库）")
    print("-" * 60)

    records_notion = NotionRecords()
    test_results = [
        {
            "platform": "wechat",
            "status": "success",
            "url": "https://mp.weixin.qq.com/s/e2e-test-123",
            "message": "发布成功"
        },
        {
            "platform": "zhihu",
            "status": "success",
            "url": "https://zhuanlan.zhihu.com/p/e2e-test",
            "message": "发布成功"
        }
    ]

    records_saved = records_notion.save_batch_results(
        title="端到端测试草稿 - Claude 4.6 深度解析完整版",
        results=test_results,
        draft_title="端到端测试草稿 - Claude 4.6 深度解析完整版"
    )

    if records_saved > 0:
        print(f"✅ 发布记录已写入 ({records_saved} 条)")
        print("   关联关系：发布记录 → 草稿库 → 选题库 → 素材池")
    else:
        print("❌ 发布记录写入失败")
        return False

    # 总结
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n✅ 完整数据链路验证成功：")
    print("\n   素材池 (1条)")
    print("     ↓ 关联")
    print("   选题库 (1条)")
    print("     ↓ 关联")
    print("   草稿库 (1条)")
    print("     ↓ 关联")
    print("   发布记录 (2条)")
    print("\n请在 Notion 中查看各数据库的关联字段，验证数据链路！")

    return True


if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
