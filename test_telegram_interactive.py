#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Telegram 交互式通知功能。

用法:
    python test_telegram_interactive.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 确保 UTF-8 输出
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

import json
from collector.telegram_notifier_interactive import InteractiveTelegramNotifier
from collector.planner import plan, find_latest_pool


def test_message_building():
    """测试消息构建。"""
    print("=== 测试 1: 消息构建 ===\n")

    # 读取最新素材池
    pool_path = find_latest_pool()
    if not pool_path:
        print("❌ 未找到素材池")
        return False

    with open(pool_path, encoding="utf-8") as f:
        pool_data = json.load(f)

    print(f"✅ 素材池: {pool_data.get('date')}, {pool_data.get('dedup_total')} 条")

    # 策划
    plan_result = plan(pool_path, direction_name=None)
    print(f"✅ 策划完成: {len(plan_result)} 个方向")

    # 构建消息
    notifier = InteractiveTelegramNotifier()
    message = notifier._build_message(pool_data, plan_result)
    buttons = notifier._build_buttons(plan_result)

    print(f"✅ 消息长度: {len(message)} 字符")
    print(f"✅ 按钮行数: {len(buttons)} 行")
    print("\n--- 消息预览 ---")
    print(message)
    print("\n--- 按钮预览 ---")
    for i, row in enumerate(buttons, 1):
        print(f"第 {i} 行:")
        for btn in row:
            print(f"  [{btn['text']}] -> {btn['callback_data']}")

    return True


def test_direction_detail():
    """测试方向详情消息。"""
    print("\n\n=== 测试 2: 方向详情消息 ===\n")

    pool_path = find_latest_pool()
    if not pool_path:
        print("❌ 未找到素材池")
        return False

    plan_result = plan(pool_path, direction_name=None)
    notifier = InteractiveTelegramNotifier()

    for direction in ["tech_ai", "auto"]:
        dir_data = plan_result.get(direction, {})
        if not dir_data:
            print(f"⚠️  {direction}: 无数据")
            continue

        label = dir_data.get("label", direction)
        items = dir_data.get("items", [])
        fresh_items = [
            item for item in items
            if notifier._is_fresh(item.get("published_at", ""), hours=24)
        ]

        print(f"\n{label}:")
        print(f"  总计: {len(items)} 条")
        print(f"  新鲜 (24h): {len(fresh_items)} 条")

        if fresh_items:
            print(f"  Top 3:")
            for i, item in enumerate(fresh_items[:3], 1):
                title = item.get("title", "无标题")[:50]
                score = (item.get("raw_data") or {}).get("score", 0)
                print(f"    {i}. {title} ⭐{score:.1f}")

    return True


def test_callback_handler():
    """测试回调处理器。"""
    print("\n\n=== 测试 3: 回调处理器 ===\n")

    from bot.callback_handler import CallbackHandler

    handler = CallbackHandler()
    print("✅ 回调处理器初始化成功")

    # 测试加载最新策划结果
    plan_result = handler._load_latest_plan()
    if plan_result:
        print(f"✅ 加载策划结果: {len(plan_result)} 个方向")
        for dir_name, dir_data in plan_result.items():
            label = dir_data.get("label", dir_name)
            items_count = len(dir_data.get("items", []))
            print(f"  - {label}: {items_count} 条")
    else:
        print("⚠️  未找到策划结果")

    return True


def test_fresh_detection():
    """测试新鲜度检测。"""
    print("\n\n=== 测试 4: 新鲜度检测 ===\n")

    from collector.telegram_notifier_interactive import InteractiveTelegramNotifier
    from datetime import datetime, timezone, timedelta

    notifier = InteractiveTelegramNotifier()

    # 测试用例
    test_cases = [
        ("", "空字符串"),
        (None, "None"),
        ((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(), "1小时前"),
        ((datetime.now(timezone.utc) - timedelta(hours=23)).isoformat(), "23小时前"),
        ((datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(), "25小时前"),
        ((datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), "2天前"),
    ]

    print("新鲜度测试 (24小时阈值):")
    for published_at, label in test_cases:
        is_fresh = notifier._is_fresh(published_at, hours=24)
        status = "✅ 新鲜" if is_fresh else "❌ 不新鲜"
        print(f"  {label}: {status}")

    return True


def main():
    """运行所有测试。"""
    print("=" * 60)
    print("Telegram 交互式通知功能测试")
    print("=" * 60)

    tests = [
        test_message_building,
        test_direction_detail,
        test_callback_handler,
        test_fresh_detection,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ {test_func.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # 总结
    print("\n\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")


if __name__ == "__main__":
    main()
