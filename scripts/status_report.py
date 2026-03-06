#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目状态自动盘点脚本

自动扫描项目结构，输出：
- 模块列表及状态
- 测试文件数量
- TODO/FIXME 数量
- 平台实现状态
- 未纳入计划的新文件
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class StatusReport:
    """项目状态报告生成器"""

    def __init__(self, project_root: Path):
        self.root = project_root
        self.src = project_root / "src"
        self.tests = project_root / "tests"
        self.docs = project_root / "docs"

    def run(self):
        """生成完整报告"""
        print("=" * 80)
        print("项目状态自动盘点")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        self.report_modules()
        self.report_tests()
        self.report_todos()
        self.report_platforms()
        self.report_untracked()
        self.report_git_status()

    def report_modules(self):
        """报告模块列表"""
        print("📦 核心模块")
        print("-" * 80)

        modules = {
            "collector": "素材采集",
            "generator": "内容生成",
            "publisher": "统一发布",
            "pipeline": "流水线调度",
            "bot": "Telegram Bot",
            "agents": "Agent Team",
            "config": "配置管理",
        }

        for name, desc in modules.items():
            path = self.src / name
            if path.exists():
                files = list(path.rglob("*.py"))
                lines = sum(self._count_lines(f) for f in files)
                print(f"  ✓ {name:15} {desc:15} ({len(files):2} 文件, {lines:5} 行)")
            else:
                print(f"  ✗ {name:15} {desc:15} (不存在)")

        print()

    def report_tests(self):
        """报告测试覆盖"""
        print("🧪 测试覆盖")
        print("-" * 80)

        if not self.tests.exists():
            print("  ✗ tests/ 目录不存在")
            print()
            return

        test_files = list(self.tests.glob("test_*.py"))
        print(f"  测试文件总数: {len(test_files)}")

        # 按模块分组
        by_module = defaultdict(list)
        for f in test_files:
            match = re.match(r"test_(\w+)_", f.name)
            if match:
                module = match.group(1)
                by_module[module].append(f)
            else:
                by_module["other"].append(f)

        for module, files in sorted(by_module.items()):
            print(f"    {module:15} {len(files)} 个文件")

        # 统计测试用例数（简单统计 def test_ 数量）
        total_cases = 0
        for f in test_files:
            content = f.read_text(encoding="utf-8")
            cases = len(re.findall(r"^\s*def test_", content, re.MULTILINE))
            total_cases += cases

        print(f"  估算测试用例数: ~{total_cases}")
        print()

    def report_todos(self):
        """报告 TODO/FIXME"""
        print("📝 待办事项")
        print("-" * 80)

        patterns = {
            "TODO": r"#\s*TODO",
            "FIXME": r"#\s*FIXME",
            "待办": r"#\s*待办",
        }

        total = 0
        for label, pattern in patterns.items():
            count = 0
            matches = []

            for py_file in self.src.rglob("*.py"):
                content = py_file.read_text(encoding="utf-8")
                file_matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if file_matches:
                    count += len(file_matches)
                    rel_path = py_file.relative_to(self.root)
                    matches.append((rel_path, len(file_matches)))

            if count > 0:
                print(f"  {label}: {count} 处")
                for path, n in matches[:5]:  # 只显示前 5 个
                    print(f"    - {path} ({n})")
                if len(matches) > 5:
                    print(f"    ... 还有 {len(matches) - 5} 个文件")

            total += count

        if total == 0:
            print("  ✓ 无待办事项")

        print()

    def report_platforms(self):
        """报告发布平台状态"""
        print("🚀 发布平台")
        print("-" * 80)

        platforms_dir = self.src / "publisher" / "platforms"
        if not platforms_dir.exists():
            print("  ✗ publisher/platforms/ 不存在")
            print()
            return

        platforms = {
            "wechat.py": "微信公众号",
            "xiaohongshu.py": "小红书",
            "zhihu.py": "知乎专栏",
            "dongchedi.py": "懂车帝",
            "bilibili.py": "B站专栏",
            "toutiao.py": "今日头条",
        }

        for filename, name in platforms.items():
            path = platforms_dir / filename
            if not path.exists():
                print(f"  ✗ {name:12} (不存在)")
                continue

            content = path.read_text(encoding="utf-8")
            lines = len(content.splitlines())
            has_todo = "TODO" in content or "待办" in content
            has_pass = re.search(r"^\s*pass\s*$", content, re.MULTILINE)

            if has_todo or has_pass or lines < 50:
                status = "skeleton"
                icon = "⚠️"
            else:
                status = "production"
                icon = "✓"

            print(f"  {icon} {name:12} {status:10} ({lines:3} 行)")

        print()

    def report_untracked(self):
        """报告未纳入版本控制的新文件"""
        print("📂 未跟踪文件")
        print("-" * 80)

        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )

            untracked = [
                line for line in result.stdout.strip().split("\n")
                if line and not line.startswith("content/")  # 排除 content/ 目录
            ]

            if untracked:
                print(f"  发现 {len(untracked)} 个未跟踪文件:")
                for path in untracked[:10]:  # 只显示前 10 个
                    print(f"    - {path}")
                if len(untracked) > 10:
                    print(f"    ... 还有 {len(untracked) - 10} 个文件")
            else:
                print("  ✓ 无未跟踪文件（content/ 目录已排除）")

        except subprocess.CalledProcessError:
            print("  ✗ 无法获取 git 状态")

        print()

    def report_git_status(self):
        """报告 git 状态"""
        print("🔄 Git 状态")
        print("-" * 80)

        try:
            # 当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True,
            )
            branch = result.stdout.strip() if result.stdout else "unknown"

            # 未推送的提交数
            ahead = subprocess.run(
                ["git", "rev-list", "--count", "@{u}..HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
            )
            ahead_count = int(ahead.stdout.strip()) if ahead.returncode == 0 and ahead.stdout else 0

            # 最近一次提交
            result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True,
            )
            last_commit = result.stdout.strip() if result.stdout else "unknown"

            print(f"  当前分支: {branch}")
            print(f"  未推送提交: {ahead_count}")
            print(f"  最近提交: {last_commit}")

        except (subprocess.CalledProcessError, Exception) as e:
            print(f"  ✗ 无法获取 git 状态: {e}")

        print()

    @staticmethod
    def _count_lines(file_path: Path) -> int:
        """统计文件行数（排除空行和注释）"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            return len(lines)
        except Exception:
            return 0


def main():
    """主入口"""
    project_root = Path(__file__).resolve().parent.parent
    reporter = StatusReport(project_root)
    reporter.run()

    print("=" * 80)
    print("💡 提示:")
    print("  - 查看详细状态: docs/项目状态总览.md")
    print("  - 查看开发计划: docs/开发计划.md")
    print("  - 运行测试: PYTHONPATH=src pytest tests/ -v")
    print("=" * 80)


if __name__ == "__main__":
    main()
