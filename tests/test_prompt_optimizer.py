# -*- coding: utf-8 -*-
"""
提示优化系统测试
"""

import importlib.util
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 屏蔽不必要的模块导入
app_module = types.ModuleType("app")
sys.modules["app"] = app_module
app_services_module = types.ModuleType("app.services")
sys.modules["app.services"] = app_services_module
app_services_llm_module = types.ModuleType("app.services.llm")
sys.modules["app.services.llm"] = app_services_llm_module

# 直接导入 prompt_optimizer
spec_prompt = importlib.util.spec_from_file_location(
    "prompt_optimizer",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/llm/prompt_optimizer.py"
    ),
)
prompt_optimizer_module = importlib.util.module_from_spec(spec_prompt)
sys.modules["app.services.llm.prompt_optimizer"] = prompt_optimizer_module
spec_prompt.loader.exec_module(prompt_optimizer_module)

FewShotExample = prompt_optimizer_module.FewShotExample
FewShotManager = prompt_optimizer_module.FewShotManager
PromptTemplate = prompt_optimizer_module.PromptTemplate
PromptVariant = prompt_optimizer_module.PromptVariant
ABTestManager = prompt_optimizer_module.ABTestManager
ABTestResult = prompt_optimizer_module.ABTestResult
PromptOptimizer = prompt_optimizer_module.PromptOptimizer
get_prompt_optimizer = prompt_optimizer_module.get_prompt_optimizer


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    separator = "=" * 60
    print(f"\n{Colors.BLUE}{separator}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{separator}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def test_few_shot_manager():
    """测试 Few-shot 示例管理器"""
    print_header("测试1: Few-shot 示例管理器")

    temp_dir = tempfile.mkdtemp()
    manager = FewShotManager(storage_dir=temp_dir)

    passed = 0
    total = 0

    total += 1
    try:
        example = manager.add_example(
            category="humor",
            user_input="今天好累啊",
            ai_response="卧槽，累成狗了吧😭",
            tags=["empathy"],
            quality_score=0.9,
        )

        if example.id and example.category == "humor":
            print_success(f"添加示例成功: {example.user_input[:20]}...")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 添加示例异常: {e}{Colors.RESET}")

    total += 1
    try:
        manager.add_example(
            category="humor", user_input="心情不好", ai_response="害，我懂😭", quality_score=0.8
        )
        manager.add_example(
            category="humor", user_input="考试挂了", ai_response="啊这，太惨了吧", quality_score=0.6
        )

        examples = manager.get_examples(category="humor", n=2, min_quality=0.7)

        if len(examples) == 2 and all(ex.quality_score >= 0.7 for ex in examples):
            print_success(f"获取高质量示例成功: {len(examples)} 个")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 获取示例异常: {e}{Colors.RESET}")

    total += 1
    try:
        manager.add_example(
            category="empathy",
            user_input="今天好累啊",
            ai_response="卧槽，累成狗了吧😭",
            tags=["empathy", "casual"],
            quality_score=0.9,
        )

        examples = manager.get_examples(category="empathy", tags=["casual"])

        if len(examples) >= 1 and "casual" in examples[0].tags:
            print_success("标签过滤成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 标签过滤异常: {e}{Colors.RESET}")

    total += 1
    try:
        example_id = manager.examples["humor"][0].id
        manager.update_example_stats(example_id, success=True)

        updated = manager.examples["humor"][0]
        if updated.usage_count == 1 and updated.success_rate > 0:
            print_success("更新示例统计成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 更新示例统计异常: {e}{Colors.RESET}")

    total += 1
    try:
        examples = manager.get_examples(category="humor", n=2)
        formatted = manager.format_examples_for_prompt(examples)

        if "【参考示例】" in formatted and "用户:" in formatted and "小花:" in formatted:
            print_success("格式化示例成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 格式化示例异常: {e}{Colors.RESET}")

    total += 1
    try:
        stats = manager.get_category_stats("humor")

        if stats and stats["total_count"] >= 3:
            print_success("类别统计成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 类别统计异常: {e}{Colors.RESET}")

    print_info(f"Few-shot 管理器通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_ab_test_manager():
    """测试 A/B 测试管理器"""
    print_header("测试2: A/B 测试管理器")

    temp_dir = tempfile.mkdtemp()
    manager = ABTestManager(storage_dir=temp_dir)

    passed = 0
    total = 0

    total += 1
    try:
        template_a = PromptTemplate(
            id="a-1",
            name="幽默风格",
            variant=PromptVariant.A,
            template="你是一个幽默的AI，喜欢开玩笑",
        )
        template_b = PromptTemplate(
            id="b-1",
            name="温柔风格",
            variant=PromptVariant.B,
            template="你是一个温柔的AI，善于倾听",
        )

        manager.create_test(
            test_name="humor_vs_gentle", template_a=template_a, template_b=template_b
        )

        if "humor_vs_gentle" in manager.templates:
            print_success("创建 A/B 测试成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 创建测试异常: {e}{Colors.RESET}")

    total += 1
    try:
        variant1 = manager.assign_variant("humor_vs_gentle", "user1")
        variant2 = manager.assign_variant("humor_vs_gentle", "user1")

        if variant1 == variant2 and variant1 in [PromptVariant.A, PromptVariant.B]:
            print_success(f"分配变体成功: {variant1.value}")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 分配变体异常: {e}{Colors.RESET}")

    total += 1
    try:
        result = manager.record_result(
            test_name="humor_vs_gentle",
            variant=PromptVariant.A,
            user_id="user1",
            user_message="今天好累啊",
            ai_response="卧槽，累成狗了吧😭",
            user_satisfaction=0.9,
            response_time=1.5,
            conversation_length=10,
            emotional_resonance=0.8,
        )

        if result.id and result.user_satisfaction == 0.9:
            print_success("记录测试结果成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 记录结果异常: {e}{Colors.RESET}")

    total += 1
    try:
        for i in range(14):
            manager.record_result(
                test_name="humor_vs_gentle",
                variant=PromptVariant.A,
                user_id=f"user{i+2}",
                user_message="测试消息",
                ai_response="测试回复",
                user_satisfaction=0.85,
                response_time=1.5,
                conversation_length=10,
                emotional_resonance=0.8,
            )

        for i in range(15):
            manager.record_result(
                test_name="humor_vs_gentle",
                variant=PromptVariant.B,
                user_id=f"user{i+20}",
                user_message="测试消息",
                ai_response="测试回复",
                user_satisfaction=0.75,
                response_time=2.0,
                conversation_length=12,
                emotional_resonance=0.7,
            )

        stats = manager.get_stats("humor_vs_gentle", min_samples=10)

        if PromptVariant.A in stats and PromptVariant.B in stats:
            print_success("获取统计成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 获取统计异常: {e}{Colors.RESET}")

    total += 1
    try:
        comparison = manager.compare_variants(
            test_name="humor_vs_gentle", variant_a=PromptVariant.A, variant_b=PromptVariant.B
        )

        if "winner" in comparison and "confidence" in comparison:
            print_success("比较变体成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 比较变体异常: {e}{Colors.RESET}")

    print_info(f"A/B 测试管理器通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_prompt_optimizer():
    """测试提示优化器"""
    print_header("测试3: 提示优化器")

    temp_dir = tempfile.mkdtemp()
    few_shot_manager = FewShotManager(storage_dir=f"{temp_dir}/few_shot")
    ab_test_manager = ABTestManager(storage_dir=f"{temp_dir}/ab_tests")
    optimizer = PromptOptimizer(few_shot_manager, ab_test_manager)

    passed = 0
    total = 0

    total += 1
    try:
        optimizer.few_shot_manager.add_example(
            category="humor",
            user_input="今天好累啊",
            ai_response="卧槽，累成狗了吧😭",
            quality_score=0.9,
        )
        optimizer.few_shot_manager.add_example(
            category="empathy", user_input="心情不好", ai_response="害，我懂😭", quality_score=0.8
        )

        base_prompt = "你是小花，一个真实的女孩。"
        enhanced = optimizer.enhance_prompt_with_examples(
            base_prompt=base_prompt, categories=["humor", "empathy"], n_per_category=1
        )

        if base_prompt in enhanced and "【参考示例】" in enhanced:
            print_success("使用示例增强提示成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 增强提示异常: {e}{Colors.RESET}")

    total += 1
    try:
        template_a = PromptTemplate(
            id="a-1", name="风格A", variant=PromptVariant.A, template="你是一个幽默的AI"
        )
        template_b = PromptTemplate(
            id="b-1", name="风格B", variant=PromptVariant.B, template="你是一个温柔的AI"
        )

        optimizer.ab_test_manager.create_test(
            test_name="style_test", template_a=template_a, template_b=template_b
        )

        template = optimizer.get_optimized_template("style_test", "user1")

        if template and template.variant in [PromptVariant.A, PromptVariant.B]:
            print_success("获取优化模板成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 获取模板异常: {e}{Colors.RESET}")

    total += 1
    try:
        example = optimizer.few_shot_manager.add_example(
            category="test", user_input="测试输入", ai_response="测试回复", quality_score=0.9
        )

        optimizer.track_prompt_effectiveness(
            test_name="style_test",
            variant=PromptVariant.A,
            user_id="user1",
            user_message="今天好累啊",
            ai_response="卧槽，累成狗了吧😭",
            user_satisfaction=0.9,
            response_time=1.5,
            conversation_length=10,
            emotional_resonance=0.8,
            used_examples=[example.id],
        )

        if "style_test" in optimizer.ab_test_manager.results:
            print_success("追踪提示效果成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 追踪效果异常: {e}{Colors.RESET}")

    total += 1
    try:
        for i in range(14):
            optimizer.ab_test_manager.record_result(
                test_name="style_test",
                variant=PromptVariant.A,
                user_id=f"user{i+2}",
                user_message="测试消息",
                ai_response="测试回复",
                user_satisfaction=0.9,
                response_time=1.5,
                conversation_length=10,
                emotional_resonance=0.8,
            )

        for i in range(15):
            optimizer.ab_test_manager.record_result(
                test_name="style_test",
                variant=PromptVariant.B,
                user_id=f"user{i+20}",
                user_message="测试消息",
                ai_response="测试回复",
                user_satisfaction=0.7,
                response_time=2.0,
                conversation_length=12,
                emotional_resonance=0.7,
            )

        report = optimizer.get_optimization_report("style_test")

        if "best_variant" in report and "recommendation" in report:
            print_success("获取优化报告成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 获取报告异常: {e}{Colors.RESET}")

    print_info(f"提示优化器通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_singleton():
    """测试单例模式"""
    print_header("测试4: 单例模式验证")

    passed = 0
    total = 1

    try:
        optimizer1 = get_prompt_optimizer()
        optimizer2 = get_prompt_optimizer()

        if optimizer1 is optimizer2:
            print_success("单例模式验证成功")
            passed += 1
    except Exception as e:
        print(f"{Colors.RED}✗ 单例模式异常: {e}{Colors.RESET}")

    print_info(f"单例模式通过率: {passed}/{total}")
    return passed == total


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 提示优化系统测试 🌸")

    results = []

    try:
        results.append(("Few-shot 示例管理", test_few_shot_manager()))
    except Exception as e:
        print(f"{Colors.RED}✗ Few-shot 示例管理测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("Few-shot 示例管理", False))

    try:
        results.append(("A/B 测试框架", test_ab_test_manager()))
    except Exception as e:
        print(f"{Colors.RED}✗ A/B 测试框架测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("A/B 测试框架", False))

    try:
        results.append(("提示优化器", test_prompt_optimizer()))
    except Exception as e:
        print(f"{Colors.RED}✗ 提示优化器测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("提示优化器", False))

    try:
        results.append(("单例模式", test_singleton()))
    except Exception as e:
        print(f"{Colors.RED}✗ 单例模式测试失败: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        results.append(("单例模式", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！提示优化系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
