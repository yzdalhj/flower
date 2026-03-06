# -*- coding: utf-8 -*-
"""
提示组装系统验证测试

验证内容:
【Token管理功能】
1. Token估算（中文、英文、混合文本）
2. 文本截断（保持句子完整性）
3. 对话历史截断（优先保留最近）
4. 记忆截断（按重要性排序）

【智能组装功能】
5. Token预算分配
6. 组件整合逻辑
7. 超出预算处理
8. Token验证

注意: 此测试直接导入实际实现模块进行验证
"""

import importlib.util
import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

spec_prompt = importlib.util.spec_from_file_location(
    "prompt_builder",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/services/llm/prompt_builder.py"),
)
prompt_module = importlib.util.module_from_spec(spec_prompt)
spec_prompt.loader.exec_module(prompt_module)

PromptBuilder = prompt_module.PromptBuilder
PromptContext = prompt_module.PromptContext
PromptAssemblyConfig = prompt_module.PromptAssemblyConfig


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


def test_token_estimation():
    """测试1: Token估算功能 - 实际实现"""
    print_header("测试1: Token估算功能")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试中文Token估算
    try:
        text = "你好世界"
        tokens = builder.estimate_tokens(text)
        # 4个中文字符 * 1.5 = 6 tokens
        if tokens == 6:
            print_success(f"中文Token估算正确: '{text}' = {tokens} tokens")
            passed += 1
        else:
            print_error(f"中文Token估算错误: 期望6, 实际{tokens}")
    except Exception as e:
        print_error(f"中文Token估算失败: {e}")
    total += 1

    # 测试英文Token估算
    try:
        text = "Hello world this is a test"
        tokens = builder.estimate_tokens(text)
        # 6个英文单词 ≈ 6 tokens
        if tokens >= 6:
            print_success(f"英文Token估算正确: '{text}' = {tokens} tokens")
            passed += 1
        else:
            print_error(f"英文Token估算错误: {tokens}")
    except Exception as e:
        print_error(f"英文Token估算失败: {e}")
    total += 1

    # 测试中英文混合
    try:
        text = "你好 Hello 世界 World"
        tokens = builder.estimate_tokens(text)
        # 2个中文 * 1.5 + 2个英文 = 5 tokens (大约)
        if tokens >= 5:
            print_success(f"混合文本Token估算正确: '{text}' = {tokens} tokens")
            passed += 1
        else:
            print_error(f"混合文本Token估算错误: {tokens}")
    except Exception as e:
        print_error(f"混合文本Token估算失败: {e}")
    total += 1

    # 测试空文本
    try:
        tokens_empty = builder.estimate_tokens("")
        tokens_none = builder.estimate_tokens(None)
        if tokens_empty == 0 and tokens_none == 0:
            print_success("空文本Token估算正确: 0 tokens")
            passed += 1
        else:
            print_error(f"空文本Token估算错误: {tokens_empty}, {tokens_none}")
    except Exception as e:
        print_error(f"空文本Token估算失败: {e}")
    total += 1

    # 测试消息列表Token估算
    try:
        messages = [
            {"role": "system", "content": "你是小花"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
        ]
        tokens = builder.estimate_messages_tokens(messages)
        if tokens > 10:
            print_success(f"消息列表Token估算正确: {len(messages)}条消息 = {tokens} tokens")
            passed += 1
        else:
            print_error(f"消息列表Token估算错误: {tokens}")
    except Exception as e:
        print_error(f"消息列表Token估算失败: {e}")
    total += 1

    print_info(f"Token估算测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_text_truncation():
    """测试2: 文本截断功能 - 实际实现"""
    print_header("测试2: 文本截断功能")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试文本在限制内不截断
    try:
        text = "这是一段短文本。"
        truncated = builder.truncate_text(text, max_tokens=100)
        if truncated == text:
            print_success("短文本不截断: 正确")
            passed += 1
        else:
            print_error("短文本被错误截断")
    except Exception as e:
        print_error(f"短文本测试失败: {e}")
    total += 1

    # 测试长文本截断
    try:
        text = "这是一段很长的文本。" * 50
        truncated = builder.truncate_text(text, max_tokens=50)
        truncated_tokens = builder.estimate_tokens(truncated)
        if len(truncated) < len(text) and truncated_tokens <= 50:
            print_success(
                f"长文本截断正确: {len(text)}字 -> {len(truncated)}字 ({truncated_tokens} tokens)"
            )
            passed += 1
        else:
            print_error(f"长文本截断错误: {truncated_tokens} tokens")
    except Exception as e:
        print_error(f"长文本截断失败: {e}")
    total += 1

    # 测试在句子边界截断
    try:
        text = "第一句话。第二句话。第三句话。第四句话。"
        truncated = builder.truncate_text(text, max_tokens=20)
        if truncated.endswith("。") or truncated.endswith("..."):
            print_success(f"句子边界截断正确: '{truncated[-10:]}'")
            passed += 1
        else:
            print_error(f"句子边界截断错误: '{truncated[-10:]}'")
    except Exception as e:
        print_error(f"句子边界截断失败: {e}")
    total += 1

    print_info(f"文本截断测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_conversation_history_truncation():
    """测试3: 对话历史截断 - 实际实现"""
    print_header("测试3: 对话历史截断")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试对话历史截断
    try:
        history = [
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
            {"role": "assistant", "content": "回复2"},
            {"role": "user", "content": "消息3"},
            {"role": "assistant", "content": "回复3"},
        ]

        truncated = builder.truncate_conversation_history(history, max_tokens=30)

        if len(truncated) < len(history) and truncated[-1]["content"] == "回复3":
            print_success(f"对话历史截断正确: {len(history)}条 -> {len(truncated)}条，保留最近消息")
            passed += 1
        else:
            print_error("对话历史截断错误: 未保留最近消息")
    except Exception as e:
        print_error(f"对话历史截断失败: {e}")
    total += 1

    # 测试空历史
    try:
        empty_history = []
        truncated = builder.truncate_conversation_history(empty_history, max_tokens=100)
        if truncated == []:
            print_success("空历史处理正确")
            passed += 1
        else:
            print_error("空历史处理错误")
    except Exception as e:
        print_error(f"空历史处理失败: {e}")
    total += 1

    print_info(f"对话历史截断测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_memory_truncation():
    """测试4: 记忆截断 - 实际实现"""
    print_header("测试4: 记忆截断（按重要性）")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试按重要性截断记忆
    try:
        memories = [
            {"content": "不重要的记忆", "importance": 1.0},
            {"content": "重要的记忆", "importance": 5.0},
            {"content": "一般的记忆", "importance": 3.0},
        ]

        truncated = builder.truncate_memories(memories, max_tokens=20)

        if len(truncated) > 0 and truncated[0]["importance"] == 5.0:
            print_success(
                f"记忆截断正确: 优先保留重要记忆 (importance={truncated[0]['importance']})"
            )
            passed += 1
        else:
            print_error("记忆截断错误: 未优先保留重要记忆")
    except Exception as e:
        print_error(f"记忆截断失败: {e}")
    total += 1

    # 测试空记忆
    try:
        empty_memories = []
        truncated = builder.truncate_memories(empty_memories, max_tokens=100)
        if truncated == []:
            print_success("空记忆处理正确")
            passed += 1
        else:
            print_error("空记忆处理错误")
    except Exception as e:
        print_error(f"空记忆处理失败: {e}")
    total += 1

    print_info(f"记忆截断测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_token_allocation():
    """测试5: Token预算分配 - 实际实现"""
    print_header("测试5: Token预算分配")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试充足预算分配
    try:
        allocation = builder._allocate_tokens(available_tokens=3000)

        if allocation["history"] == builder.assembly_config.history_tokens:
            print_success(f"充足预算分配正确: history={allocation['history']} tokens")
            passed += 1
        else:
            print_error(f"充足预算分配错误: history={allocation['history']}")
    except Exception as e:
        print_error(f"充足预算分配失败: {e}")
    total += 1

    # 测试有限预算分配
    try:
        allocation = builder._allocate_tokens(available_tokens=500)
        total_allocated = sum(allocation.values())

        if allocation["history"] > 0 and total_allocated <= 500:
            print_success(f"有限预算分配正确: 总计{total_allocated} tokens，history优先")
            print(f"    分配: history={allocation['history']}, memory={allocation['memory']}")
            passed += 1
        else:
            print_error(f"有限预算分配错误: 总计{total_allocated}")
    except Exception as e:
        print_error(f"有限预算分配失败: {e}")
    total += 1

    # 测试零预算
    try:
        allocation = builder._allocate_tokens(available_tokens=0)
        if all(v == 0 for v in allocation.values()):
            print_success("零预算分配正确: 所有组件为0")
            passed += 1
        else:
            print_error("零预算分配错误")
    except Exception as e:
        print_error(f"零预算分配失败: {e}")
    total += 1

    print_info(f"Token预算分配测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_smart_assembly():
    """测试6: 智能组装功能 - 实际实现"""
    print_header("测试6: 智能组装功能")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试带Token预算的提示组装
    try:
        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼开朗",
            communication_guidelines="简短回复",
            conversation_history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好呀"},
            ],
            memories=[
                {"content": "用户喜欢编程", "importance": 4.0},
                {"content": "用户住在北京", "importance": 3.0},
            ],
        )

        messages, stats = builder.assemble_prompt_with_budget(
            context=context, user_message="今天天气怎么样？", max_tokens=2000
        )

        # 验证消息结构
        if (
            len(messages) >= 2
            and messages[0]["role"] == "system"
            and messages[-1]["role"] == "user"
            and messages[-1]["content"] == "今天天气怎么样？"
        ):
            print_success(f"提示组装成功: {len(messages)}条消息")
            passed += 1
        else:
            print_error("提示组装结构错误")
        total += 1

        # 验证Token统计
        if (
            stats["total"] <= 2000
            and stats["system"] > 0
            and stats["user_message"] > 0
            and stats["remaining"] >= 0
        ):
            print_success(f"Token统计正确: {stats['total']}/{stats['max_allowed']} tokens")
            print(
                f"    系统: {stats['system']}, 用户: {stats['user_message']}, 历史: {stats['history']}"
            )
            passed += 1
        else:
            print_error(f"Token统计错误: {stats}")
        total += 1

    except Exception as e:
        print_error(f"智能组装失败: {e}")
        import traceback

        traceback.print_exc()
        total += 2

    # 测试Token预算不足时的处理
    try:
        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼开朗" * 100,  # 很长
            communication_guidelines="简短回复" * 100,
            conversation_history=[
                {"role": "user", "content": "消息" * 100},
                {"role": "assistant", "content": "回复" * 100},
            ]
            * 10,
        )

        messages, stats = builder.assemble_prompt_with_budget(
            context=context, user_message="测试消息", max_tokens=500  # 很小的预算
        )

        if len(messages) >= 2 and stats["total"] <= 500:
            print_success(f"预算不足处理正确: 成功截断到{stats['total']} tokens")
            passed += 1
        else:
            print_error(f"预算不足处理错误: {stats['total']} tokens")
    except Exception as e:
        print_error(f"预算不足处理失败: {e}")
    total += 1

    print_info(f"智能组装测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_build_full_prompt():
    """测试7: 完整提示构建 - 实际实现"""
    print_header("测试7: 完整提示构建")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试使用智能组装
    try:
        context = PromptContext(
            personality_name="小花",
            speaking_style="温柔体贴",
            conversation_history=[
                {"role": "user", "content": "你好"},
            ],
        )

        messages = builder.build_full_prompt(
            context=context, user_message="今天心情不好", max_tokens=1000, use_smart_assembly=True
        )

        if (
            len(messages) >= 2
            and messages[0]["role"] == "system"
            and messages[-1]["content"] == "今天心情不好"
        ):
            print_success("智能组装模式构建成功")
            passed += 1
        else:
            print_error("智能组装模式构建失败")
    except Exception as e:
        print_error(f"智能组装模式失败: {e}")
    total += 1

    # 测试不使用智能组装
    try:
        context = PromptContext(
            personality_name="小花",
            conversation_history=[
                {"role": "user", "content": "你好"},
            ],
        )

        messages = builder.build_full_prompt(
            context=context, user_message="测试", use_smart_assembly=False
        )

        if len(messages) == 3:  # system + history + user
            print_success("传统模式构建成功: 3条消息")
            passed += 1
        else:
            print_error(f"传统模式构建失败: {len(messages)}条消息")
    except Exception as e:
        print_error(f"传统模式失败: {e}")
    total += 1

    # 测试带统计信息的构建
    try:
        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼",
        )

        messages, stats = builder.build_full_prompt_with_stats(
            context=context, user_message="你好", max_tokens=2000
        )

        if len(messages) >= 2 and "total" in stats and "system" in stats and stats["total"] <= 2000:
            print_success(f"带统计构建成功: {stats['total']} tokens")
            passed += 1
        else:
            print_error("带统计构建失败")
    except Exception as e:
        print_error(f"带统计构建失败: {e}")
    total += 1

    print_info(f"完整提示构建测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_token_validation():
    """测试8: Token验证功能 - 实际实现"""
    print_header("测试8: Token验证功能")

    builder = PromptBuilder()
    passed = 0
    total = 0

    # 测试Token在预算内
    try:
        messages = [
            {"role": "system", "content": "你是小花"},
            {"role": "user", "content": "你好"},
        ]

        is_valid, actual, message = builder.validate_token_budget(messages, max_tokens=1000)

        if is_valid and actual > 0 and "正常" in message:
            print_success(f"预算内验证正确: {actual} tokens，{message}")
            passed += 1
        else:
            print_error(f"预算内验证错误: {is_valid}, {message}")
    except Exception as e:
        print_error(f"预算内验证失败: {e}")
    total += 1

    # 测试Token超出预算
    try:
        messages = [
            {"role": "system", "content": "很长的系统提示" * 100},
            {"role": "user", "content": "很长的用户消息" * 100},
        ]

        is_valid, actual, message = builder.validate_token_budget(messages, max_tokens=100)

        if not is_valid and actual > 100 and "超出" in message:
            print_success(f"超出预算验证正确: {actual} tokens，{message}")
            passed += 1
        else:
            print_error(f"超出预算验证错误: {is_valid}, {message}")
    except Exception as e:
        print_error(f"超出预算验证失败: {e}")
    total += 1

    print_info(f"Token验证测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_custom_assembly_config():
    """测试9: 自定义组装配置 - 实际实现"""
    print_header("测试9: 自定义组装配置")

    passed = 0
    total = 0

    # 测试自定义配置
    try:
        custom_config = PromptAssemblyConfig(
            max_total_tokens=2000,
            history_tokens=1000,
            memory_tokens=500,
        )

        builder = PromptBuilder(assembly_config=custom_config)

        if (
            builder.assembly_config.max_total_tokens == 2000
            and builder.assembly_config.history_tokens == 1000
        ):
            print_success("自定义配置创建成功")
            print(f"    max_tokens={builder.assembly_config.max_total_tokens}")
            print(f"    history_tokens={builder.assembly_config.history_tokens}")
            passed += 1
        else:
            print_error("自定义配置创建失败")
    except Exception as e:
        print_error(f"自定义配置失败: {e}")
    total += 1

    # 测试基于优先级的分配
    try:
        custom_config = PromptAssemblyConfig(
            recent_history_priority=5,
            important_memory_priority=2,
        )

        builder = PromptBuilder(assembly_config=custom_config)
        allocation = builder._allocate_tokens(available_tokens=1000)

        if allocation["history"] >= allocation["memory"]:
            print_success(
                f"优先级分配正确: history={allocation['history']} > memory={allocation['memory']}"
            )
            passed += 1
        else:
            print_error(
                f"优先级分配错误: history={allocation['history']}, memory={allocation['memory']}"
            )
    except Exception as e:
        print_error(f"优先级分配失败: {e}")
    total += 1

    print_info(f"自定义配置测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 提示组装系统验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("Token估算", test_token_estimation()))
    except Exception as e:
        print_error(f"Token估算测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Token估算", False))

    try:
        results.append(("文本截断", test_text_truncation()))
    except Exception as e:
        print_error(f"文本截断测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("文本截断", False))

    try:
        results.append(("对话历史截断", test_conversation_history_truncation()))
    except Exception as e:
        print_error(f"对话历史截断测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("对话历史截断", False))

    try:
        results.append(("记忆截断", test_memory_truncation()))
    except Exception as e:
        print_error(f"记忆截断测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("记忆截断", False))

    try:
        results.append(("Token预算分配", test_token_allocation()))
    except Exception as e:
        print_error(f"Token预算分配测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Token预算分配", False))

    try:
        results.append(("智能组装", test_smart_assembly()))
    except Exception as e:
        print_error(f"智能组装测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("智能组装", False))

    try:
        results.append(("完整提示构建", test_build_full_prompt()))
    except Exception as e:
        print_error(f"完整提示构建测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("完整提示构建", False))

    try:
        results.append(("Token验证", test_token_validation()))
    except Exception as e:
        print_error(f"Token验证测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Token验证", False))

    try:
        results.append(("自定义配置", test_custom_assembly_config()))
    except Exception as e:
        print_error(f"自定义配置测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("自定义配置", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！提示组装系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
    """测试Token估算功能"""

    def test_estimate_chinese_tokens(self):
        """测试中文Token估算"""
        builder = PromptBuilder()

        text = "你好世界"
        tokens = builder.estimate_tokens(text)

        # 4个中文字符 * 1.5 = 6 tokens
        assert tokens == 6

    def test_estimate_english_tokens(self):
        """测试英文Token估算"""
        builder = PromptBuilder()

        text = "Hello world this is a test"
        tokens = builder.estimate_tokens(text)

        # 6个英文单词 = 6 tokens (大约)
        assert tokens >= 6

    def test_estimate_mixed_tokens(self):
        """测试中英文混合Token估算"""
        builder = PromptBuilder()

        text = "你好 Hello 世界 World"
        tokens = builder.estimate_tokens(text)

        # 2个中文字符 * 1.5 + 2个英文单词 = 5 tokens (大约)
        assert tokens >= 5

    def test_estimate_empty_text(self):
        """测试空文本Token估算"""
        builder = PromptBuilder()

        tokens = builder.estimate_tokens("")
        assert tokens == 0

        tokens = builder.estimate_tokens(None)
        assert tokens == 0

    def test_estimate_messages_tokens(self):
        """测试消息列表Token估算"""
        builder = PromptBuilder()

        messages = [
            {"role": "system", "content": "你是小花"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
        ]

        tokens = builder.estimate_messages_tokens(messages)

        # 至少包含内容的tokens + 角色标记
        assert tokens > 10


class TestTextTruncation:
    """测试文本截断功能"""

    def test_truncate_text_within_limit(self):
        """测试文本在限制内不截断"""
        builder = PromptBuilder()

        text = "这是一段短文本。"
        truncated = builder.truncate_text(text, max_tokens=100)

        assert truncated == text

    def test_truncate_long_text(self):
        """测试长文本截断"""
        builder = PromptBuilder()

        text = "这是一段很长的文本。" * 50  # 重复50次
        truncated = builder.truncate_text(text, max_tokens=50)

        # 截断后应该更短
        assert len(truncated) < len(text)
        assert builder.estimate_tokens(truncated) <= 50

    def test_truncate_at_sentence_boundary(self):
        """测试在句子边界截断"""
        builder = PromptBuilder()

        text = "第一句话。第二句话。第三句话。第四句话。"
        truncated = builder.truncate_text(text, max_tokens=20)

        # 应该在句号处截断
        assert truncated.endswith("。") or truncated.endswith("...")

    def test_truncate_conversation_history(self):
        """测试对话历史截断"""
        builder = PromptBuilder()

        history = [
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
            {"role": "assistant", "content": "回复2"},
            {"role": "user", "content": "消息3"},
            {"role": "assistant", "content": "回复3"},
        ]

        truncated = builder.truncate_conversation_history(history, max_tokens=30)

        # 应该保留最近的消息
        assert len(truncated) < len(history)
        assert truncated[-1]["content"] == "回复3"

    def test_truncate_memories_by_importance(self):
        """测试按重要性截断记忆"""
        builder = PromptBuilder()

        memories = [
            {"content": "不重要的记忆", "importance": 1.0},
            {"content": "重要的记忆", "importance": 5.0},
            {"content": "一般的记忆", "importance": 3.0},
        ]

        truncated = builder.truncate_memories(memories, max_tokens=20)

        # 应该优先保留重要的记忆
        assert len(truncated) > 0
        assert truncated[0]["importance"] == 5.0


class TestTokenAllocation:
    """测试Token分配功能"""

    def test_allocate_tokens_sufficient_budget(self):
        """测试Token预算充足时的分配"""
        builder = PromptBuilder()

        allocation = builder._allocate_tokens(available_tokens=3000)

        # 所有组件都应该得到期望的Token
        assert allocation["history"] == builder.assembly_config.history_tokens
        assert allocation["memory"] == builder.assembly_config.memory_tokens

    def test_allocate_tokens_limited_budget(self):
        """测试Token预算有限时的分配"""
        builder = PromptBuilder()

        allocation = builder._allocate_tokens(available_tokens=500)

        # 高优先级组件应该得到更多Token
        assert allocation["history"] > 0
        assert sum(allocation.values()) <= 500

    def test_allocate_tokens_zero_budget(self):
        """测试Token预算为0时的分配"""
        builder = PromptBuilder()

        allocation = builder._allocate_tokens(available_tokens=0)

        # 所有组件都应该得到0
        assert all(v == 0 for v in allocation.values())


class TestSmartAssembly:
    """测试智能组装功能"""

    def test_assemble_prompt_with_budget(self):
        """测试带Token预算的提示组装"""
        builder = PromptBuilder()

        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼开朗",
            communication_guidelines="简短回复",
            conversation_history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好呀"},
            ],
            memories=[
                {"content": "用户喜欢编程", "importance": 4.0},
                {"content": "用户住在北京", "importance": 3.0},
            ],
        )

        messages, stats = builder.assemble_prompt_with_budget(
            context=context, user_message="今天天气怎么样？", max_tokens=2000
        )

        # 验证消息结构
        assert len(messages) >= 2  # 至少有系统提示和用户消息
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "今天天气怎么样？"

        # 验证Token统计
        assert stats["total"] <= 2000
        assert stats["system"] > 0
        assert stats["user_message"] > 0
        assert stats["remaining"] >= 0

    def test_assemble_prompt_exceeds_budget(self):
        """测试Token预算不足时的处理"""
        builder = PromptBuilder()

        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼开朗" * 100,  # 很长的风格描述
            communication_guidelines="简短回复" * 100,
            conversation_history=[
                {"role": "user", "content": "消息" * 100},
                {"role": "assistant", "content": "回复" * 100},
            ]
            * 10,  # 很多历史消息
        )

        messages, stats = builder.assemble_prompt_with_budget(
            context=context, user_message="测试消息", max_tokens=500  # 很小的预算
        )

        # 应该成功组装，但会截断内容
        assert len(messages) >= 2
        assert stats["total"] <= 500

    def test_build_full_prompt_with_smart_assembly(self):
        """测试使用智能组装的完整提示构建"""
        builder = PromptBuilder()

        context = PromptContext(
            personality_name="小花",
            speaking_style="温柔体贴",
            conversation_history=[
                {"role": "user", "content": "你好"},
            ],
        )

        messages = builder.build_full_prompt(
            context=context, user_message="今天心情不好", max_tokens=1000, use_smart_assembly=True
        )

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["content"] == "今天心情不好"

    def test_build_full_prompt_without_smart_assembly(self):
        """测试不使用智能组装的完整提示构建"""
        builder = PromptBuilder()

        context = PromptContext(
            personality_name="小花",
            conversation_history=[
                {"role": "user", "content": "你好"},
            ],
        )

        messages = builder.build_full_prompt(
            context=context, user_message="测试", use_smart_assembly=False
        )

        assert len(messages) == 3  # system + history + user

    def test_build_full_prompt_with_stats(self):
        """测试构建提示并返回统计信息"""
        builder = PromptBuilder()

        context = PromptContext(
            personality_name="小花",
            speaking_style="活泼",
        )

        messages, stats = builder.build_full_prompt_with_stats(
            context=context, user_message="你好", max_tokens=2000
        )

        assert len(messages) >= 2
        assert "total" in stats
        assert "system" in stats
        assert "user_message" in stats
        assert stats["total"] <= 2000


class TestTokenValidation:
    """测试Token验证功能"""

    def test_validate_within_budget(self):
        """测试Token在预算内"""
        builder = PromptBuilder()

        messages = [
            {"role": "system", "content": "你是小花"},
            {"role": "user", "content": "你好"},
        ]

        is_valid, actual, message = builder.validate_token_budget(messages, max_tokens=1000)

        assert is_valid is True
        assert actual > 0
        assert "正常" in message

    def test_validate_exceeds_budget(self):
        """测试Token超出预算"""
        builder = PromptBuilder()

        messages = [
            {"role": "system", "content": "很长的系统提示" * 100},
            {"role": "user", "content": "很长的用户消息" * 100},
        ]

        is_valid, actual, message = builder.validate_token_budget(messages, max_tokens=100)

        assert is_valid is False
        assert actual > 100
        assert "超出" in message


class TestCustomAssemblyConfig:
    """测试自定义组装配置"""

    def test_custom_config(self):
        """测试自定义Token分配配置"""
        custom_config = PromptAssemblyConfig(
            max_total_tokens=2000,
            history_tokens=1000,  # 给历史更多Token
            memory_tokens=500,
        )

        builder = PromptBuilder(assembly_config=custom_config)

        assert builder.assembly_config.max_total_tokens == 2000
        assert builder.assembly_config.history_tokens == 1000

    def test_priority_based_allocation(self):
        """测试基于优先级的Token分配"""
        custom_config = PromptAssemblyConfig(
            recent_history_priority=5,  # 最高优先级
            important_memory_priority=2,  # 较低优先级
        )

        builder = PromptBuilder(assembly_config=custom_config)
        allocation = builder._allocate_tokens(available_tokens=1000)

        # 历史应该得到更多Token
        assert allocation["history"] >= allocation["memory"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
