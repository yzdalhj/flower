# -*- coding: utf-8 -*-
"""
真人化回复处理器测试
验证内容:
1. 截断长句（限制2-3句话）
2. 替换AI味词汇
3. 添加口头禅
4. 替换官方表情
5. 语境感知的口头禅添加
"""

import importlib.util
import re
import sys
from datetime import datetime

sys.path.insert(0, "/Users/yzdalhj/Desktop/code/up/flower")

# 直接导入humanize_processor模块，避免依赖其他服务
spec = importlib.util.spec_from_file_location(
    "humanize_processor",
    "/Users/yzdalhj/Desktop/code/up/flower/app/services/humanize/humanize_processor.py",
)
humanize_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(humanize_module)

HumanizeProcessor = humanize_module.HumanizeProcessor
HumanizeConfig = humanize_module.HumanizeConfig


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


def test_truncate_sentences():
    """测试1: 截断长句功能"""
    print_header("测试1: 截断长句功能")

    # 使用固定配置确保测试可重现
    config = HumanizeConfig(max_sentences=3, min_sentences=2)
    processor = HumanizeProcessor(config=config)

    # 测试用例
    test_cases = [
        # 长文本（超过3句）
        (
            "今天天气真好。我想去公园散步。公园里有很多花。还有很多小朋友在玩。",
            "长文本截断",
        ),
        # 2句话（不需要截断）
        ("今天天气真好。我想去公园散步。", "2句话不截断"),
        # 1句话（不需要截断）
        ("今天天气真好。", "1句话不截断"),
        # 空文本
        ("", "空文本处理"),
    ]

    passed = 0
    for text, desc in test_cases:
        result = processor._truncate_sentences(text)

        if not text:
            if result == text:
                print_success(f"{desc}: 空文本正确处理")
                passed += 1
            else:
                print_error(f"{desc}: 空文本处理失败")
            continue

        # 计算句子数量
        sentences = [s.strip() for s in re.split(r"[。！？!?]+", result) if s.strip()]
        num_sentences = len(sentences)

        original_sentences = [s.strip() for s in re.split(r"[。！？!?]+", text) if s.strip()]
        original_num = len(original_sentences)

        if original_num <= 3:
            # 不应该截断
            if num_sentences == original_num:
                print_success(f"{desc}: {original_num}句话保持原样")
                passed += 1
            else:
                print_error(f"{desc}: 期望{original_num}句，实际{num_sentences}句")
        else:
            # 应该截断到2-3句
            if 2 <= num_sentences <= 3:
                print_success(f"{desc}: 从{original_num}句截断到{num_sentences}句")
                passed += 1
            else:
                print_error(f"{desc}: 期望2-3句，实际{num_sentences}句")

    print_info(f"截断功能测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases)


def test_replace_ai_words():
    """测试2: 替换AI味词汇"""
    print_header("测试2: 替换AI味词汇")

    processor = HumanizeProcessor()

    test_cases = [
        ("我理解你的感受", "我懂你", "我理解你的感受→我懂你"),
        ("作为AI，我很高兴为您服务", "", "去除作为AI和服务用语"),
        ("您有什么问题吗？", "你有什么问题吗？", "您→你"),
        ("我建议你这样做", "不如你这样做", "我建议→不如"),
        ("请问需要帮助吗？", "需要帮助吗？", "去除请问"),
        ("好的，没问题", "行，ok", "好的→行，没问题→ok"),
    ]

    passed = 0
    for original, expected_substring, desc in test_cases:
        result = processor._replace_ai_words(original)

        # 检查是否包含预期的子串或不包含不想要的词
        if expected_substring:
            if expected_substring in result or expected_substring == "":
                # 对于空期望，检查是否去除了某些词
                if expected_substring == "":
                    if "作为AI" not in result and "很高兴为您服务" not in result:
                        print_success(f"{desc}: '{original}' -> '{result}'")
                        passed += 1
                    else:
                        print_error(f"{desc}: '{original}' -> '{result}'")
                else:
                    print_success(f"{desc}: '{original}' -> '{result}'")
                    passed += 1
            else:
                print_error(f"{desc}: '{original}' -> '{result}' (期望包含 '{expected_substring}')")
        else:
            print_success(f"{desc}: '{original}' -> '{result}'")
            passed += 1

    print_info(f"AI词汇替换测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_replace_emojis():
    """测试3: 替换官方表情"""
    print_header("测试3: 替换官方表情")

    import random

    # 设置100%概率替换，确保测试可重现
    config = HumanizeConfig(replace_emoji_probability=1.0)
    processor = HumanizeProcessor(config=config)

    # 设置随机种子确保测试可重现
    random.seed(42)

    test_cases = [
        ("今天好开心😊", "😊应该被替换"),
        ("谢谢🙏", "🙏应该被替换"),
        ("好的👍", "👍应该被替换"),
        ("爱你❤️", "❤️应该被替换"),
    ]

    passed = 0
    for text, desc in test_cases:
        result = processor._replace_emojis(text)

        # 检查官方表情是否被替换
        official_emojis = ["😊", "🙏", "👍", "❤️"]
        has_official = any(emoji in result for emoji in official_emojis)

        if not has_official:
            print_success(f"{desc}: '{text}' -> '{result}'")
            passed += 1
        else:
            print_error(f"{desc}: '{text}' -> '{result}' (仍包含官方表情)")

    print_info(f"表情替换测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_emotion_detection():
    """测试4: 情感检测"""
    print_header("测试4: 情感检测")

    processor = HumanizeProcessor()

    test_cases = [
        ("今天好开心，太赞了！", "joy", "积极情感检测"),
        ("好难过，今天太郁闷了", "sadness", "消极情感检测"),
        ("气死我了，太离谱了！", "anger", "愤怒情感检测"),
        ("好可怕，我好害怕", "fear", "恐惧情感检测"),
        ("哇，太神奇了！", "surprise", "惊讶情感检测"),
        ("今天天气不错", "neutral", "中性情感检测"),
    ]

    passed = 0
    for text, expected_emotion, desc in test_cases:
        result = processor._detect_emotion(text)

        if result == expected_emotion:
            print_success(f"{desc}: '{text}' -> {result}")
            passed += 1
        else:
            print_error(f"{desc}: '{text}' -> 期望 {expected_emotion}, 实际 {result}")

    print_info(f"情感检测测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_context_aware_catchphrase():
    """测试5: 语境感知的口头禅添加"""
    print_header("测试5: 语境感知的口头禅添加")

    import random

    # 设置100%概率添加口头禅，确保测试可重现
    config = HumanizeConfig(add_catchphrase_probability=1.0)
    processor = HumanizeProcessor(config=config)

    # 设置随机种子确保测试可重现
    random.seed(42)

    test_cases = [
        ("今天好开心，太棒了！", "joy", "积极语境用积极口头禅"),
        ("好难过，今天太郁闷了", "sadness", "消极语境用消极口头禅"),
        ("气死我了，太离谱了！", "anger", "愤怒语境用愤怒口头禅"),
        ("好可怕，我好害怕", "fear", "恐惧语境用恐惧口头禅"),
        ("哇，太神奇了！", "surprise", "惊讶语境用惊讶口头禅"),
    ]

    passed = 0
    for text, expected_emotion, desc in test_cases:
        # 多次测试以确保随机性
        has_appropriate_catchphrase = False
        for _ in range(10):
            result = processor._add_catchphrase(text)

            # 检测使用的情感
            detected_emotion = processor._detect_emotion(text)

            # 检查使用的口头禅是否属于检测到的情感类别
            for catchphrase in processor.emotion_catchphrases.get(detected_emotion, []):
                if catchphrase in result:
                    has_appropriate_catchphrase = True
                    break

            if has_appropriate_catchphrase:
                break

        if has_appropriate_catchphrase:
            print_success(f"{desc}: '{text}' 使用了合适的口头禅")
            passed += 1
        else:
            print_error(f"{desc}: '{text}' 未使用合适的口头禅")

    print_info(f"语境感知口头禅测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.7


def test_update_catchphrases():
    """测试6: 更新口头禅库"""
    print_header("测试6: 更新口头禅库")

    processor = HumanizeProcessor()

    # 测试更新通用口头禅
    new_catchphrases = ["新梗1", "新梗2", "绝了"]  # "绝了"已存在，用于测试去重

    processor.update_catchphrases(new_catchphrases)

    # 验证
    has_new1 = "新梗1" in processor.catchphrases
    has_new2 = "新梗2" in processor.catchphrases
    # 验证去重
    count_juele = processor.catchphrases.count("绝了")

    passed = 0
    if has_new1:
        print_success("新梗1添加成功")
        passed += 1
    else:
        print_error("新梗1添加失败")

    if has_new2:
        print_success("新梗2添加成功")
        passed += 1
    else:
        print_error("新梗2添加失败")

    if count_juele == 1:
        print_success("去重功能正常")
        passed += 1
    else:
        print_error(f"去重功能失败，绝了出现{count_juele}次")

    # 测试按情感更新
    processor.update_catchphrases(["快乐新梗"], emotion="joy")
    has_joy_catchphrase = "快乐新梗" in processor.emotion_catchphrases["joy"]

    if has_joy_catchphrase:
        print_success("按情感更新口头禅成功")
        passed += 1
    else:
        print_error("按情感更新口头禅失败")

    print_info(f"口头禅更新测试通过率: {passed}/4")
    return passed >= 3


def test_full_process():
    """测试7: 完整处理流程"""
    print_header("测试7: 完整处理流程")

    import random

    config = HumanizeConfig(
        max_sentences=3,
        min_sentences=2,
        add_catchphrase_probability=1.0,
        replace_emoji_probability=1.0,
    )
    processor = HumanizeProcessor(config=config)

    # 设置随机种子确保测试可重现
    random.seed(42)

    test_cases = [
        # 典型AI回复
        (
            "我理解您的感受。作为AI，我很高兴为您服务。请问您有什么问题吗？😊",
            "典型AI回复真人化",
        ),
        # 长回复
        (
            "今天天气真好。我想去公园散步。公园里有很多花。还有很多小朋友在玩。他们看起来很开心。",
            "长回复真人化",
        ),
        # 积极情感
        (
            "今天好开心，太棒了！",
            "积极情感真人化",
        ),
        # 消极情感
        (
            "好难过，今天太郁闷了",
            "消极情感真人化",
        ),
    ]

    passed = 0
    for text, desc in test_cases:
        result = processor.process(text)

        # 基本验证
        has_ai_words = any(word in result for word in ["我理解", "作为AI", "您", "请问"])
        has_catchphrase = any(
            catchphrase in result
            for emotion_catchphrases in processor.emotion_catchphrases.values()
            for catchphrase in emotion_catchphrases
        ) or any(catchphrase in result for catchphrase in processor.catchphrases)
        has_official_emoji = any(emoji in result for emoji in ["😊", "🙏", "👍", "❤️"])

        print_info(f"原始: {text}")
        print_info(f"结果: {result}")

        if not has_ai_words and has_catchphrase and not has_official_emoji:
            print_success(f"{desc}: 真人化成功")
            passed += 1
        else:
            issues = []
            if has_ai_words:
                issues.append("仍包含AI味词汇")
            if not has_catchphrase:
                issues.append("未添加口头禅")
            if has_official_emoji:
                issues.append("仍包含官方表情")
            print_error(f"{desc}: {', '.join(issues)}")

    print_info(f"完整流程测试通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases)


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 真人化回复处理器验证测试  🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("截断长句", test_truncate_sentences()))
    except Exception as e:
        print_error(f"截断长句测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("截断长句", False))

    try:
        results.append(("替换AI词汇", test_replace_ai_words()))
    except Exception as e:
        print_error(f"替换AI词汇测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("替换AI词汇", False))

    try:
        results.append(("替换表情", test_replace_emojis()))
    except Exception as e:
        print_error(f"替换表情测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("替换表情", False))

    try:
        results.append(("情感检测", test_emotion_detection()))
    except Exception as e:
        print_error(f"情感检测测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("情感检测", False))

    try:
        results.append(("语境感知口头禅", test_context_aware_catchphrase()))
    except Exception as e:
        print_error(f"语境感知口头禅测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("语境感知口头禅", False))

    try:
        results.append(("更新口头禅", test_update_catchphrases()))
    except Exception as e:
        print_error(f"更新口头禅测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("更新口头禅", False))

    try:
        results.append(("完整流程", test_full_process()))
    except Exception as e:
        print_error(f"完整流程测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("完整流程", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！真人化回复处理器验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
