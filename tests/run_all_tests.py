# -*- coding: utf-8 -*-
"""
统一测试入口
运行所有测试文件
"""

import os
import subprocess
import sys
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def run_test(test_file):
    """运行单个测试文件"""
    print_info(f"运行测试: {test_file}")

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )

        print(result.stdout)
        if result.stderr:
            print(f"{Colors.YELLOW}{result.stderr}{Colors.RESET}")

        return result.returncode == 0
    except Exception as e:
        print_error(f"运行测试失败: {e}")
        return False


def main():
    """主函数"""
    print_header("🌸 统一测试运行器 🌸")

    test_dir = Path(__file__).parent

    test_files = [
        "test_cost_optimizer.py",
        "test_personality_consistency.py",
        "test_personality_system_checkpoint.py",
        "test_emotion_system.py",
        "test_memory.py",
        "test_profile_relationship_system.py",
        "test_reinforcement_learning.py",
        "test_api.py",
    ]

    results = []

    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            success = run_test(str(test_path))
            results.append((test_file, success))
        else:
            print_info(f"跳过: {test_file} (文件不存在)")

    print_header("📊 测试结果汇总")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(
        f"\n总计: {Colors.GREEN if passed == total else Colors.YELLOW}{passed}/{total}{Colors.RESET} 通过"
    )

    if passed == total:
        print(f"\n{Colors.GREEN}🎉 所有测试通过！{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过。{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
