"""
强化学习优化系统验证测试

验证内容:
1. 用户反馈数据结构
2. 奖励函数计算
3. 正向奖励处理
4. 负向奖励处理
5. 策略更新
6. 人格优化

注意: 此测试直接导入实际实现模块进行验证
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

from app.models.personality import PERSONALITY_TEMPLATES  # noqa: E402
from app.services.learning.continual_learning import ContinualLearningService  # noqa: E402
from app.services.learning.reinforcement_learning import (  # noqa: E402
    FeedbackType,
    PolicyUpdater,
    ReinforcementLearningService,
    RewardFunction,
    RewardSignal,
    UserFeedback,
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


# ============ 测试函数 ============


def test_user_feedback():
    """测试1: 用户反馈数据结构 - 使用实际实现"""
    print_header("测试1: 用户反馈数据结构 - 实际实现")

    checks = []

    # 创建反馈
    feedback = UserFeedback(
        id="test_feedback_1",
        user_id="user_123",
        conversation_id="conv_456",
        message_id="msg_789",
        timestamp=datetime.now(),
        feedback_type=FeedbackType.THUMBS_UP,
        feedback_value=1.0,
        user_message="你好",
        ai_response="你好呀！",
        conversation_length=5,
        response_time=1.5,
    )

    if feedback.id == "test_feedback_1":
        print_success(f"反馈ID正确: {feedback.id}")
        checks.append(True)
    else:
        print_error(f"反馈ID错误: {feedback.id}")
        checks.append(False)

    if feedback.feedback_type == FeedbackType.THUMBS_UP:
        print_success(f"反馈类型正确: {feedback.feedback_type}")
        checks.append(True)
    else:
        print_error(f"反馈类型错误: {feedback.feedback_type}")
        checks.append(False)

    if feedback.feedback_value == 1.0:
        print_success(f"反馈值正确: {feedback.feedback_value}")
        checks.append(True)
    else:
        print_error(f"反馈值错误: {feedback.feedback_value}")
        checks.append(False)

    # 测试序列化
    data = feedback.to_dict()
    if data["id"] == "test_feedback_1":
        print_success("序列化成功")
        checks.append(True)
    else:
        print_error("序列化失败")
        checks.append(False)

    # 测试反序列化
    restored = UserFeedback.from_dict(data)
    if restored.id == feedback.id and restored.feedback_type == feedback.feedback_type:
        print_success("反序列化成功")
        checks.append(True)
    else:
        print_error("反序列化失败")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.8


def test_reward_function_positive():
    """测试2: 正向奖励计算 - 使用实际实现"""
    print_header("测试2: 正向奖励计算 - 实际实现")

    reward_func = RewardFunction()

    checks = []

    feedback = UserFeedback(
        id="test_1",
        user_id="user_1",
        conversation_id="conv_1",
        message_id="msg_1",
        timestamp=datetime.now(),
        feedback_type=FeedbackType.THUMBS_UP,
        feedback_value=0.9,  # 高满意度
        user_message="你真有趣",
        ai_response="哈哈谢谢",
        conversation_length=10,  # 长对话
        response_time=2.0,
        emotional_resonance=0.8,  # 高共鸣
    )

    reward = reward_func.calculate_reward(feedback)

    if reward.user_satisfaction == 0.9:
        print_success(f"用户满意度正确: {reward.user_satisfaction}")
        checks.append(True)
    else:
        print_error(f"用户满意度错误: {reward.user_satisfaction}")
        checks.append(False)

    if reward.conversation_quality > 0.5:
        print_success(f"对话质量良好: {reward.conversation_quality:.2f}")
        checks.append(True)
    else:
        print_error(f"对话质量不足: {reward.conversation_quality:.2f}")
        checks.append(False)

    if reward.emotional_resonance == 0.8:
        print_success(f"情感共鸣正确: {reward.emotional_resonance}")
        checks.append(True)
    else:
        print_error(f"情感共鸣错误: {reward.emotional_resonance}")
        checks.append(False)

    total_reward = reward.calculate_total_reward()
    if total_reward > 0.5:
        print_success(f"总奖励值良好: {total_reward:.2f}")
        checks.append(True)
    else:
        print_error(f"总奖励值不足: {total_reward:.2f}")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.75


def test_reward_function_negative():
    """测试3: 负向奖励计算 - 使用实际实现"""
    print_header("测试3: 负向奖励计算 - 实际实现")

    reward_func = RewardFunction()

    checks = []

    # 回复过长且有AI味
    long_response = "我理解你的感受。" + "非常感谢。" * 50

    feedback = UserFeedback(
        id="test_2",
        user_id="user_1",
        conversation_id="conv_1",
        message_id="msg_2",
        timestamp=datetime.now(),
        feedback_type=FeedbackType.THUMBS_DOWN,
        feedback_value=0.2,  # 低满意度
        user_message="你好",
        ai_response=long_response,
        conversation_length=1,  # 短对话
        response_time=0.3,
        emotional_resonance=0.3,
    )

    reward = reward_func.calculate_reward(feedback)

    if reward.user_satisfaction == 0.2:
        print_success(f"用户满意度正确: {reward.user_satisfaction}")
        checks.append(True)
    else:
        print_error(f"用户满意度错误: {reward.user_satisfaction}")
        checks.append(False)

    if reward.response_too_long > 0:
        print_success(f"检测到回复过长惩罚: {reward.response_too_long:.2f}")
        checks.append(True)
    else:
        print_error("未检测到回复过长惩罚")
        checks.append(False)

    if reward.ai_flavor_penalty > 0:
        print_success(f"检测到AI味惩罚: {reward.ai_flavor_penalty:.2f}")
        checks.append(True)
    else:
        print_error("未检测到AI味惩罚")
        checks.append(False)

    total_reward = reward.calculate_total_reward()
    if total_reward < 0.3:
        print_success(f"总奖励值较低（符合预期）: {total_reward:.2f}")
        checks.append(True)
    else:
        print_error(f"总奖励值过高: {total_reward:.2f}")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.75


def test_policy_updater():
    """测试4: 策略更新器 - 使用实际实现"""
    print_header("测试4: 策略更新器 - 实际实现")

    updater = PolicyUpdater(learning_rate=0.1)
    sample_personality = PERSONALITY_TEMPLATES["default"]

    checks = []

    # 正向奖励
    reward = RewardSignal(
        user_satisfaction=0.9,
        conversation_quality=0.8,
        emotional_resonance=0.85,
    )

    feedback = UserFeedback(
        id="test_1",
        user_id="user_1",
        conversation_id="conv_1",
        message_id="msg_1",
        timestamp=datetime.now(),
        feedback_type=FeedbackType.THUMBS_UP,
        feedback_value=0.9,
        user_message="测试",
        ai_response="好的",
        conversation_length=5,
        response_time=2.0,
    )

    adjustments = updater.update_policy(sample_personality, reward, feedback)

    if len(adjustments) > 0:
        print_success(f"生成了策略调整: {len(adjustments)}项")
        checks.append(True)
    else:
        print_error("未生成策略调整")
        checks.append(False)

    # 检查调整幅度
    reasonable = all(abs(delta) < 10.0 for delta in adjustments.values())
    if reasonable:
        print_success("调整幅度合理（受学习率限制）")
        checks.append(True)
    else:
        print_error("调整幅度过大")
        checks.append(False)

    print_info(f"调整项: {list(adjustments.keys())[:3]}...")
    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) == len(checks)


def test_rl_service():
    """测试5: 强化学习服务 - 使用实际实现"""
    print_header("测试5: 强化学习服务 - 实际实现")

    cl_service = ContinualLearningService()
    rl_service = ReinforcementLearningService(cl_service, storage_dir="./data/test_rl")
    sample_personality = PERSONALITY_TEMPLATES["default"]

    checks = []

    # 收集显式反馈
    feedback = rl_service.collect_explicit_feedback(
        user_id="user_123",
        conversation_id="conv_456",
        message_id="msg_789",
        feedback_type=FeedbackType.THUMBS_UP,
        feedback_value=1.0,
        user_message="你好",
        ai_response="你好呀！",
        conversation_length=5,
        response_time=1.5,
        personality=sample_personality,
        emotional_resonance=0.8,
    )

    if feedback.user_id == "user_123":
        print_success(f"显式反馈收集成功: user_id={feedback.user_id}")
        checks.append(True)
    else:
        print_error("显式反馈收集失败")
        checks.append(False)

    if len(rl_service.feedback_history) > 0:
        print_success(f"反馈历史已记录: {len(rl_service.feedback_history)}条")
        checks.append(True)
    else:
        print_error("反馈历史未记录")
        checks.append(False)

    # 收集隐式反馈
    implicit_feedback = rl_service.collect_implicit_feedback(
        user_id="user_123",
        conversation_id="conv_456",
        message_id="msg_790",
        user_message="聊得很开心",
        ai_response="我也是！",
        conversation_length=10,  # 长对话
        response_time=2.0,
        personality=sample_personality,
        emotional_resonance=0.9,  # 高共鸣
    )

    if implicit_feedback.feedback_type == FeedbackType.IMPLICIT:
        print_success("隐式反馈类型正确")
        checks.append(True)
    else:
        print_error(f"隐式反馈类型错误: {implicit_feedback.feedback_type}")
        checks.append(False)

    if implicit_feedback.feedback_value > 0.6:
        print_success(f"隐式满意度较高: {implicit_feedback.feedback_value:.2f}")
        checks.append(True)
    else:
        print_error(f"隐式满意度过低: {implicit_feedback.feedback_value:.2f}")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.75


def test_personality_optimization():
    """测试6: 人格优化 - 使用实际实现"""
    print_header("测试6: 人格优化 - 实际实现")

    cl_service = ContinualLearningService()
    rl_service = ReinforcementLearningService(cl_service, storage_dir="./data/test_rl")
    sample_personality = PERSONALITY_TEMPLATES["default"]

    checks = []

    # 收集一些正向反馈
    print_info("收集5次正向反馈...")
    for i in range(5):
        rl_service.collect_explicit_feedback(
            user_id="user_opt_test",
            conversation_id=f"conv_{i}",
            message_id=f"msg_{i}",
            feedback_type=FeedbackType.THUMBS_UP,
            feedback_value=0.9,
            user_message="你很幽默",
            ai_response="哈哈谢谢",
            conversation_length=8,
            response_time=2.0,
            personality=sample_personality,
            user_emotion="amused",
            emotional_resonance=0.85,
        )

    # 优化人格
    optimized = rl_service.optimize_personality(
        user_id="user_opt_test",
        current_personality=sample_personality,
        recent_feedback_count=5,
    )

    if optimized is not None:
        print_success("人格优化成功")
        checks.append(True)
    else:
        print_error("人格优化失败")
        checks.append(False)

    if optimized and optimized.version > sample_personality.version:
        print_success(f"版本号递增: {optimized.version} > {sample_personality.version}")
        checks.append(True)
    else:
        print_error("版本号未递增")
        checks.append(False)

    # 获取反馈统计
    stats = rl_service.get_feedback_stats(user_id="user_opt_test")

    if stats["total_feedbacks"] >= 5:
        print_success(f"反馈统计正确: {stats['total_feedbacks']}条")
        checks.append(True)
    else:
        print_error(f"反馈统计错误: {stats['total_feedbacks']}条")
        checks.append(False)

    if stats["avg_satisfaction"] > 0.8:
        print_success(f"平均满意度: {stats['avg_satisfaction']:.2f}")
        checks.append(True)
    else:
        print_error(f"平均满意度过低: {stats['avg_satisfaction']:.2f}")
        checks.append(False)

    print_info(f"通过率: {sum(checks)}/{len(checks)}")
    return sum(checks) >= len(checks) * 0.75


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 强化学习优化系统验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("用户反馈数据结构", test_user_feedback()))
    except Exception as e:
        print_error(f"用户反馈数据结构测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("用户反馈数据结构", False))

    try:
        results.append(("正向奖励计算", test_reward_function_positive()))
    except Exception as e:
        print_error(f"正向奖励计算测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("正向奖励计算", False))

    try:
        results.append(("负向奖励计算", test_reward_function_negative()))
    except Exception as e:
        print_error(f"负向奖励计算测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("负向奖励计算", False))

    try:
        results.append(("策略更新器", test_policy_updater()))
    except Exception as e:
        print_error(f"策略更新器测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("策略更新器", False))

    try:
        results.append(("强化学习服务", test_rl_service()))
    except Exception as e:
        print_error(f"强化学习服务测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("强化学习服务", False))

    try:
        results.append(("人格优化", test_personality_optimization()))
    except Exception as e:
        print_error(f"人格优化测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("人格优化", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！强化学习优化系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
