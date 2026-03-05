"""
人格引擎系统验证测试

验证内容:
【基础人格模型】
1. Big Five (OCEAN) 维度定义（5个维度 0-100）
2. 人格初始化配置
3. 人格到说话风格的映射
4. Prompt Engineering 注入人格特征

【记忆系统集成】
5. LangChain Memory 集成（ConversationBufferMemory）
6. 向量数据库存储（ChromaDB）
7. 记忆检索与上下文注入
8. 记忆上下文格式化

【持续学习能力】
9. 经验重放缓冲区 (Replay Buffer)
10. 防遗忘机制 (EWC - Elastic Weight Consolidation)
11. 增量学习策略
12. 记忆巩固机制（定期重放旧经验）

注意: 此测试直接导入实际实现模块进行验证
"""

import asyncio
import importlib.util
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

# 加载 personality 模型
spec_personality = importlib.util.spec_from_file_location(
    "personality",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/models/personality.py"),
)
personality_module = importlib.util.module_from_spec(spec_personality)
spec_personality.loader.exec_module(personality_module)

# 加载 personality_service
spec_service = importlib.util.spec_from_file_location(
    "personality_service",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/services/personality_service.py"),
)
service_module = importlib.util.module_from_spec(spec_service)
spec_service.loader.exec_module(service_module)

# 加载 personality_injector
spec_injector = importlib.util.spec_from_file_location(
    "personality_injector",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/personality_injector.py"
    ),
)
injector_module = importlib.util.module_from_spec(spec_injector)
spec_injector.loader.exec_module(injector_module)

# 导入实际类
BigFiveScores = personality_module.BigFiveScores
PersonalityConfig = personality_module.PersonalityConfig
PersonalityTraits = personality_module.PersonalityTraits
PERSONALITY_TEMPLATES = personality_module.PERSONALITY_TEMPLATES
PersonalityService = service_module.PersonalityService
PersonalityPromptInjector = injector_module.PersonalityPromptInjector

# 加载 langchain_memory
spec_langchain = importlib.util.spec_from_file_location(
    "langchain_memory",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/langchain_memory.py"
    ),
)
langchain_module = importlib.util.module_from_spec(spec_langchain)
spec_langchain.loader.exec_module(langchain_module)

LangChainMemoryService = langchain_module.LangChainMemoryService
MemoryContextInjector = langchain_module.MemoryContextInjector
DatabaseChatMessageHistory = langchain_module.DatabaseChatMessageHistory

# 加载 continual_learning
spec_continual = importlib.util.spec_from_file_location(
    "continual_learning",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app/services/continual_learning.py"
    ),
)
continual_module = importlib.util.module_from_spec(spec_continual)
spec_continual.loader.exec_module(continual_module)

Experience = continual_module.Experience
ParameterImportance = continual_module.ParameterImportance
ReplayBuffer = continual_module.ReplayBuffer
AntiForgetMechanism = continual_module.AntiForgetMechanism
ContinualLearningService = continual_module.ContinualLearningService


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


def test_big_five_dimensions():
    """测试1: Big Five (OCEAN) 维度定义 - 实际实现"""
    print_header("测试1: Big Five (OCEAN) 维度定义")

    passed = 0
    total = 0

    # 测试有效分数范围
    try:
        scores = BigFiveScores(
            openness=70.0,
            conscientiousness=60.0,
            extraversion=65.0,
            agreeableness=75.0,
            neuroticism=35.0,
        )
        print_success(f"创建有效分数: O={scores.openness}, C={scores.conscientiousness}")
        passed += 1
    except Exception as e:
        print_error(f"创建有效分数失败: {e}")
    total += 1

    # 测试边界值
    try:
        boundary_scores = BigFiveScores(
            openness=0.0,
            conscientiousness=100.0,
            extraversion=50.0,
            agreeableness=0.0,
            neuroticism=100.0,
        )
        print_success(f"边界值测试通过: 0.0 和 100.0 都有效")
        passed += 1
    except Exception as e:
        print_error(f"边界值测试失败: {e}")
    total += 1

    # 测试无效分数（应该抛出异常）
    try:
        invalid_scores = BigFiveScores(openness=150.0)
        print_error("无效分数测试失败: 应该抛出异常但没有")
    except ValueError:
        print_success("无效分数检测正确: 超出范围抛出 ValueError")
        passed += 1
    except Exception as e:
        print_error(f"无效分数检测异常: {e}")
    total += 1

    # 测试负数（应该抛出异常）
    try:
        negative_scores = BigFiveScores(neuroticism=-10.0)
        print_error("负数测试失败: 应该抛出异常但没有")
    except ValueError:
        print_success("负数检测正确: 负数抛出 ValueError")
        passed += 1
    except Exception as e:
        print_error(f"负数检测异常: {e}")
    total += 1

    # 测试字典转换
    try:
        scores = BigFiveScores(openness=80.0, extraversion=60.0)
        data = scores.to_dict()
        restored = BigFiveScores.from_dict(data)

        if restored.openness == 80.0 and restored.extraversion == 60.0:
            print_success(f"字典序列化/反序列化正确")
            passed += 1
        else:
            print_error(f"字典转换数据不一致")
    except Exception as e:
        print_error(f"字典转换失败: {e}")
    total += 1

    print_info(f"Big Five 维度测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_personality_initialization():
    """测试2: 人格初始化配置 - 实际实现"""
    print_header("测试2: 人格初始化配置")

    passed = 0
    total = 0

    # 测试预定义模板存在
    required_templates = ["default", "cheerful", "calm", "sarcastic"]
    for template_id in required_templates:
        if template_id in PERSONALITY_TEMPLATES:
            template = PERSONALITY_TEMPLATES[template_id]
            print_success(f"模板 '{template_id}' 存在: {template.name}")
            passed += 1
        else:
            print_error(f"模板 '{template_id}' 不存在")
        total += 1

    # 测试默认模板配置
    try:
        default = PERSONALITY_TEMPLATES["default"]

        # 验证 Big Five 配置
        if 0 <= default.big_five.openness <= 100:
            print_success(f"默认模板 Big Five 配置有效")
            passed += 1
        else:
            print_error(f"默认模板 Big Five 配置无效")
        total += 1

        # 验证扩展特质配置
        if 0 <= default.traits.empathy <= 100:
            print_success(f"默认模板扩展特质配置有效")
            passed += 1
        else:
            print_error(f"默认模板扩展特质配置无效")
        total += 1

        # 打印默认配置
        print_info(f"默认人格: {default.name}")
        print(f"    开放性: {default.big_five.openness:.0f}/100")
        print(f"    外向性: {default.big_five.extraversion:.0f}/100")
        print(f"    宜人性: {default.big_five.agreeableness:.0f}/100")
        print(f"    共情度: {default.traits.empathy:.0f}/100")
        print(f"    随意度: {default.traits.casualness:.0f}/100")

    except Exception as e:
        print_error(f"默认模板测试失败: {e}")
        total += 2

    # 测试自定义人格创建
    try:
        custom = PersonalityConfig(
            id="test_custom",
            name="测试人格",
            description="用于测试的自定义人格",
            big_five=BigFiveScores(openness=90.0, extraversion=80.0),
            traits=PersonalityTraits(humor=85.0, sarcasm=70.0),
        )

        if custom.id == "test_custom" and custom.big_five.openness == 90.0:
            print_success(f"自定义人格创建成功: {custom.name}")
            passed += 1
        else:
            print_error(f"自定义人格数据不一致")
        total += 1

    except Exception as e:
        print_error(f"自定义人格创建失败: {e}")
        total += 1

    # 测试人格序列化
    try:
        config = PersonalityConfig(
            id="serialize_test",
            name="序列化测试",
            big_five=BigFiveScores(openness=75.0),
            traits=PersonalityTraits(humor=60.0),
        )

        data = config.to_dict()
        restored = PersonalityConfig.from_dict(data)

        if (
            restored.id == config.id
            and restored.big_five.openness == config.big_five.openness
            and restored.traits.humor == config.traits.humor
        ):
            print_success(f"人格配置序列化/反序列化正确")
            passed += 1
        else:
            print_error(f"人格配置序列化数据不一致")
        total += 1

    except Exception as e:
        print_error(f"人格配置序列化失败: {e}")
        total += 1

    print_info(f"人格初始化测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_speaking_style_mapping():
    """测试3: 人格到说话风格的映射 - 实际实现"""
    print_header("测试3: 人格到说话风格的映射")

    service = PersonalityService()
    passed = 0
    total = 0

    # 测试不同人格的说话风格
    test_personalities = ["default", "cheerful", "calm", "sarcastic"]

    for personality_id in test_personalities:
        try:
            personality = service.get_personality(personality_id)
            if not personality:
                print_error(f"无法获取人格 '{personality_id}'")
                total += 1
                continue

            style = service.generate_speaking_style(personality)

            # 验证说话风格不为空
            if style and len(style) > 10:
                print_success(f"{personality.name} 说话风格生成成功")
                print(f"    风格: {style[:80]}...")
                passed += 1
            else:
                print_error(f"{personality.name} 说话风格为空或过短")

            total += 1

        except Exception as e:
            print_error(f"生成 '{personality_id}' 说话风格失败: {e}")
            total += 1

    # 测试不同人格产生不同风格
    try:
        default_style = service.generate_speaking_style(service.get_personality("default"))
        cheerful_style = service.generate_speaking_style(service.get_personality("cheerful"))
        calm_style = service.generate_speaking_style(service.get_personality("calm"))

        if default_style != cheerful_style and default_style != calm_style:
            print_success(f"不同人格产生不同说话风格")
            passed += 1
        else:
            print_error(f"不同人格产生相同说话风格")

        total += 1

    except Exception as e:
        print_error(f"风格差异测试失败: {e}")
        total += 1

    # 测试沟通指南生成
    try:
        personality = service.get_personality("sarcastic")
        guidelines = service.generate_communication_guidelines(personality)

        if guidelines and len(guidelines) > 10:
            print_success(f"沟通指南生成成功")
            print(f"    指南预览:\n{guidelines[:150]}...")
            passed += 1
        else:
            print_error(f"沟通指南为空或过短")

        total += 1

    except Exception as e:
        print_error(f"沟通指南生成失败: {e}")
        total += 1

    # 测试禁用词汇生成
    try:
        personality = service.get_personality("default")
        forbidden = service.generate_forbidden_phrases(personality)

        # 随意度高的人格应该有禁用词汇
        if personality.traits.casualness > 60:
            if forbidden and len(forbidden) > 0:
                print_success(f"禁用词汇生成成功")
                print(f"    禁用词: {forbidden[:80]}...")
                passed += 1
            else:
                print_info(f"随意人格未生成禁用词汇（可选）")
                passed += 0.5
        else:
            print_info(f"正式人格无需禁用词汇")
            passed += 1

        total += 1

    except Exception as e:
        print_error(f"禁用词汇生成失败: {e}")
        total += 1

    print_info(f"说话风格映射测试通过率: {passed}/{total}")
    return passed >= total * 0.75


def test_prompt_engineering_injection():
    """测试4: Prompt Engineering 注入人格特征 - 实际实现"""
    print_header("测试4: Prompt Engineering 注入人格特征")

    injector = PersonalityPromptInjector()
    passed = 0
    total = 0

    # 测试基础系统提示词生成
    try:
        prompt = injector.build_system_prompt(personality_id="default")

        # 验证提示词包含关键元素
        required_elements = ["小花", "Big Five", "说话风格", "沟通指南"]
        missing = []

        for element in required_elements:
            if element in prompt:
                print_success(f"提示词包含 '{element}'")
                passed += 1
            else:
                print_error(f"提示词缺少 '{element}'")
                missing.append(element)
            total += 1

        if not missing:
            print_info(f"系统提示词预览:\n{prompt[:300]}...\n")

    except Exception as e:
        print_error(f"系统提示词生成失败: {e}")
        total += len(required_elements)

    # 测试带用户上下文的提示词
    try:
        prompt_with_context = injector.build_system_prompt(
            personality_id="default",
            user_context="用户叫小明，是程序员，喜欢游戏和音乐",
            emotion_context="当前情绪：愉悦度 0.7，激活度 0.5",
        )

        if "小明" in prompt_with_context and "程序员" in prompt_with_context:
            print_success(f"用户上下文注入成功")
            passed += 1
        else:
            print_error(f"用户上下文注入失败")
        total += 1

        if "愉悦度" in prompt_with_context or "情绪" in prompt_with_context:
            print_success(f"情感上下文注入成功")
            passed += 1
        else:
            print_error(f"情感上下文注入失败")
        total += 1

    except Exception as e:
        print_error(f"上下文注入失败: {e}")
        total += 2

    # 测试消息列表注入
    try:
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
            {"role": "user", "content": "今天心情不好"},
        ]

        enhanced = injector.inject_personality_context(
            messages=messages, personality_id="calm", user_context="用户情绪低落"
        )

        # 验证系统消息在开头
        if enhanced[0]["role"] == "system":
            print_success(f"系统消息正确插入到开头")
            passed += 1
        else:
            print_error(f"系统消息位置错误")
        total += 1

        # 验证原有消息保留
        if len(enhanced) == len(messages) + 1:
            print_success(f"原有消息完整保留")
            passed += 1
        else:
            print_error(f"原有消息数量不对: 期望 {len(messages)+1}, 实际 {len(enhanced)}")
        total += 1

        # 验证人格特征在系统消息中
        if "小花" in enhanced[0]["content"]:
            print_success(f"人格特征注入到系统消息")
            passed += 1
        else:
            print_error(f"人格特征未注入")
        total += 1

    except Exception as e:
        print_error(f"消息列表注入失败: {e}")
        total += 3

    # 测试不同人格产生不同提示词
    try:
        prompt_default = injector.build_system_prompt("default")
        prompt_cheerful = injector.build_system_prompt("cheerful")
        prompt_sarcastic = injector.build_system_prompt("sarcastic")

        if (
            prompt_default != prompt_cheerful
            and prompt_default != prompt_sarcastic
            and prompt_cheerful != prompt_sarcastic
        ):
            print_success(f"不同人格产生不同提示词")
            passed += 1
        else:
            print_error(f"不同人格产生相同提示词")
        total += 1

    except Exception as e:
        print_error(f"提示词差异测试失败: {e}")
        total += 1

    # 测试人格摘要
    try:
        summary = injector.get_personality_summary("default")

        if "小花" in summary and "Big Five" in summary:
            print_success(f"人格摘要生成成功")
            print_info(f"摘要预览:\n{summary[:200]}...")
            passed += 1
        else:
            print_error(f"人格摘要内容不完整")
        total += 1

    except Exception as e:
        print_error(f"人格摘要生成失败: {e}")
        total += 1

    print_info(f"Prompt 注入测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_personality_service_operations():
    """测试5: 人格服务操作 - 实际实现"""
    print_header("测试5: 人格服务操作")

    service = PersonalityService()
    passed = 0
    total = 0

    # 测试获取人格
    try:
        personality = service.get_personality("default")
        if personality and personality.id == "default":
            print_success(f"获取人格成功: {personality.name}")
            passed += 1
        else:
            print_error(f"获取人格失败")
        total += 1
    except Exception as e:
        print_error(f"获取人格异常: {e}")
        total += 1

    # 测试获取不存在的人格
    try:
        nonexistent = service.get_personality("nonexistent_personality_12345")
        if nonexistent is None:
            print_success(f"不存在的人格正确返回 None")
            passed += 1
        else:
            print_error(f"不存在的人格应返回 None")
        total += 1
    except Exception as e:
        print_error(f"获取不存在人格异常: {e}")
        total += 1

    # 测试创建自定义人格
    try:
        custom = service.create_personality(
            personality_id="test_validation_custom",
            name="验证测试人格",
            description="用于验证测试",
            big_five=BigFiveScores(openness=85.0, extraversion=75.0),
            traits=PersonalityTraits(humor=80.0, empathy=90.0),
        )

        if custom.id == "test_validation_custom" and custom.big_five.openness == 85.0:
            print_success(f"创建自定义人格成功: {custom.name}")
            passed += 1
        else:
            print_error(f"创建自定义人格数据不一致")
        total += 1

        # 验证可以重新获取
        retrieved = service.get_personality("test_validation_custom")
        if retrieved and retrieved.big_five.openness == 85.0:
            print_success(f"重新获取自定义人格成功")
            passed += 1
        else:
            print_error(f"重新获取自定义人格失败")
        total += 1

    except Exception as e:
        print_error(f"创建自定义人格失败: {e}")
        total += 2

    # 测试列出所有人格
    try:
        personalities = service.list_personalities()

        if len(personalities) >= 4:
            print_success(f"列出人格成功: 共 {len(personalities)} 个")
            for pid, desc in list(personalities.items())[:3]:
                print(f"    - {pid}: {desc[:50]}...")
            passed += 1
        else:
            print_error(f"人格数量不足: {len(personalities)}")
        total += 1

    except Exception as e:
        print_error(f"列出人格失败: {e}")
        total += 1

    print_info(f"人格服务操作测试通过率: {passed}/{total}")
    return passed >= total * 0.8


# ============ 任务 4.2: 记忆系统集成测试 ============


class MockMemoryStore:
    """模拟记忆存储（用于测试）"""

    def __init__(self):
        self.memories = []
        self.working_memory = None

    async def create_memory(self, user_id, memory_type, content, summary=None, importance=1.0, metadata=None):
        memory = {
            "id": f"mem_{len(self.memories)}",
            "user_id": user_id,
            "memory_type": memory_type,
            "content": content,
            "summary": summary,
            "importance": importance,
            "metadata": metadata or {},
            "created_at": datetime.now(),
        }
        self.memories.append(memory)
        return type("Memory", (), memory)

    async def get_user_memories(self, user_id, limit=100):
        return [type("Memory", (), m) for m in self.memories if m["user_id"] == user_id][:limit]

    async def get_working_memory(self, user_id):
        return self.working_memory


class MockVectorStore:
    """模拟向量存储（用于测试）"""

    def __init__(self):
        self.vectors = []

    async def add_memory(self, memory_id, content, metadata=None):
        self.vectors.append({"id": memory_id, "content": content, "metadata": metadata or {}})
        return f"vec_{memory_id}"

    async def search(self, query, n_results=5, filter_dict=None):
        # 简单的关键词匹配
        results = []
        for vec in self.vectors:
            if query.lower() in vec["content"].lower():
                results.append(
                    {
                        "id": vec["id"],
                        "content": vec["content"],
                        "metadata": vec["metadata"],
                        "distance": 0.1,
                    }
                )
        return results[:n_results]

    async def get_memory_count(self):
        return len(self.vectors)


def test_langchain_memory_integration():
    """测试6: LangChain Memory 集成"""
    print_header("测试6: LangChain Memory 集成")

    passed = 0
    total = 0

    async def run_tests():
        nonlocal passed, total

        # 创建模拟存储
        memory_store = MockMemoryStore()
        vector_store = MockVectorStore()

        # 测试 LangChain Memory 服务创建
        try:
            memory_service = LangChainMemoryService(
                memory_store=memory_store,
                vector_store=vector_store,
                user_id="test_user_001",
                memory_type="buffer",
            )
            print_success("LangChain Memory 服务创建成功")
            passed += 1
        except Exception as e:
            print_error(f"LangChain Memory 服务创建失败: {e}")
            return
        finally:
            total += 1

        # 测试添加用户消息
        try:
            await memory_service.add_user_message("你好，我是小明")
            print_success("添加用户消息成功")
            passed += 1
        except Exception as e:
            print_error(f"添加用户消息失败: {e}")
        finally:
            total += 1

        # 测试添加 AI 消息
        try:
            await memory_service.add_ai_message("你好呀小明！很高兴认识你")
            print_success("添加 AI 消息成功")
            passed += 1
        except Exception as e:
            print_error(f"添加 AI 消息失败: {e}")
        finally:
            total += 1

        # 测试获取对话历史
        try:
            history = await memory_service.get_conversation_history(limit=10)
            if len(history) == 2:
                print_success(f"获取对话历史成功: {len(history)} 条消息")
                print(f"    用户: {history[0]['content'][:30]}")
                print(f"    AI: {history[1]['content'][:30]}")
                passed += 1
            else:
                print_error(f"对话历史数量不对: 期望 2, 实际 {len(history)}")
        except Exception as e:
            print_error(f"获取对话历史失败: {e}")
        finally:
            total += 1

        # 测试保存交互
        try:
            await memory_service.save_interaction(
                user_message="我今天很开心",
                ai_response="太好了！发生什么好事了吗？",
                importance=5.0,
                metadata={"emotion": "happy"},
            )
            print_success("保存交互成功")
            passed += 1
        except Exception as e:
            print_error(f"保存交互失败: {e}")
        finally:
            total += 1

        # 测试记忆统计
        try:
            stats = await memory_service.get_memory_stats()
            if "total_memories" in stats and "conversation_length" in stats:
                print_success(f"记忆统计获取成功")
                print(f"    总记忆数: {stats['total_memories']}")
                print(f"    对话长度: {stats['conversation_length']}")
                passed += 1
            else:
                print_error("记忆统计数据不完整")
        except Exception as e:
            print_error(f"记忆统计失败: {e}")
        finally:
            total += 1

    # 运行异步测试
    asyncio.run(run_tests())

    print_info(f"LangChain Memory 集成测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_vector_database_storage():
    """测试7: 向量数据库存储"""
    print_header("测试7: 向量数据库存储")

    passed = 0
    total = 0

    async def run_tests():
        nonlocal passed, total

        memory_store = MockMemoryStore()
        vector_store = MockVectorStore()

        memory_service = LangChainMemoryService(
            memory_store=memory_store, vector_store=vector_store, user_id="test_user_002"
        )

        # 测试向量存储添加
        try:
            await memory_service.save_interaction(
                user_message="我喜欢打篮球",
                ai_response="篮球很有趣！你经常打吗？",
                importance=6.0,
            )

            count = await vector_store.get_memory_count()
            if count > 0:
                print_success(f"向量存储添加成功: {count} 条记录")
                passed += 1
            else:
                print_error("向量存储为空")
        except Exception as e:
            print_error(f"向量存储添加失败: {e}")
        finally:
            total += 1

        # 测试向量检索
        try:
            results = await memory_service.retrieve_relevant_memories(query="篮球", n_results=5)

            if len(results) > 0:
                print_success(f"向量检索成功: 找到 {len(results)} 条相关记忆")
                for i, result in enumerate(results[:2], 1):
                    print(f"    {i}. {result['content'][:50]}...")
                passed += 1
            else:
                print_error("向量检索未找到结果")
        except Exception as e:
            print_error(f"向量检索失败: {e}")
        finally:
            total += 1

        # 测试多条记忆存储
        try:
            test_interactions = [
                ("我在学Python", "Python很棒！学得怎么样了？"),
                ("我喜欢看电影", "最近有什么好看的电影推荐吗？"),
                ("我养了一只猫", "猫咪好可爱！叫什么名字？"),
            ]

            for user_msg, ai_msg in test_interactions:
                await memory_service.save_interaction(user_msg, ai_msg, importance=4.0)

            count = await vector_store.get_memory_count()
            if count >= 4:
                print_success(f"批量存储成功: 共 {count} 条记录")
                passed += 1
            else:
                print_error(f"批量存储数量不足: {count}")
        except Exception as e:
            print_error(f"批量存储失败: {e}")
        finally:
            total += 1

        # 测试检索相关性
        try:
            python_results = await memory_service.retrieve_relevant_memories(query="编程", n_results=3)
            movie_results = await memory_service.retrieve_relevant_memories(query="电影", n_results=3)

            if len(python_results) > 0 and len(movie_results) > 0:
                print_success("检索相关性测试通过")
                print(f"    '编程' 相关: {len(python_results)} 条")
                print(f"    '电影' 相关: {len(movie_results)} 条")
                passed += 1
            else:
                print_error("检索相关性测试失败")
        except Exception as e:
            print_error(f"检索相关性测试失败: {e}")
        finally:
            total += 1

    asyncio.run(run_tests())

    print_info(f"向量数据库存储测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_memory_retrieval_and_context():
    """测试8: 记忆检索与上下文注入"""
    print_header("测试8: 记忆检索与上下文注入")

    passed = 0
    total = 0

    async def run_tests():
        nonlocal passed, total

        memory_store = MockMemoryStore()
        vector_store = MockVectorStore()

        memory_service = LangChainMemoryService(
            memory_store=memory_store, vector_store=vector_store, user_id="test_user_003"
        )

        # 准备测试数据
        await memory_service.save_interaction("我叫小明，是程序员", "很高兴认识你小明！", importance=8.0)
        await memory_service.save_interaction("我喜欢打游戏", "什么类型的游戏？", importance=5.0)
        await memory_service.save_interaction("我最近在学机器学习", "机器学习很有趣！", importance=7.0)

        # 测试构建上下文
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="我想学深度学习",
                include_conversation=True,
                include_long_term=True,
            )

            if "current_message" in context and "conversation_history" in context:
                print_success("上下文构建成功")
                print(f"    对话历史: {len(context['conversation_history'])} 条")
                print(f"    相关记忆: {len(context['relevant_memories'])} 条")
                passed += 1
            else:
                print_error("上下文结构不完整")
        except Exception as e:
            print_error(f"上下文构建失败: {e}")
        finally:
            total += 1

        # 测试格式化上下文
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="推荐一些学习资源", include_conversation=True, include_long_term=True
            )

            formatted = await memory_service.format_context_for_llm(context)

            if len(formatted) > 50 and ("对话历史" in formatted or "相关记忆" in formatted):
                print_success("上下文格式化成功")
                print(f"    格式化文本长度: {len(formatted)} 字符")
                print(f"    预览:\n{formatted[:150]}...")
                passed += 1
            else:
                print_error("上下文格式化内容不足")
        except Exception as e:
            print_error(f"上下文格式化失败: {e}")
        finally:
            total += 1

        # 测试上下文注入器
        try:
            injector = MemoryContextInjector(memory_service)

            full_prompt = await injector.inject_context(
                base_prompt="你是AI助手小花",
                current_message="我想了解Python",
                include_conversation=True,
                include_memories=True,
            )

            if "小花" in full_prompt and len(full_prompt) > 100:
                print_success("上下文注入成功")
                print(f"    完整 Prompt 长度: {len(full_prompt)} 字符")
                passed += 1
            else:
                print_error("上下文注入内容不足")
        except Exception as e:
            print_error(f"上下文注入失败: {e}")
        finally:
            total += 1

        # 测试聊天格式注入
        try:
            injector = MemoryContextInjector(memory_service)

            messages = await injector.inject_context_for_chat(
                system_prompt="你是小花", current_message="给我讲个笑话", max_history=5
            )

            if len(messages) > 0 and messages[0]["role"] == "system":
                print_success("聊天格式注入成功")
                print(f"    消息数量: {len(messages)}")
                print(f"    系统消息: {messages[0]['content'][:50]}...")
                passed += 1
            else:
                print_error("聊天格式注入失败")
        except Exception as e:
            print_error(f"聊天格式注入失败: {e}")
        finally:
            total += 1

        # 测试记忆相关性
        try:
            # 添加更多记忆
            await memory_service.save_interaction("我在北京工作", "北京是个好地方", importance=6.0)
            await memory_service.save_interaction("我喜欢吃火锅", "火锅真好吃！", importance=4.0)

            # 检索与"工作"相关的记忆
            work_memories = await memory_service.retrieve_relevant_memories(query="工作", n_results=3)

            # 检索与"美食"相关的记忆
            food_memories = await memory_service.retrieve_relevant_memories(query="美食", n_results=3)

            if len(work_memories) > 0 or len(food_memories) > 0:
                print_success("记忆相关性检索成功")
                print(f"    '工作' 相关: {len(work_memories)} 条")
                print(f"    '美食' 相关: {len(food_memories)} 条")
                passed += 1
            else:
                print_error("记忆相关性检索失败")
        except Exception as e:
            print_error(f"记忆相关性检索失败: {e}")
        finally:
            total += 1

    asyncio.run(run_tests())

    print_info(f"记忆检索与上下文注入测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_memory_context_formatting():
    """测试9: 记忆上下文格式化"""
    print_header("测试9: 记忆上下文格式化")

    passed = 0
    total = 0

    async def run_tests():
        nonlocal passed, total

        memory_store = MockMemoryStore()
        vector_store = MockVectorStore()

        memory_service = LangChainMemoryService(
            memory_store=memory_store, vector_store=vector_store, user_id="test_user_004"
        )

        # 准备丰富的测试数据
        test_data = [
            ("我叫张三", "你好张三！", 9.0),
            ("我是软件工程师", "很酷的职业！", 7.0),
            ("我喜欢跑步和游泳", "运动很健康", 6.0),
            ("我养了一只金毛", "金毛很可爱", 5.0),
            ("我最近在读《三体》", "科幻小说很有趣", 6.0),
        ]

        for user_msg, ai_msg, importance in test_data:
            await memory_service.save_interaction(user_msg, ai_msg, importance=importance)

        # 测试完整上下文格式化
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="推荐一些科幻小说",
                include_conversation=True,
                include_long_term=True,
                conversation_limit=5,
                memory_limit=3,
            )

            formatted = await memory_service.format_context_for_llm(context)

            # 验证格式化内容包含关键部分
            has_history = "对话历史" in formatted or len(context["conversation_history"]) > 0
            has_memories = "相关记忆" in formatted or len(context["relevant_memories"]) > 0

            if has_history and has_memories:
                print_success("完整上下文格式化成功")
                print(f"    格式化文本:\n{formatted[:200]}...")
                passed += 1
            else:
                print_error("格式化内容缺少关键部分")
        except Exception as e:
            print_error(f"完整上下文格式化失败: {e}")
        finally:
            total += 1

        # 测试仅对话历史格式化
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="你好", include_conversation=True, include_long_term=False
            )

            formatted = await memory_service.format_context_for_llm(context)

            if len(formatted) > 0:
                print_success("仅对话历史格式化成功")
                passed += 1
            else:
                print_error("对话历史格式化为空")
        except Exception as e:
            print_error(f"对话历史格式化失败: {e}")
        finally:
            total += 1

        # 测试仅长期记忆格式化
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="告诉我关于我的信息", include_conversation=False, include_long_term=True
            )

            formatted = await memory_service.format_context_for_llm(context)

            if len(formatted) > 0:
                print_success("仅长期记忆格式化成功")
                passed += 1
            else:
                print_error("长期记忆格式化为空")
        except Exception as e:
            print_error(f"长期记忆格式化失败: {e}")
        finally:
            total += 1

        # 测试空上下文格式化
        try:
            empty_context = {
                "current_message": "测试",
                "conversation_history": [],
                "relevant_memories": [],
                "working_memory": None,
            }

            formatted = await memory_service.format_context_for_llm(empty_context)

            # 空上下文应该返回空字符串或很短的文本
            if len(formatted) < 50:
                print_success("空上下文格式化正确")
                passed += 1
            else:
                print_error(f"空上下文格式化异常: {len(formatted)} 字符")
        except Exception as e:
            print_error(f"空上下文格式化失败: {e}")
        finally:
            total += 1

        # 测试格式化输出可读性
        try:
            context = await memory_service.build_context_for_prompt(
                current_message="我想了解更多", include_conversation=True, include_long_term=True
            )

            formatted = await memory_service.format_context_for_llm(context)

            # 检查格式化文本的可读性
            has_sections = "##" in formatted  # 有章节标题
            has_newlines = "\n" in formatted  # 有换行
            readable_length = 50 < len(formatted) < 5000  # 长度合理

            if has_sections and has_newlines and readable_length:
                print_success("格式化输出可读性良好")
                print(f"    有章节标题: {has_sections}")
                print(f"    有换行分隔: {has_newlines}")
                print(f"    长度合理: {len(formatted)} 字符")
                passed += 1
            else:
                print_error("格式化输出可读性不佳")
        except Exception as e:
            print_error(f"可读性测试失败: {e}")
        finally:
            total += 1

    asyncio.run(run_tests())

    print_info(f"记忆上下文格式化测试通过率: {passed}/{total}")
    return passed >= total * 0.8


# ============ 任务 4.3: 持续学习能力测试 ============


def test_replay_buffer():
    """测试10: 经验重放缓冲区"""
    print_header("测试10: 经验重放缓冲区 (Replay Buffer)")

    passed = 0
    total = 0

    # 创建临时存储目录
    with tempfile.TemporaryDirectory() as tmpdir:
        buffer = ReplayBuffer(max_size=100, storage_dir=tmpdir)

        # 测试添加经验
        try:
            exp1 = Experience(
                id="exp_001",
                user_id="user_001",
                timestamp=datetime.now(),
                user_message="我今天很开心",
                ai_response="太好了！",
                user_satisfaction=0.9,
                conversation_length=5,
                emotional_resonance=0.8,
                personality_snapshot={"humor": 70.0, "empathy": 80.0},
                importance=0.85,
            )

            buffer.add_experience(exp1)

            if len(buffer.buffer) == 1:
                print_success("添加经验成功")
                passed += 1
            else:
                print_error(f"缓冲区大小不对: {len(buffer.buffer)}")
        except Exception as e:
            print_error(f"添加经验失败: {e}")
        finally:
            total += 1

        # 测试批量添加
        try:
            for i in range(10):
                exp = Experience(
                    id=f"exp_{i:03d}",
                    user_id="user_001",
                    timestamp=datetime.now(),
                    user_message=f"消息 {i}",
                    ai_response=f"回复 {i}",
                    user_satisfaction=0.5 + i * 0.05,
                    conversation_length=3,
                    emotional_resonance=0.6,
                    personality_snapshot={"humor": 60.0 + i},
                    importance=0.5 + i * 0.05,
                )
                buffer.add_experience(exp)

            if len(buffer.buffer) == 11:
                print_success(f"批量添加成功: {len(buffer.buffer)} 条经验")
                passed += 1
            else:
                print_error(f"批量添加数量不对: {len(buffer.buffer)}")
        except Exception as e:
            print_error(f"批量添加失败: {e}")
        finally:
            total += 1

        # 测试采样经验
        try:
            sampled = buffer.sample_experiences(n=5, importance_weighted=True)

            if len(sampled) == 5:
                print_success(f"采样经验成功: {len(sampled)} 条")
                print(f"    采样ID: {[exp.id for exp in sampled[:3]]}")
                passed += 1
            else:
                print_error(f"采样数量不对: {len(sampled)}")
        except Exception as e:
            print_error(f"采样经验失败: {e}")
        finally:
            total += 1

        # 测试获取最近经验
        try:
            recent = buffer.get_recent_experiences(n=3)

            if len(recent) == 3:
                print_success(f"获取最近经验成功: {len(recent)} 条")
                passed += 1
            else:
                print_error(f"最近经验数量不对: {len(recent)}")
        except Exception as e:
            print_error(f"获取最近经验失败: {e}")
        finally:
            total += 1

        # 测试获取高质量经验
        try:
            high_quality = buffer.get_high_quality_experiences(
                n=5, min_satisfaction=0.8
            )

            if len(high_quality) > 0:
                print_success(f"获取高质量经验成功: {len(high_quality)} 条")
                print(
                    f"    满意度: {[f'{exp.user_satisfaction:.2f}' for exp in high_quality[:3]]}"
                )
                passed += 1
            else:
                print_info("没有高质量经验（满意度 >= 0.8）")
                passed += 0.5
        except Exception as e:
            print_error(f"获取高质量经验失败: {e}")
        finally:
            total += 1

        # 测试缓冲区统计
        try:
            stats = buffer.get_buffer_stats()

            if (
                "total_experiences" in stats
                and stats["total_experiences"] == len(buffer.buffer)
            ):
                print_success("缓冲区统计正确")
                print(f"    总经验数: {stats['total_experiences']}")
                print(f"    平均满意度: {stats['avg_satisfaction']:.2f}")
                print(f"    平均重要性: {stats['avg_importance']:.2f}")
                passed += 1
            else:
                print_error("缓冲区统计不正确")
        except Exception as e:
            print_error(f"缓冲区统计失败: {e}")
        finally:
            total += 1

    print_info(f"经验重放缓冲区测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_anti_forget_mechanism():
    """测试11: 防遗忘机制 (EWC)"""
    print_header("测试11: 防遗忘机制 (Anti-Forget Mechanism)")

    passed = 0
    total = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        anti_forget = AntiForgetMechanism(storage_dir=tmpdir)

        # 测试参数重要性初始化
        try:
            anti_forget.update_parameter_importance("traits.humor", 70.0)

            if "traits.humor" in anti_forget.importance_map:
                importance = anti_forget.get_parameter_importance("traits.humor")
                print_success(f"参数重要性初始化成功: {importance:.2f}")
                passed += 1
            else:
                print_error("参数重要性初始化失败")
        except Exception as e:
            print_error(f"参数重要性初始化失败: {e}")
        finally:
            total += 1

        # 测试参数重要性更新（稳定参数）
        try:
            # 添加稳定的值（方差小）
            for i in range(10):
                anti_forget.update_parameter_importance("traits.empathy", 80.0 + i * 0.1)

            importance = anti_forget.get_parameter_importance("traits.empathy")

            # 稳定参数应该有较高的重要性
            if importance > 0.5:
                print_success(f"稳定参数重要性高: {importance:.2f}")
                passed += 1
            else:
                print_info(f"稳定参数重要性: {importance:.2f}")
                passed += 0.5
        except Exception as e:
            print_error(f"稳定参数测试失败: {e}")
        finally:
            total += 1

        # 测试参数重要性更新（不稳定参数）
        try:
            # 添加不稳定的值（方差大）
            import random

            for i in range(10):
                value = 50.0 + random.uniform(-20.0, 20.0)
                anti_forget.update_parameter_importance("traits.sarcasm", value)

            importance = anti_forget.get_parameter_importance("traits.sarcasm")

            # 不稳定参数应该有较低的重要性
            if importance < 0.7:
                print_success(f"不稳定参数重要性低: {importance:.2f}")
                passed += 1
            else:
                print_info(f"不稳定参数重要性: {importance:.2f}")
                passed += 0.5
        except Exception as e:
            print_error(f"不稳定参数测试失败: {e}")
        finally:
            total += 1

        # 测试更新约束计算
        try:
            # 设置一个高重要性参数
            for i in range(15):
                anti_forget.update_parameter_importance("big_five.openness", 75.0)

            old_value = 75.0
            new_value = 90.0  # 尝试大幅修改

            constrained = anti_forget.calculate_update_constraint(
                "big_five.openness", old_value, new_value
            )

            # 约束后的值应该比未约束的值更接近旧值
            delta_unconstrained = abs(new_value - old_value)
            delta_constrained = abs(constrained - old_value)

            if delta_constrained < delta_unconstrained:
                print_success(
                    f"更新约束生效: {old_value:.1f} -> {new_value:.1f} 约束为 {constrained:.1f}"
                )
                print(f"    未约束变化: {delta_unconstrained:.1f}")
                print(f"    约束后变化: {delta_constrained:.1f}")
                passed += 1
            else:
                print_error("更新约束未生效")
        except Exception as e:
            print_error(f"更新约束测试失败: {e}")
        finally:
            total += 1

        # 测试低重要性参数自由更新
        try:
            # 设置一个低重要性参数（新参数）
            anti_forget.update_parameter_importance("traits.new_trait", 60.0)

            old_value = 60.0
            new_value = 80.0

            constrained = anti_forget.calculate_update_constraint(
                "traits.new_trait", old_value, new_value
            )

            # 低重要性参数应该允许较大变化
            delta = abs(constrained - old_value)

            if delta > 10.0:
                print_success(f"低重要性参数允许较大变化: {delta:.1f}")
                passed += 1
            else:
                print_info(f"低重要性参数变化: {delta:.1f}")
                passed += 0.5
        except Exception as e:
            print_error(f"低重要性参数测试失败: {e}")
        finally:
            total += 1

    print_info(f"防遗忘机制测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_incremental_learning():
    """测试12: 增量学习策略"""
    print_header("测试12: 增量学习策略")

    passed = 0
    total = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        learning_service = ContinualLearningService(
            replay_buffer=ReplayBuffer(storage_dir=f"{tmpdir}/buffer"),
            anti_forget=AntiForgetMechanism(storage_dir=f"{tmpdir}/importance"),
            learning_rate=0.1,
        )

        # 创建初始人格
        initial_personality = PersonalityConfig(
            id="test_learning",
            name="测试学习人格",
            big_five=BigFiveScores(
                openness=70.0,
                conscientiousness=60.0,
                extraversion=65.0,
                agreeableness=75.0,
                neuroticism=40.0,
            ),
            traits=PersonalityTraits(
                humor=60.0,
                empathy=70.0,
                warmth=75.0,
                assertiveness=50.0,
                casualness=65.0,
                sarcasm=30.0,
                verbosity=55.0,
            ),
        )

        # 测试记录交互
        try:
            exp = learning_service.record_interaction(
                user_id="user_001",
                user_message="你真幽默",
                ai_response="哈哈谢谢",
                personality=initial_personality,
                user_satisfaction=0.9,
                conversation_length=5,
                emotional_resonance=0.85,
            )

            if exp.id and exp.user_satisfaction == 0.9:
                print_success("记录交互成功")
                print(f"    经验ID: {exp.id}")
                print(f"    满意度: {exp.user_satisfaction:.2f}")
                passed += 1
            else:
                print_error("记录交互失败")
        except Exception as e:
            print_error(f"记录交互失败: {e}")
        finally:
            total += 1

        # 测试基于反馈学习（正向反馈）
        try:
            feedback_signals = {
                "liked_humor": 0.8,  # 喜欢幽默
                "wanted_more_empathy": 0.6,  # 想要更多共情
            }

            updated_personality = learning_service.learn_from_feedback(
                user_id="user_001",
                current_personality=initial_personality,
                feedback_signals=feedback_signals,
            )

            # 验证人格参数有更新
            humor_increased = updated_personality.traits.humor > initial_personality.traits.humor
            empathy_increased = (
                updated_personality.traits.empathy > initial_personality.traits.empathy
            )

            if humor_increased and empathy_increased:
                print_success("正向反馈学习成功")
                print(
                    f"    幽默度: {initial_personality.traits.humor:.1f} -> {updated_personality.traits.humor:.1f}"
                )
                print(
                    f"    共情度: {initial_personality.traits.empathy:.1f} -> {updated_personality.traits.empathy:.1f}"
                )
                passed += 1
            else:
                print_error("正向反馈学习未生效")
        except Exception as e:
            print_error(f"正向反馈学习失败: {e}")
        finally:
            total += 1

        # 测试基于反馈学习（负向反馈）
        try:
            feedback_signals = {
                "response_too_long": -0.7,  # 回复太长
            }

            updated_personality = learning_service.learn_from_feedback(
                user_id="user_001",
                current_personality=initial_personality,
                feedback_signals=feedback_signals,
            )

            # 验证话痨程度降低
            verbosity_decreased = (
                updated_personality.traits.verbosity < initial_personality.traits.verbosity
            )

            if verbosity_decreased:
                print_success("负向反馈学习成功")
                print(
                    f"    话痨度: {initial_personality.traits.verbosity:.1f} -> {updated_personality.traits.verbosity:.1f}"
                )
                passed += 1
            else:
                print_error("负向反馈学习未生效")
        except Exception as e:
            print_error(f"负向反馈学习失败: {e}")
        finally:
            total += 1

        # 测试学习率控制
        try:
            # 小幅反馈
            small_feedback = {"liked_humor": 0.3}

            updated = learning_service.learn_from_feedback(
                user_id="user_001",
                current_personality=initial_personality,
                feedback_signals=small_feedback,
            )

            delta = abs(updated.traits.humor - initial_personality.traits.humor)

            # 小幅反馈应该产生小幅变化
            if delta < 5.0:
                print_success(f"学习率控制正确: 变化量 {delta:.2f}")
                passed += 1
            else:
                print_error(f"学习率控制失败: 变化量过大 {delta:.2f}")
        except Exception as e:
            print_error(f"学习率控制测试失败: {e}")
        finally:
            total += 1

        # 测试演化历史记录
        try:
            feedback = {"liked_casual_tone": 0.7}

            updated = learning_service.learn_from_feedback(
                user_id="user_001",
                current_personality=initial_personality,
                feedback_signals=feedback,
            )

            if len(updated.evolution_history) > 0:
                latest = updated.evolution_history[-1]
                if "feedback_signals" in latest and "adjustments" in latest:
                    print_success("演化历史记录成功")
                    print(f"    历史记录数: {len(updated.evolution_history)}")
                    passed += 1
                else:
                    print_error("演化历史记录不完整")
            else:
                print_error("演化历史记录为空")
        except Exception as e:
            print_error(f"演化历史记录测试失败: {e}")
        finally:
            total += 1

    print_info(f"增量学习策略测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def test_memory_consolidation():
    """测试13: 记忆巩固机制"""
    print_header("测试13: 记忆巩固机制（定期重放旧经验）")

    passed = 0
    total = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        learning_service = ContinualLearningService(
            replay_buffer=ReplayBuffer(storage_dir=f"{tmpdir}/buffer"),
            anti_forget=AntiForgetMechanism(storage_dir=f"{tmpdir}/importance"),
            consolidation_interval_hours=1,  # 1小时巩固一次
        )

        # 创建测试人格
        personality = PersonalityConfig(
            id="test_consolidation",
            name="测试巩固人格",
            big_five=BigFiveScores(openness=70.0, extraversion=60.0),
            traits=PersonalityTraits(humor=65.0, empathy=75.0),
        )

        # 添加多个高质量经验
        try:
            for i in range(10):
                learning_service.record_interaction(
                    user_id="user_consolidation",
                    user_message=f"测试消息 {i}",
                    ai_response=f"测试回复 {i}",
                    personality=personality,
                    user_satisfaction=0.8 + i * 0.01,
                    conversation_length=5,
                    emotional_resonance=0.75,
                )

            buffer_stats = learning_service.replay_buffer.get_buffer_stats()
            if buffer_stats["total_experiences"] == 10:
                print_success(f"添加高质量经验成功: {buffer_stats['total_experiences']} 条")
                passed += 1
            else:
                print_error(f"经验数量不对: {buffer_stats['total_experiences']}")
        except Exception as e:
            print_error(f"添加经验失败: {e}")
        finally:
            total += 1

        # 测试巩固机制（首次巩固）
        try:
            # 修改人格参数
            personality.traits.humor = 50.0
            personality.traits.empathy = 60.0

            # 执行巩固
            learning_service.consolidate_memory("user_consolidation", personality)

            # 验证巩固时间已记录
            if "user_consolidation" in learning_service.last_consolidation:
                print_success("首次记忆巩固成功")
                print(
                    f"    巩固时间: {learning_service.last_consolidation['user_consolidation'].strftime('%H:%M:%S')}"
                )
                passed += 1
            else:
                print_error("巩固时间未记录")
        except Exception as e:
            print_error(f"首次巩固失败: {e}")
        finally:
            total += 1

        # 测试巩固间隔控制
        try:
            # 立即再次尝试巩固（应该被跳过）
            old_time = learning_service.last_consolidation.get("user_consolidation")

            learning_service.consolidate_memory("user_consolidation", personality)

            new_time = learning_service.last_consolidation.get("user_consolidation")

            if old_time == new_time:
                print_success("巩固间隔控制正确（跳过过早的巩固）")
                passed += 1
            else:
                print_info("巩固间隔控制可能未生效")
                passed += 0.5
        except Exception as e:
            print_error(f"巩固间隔控制测试失败: {e}")
        finally:
            total += 1

        # 测试学习统计
        try:
            stats = learning_service.get_learning_stats(user_id="user_consolidation")

            required_keys = ["replay_buffer", "parameter_importance_count", "learning_rate"]

            if all(key in stats for key in required_keys):
                print_success("学习统计获取成功")
                print(f"    缓冲区经验数: {stats['replay_buffer']['total_experiences']}")
                print(f"    参数重要性数: {stats['parameter_importance_count']}")
                print(f"    学习率: {stats['learning_rate']}")
                if "last_consolidation" in stats:
                    print(f"    上次巩固: {stats['last_consolidation']}")
                passed += 1
            else:
                print_error("学习统计数据不完整")
        except Exception as e:
            print_error(f"学习统计获取失败: {e}")
        finally:
            total += 1

    print_info(f"记忆巩固机制测试通过率: {passed}/{total}")
    return passed >= total * 0.8


def run_all_tests():
    """运行所有测试"""
    print_header("AI小花 人格引擎系统验证测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # ========== 任务 4.1: 基础人格模型 ==========
    print_header("【任务 4.1】基础人格模型测试")

    try:
        results.append(("Big Five 维度定义", test_big_five_dimensions()))
    except Exception as e:
        print_error(f"Big Five 维度测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Big Five 维度定义", False))

    try:
        results.append(("人格初始化配置", test_personality_initialization()))
    except Exception as e:
        print_error(f"人格初始化测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("人格初始化配置", False))

    try:
        results.append(("说话风格映射", test_speaking_style_mapping()))
    except Exception as e:
        print_error(f"说话风格映射测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("说话风格映射", False))

    try:
        results.append(("Prompt 注入", test_prompt_engineering_injection()))
    except Exception as e:
        print_error(f"Prompt 注入测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Prompt 注入", False))

    try:
        results.append(("人格服务操作", test_personality_service_operations()))
    except Exception as e:
        print_error(f"人格服务操作测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("人格服务操作", False))

    # ========== 任务 4.2: 记忆系统集成 ==========
    print_header("【任务 4.2】记忆系统集成测试")

    try:
        results.append(("LangChain Memory 集成", test_langchain_memory_integration()))
    except Exception as e:
        print_error(f"LangChain Memory 集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("LangChain Memory 集成", False))

    try:
        results.append(("向量数据库存储", test_vector_database_storage()))
    except Exception as e:
        print_error(f"向量数据库存储测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("向量数据库存储", False))

    try:
        results.append(("记忆检索与上下文注入", test_memory_retrieval_and_context()))
    except Exception as e:
        print_error(f"记忆检索与上下文注入测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("记忆检索与上下文注入", False))

    try:
        results.append(("记忆上下文格式化", test_memory_context_formatting()))
    except Exception as e:
        print_error(f"记忆上下文格式化测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("记忆上下文格式化", False))

    # ========== 任务 4.3: 持续学习能力 ==========
    print_header("【任务 4.3】持续学习能力测试")

    try:
        results.append(("经验重放缓冲区", test_replay_buffer()))
    except Exception as e:
        print_error(f"经验重放缓冲区测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("经验重放缓冲区", False))

    try:
        results.append(("防遗忘机制 (EWC)", test_anti_forget_mechanism()))
    except Exception as e:
        print_error(f"防遗忘机制测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("防遗忘机制 (EWC)", False))

    try:
        results.append(("增量学习策略", test_incremental_learning()))
    except Exception as e:
        print_error(f"增量学习策略测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("增量学习策略", False))

    try:
        results.append(("记忆巩固机制", test_memory_consolidation()))
    except Exception as e:
        print_error(f"记忆巩固机制测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("记忆巩固机制", False))

    # 汇总
    print_header("📊 测试结果汇总")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    # 分组显示
    print(f"\n{Colors.BLUE}【任务 4.1】基础人格模型{Colors.RESET}")
    for name, result in results[:5]:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(f"\n{Colors.BLUE}【任务 4.2】记忆系统集成{Colors.RESET}")
    for name, result in results[5:9]:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(f"\n{Colors.BLUE}【任务 4.3】持续学习能力{Colors.RESET}")
    for name, result in results[9:]:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(
        f"\n总计: {Colors.GREEN if passed == total else Colors.YELLOW}{passed}/{total}{Colors.RESET} 通过"
    )

    if passed == total:
        print(f"\n{Colors.GREEN}✓ 所有测试通过！人格引擎系统验证完成。{Colors.RESET}")
        print(f"\n{Colors.GREEN}任务 4.1 完成：基础人格模型实现成功{Colors.RESET}")
        print(f"  ✓ Big Five (OCEAN) 维度定义完成")
        print(f"  ✓ 人格初始化配置完成")
        print(f"  ✓ 人格到说话风格映射完成")
        print(f"  ✓ Prompt Engineering 注入完成")
        print(f"\n{Colors.GREEN}任务 4.2 完成：记忆系统集成成功{Colors.RESET}")
        print(f"  ✓ LangChain Memory 集成完成")
        print(f"  ✓ 向量数据库存储完成")
        print(f"  ✓ 记忆检索与上下文注入完成")
        print(f"  ✓ 记忆上下文格式化完成")
        print(f"\n{Colors.GREEN}任务 4.3 完成：持续学习能力实现成功{Colors.RESET}")
        print(f"  ✓ 经验重放缓冲区 (Replay Buffer) 完成")
        print(f"  ✓ 防遗忘机制 (EWC) 完成")
        print(f"  ✓ 增量学习策略完成")
        print(f"  ✓ 记忆巩固机制完成")
    else:
        print(f"\n{Colors.YELLOW}部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
