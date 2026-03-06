# -*- coding: utf-8 -*-
"""
记忆提取器测试
验证重要信息提取、事件检测和自动摘要生成
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

# 导入记忆提取器
spec_extractor = importlib.util.spec_from_file_location(
    "memory_extractor",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/memory/memory_extractor.py"
    ),
)
memory_extractor_module = importlib.util.module_from_spec(spec_extractor)
sys.modules["app.services.memory.memory_extractor"] = memory_extractor_module
spec_extractor.loader.exec_module(memory_extractor_module)

MemoryExtractor = memory_extractor_module.MemoryExtractor
get_memory_extractor = memory_extractor_module.get_memory_extractor


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


def test_name_extraction():
    """测试名字提取"""
    print_header("测试1: 名字提取")

    extractor = MemoryExtractor()

    test_cases = [
        ("我叫李明", "李明", True),
        ("我的名字是张三", "张三", True),
        ("大家都叫我小红", "小红", True),
        ("今天天气真好", "", False),
    ]

    passed = 0
    for text, expected_name, should_extract in test_cases:
        extracted = extractor.extract_names(text)

        if should_extract:
            if extracted and any(info.value == expected_name for info in extracted):
                print_success(f"'{text}' -> 提取到名字: {expected_name}")
                passed += 1
            else:
                print_error(f"'{text}' -> 未提取到期望的名字: {expected_name}")
        else:
            if not extracted:
                print_success(f"'{text}' -> 正确不提取")
                passed += 1
            else:
                print_error(f"'{text}' -> 不应该提取但提取了")

    print_info(f"名字提取测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_preference_extraction():
    """测试偏好提取"""
    print_header("测试2: 偏好提取")

    extractor = MemoryExtractor()

    test_cases = [
        ("我喜欢吃火锅", "吃火锅", "like", True),
        ("我爱看电影", "看电影", "like", True),
        ("我讨厌香菜", "香菜", "dislike", True),
        ("我不喜欢早起", "早起", "dislike", True),
    ]

    passed = 0
    for text, expected_value, expected_type, should_extract in test_cases:
        extracted = extractor.extract_preferences(text)

        if should_extract:
            if extracted and any(
                info.value == expected_value and info.key == expected_type for info in extracted
            ):
                print_success(f"'{text}' -> 提取到{expected_type}: {expected_value}")
                passed += 1
            else:
                print_error(f"'{text}' -> 未提取到期望的偏好")
        else:
            passed += 1

    print_info(f"偏好提取测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_event_detection():
    """测试事件检测"""
    print_header("测试3: 事件检测")

    extractor = MemoryExtractor()

    test_cases = [
        ("我生日是10月15日", "birthday", True),
        ("我换工作了", "job_change", True),
        ("今天是我的生日", "birthday", True),
        ("我找到新工作了", "job_change", True),
    ]

    passed = 0
    for text, expected_type, should_detect in test_cases:
        events = extractor.detect_events(text)

        if should_detect:
            if events and any(event.event_type == expected_type for event in events):
                print_success(f"'{text}' -> 检测到事件: {expected_type}")
                passed += 1
            else:
                print_error(f"'{text}' -> 未检测到期望的事件: {expected_type}")
        else:
            passed += 1

    print_info(f"事件检测测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_summary_generation():
    """测试摘要生成"""
    print_header("测试4: 摘要生成")

    extractor = MemoryExtractor()

    test_conversation = [
        {"role": "user", "content": "你好，我叫李明"},
        {"role": "assistant", "content": "你好呀李明！很高兴认识你～"},
        {"role": "user", "content": "我喜欢打篮球，生日是5月20日"},
        {"role": "assistant", "content": "哇，520生日好浪漫！打篮球一定很帅吧～"},
    ]

    summary = extractor.generate_summary(test_conversation)

    passed = 0
    if summary.summary:
        print_success(f"生成摘要: {summary.summary[:100]}...")
        passed += 1
    else:
        print_error("未生成摘要")

    if summary.extracted_info:
        print_success(f"提取到 {len(summary.extracted_info)} 条信息")
        for info in summary.extracted_info[:3]:
            print(f"  - {info.key}: {info.value}")
        passed += 1
    else:
        print_error("未提取到信息")

    if len(summary.key_topics) > 0:
        print_success(f"提取到话题: {', '.join(summary.key_topics)}")
        passed += 1

    print_info(f"摘要生成测试通过率: {passed}/3")
    return passed >= 2


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 记忆提取器测试 🌸")

    results = []

    try:
        results.append(("名字提取", test_name_extraction()))
    except Exception as e:
        print_error(f"名字提取测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("名字提取", False))

    try:
        results.append(("偏好提取", test_preference_extraction()))
    except Exception as e:
        print_error(f"偏好提取测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("偏好提取", False))

    try:
        results.append(("事件检测", test_event_detection()))
    except Exception as e:
        print_error(f"事件检测测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("事件检测", False))

    try:
        results.append(("摘要生成", test_summary_generation()))
    except Exception as e:
        print_error(f"摘要生成测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("摘要生成", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！记忆提取器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
