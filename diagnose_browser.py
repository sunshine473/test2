#!/usr/bin/env python3
"""诊断当前浏览器状态"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from playwright.sync_api import sync_playwright

print("\n正在连接到现有浏览器...")
print("提示：这个脚本会尝试连接到已打开的浏览器并显示当前状态\n")

# 注意：这个脚本无法连接到已存在的浏览器实例
# 只能作为参考，实际需要在原脚本中添加调试输出

print("由于 Playwright 限制，无法连接到已运行的浏览器实例")
print("\n建议操作：")
print("1. 在浏览器中，登录后手动访问：https://zhuanlan.zhihu.com/write")
print("2. 观察脚本是否自动继续")
print("3. 如果长时间无响应，可以：")
print("   - 关闭浏览器窗口")
print("   - 按 Ctrl+C 停止脚本")
print("   - 重新运行测试")
print("\n当前浏览器窗口的 URL 应该是什么？")
print("- 如果还在登录页（包含 signin/login），脚本会继续等待")
print("- 如果已经跳转到其他页面，脚本应该会自动继续")
