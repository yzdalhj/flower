"""
情感系统验证测试
验证内容:
1. 多语言情感分析器 (中文优先)
2. 中文语境增强
3. 表情包/贴图解析
4. PAD三维情感模型
5. AI情感状态管理
6. 情感动力学

注意: 此测试直接导入实际实现模块进行验证
"""

import importlib.util
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

# 直接加载 emotion_analyzer.py
spec = importlib.util.spec_from_file_location(
    "emotion_analyzer",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/services/emotion_analyzer.py"),
)
emotion_analyzer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emotion_analyzer_module)

# 导入实际类
MultilingualEmotionAnalyzer = emotion_analyzer_module.MultilingualEmotionAnalyzer
ChineseEmotionLexicon = emotion_analyzer_module.ChineseEmotionLexicon
EmotionResult = emotion_analyzer_module.EmotionResult


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


def test_chinese_emotion_analyzer():
    """测试中文情感分析器 - 使用实际实现"""
    print_header("测试1: 多语言情感分析器 (中文优先) - 实际实现")

    analyzer = MultilingualEmotionAnalyzer()

    test_cases = [
        ("今天天气真好，心情棒极了！", "joy", "积极情感"),
        ("好难过，考试没考好...", "sadness", "消极情感"),
        ("气死我了，怎么能这样！", "anger", "愤怒情感"),
        ("这个产品太赞了，yyds！", "joy", "网络用语"),
        ("最近有点emo，不想说话", "sadness", "网络流行语"),
        ("I am so happy today!", "joy", "英文情感"),
    ]

    passed = 0
    for text, expected_emotion, desc in test_cases:
        result = analyzer.analyze(text)
        is_correct = result.primary_emotion == expected_emotion

        if is_correct:
            print_success(
                f"{desc}: '{text[:20]}...' -> {result.primary_emotion} ({result.confidence:.2f})"
            )
            passed += 1
        else:
            print_error(
                f"{desc}: '{text[:20]}...' -> 期望 {expected_emotion}, 实际 {result.primary_emotion}"
            )

        print(f"    PAD: V={result.valence:.2f}, A={result.arousal:.2f}, D={result.dominance:.2f}")

    print_info(f"通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.8


def test_chinese_context_enhancement():
    """测试中文语境增强 - 使用实际实现"""
    print_header("测试2: 中文语境增强 - 实际实现")

    lexicon = ChineseEmotionLexicon()

    # 测试情感词检测
    test_words = [
        ("开心", "joy"),
        ("难过", "sadness"),
        ("生气", "anger"),
        ("害怕", "fear"),
        ("惊讶", "surprise"),
    ]

    passed = 0
    for word, expected in test_words:
        emotion, intensity = lexicon.get_emotion(word)
        if emotion == expected:
            print_success(f"'{word}' -> {emotion} ({intensity:.2f})")
            passed += 1
        else:
            print_error(f"'{word}' -> 期望 {expected}, 实际 {emotion}")

    # 测试网络用语
    slang_tests = [
        ("yyds", "joy"),
        ("emo", "sadness"),
        ("躺平", "sadness"),
    ]

    for word, expected in slang_tests:
        emotion, intensity = lexicon.get_emotion(word)
        if emotion == expected:
            print_success(f"网络语 '{word}' -> {emotion} ({intensity:.2f})")
            passed += 1
        else:
            print_error(f"网络语 '{word}' -> 期望 {expected}, 实际 {emotion}")

    print_info(f"情感词检测通过率: {passed}/{len(test_words) + len(slang_tests)}")
    return passed >= len(test_words)


def test_emoji_sticker_parsing():
    """测试表情包/贴图解析 - 使用实际实现"""
    print_header("测试3: 表情包/贴图解析 - 实际实现")

    analyzer = MultilingualEmotionAnalyzer()

    emoji_tests = [
        ("今天好开心😊", "joy", "开心表情"),
        ("好难过😢", "sadness", "难过表情"),
        ("太棒了👍", "joy", "点赞表情"),
        ("爱你❤️", "joy", "爱心表情"),
        ("哈哈哈😂", "joy", "大笑表情"),
        ("好可怕😱", "fear", "恐惧表情"),
    ]

    passed = 0
    for text, expected, desc in emoji_tests:
        result = analyzer.analyze(text)
        # 允许一定容错
        is_joy = result.primary_emotion == "joy" or result.valence > 0.3
        is_sad = result.primary_emotion == "sadness" or result.valence < -0.3

        if (
            (expected == "joy" and is_joy)
            or (expected == "sadness" and is_sad)
            or result.primary_emotion == expected
        ):
            print_success(f"{desc}: '{text}' -> {result.primary_emotion}")
            passed += 1
        else:
            print_error(f"{desc}: '{text}' -> 期望 {expected}, 实际 {result.primary_emotion}")

    # 测试表情包描述
    sticker_result = analyzer.analyze_sticker("用户发送了一个[大笑]表情包")
    print_info(
        f"表情包解析: {sticker_result.primary_emotion} (置信度: {sticker_result.confidence:.2f})"
    )

    print_info(f"表情解析通过率: {passed}/{len(emoji_tests)}")
    return passed >= len(emoji_tests) * 0.7


def test_pad_model():
    """测试PAD三维情感模型 - 通过分析结果验证"""
    print_header("测试4: PAD三维情感模型 - 实际实现")

    analyzer = MultilingualEmotionAnalyzer()

    # 测试不同情感文本的PAD值
    pad_tests = [
        ("开心", "joy", 0.3, 1.0, -0.5, 0.5),  # 愉悦度应该为正
        ("难过", "sadness", -1.0, -0.3, -0.5, 0.0),  # 愉悦度应该为负
        ("生气", "anger", -0.5, 0.5, 0.0, 0.8),  # 激活度应该较高
        ("害怕", "fear", -1.0, 0.0, -0.5, 0.5),  # 支配度应该为负
    ]

    passed = 0
    for text, expected_emotion, min_v, max_v, min_a, max_a in pad_tests:
        result = analyzer.analyze(text)

        # 检查情感类别
        emotion_correct = result.primary_emotion == expected_emotion

        # 检查PAD值范围
        v_correct = min_v <= result.valence <= max_v
        a_correct = min_a <= result.arousal <= max_a

        if emotion_correct and v_correct and a_correct:
            print_success(
                f"{text} -> {result.primary_emotion}, V={result.valence:.2f}, A={result.arousal:.2f}"
            )
            passed += 1
        else:
            print_error(
                f"{text} -> 期望 {expected_emotion} V=[{min_v},{max_v}] A=[{min_a},{max_a}]"
            )
            print(
                f"    实际: {result.primary_emotion}, V={result.valence:.2f}, A={result.arousal:.2f}"
            )

    print_info(f"PAD模型测试通过率: {passed}/{len(pad_tests)}")
    return passed >= len(pad_tests) * 0.75


def test_ai_emotion_state_management():
    """测试AI情感状态管理 - 使用实际实现"""
    print_header("测试5: AI情感状态管理 - 实际实现")

    # 加载 emotion_dynamics 模块（emotion_state 依赖它）
    spec_dynamics = importlib.util.spec_from_file_location(
        "emotion_dynamics",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "app/services/emotion_dynamics.py"
        ),
    )
    emotion_dynamics_module = importlib.util.module_from_spec(spec_dynamics)
    spec_dynamics.loader.exec_module(emotion_dynamics_module)

    # 将 dynamics 模块添加到 sys.modules
    sys.modules["emotion_dynamics"] = emotion_dynamics_module
    sys.modules["app.services.emotion_dynamics"] = emotion_dynamics_module

    # 加载 emotion_state 模块
    spec_state = importlib.util.spec_from_file_location(
        "emotion_state",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/services/emotion_state.py"),
    )
    emotion_state_module = importlib.util.module_from_spec(spec_state)
    spec_state.loader.exec_module(emotion_state_module)

    AIEmotionManager = emotion_state_module.AIEmotionManager
    AIEmotionalState = emotion_dynamics_module.AIEmotionalState

    # 创建管理器
    manager = AIEmotionManager("test_user_001")

    # 测试初始状态
    state = manager.get_current_state()
    print_info(
        f"初始状态: {state.primary_emotion.value}, PAD=({state.valence:.2f}, {state.arousal:.2f}, {state.dominance:.2f})"
    )

    # 测试用户情感共情 - 使用简单字典代替 EmotionResult
    user_emotion = {
        "label": "joy",
        "confidence": 0.9,
        "valence": 0.8,
        "arousal": 0.6,
        "dominance": 0.5,
        "intensity": 0.9,
    }

    new_state = manager.update_from_user_emotion(user_emotion, {"intimacy": 0.7})
    print_success(f"用户开心 -> AI共情: {new_state.primary_emotion.value}")
    print(f"    PAD: V={new_state.valence:.2f}, A={new_state.arousal:.2f}")

    # 验证共情效果（AI应该也变得开心）
    empathy_correct = new_state.valence > 0 and new_state.primary_emotion in [
        AIEmotionalState.HAPPY,
        AIEmotionalState.EXCITED,
        AIEmotionalState.GRATEFUL,
    ]

    # 测试事件响应
    manager2 = AIEmotionManager("test_user_002")
    manager2.update_from_event("user_compliment", 0.8)
    compliment_state = manager2.get_current_state()
    print_success(f"用户夸奖 -> AI状态: {compliment_state.primary_emotion.value}")

    manager2.update_from_event("user_anger", 0.7)
    anger_state = manager2.get_current_state()
    print_success(f"用户生气 -> AI状态: {anger_state.primary_emotion.value}")

    # 测试情感描述
    description = manager2.get_emotion_description()
    print_info(f"情感描述: {description}")

    passed = 0
    if empathy_correct:
        passed += 1
        print_success("共情反应正确")
    else:
        print_error("共情反应不正确")

    if compliment_state.valence > 0:
        passed += 1
        print_success("夸奖事件响应正确")
    else:
        print_error("夸奖事件响应不正确")

    print_info(f"AI情感管理测试通过率: {passed}/2")
    return passed >= 2


def test_emotion_dynamics():
    """测试情感动力学 - 使用实际实现"""
    print_header("测试6: 情感动力学 - 实际实现")

    # emotion_dynamics 模块已在 test_ai_emotion_state_management 中加载
    # 如果前面的测试没运行，需要重新加载
    if "emotion_dynamics" not in sys.modules:
        spec_dynamics = importlib.util.spec_from_file_location(
            "emotion_dynamics",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "app/services/emotion_dynamics.py"
            ),
        )
        emotion_dynamics_module = importlib.util.module_from_spec(spec_dynamics)
        spec_dynamics.loader.exec_module(emotion_dynamics_module)
        sys.modules["emotion_dynamics"] = emotion_dynamics_module
    else:
        emotion_dynamics_module = sys.modules["emotion_dynamics"]

    EmotionDynamics = emotion_dynamics_module.EmotionDynamics
    EmotionState = emotion_dynamics_module.EmotionState
    AIEmotionalState = emotion_dynamics_module.AIEmotionalState
    DecayCurve = emotion_dynamics_module.DecayCurve
    Stimulus = emotion_dynamics_module.Stimulus

    # 测试自然衰减
    dynamics = EmotionDynamics(decay_rate=0.1, decay_curve=DecayCurve.EXPONENTIAL)

    initial = EmotionState(
        valence=0.8,
        arousal=0.7,
        dominance=0.6,
        intensity=0.9,
        primary_emotion=AIEmotionalState.HAPPY,
    )

    # 1小时后
    after_1h = dynamics.apply_natural_decay(initial, 1.0)
    print_info(f"1小时衰减: V {initial.valence:.2f} -> {after_1h.valence:.2f}")

    # 验证衰减效果
    decay_correct = after_1h.valence < initial.valence

    # 测试刺激响应
    stimulus = Stimulus(
        source="test", valence_delta=0.5, arousal_delta=0.3, dominance_delta=0.1, intensity=0.8
    )
    after_stimulus = dynamics.calculate_stimulus_response(after_1h, stimulus)
    print_success(f"积极刺激后: V={after_stimulus.valence:.2f}, A={after_stimulus.arousal:.2f}")

    # 验证刺激效果
    stimulus_correct = after_stimulus.valence > after_1h.valence

    # 测试惯性
    target = EmotionState(
        valence=-0.5,
        arousal=0.8,
        dominance=0.4,
        intensity=0.7,
        primary_emotion=AIEmotionalState.ANGRY,
    )

    with_inertia = dynamics.apply_inertia(after_stimulus, target)
    print_info(
        f"惯性效果: V {after_stimulus.valence:.2f} -> {with_inertia.valence:.2f} (目标: {target.valence:.2f})"
    )

    # 验证惯性效果（应该在当前和目标之间）
    inertia_correct = (after_stimulus.valence > with_inertia.valence > target.valence) or (
        after_stimulus.valence < with_inertia.valence < target.valence
    )

    # 测试情感演化
    dynamics2 = EmotionDynamics()
    evolved = dynamics2.evolve_state(initial, hours_passed=2.0, new_stimulus=stimulus)
    print_success(f"综合演化后: {evolved.primary_emotion.value}, V={evolved.valence:.2f}")

    # 测试情感动量
    momentum = dynamics2.get_emotional_momentum()
    print_info(f"情感动量: V={momentum['valence']:.4f}")

    passed = 0
    if decay_correct:
        passed += 1
        print_success("自然衰减正确")
    else:
        print_error("自然衰减不正确")

    if stimulus_correct:
        passed += 1
        print_success("刺激响应正确")
    else:
        print_error("刺激响应不正确")

    if inertia_correct:
        passed += 1
        print_success("惯性效果正确")
    else:
        print_error("惯性效果不正确")

    print_info(f"情感动力学测试通过率: {passed}/3")
    return passed >= 2


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 情感系统验证测试  🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("中文情感分析", test_chinese_emotion_analyzer()))
    except Exception as e:
        print_error(f"中文情感分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("中文情感分析", False))

    try:
        results.append(("中文语境增强", test_chinese_context_enhancement()))
    except Exception as e:
        print_error(f"中文语境增强测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("中文语境增强", False))

    try:
        results.append(("表情包解析", test_emoji_sticker_parsing()))
    except Exception as e:
        print_error(f"表情包解析测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("表情包解析", False))

    try:
        results.append(("PAD模型", test_pad_model()))
    except Exception as e:
        print_error(f"PAD模型测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("PAD模型", False))

    try:
        results.append(("AI情感管理", test_ai_emotion_state_management()))
    except Exception as e:
        print_error(f"AI情感管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("AI情感管理", False))

    try:
        results.append(("情感动力学", test_emotion_dynamics()))
    except Exception as e:
        print_error(f"情感动力学测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("情感动力学", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！情感系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
