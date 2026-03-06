# -*- coding: utf-8 -*-
"""成本优化器测试"""

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
app_services_llm_module = types.ModuleType("app.services.llm")
sys.modules["app.services.llm"] = app_services_llm_module
app_services_memory_module = types.ModuleType("app.services.memory")
sys.modules["app.services.memory"] = app_services_memory_module

# 直接导入cost_optimizer
spec_cost = importlib.util.spec_from_file_location(
    "cost_optimizer",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/services/llm/cost_optimizer.py"),
)
cost_optimizer_module = importlib.util.module_from_spec(spec_cost)
sys.modules["app.services.llm.cost_optimizer"] = cost_optimizer_module
spec_cost.loader.exec_module(cost_optimizer_module)

get_cost_optimizer = cost_optimizer_module.get_cost_optimizer


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


async def test_rule_based_responder():
    """测试规则回复"""
    print_header("测试1: 规则回复功能")

    optimizer = get_cost_optimizer()
    optimizer.clear_cache()

    test_cases = [
        ("你好", "default", True),
        ("在吗", "default", True),
        ("谢谢", "default", True),
        ("晚安", "default", True),
        ("哈哈", "default", True),
        ("嗯", "default", True),
        ("这是一个复杂的问题，需要仔细思考", "default", False),
    ]

    passed = 0
    for message, personality, should_match in test_cases:
        response = optimizer.rule_responder.match(message, personality)
        matched = response is not None

        if matched == should_match:
            if should_match:
                print_success(f"'{message}' -> 规则匹配: '{response}'")
            else:
                print_success(f"'{message}' -> 正确不匹配")
            passed += 1
        else:
            print(
                f"{Colors.RED}✗{Colors.RESET} '{message}' -> 期望匹配: {should_match}, 实际: {matched}"
            )

    print_info(f"规则回复测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases)


async def test_response_cache():
    """测试响应缓存"""
    print_header("测试2: 响应缓存功能")

    optimizer = get_cost_optimizer()
    optimizer.clear_cache()

    test_message = "缓存测试消息"
    test_response = "这是缓存的回复"
    personality = "default"

    cache_hit = optimizer.cache.get(test_message, personality)
    if cache_hit is None:
        print_success("初始缓存为空")
    else:
        print(f"{Colors.RED}✗{Colors.RESET} 初始缓存不为空")
        return False

    optimizer.cache.put(test_message, personality, test_response)

    cache_hit = optimizer.cache.get(test_message, personality)
    if cache_hit == test_response:
        print_success(f"缓存命中: '{cache_hit}'")
    else:
        print(f"{Colors.RED}✗{Colors.RESET} 缓存未命中")
        return False

    stats = optimizer.cache.stats()
    print_info(f"缓存统计: {stats}")

    return True


async def test_stats():
    """测试统计功能"""
    print_header("测试3: 统计功能")

    optimizer = get_cost_optimizer()
    optimizer.clear_cache()

    test_cases = [
        ("你好", "default"),
        ("你好", "default"),
        ("在吗", "default"),
        ("复杂的问题需要LLM回复", "default"),
    ]

    async def mock_llm():
        class MockLLMResponse:
            content = "LLM生成的回复"
            model = "test-model"
            tokens_used = 100

        return MockLLMResponse()

    for message, personality in test_cases:
        await optimizer.process(message, personality, mock_llm)

    stats = optimizer.get_stats()
    print_info(f"统计信息: {stats}")

    if stats["total_requests"] == 4:
        print_success("总请求数正确")
    else:
        print(f"{Colors.RED}✗{Colors.RESET} 总请求数错误: {stats['total_requests']}")
        return False

    if stats["rule_hits"] >= 2:
        print_success("规则命中数正确")
    else:
        print(f"{Colors.RED}✗{Colors.RESET} 规则命中数错误: {stats['rule_hits']}")
        return False

    return True


async def run_all_tests():
    """运行所有测试"""
    print_header("🌸 成本优化器测试 🌸")

    results = []

    try:
        results.append(("规则回复功能", await test_rule_based_responder()))
    except Exception as e:
        print(f"{Colors.RED}✗ 规则回复功能测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("规则回复功能", False))

    try:
        results.append(("响应缓存功能", await test_response_cache()))
    except Exception as e:
        print(f"{Colors.RED}✗ 响应缓存功能测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("响应缓存功能", False))

    try:
        results.append(("统计功能", await test_stats()))
    except Exception as e:
        print(f"{Colors.RED}✗ 统计功能测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("统计功能", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！成本优化器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
