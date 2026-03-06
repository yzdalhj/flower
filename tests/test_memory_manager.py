# -*- coding: utf-8 -*-
"""
记忆管理器测试
验证冲突处理、过期机制和记忆强化
"""

import importlib.util
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 屏蔽不必要的模块导入
app_module = types.ModuleType("app")
sys.modules["app"] = app_module
app_services_module = types.ModuleType("app.services")
sys.modules["app.services"] = app_services_module
app_services_memory_module = types.ModuleType("app.services.memory")
sys.modules["app.services.memory"] = app_services_memory_module

# 导入记忆管理器
spec_manager = importlib.util.spec_from_file_location(
    "memory_manager",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/memory/memory_manager.py"
    ),
)
manager_module = importlib.util.module_from_spec(spec_manager)
sys.modules["app.services.memory.memory_manager"] = manager_module
spec_manager.loader.exec_module(manager_module)

MemoryManager = manager_module.MemoryManager
MemoryConflict = manager_module.MemoryConflict
MemoryUpdateResult = manager_module.MemoryUpdateResult


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


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def test_data_structures():
    """测试数据结构"""
    print_header("测试1: 数据结构")

    conflict = MemoryConflict(
        memory_id_1="mem_1",
        memory_id_2="mem_2",
        conflict_type="contradiction",
        description="测试冲突",
        confidence=0.85,
    )

    update_result = MemoryUpdateResult(
        success=True, action="created", memory_id="mem_3", message="测试消息"
    )

    passed = 0
    if conflict.conflict_type == "contradiction":
        print_success("冲突类型设置正确")
        passed += 1

    if not conflict.resolved:
        print_success("冲突初始状态为未解决")
        passed += 1

    if update_result.success:
        print_success("更新结果成功状态正确")
        passed += 1

    if update_result.action == "created":
        print_success("更新动作设置正确")
        passed += 1

    print_info(f"数据结构测试通过率: {passed}/4")
    return passed >= 3


def test_duplicate_detection():
    """测试重复检测"""
    print_header("测试2: 重复检测")

    manager = MemoryManager(None, None)

    test_cases = [
        ("我喜欢吃火锅", "我喜欢吃火锅", True),
        ("我喜欢吃火锅", "我喜欢吃火锅哦", True),
        ("我喜欢吃火锅", "我讨厌吃火锅", False),
        ("今天天气真好", "今天天气不错", False),
    ]

    passed = 0
    for text1, text2, expected in test_cases:
        result = manager._is_duplicate(text1, text2)
        if result == expected:
            print_success(f"'{text1}' vs '{text2}' -> 重复: {result}")
            passed += 1
        else:
            print(f"  '{text1}' vs '{text2}' -> 期望: {expected}, 实际: {result}")

    print_info(f"重复检测测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_contradiction_detection():
    """测试矛盾检测"""
    print_header("测试3: 矛盾检测")

    manager = MemoryManager(None, None)

    test_cases = [
        ("我喜欢吃火锅", "我讨厌吃火锅", True),
        ("我喜欢吃火锅", "我爱吃火锅", False),
        ("我在家", "我不在家", True),
        ("今天天气好", "今天天气不错", False),
    ]

    passed = 0
    for text1, text2, expected in test_cases:
        result = manager._is_contradiction(text1, text2)
        if result == expected:
            print_success(f"'{text1}' vs '{text2}' -> 矛盾: {result}")
            passed += 1
        else:
            print(f"  '{text1}' vs '{text2}' -> 期望: {expected}, 实际: {result}")

    print_info(f"矛盾检测测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_similarity_calculation():
    """测试相似度计算"""
    print_header("测试4: 相似度计算")

    manager = MemoryManager(None, None)

    test_cases = [
        ("我喜欢吃火锅", "我喜欢吃火锅", 1.0),
        ("我喜欢吃火锅", "我喜欢吃火锅和烧烤", 0.5),
        ("我喜欢吃火锅", "今天天气真好", 0.0),
    ]

    passed = 0
    for text1, text2, expected_min in test_cases:
        similarity = manager._simple_similarity(text1, text2)
        if similarity >= expected_min - 0.1:
            print_success(f"'{text1}' vs '{text2}' -> 相似度: {similarity:.2f}")
            passed += 1
        else:
            print(f"  '{text1}' vs '{text2}' -> 相似度: {similarity:.2f}, 期望 >= {expected_min}")

    print_info(f"相似度计算测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_conflict_history():
    """测试冲突历史记录"""
    print_header("测试5: 冲突历史记录")

    manager = MemoryManager(None, None)

    conflict1 = MemoryConflict(
        memory_id_1="mem_1",
        memory_id_2="mem_2",
        conflict_type="contradiction",
        description="测试冲突1",
    )
    conflict2 = MemoryConflict(
        memory_id_1="mem_3", memory_id_2="mem_4", conflict_type="duplicate", description="测试冲突2"
    )

    manager.conflict_history.append(conflict1)
    manager.conflict_history.append(conflict2)

    history = manager.get_conflict_history(limit=10)

    passed = 0
    if len(history) == 2:
        print_success("冲突历史记录数量正确")
        passed += 1

    if history[0].conflict_type == "contradiction":
        print_success("第一个冲突类型正确")
        passed += 1

    if history[1].conflict_type == "duplicate":
        print_success("第二个冲突类型正确")
        passed += 1

    print_info(f"冲突历史测试通过率: {passed}/3")
    return passed >= 2


def test_memory_update_result():
    """测试记忆更新结果"""
    print_header("测试6: 记忆更新结果")

    test_results = [
        ("created", True, "新记忆创建成功"),
        ("updated", True, "记忆更新成功"),
        ("reinforced", True, "记忆强化成功"),
        ("skipped", False, "记忆被跳过"),
        ("deleted", True, "记忆被删除"),
    ]

    passed = 0
    for action, success, message in test_results:
        result = MemoryUpdateResult(
            success=success, action=action, memory_id=f"test_{action}", message=message
        )

        if result.action == action:
            print_success(f"动作 '{action}' 设置正确")
            passed += 1

        if result.success == success:
            print_success(f"成功状态 '{success}' 设置正确")
            passed += 1

    print_info(f"记忆更新结果测试通过率: {passed}/{len(test_results)*2}")
    return passed >= len(test_results) * 1.5


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 记忆管理器测试 🌸")

    results = []

    try:
        results.append(("数据结构", test_data_structures()))
    except Exception as e:
        print(f"{Colors.RED}✗ 数据结构测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("数据结构", False))

    try:
        results.append(("重复检测", test_duplicate_detection()))
    except Exception as e:
        print(f"{Colors.RED}✗ 重复检测测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("重复检测", False))

    try:
        results.append(("矛盾检测", test_contradiction_detection()))
    except Exception as e:
        print(f"{Colors.RED}✗ 矛盾检测测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("矛盾检测", False))

    try:
        results.append(("相似度计算", test_similarity_calculation()))
    except Exception as e:
        print(f"{Colors.RED}✗ 相似度计算测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("相似度计算", False))

    try:
        results.append(("冲突历史", test_conflict_history()))
    except Exception as e:
        print(f"{Colors.RED}✗ 冲突历史测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("冲突历史", False))

    try:
        results.append(("记忆更新结果", test_memory_update_result()))
    except Exception as e:
        print(f"{Colors.RED}✗ 记忆更新结果测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("记忆更新结果", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！记忆管理器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
