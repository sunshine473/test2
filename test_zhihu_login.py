#!/usr/bin/env python3
"""简化的知乎发布测试 - 用于调试登录流程"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from playwright.sync_api import sync_playwright

def test_zhihu_login():
    """测试知乎登录流程"""
    print("\n" + "="*60)
    print("知乎登录测试")
    print("="*60)

    login_url = "https://www.zhihu.com/signin"
    editor_url = "https://zhuanlan.zhihu.com/write"

    with sync_playwright() as p:
        print("\n1. 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        print("2. 打开知乎编辑器页面...")
        page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        print(f"3. 当前 URL: {page.url}")

        # 检查是否在登录页
        url = page.url.lower()
        is_login = "signin" in url or "login" in url

        if is_login:
            print("\n✅ 检测到登录页面")
            print("\n请在浏览器中完成以下操作：")
            print("  1. 输入手机号/邮箱")
            print("  2. 输入密码或验证码")
            print("  3. 点击登录")
            print("\n等待登录中（最多 10 分钟）...")

            # 等待登录完成
            for i in range(300):  # 10 分钟
                time.sleep(2)
                current_url = page.url.lower()

                # 检查是否已经跳转离开登录页
                if "signin" not in current_url and "login" not in current_url:
                    print(f"\n✅ 登录成功！当前 URL: {page.url}")

                    # 保存 Cookie
                    state_dir = PROJECT_ROOT / ".browser_state"
                    state_dir.mkdir(parents=True, exist_ok=True)
                    state_file = state_dir / "zhihu_state.json"
                    context.storage_state(path=str(state_file))
                    print(f"✅ Cookie 已保存到: {state_file}")

                    # 尝试填写内容
                    print("\n4. 尝试填写测试内容...")
                    time.sleep(3)

                    # 跳转到编辑器
                    if "write" not in page.url:
                        page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(3)

                    # 填写标题
                    try:
                        title_input = page.locator('textarea[placeholder*="标题"]').first
                        title_input.click()
                        title_input.fill("测试文章标题")
                        print("✅ 标题填写成功")
                        time.sleep(2)

                        # 填写内容
                        editor = page.locator('.public-DraftEditor-content, [contenteditable="true"]').first
                        editor.click()
                        time.sleep(1)
                        editor.type("这是测试内容")
                        print("✅ 内容填写成功")

                        print("\n✅ 测试完成！请在浏览器中查看效果")
                        print("按 Enter 键关闭浏览器...")
                        input()

                    except Exception as e:
                        print(f"❌ 填写失败: {e}")
                        print("按 Enter 键关闭浏览器...")
                        input()

                    break

                if (i + 1) % 30 == 0:
                    print(f"  已等待 {(i+1)*2} 秒...")
            else:
                print("\n❌ 登录超时（10 分钟）")
        else:
            print("\n✅ 已经登录，无需手动登录")
            print(f"当前页面: {page.url}")
            print("\n按 Enter 键关闭浏览器...")
            input()

        browser.close()

if __name__ == "__main__":
    test_zhihu_login()
