#!/usr/bin/env python3
"""测试知乎和小红书发布功能的简化脚本"""

import sys
from pathlib import Path

# 添加 src 到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from publisher.models import Article
from publisher.registry import get_publisher
import publisher.platforms.zhihu
import publisher.platforms.xiaohongshu

def test_zhihu():
    """测试知乎发布"""
    print("\n" + "="*50)
    print("测试知乎发布")
    print("="*50)

    article = Article(
        title="AI 编程助手测试文章",
        content="""# AI 编程助手测试文章

这是一篇用于测试知乎发布功能的文章。

## 为什么需要 AI 编程助手？

在 2026 年，AI 编程助手已经成为开发者的标配工具。

## 主流 AI 编程助手对比

### GitHub Copilot
- 优点：与 VS Code 深度集成
- 缺点：需要付费订阅

### Claude Code
- 优点：支持多模态，理解能力强
- 缺点：需要 API Key

## 总结

AI 编程助手正在改变软件开发的方式。
""",
        tags=["AI", "编程", "测试"],
        images=[],
        metadata={"content_format": "markdown"}
    )

    config = {"headless": False}

    try:
        publisher = get_publisher("zhihu")
        print(f"\n使用发布器: {publisher.__class__.__name__}")
        print("提示：浏览器将打开，请手动登录知乎")
        print("登录后，脚本会自动填写标题和内容\n")

        result = publisher.publish(article, config)

        print(f"\n发布结果:")
        print(f"  状态: {result.status.value}")
        print(f"  消息: {result.message}")
        if result.url:
            print(f"  链接: {result.url}")

        return result.status.value == "success"

    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_xiaohongshu():
    """测试小红书发布"""
    print("\n" + "="*50)
    print("测试小红书发布")
    print("="*50)

    # 小红书需要图片，这里使用测试图片
    article = Article(
        title="AI 编程助手测试 #AI编程 #开发工具",
        content="""AI 编程助手正在改变软件开发方式 ✨

🔥 主流工具对比：
• GitHub Copilot - VS Code 深度集成
• Claude Code - 多模态理解能力强
• Cursor - 专为 AI 编程设计

💡 选择适合自己的工具很重要！

#AI编程 #开发工具 #效率提升
""",
        tags=["AI编程", "开发工具", "效率提升"],
        images=[],  # 实际使用时需要提供图片路径
        metadata={"content_format": "markdown"}
    )

    config = {"headless": False}

    print("\n⚠️  注意：小红书需要至少 1 张图片")
    print("由于测试文章没有图片，此测试将跳过\n")
    return False

    # 实际发布代码（需要图片）
    # try:
    #     publisher = get_publisher("xiaohongshu")
    #     result = publisher.publish(article, config)
    #     print(f"\n发布结果: {result.status.value} - {result.message}")
    #     return result.status.value == "success"
    # except Exception as e:
    #     print(f"\n❌ 发布失败: {e}")
    #     return False

def main():
    print("\n🚀 开始测试发布功能\n")

    # 测试知乎
    zhihu_ok = test_zhihu()

    # 测试小红书
    # xiaohongshu_ok = test_xiaohongshu()

    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    print(f"知乎: {'✅ 成功' if zhihu_ok else '❌ 失败'}")
    # print(f"小红书: {'✅ 成功' if xiaohongshu_ok else '❌ 失败'}")
    print()

if __name__ == "__main__":
    main()
