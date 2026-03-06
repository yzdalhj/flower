"""
人格演化系统验证测试

验证内容:
1. 演化约束配置
2. 单次变化限制
3. 核心特质保护
4. 边界特质演化
5. 演化历史记录
6. 人格一致性验证

注意: 此测试直接导入实际实现模块进行验证
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

from app.models.personality import BigFiveScores, PersonalityConfig, PersonalityTraits  # noqa: E402
from app.services.personality.personality_evolution import (  # noqa: E402
    EvolutionConstraints,
    PersonalityEvolutionService,
)

# ============ 颜色输出 ============


class Colors:
    """终端颜色"""

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


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


# ============ 辅助函数 ============


def create_base_personality():
    """创建基础人格配置"""
    return PersonalityConfig(
        id="test_user_1",
        name="测试小花",
        big_five=BigFiveScores(
            openness=70.0,
            conscientiousness=60.0,
            extraversion=65.0,
            agreeableness=75.0,
            neuroticism=35.0,
        ),
        traits=PersonalityTraits(
            expressiveness=70.0,
            humor=60.0,
            sarcasm=40.0,
            verbosity=40.0,
            empathy=80.0,
            warmth=80.0,
            emotional_stability=70.0,
            assertiveness=50.0,
            casualness=70.0,
            formality=20.0,
        ),
    )


# ============ 测试函数 ============


def test_evolution_constraints():
    """测试1: 演化约束配置 - 使用实际实现"""
    print_header("测试1: 演化约束配置 - 实际实现")

    checks = []

    # 测试默认约束
    constraints = EvolutionConstraints()

    if constraints.max_single_change_percent == 5.0:
        print_success(f"单次变化限制正确: {constraints.max_single_change_percent}%")
        checks.append(True)
    else:
        print_error(f"单次变化限制错误: {constraints.max_single_change_percent}%")
        checks.append(False)

    if constraints.max_core_trait_change_percent == 20.0:
        print_success(f"核心特质变化限制正确: {constraints.max_core_trait_change_percent}%")
        checks.append(True)
    else:
        print_error(f"核心特质变化限制错误: {constraints.max_core_trait_change_percent}%")
        checks.append(False)

    if "empathy" in constraints.core_traits:
        print_success("核心特质包含 empathy")
        checks.append(True)
    else:
        print_error("核心特质不包含 empathy")
        checks.append(False)

    if "humor" in constraints.boundary_traits:
        print_success("边界特质包含 humor")
        checks.append(True)
    else:
        print_error("边界特质不包含 humor")
        checks.append(False)

    # 测试自定义约束
    custom_constraints = EvolutionConstraints(
        max_single_change_percent=3.0,
        max_core_trait_change_percent=15.0,
    )

    if custom_constraints.max_single_change_percent == 3.0:
        print_success("自定义约束设置成功")
        checks.append(True)
    else:
        print_error("自定义约束设置失败")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.8


def test_single_change_constraint():
    """测试2: 单次变化限制 - 使用实际实现"""
    print_header("测试2: 单次变化限制（≤5%） - 实际实现")

    evolution_service = PersonalityEvolutionService()
    base_personality = create_base_personality()

    checks = []

    # 尝试大幅调整幽默程度
    adjustments = {"humor": 20.0}  # 尝试增加 20 分

    updated = evolution_service.adjust_personality(
        current_personality=base_personality,
        adjustments=adjustments,
        trigger="test",
        reason="测试单次变化限制",
    )

    # 单次变化应该被限制在 5% 以内
    # 60.0 * 5% = 3.0
    change = updated.traits.humor - base_personality.traits.humor

    if change <= 3.0:
        print_success(f"单次变化被正确限制: {change:.2f} ≤ 3.0")
        checks.append(True)
    else:
        print_error(f"单次变化超过限制: {change:.2f} > 3.0")
        checks.append(False)

    if change > 0:
        print_success("变化方向正确（正向）")
        checks.append(True)
    else:
        print_error("变化方向错误")
        checks.append(False)

    print_info(f"原始值: {base_personality.traits.humor}")
    print_info(f"更新值: {updated.traits.humor}")
    print_info(f"变化量: {change:.2f}")
    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) == len(checks)


def test_core_trait_constraint():
    """测试3: 核心特质保护（≤20%） - 使用实际实现"""
    print_header("测试3: 核心特质保护（≤20%） - 实际实现")

    evolution_service = PersonalityEvolutionService()
    base_personality = create_base_personality()

    evolution_service.register_initial_personality("user_core_test", base_personality)

    checks = []

    # 多次尝试调整核心特质（共情能力）
    current = base_personality
    initial_empathy = base_personality.traits.empathy  # 80.0

    print_info(f"初始共情值: {initial_empathy}")

    for i in range(20):
        adjustments = {"empathy": 3.0}
        current = evolution_service.adjust_personality(
            current_personality=current,
            adjustments=adjustments,
            trigger="test",
            user_id="user_core_test",
        )

    # 核心特质变化应该被限制在 20% 以内
    # 80.0 * 20% = 16.0
    total_change = abs(current.traits.empathy - initial_empathy)

    print_info(f"最终共情值: {current.traits.empathy}")
    print_info(f"总变化量: {total_change:.2f}")
    print_info("限制阈值: 16.0 (20%)")

    if total_change <= 16.0:
        print_success(f"核心特质变化被正确限制: {total_change:.2f} ≤ 16.0")
        checks.append(True)
    else:
        print_error(f"核心特质变化超过限制: {total_change:.2f} > 16.0")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) == len(checks)


def test_boundary_trait_evolution():
    """测试4: 边界特质演化 - 使用实际实现"""
    print_header("测试4: 边界特质演化 - 实际实现")

    evolution_service = PersonalityEvolutionService()
    base_personality = create_base_personality()

    evolution_service.register_initial_personality("user_boundary_test", base_personality)

    checks = []

    # 多次调整边界特质（幽默程度）
    current = base_personality
    initial_humor = base_personality.traits.humor

    print_info(f"初始幽默值: {initial_humor}")

    for i in range(10):
        adjustments = {"humor": 3.0}
        current = evolution_service.adjust_personality(
            current_personality=current,
            adjustments=adjustments,
            trigger="test",
            user_id="user_boundary_test",
        )

    # 边界特质可以累积较大变化
    total_change = current.traits.humor - initial_humor

    print_info(f"最终幽默值: {current.traits.humor}")
    print_info(f"总变化量: {total_change:.2f}")

    if total_change > 10.0:
        print_success(f"边界特质可以累积较大变化: {total_change:.2f} > 10.0")
        checks.append(True)
    else:
        print_error(f"边界特质变化不足: {total_change:.2f} ≤ 10.0")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) == len(checks)


def test_evolution_history():
    """测试5: 演化历史记录 - 使用实际实现"""
    print_header("测试5: 演化历史记录 - 实际实现")

    evolution_service = PersonalityEvolutionService()
    base_personality = create_base_personality()

    checks = []

    initial_history_count = len(base_personality.evolution_history)

    adjustments = {"humor": 2.0, "empathy": 1.0}
    updated = evolution_service.adjust_personality(
        current_personality=base_personality,
        adjustments=adjustments,
        trigger="user_feedback",
        reason="用户反馈喜欢幽默",
        user_id="user_history_test",
    )

    # 验证历史记录增加
    if len(updated.evolution_history) == initial_history_count + 1:
        print_success(f"历史记录增加: {len(updated.evolution_history)}条")
        checks.append(True)
    else:
        print_error(
            f"历史记录数量错误: 期望{initial_history_count + 1}, "
            f"实际{len(updated.evolution_history)}"
        )
        checks.append(False)

    # 验证记录内容
    if len(updated.evolution_history) > 0:
        last_record = updated.evolution_history[-1]

        if last_record.get("trigger") == "user_feedback":
            print_success("触发器记录正确")
            checks.append(True)
        else:
            print_error(f"触发器记录错误: {last_record.get('trigger')}")
            checks.append(False)

        if last_record.get("reason") == "用户反馈喜欢幽默":
            print_success("原因记录正确")
            checks.append(True)
        else:
            print_error(f"原因记录错误: {last_record.get('reason')}")
            checks.append(False)

        if "adjustments" in last_record:
            print_success("调整内容已记录")
            checks.append(True)
        else:
            print_error("调整内容未记录")
            checks.append(False)

    # 验证版本号递增
    if updated.version == base_personality.version + 1:
        print_success(f"版本号递增: {updated.version}")
        checks.append(True)
    else:
        print_error(f"版本号错误: {updated.version}")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.8


def test_personality_consistency():
    """测试6: 人格一致性验证 - 使用实际实现"""
    print_header("测试6: 人格一致性验证 - 实际实现")

    evolution_service = PersonalityEvolutionService()
    base_personality = create_base_personality()

    evolution_service.register_initial_personality("user_consistency_test", base_personality)

    checks = []

    # 小幅调整
    adjustments = {"humor": 2.0, "empathy": 1.0}
    updated = evolution_service.adjust_personality(
        current_personality=base_personality,
        adjustments=adjustments,
        user_id="user_consistency_test",
    )

    result = evolution_service.validate_personality_consistency(
        updated, user_id="user_consistency_test"
    )

    if result.get("is_valid") is True:
        print_success("人格一致性验证通过")
        checks.append(True)
    else:
        print_error("人格一致性验证失败")
        checks.append(False)

    if len(result.get("violations", [])) == 0:
        print_success("无违规项")
        checks.append(True)
    else:
        print_error(f"存在违规项: {result.get('violations')}")
        checks.append(False)

    # 测试超限检测
    violated_personality = PersonalityConfig(
        id="test_violated",
        name="超限人格",
        big_five=base_personality.big_five,
        traits=PersonalityTraits(
            empathy=base_personality.traits.empathy + 20.0,  # 超过 20% 限制
            humor=base_personality.traits.humor,
        ),
    )

    result2 = evolution_service.validate_personality_consistency(
        violated_personality, user_id="user_consistency_test"
    )

    if result2.get("is_valid") is False:
        print_success("超限检测正确")
        checks.append(True)
    else:
        print_error("超限检测失败")
        checks.append(False)

    if len(result2.get("violations", [])) > 0:
        print_success(f"检测到违规项: {len(result2.get('violations'))}个")
        checks.append(True)
    else:
        print_error("未检测到违规项")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.75


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 人格演化系统验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("演化约束配置", test_evolution_constraints()))
    except Exception as e:
        print_error(f"演化约束配置测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("演化约束配置", False))

    try:
        results.append(("单次变化限制", test_single_change_constraint()))
    except Exception as e:
        print_error(f"单次变化限制测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("单次变化限制", False))

    try:
        results.append(("核心特质保护", test_core_trait_constraint()))
    except Exception as e:
        print_error(f"核心特质保护测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("核心特质保护", False))

    try:
        results.append(("边界特质演化", test_boundary_trait_evolution()))
    except Exception as e:
        print_error(f"边界特质演化测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("边界特质演化", False))

    try:
        results.append(("演化历史记录", test_evolution_history()))
    except Exception as e:
        print_error(f"演化历史记录测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("演化历史记录", False))

    try:
        results.append(("人格一致性验证", test_personality_consistency()))
    except Exception as e:
        print_error(f"人格一致性验证测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("人格一致性验证", False))

    # 汇总
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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！人格演化系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
