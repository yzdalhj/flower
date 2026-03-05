"""
用户画像与关系系统验证测试

验证内容:
1. 用户画像创建与管理
2. 实体提取功能
3. 互动记录与分析
4. 亲密度与信任度计算
5. 关系阶段跃迁
6. Prompt注入功能
7. 关系图分析
8. 自我披露深度分析

注意: 此测试直接导入实际实现模块进行验证
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

from app.services.profile import (  # noqa: E402
    ProfilePromptInjector,
    RelationshipStage,
    UserProfileService,
)
from app.services.relationship import RelationshipGraphService, RelationshipService  # noqa: E402

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


def test_user_profile_creation():
    """测试1: 用户画像创建 - 使用实际实现"""
    print_header("测试1: 用户画像创建 - 实际实现")

    profile_service = UserProfileService()
    test_user_id = "test_user_001"

    async def run_test():
        profile = await profile_service.get_or_create_profile(test_user_id)

        checks = []

        # 检查画像是否创建成功
        if profile is not None:
            print_success(f"用户画像创建成功: {test_user_id}")
            checks.append(True)
        else:
            print_error("用户画像创建失败")
            checks.append(False)

        # 检查用户ID
        if profile.user_id == test_user_id:
            print_success(f"用户ID正确: {profile.user_id}")
            checks.append(True)
        else:
            print_error(f"用户ID错误: 期望 {test_user_id}, 实际 {profile.user_id}")
            checks.append(False)

        # 检查初始关系阶段
        if profile.relationship.stage == RelationshipStage.STRANGER:
            print_success(f"初始关系阶段正确: {profile.relationship.stage.value}")
            checks.append(True)
        else:
            print_error(f"初始关系阶段错误: {profile.relationship.stage.value}")
            checks.append(False)

        # 检查初始亲密度和信任度
        if profile.relationship.intimacy == 0.0 and profile.relationship.trust == 0.0:
            print_success(
                f"初始亲密度和信任度正确: intimacy={profile.relationship.intimacy}, trust={profile.relationship.trust}"
            )
            checks.append(True)
        else:
            print_error(
                f"初始值错误: intimacy={profile.relationship.intimacy}, trust={profile.relationship.trust}"
            )
            checks.append(False)

        print_info(f"通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.75

    return asyncio.run(run_test())


def test_entity_extraction():
    """测试2: 实体提取功能 - 使用实际实现"""
    print_header("测试2: 实体提取功能 - 实际实现")

    profile_service = UserProfileService()

    async def run_test():
        text = "我叫张三，在北京的腾讯工作，我喜欢打篮球和听周杰伦的歌，讨厌加班。"
        entities = await profile_service.extract_entities(text)

        checks = []

        # 检查人名提取
        if "PERSON" in entities and "张三" in entities["PERSON"]:
            print_success(f"人名提取成功: {entities['PERSON']}")
            checks.append(True)
        else:
            print_error("人名提取失败")
            checks.append(False)

        # 检查地点提取
        if "GPE" in entities and "北京" in entities["GPE"]:
            print_success(f"地点提取成功: {entities['GPE']}")
            checks.append(True)
        else:
            print_error("地点提取失败")
            checks.append(False)

        # 检查组织提取
        if "ORG" in entities and "腾讯" in entities["ORG"]:
            print_success(f"组织提取成功: {entities['ORG']}")
            checks.append(True)
        else:
            print_error("组织提取失败")
            checks.append(False)

        # 检查喜好提取
        if "LIKES" in entities and (
            "打篮球" in entities["LIKES"] or "听周杰伦的歌" in entities["LIKES"]
        ):
            print_success(f"喜好提取成功: {entities['LIKES']}")
            checks.append(True)
        else:
            print_error("喜好提取失败")
            checks.append(False)

        # 检查厌恶提取
        if "DISLIKES" in entities and "加班" in entities["DISLIKES"]:
            print_success(f"厌恶提取成功: {entities['DISLIKES']}")
            checks.append(True)
        else:
            print_error("厌恶提取失败")
            checks.append(False)

        print_info(f"实体提取通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.6

    return asyncio.run(run_test())


def test_profile_update_from_interaction():
    """测试3: 基于互动更新用户画像 - 使用实际实现"""
    print_header("测试3: 基于互动更新用户画像 - 实际实现")

    profile_service = UserProfileService()
    test_user_id = "test_user_002"

    async def run_test():
        text = "我叫李四，在上海做程序员，我喜欢玩游戏和旅行，讨厌早起。"
        profile = await profile_service.update_profile_from_interaction(
            test_user_id, text, "哇，你也喜欢玩游戏啊？我也超喜欢的~"
        )

        checks = []

        # 检查基本信息更新
        if profile.basic_info.get("name") == "李四":
            print_success(f"姓名更新成功: {profile.basic_info.get('name')}")
            checks.append(True)
        else:
            print_error(f"姓名更新失败: {profile.basic_info.get('name')}")
            checks.append(False)

        if profile.basic_info.get("location") == "上海":
            print_success(f"地点更新成功: {profile.basic_info.get('location')}")
            checks.append(True)
        else:
            print_error(f"地点更新失败: {profile.basic_info.get('location')}")
            checks.append(False)

        if profile.basic_info.get("occupation") == "程序员":
            print_success(f"职业更新成功: {profile.basic_info.get('occupation')}")
            checks.append(True)
        else:
            print_error(f"职业更新失败: {profile.basic_info.get('occupation')}")
            checks.append(False)

        # 检查喜好更新
        if "玩游戏" in profile.preferences["likes"] and "旅行" in profile.preferences["likes"]:
            print_success(f"喜好更新成功: {profile.preferences['likes']}")
            checks.append(True)
        else:
            print_error(f"喜好更新失败: {profile.preferences['likes']}")
            checks.append(False)

        # 检查厌恶更新
        if "早起" in profile.preferences["dislikes"]:
            print_success(f"厌恶更新成功: {profile.preferences['dislikes']}")
            checks.append(True)
        else:
            print_error(f"厌恶更新失败: {profile.preferences['dislikes']}")
            checks.append(False)

        print_info(f"画像更新通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.6

    return asyncio.run(run_test())


def test_interaction_recording():
    """测试4: 互动记录 - 使用实际实现"""
    print_header("测试4: 互动记录 - 实际实现")

    relationship_service = RelationshipService()
    test_user_id = "test_user_003"

    async def run_test():
        interaction = await relationship_service.record_interaction(
            test_user_id,
            "今天工作好累啊，加班到现在，好难过。",
            "哎呀，太辛苦了，抱抱你~ 快休息休息吧",
            emotional_context={
                "user_emotion": {"valence": -0.5, "arousal": 0.6, "intensity": 0.8},
                "ai_emotion": {"valence": -0.3, "arousal": 0.4},
            },
        )

        checks = []

        # 检查互动记录创建
        if interaction is not None:
            print_success("互动记录创建成功")
            checks.append(True)
        else:
            print_error("互动记录创建失败")
            checks.append(False)
            return False

        # 检查用户ID
        if interaction.user_id == test_user_id:
            print_success(f"用户ID正确: {interaction.user_id}")
            checks.append(True)
        else:
            print_error(f"用户ID错误: {interaction.user_id}")
            checks.append(False)

        # 检查质量分数
        if interaction.quality_score > 0:
            print_success(f"质量分数计算成功: {interaction.quality_score:.2f}")
            checks.append(True)
        else:
            print_error(f"质量分数异常: {interaction.quality_score}")
            checks.append(False)

        # 检查情感共鸣
        if interaction.emotional_resonance > 0:
            print_success(f"情感共鸣计算成功: {interaction.emotional_resonance:.2f}")
            checks.append(True)
        else:
            print_error(f"情感共鸣异常: {interaction.emotional_resonance}")
            checks.append(False)

        # 检查自我披露深度
        if interaction.user_disclosure_depth > 0.3:
            print_success(f"自我披露深度正确: {interaction.user_disclosure_depth:.2f} (深层话题)")
            checks.append(True)
        else:
            print_error(f"自我披露深度异常: {interaction.user_disclosure_depth:.2f}")
            checks.append(False)

        print_info(f"互动记录通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.75

    return asyncio.run(run_test())


def test_intimacy_calculation():
    """测试5: 亲密度与信任度计算 - 使用实际实现"""
    print_header("测试5: 亲密度与信任度计算 - 实际实现")

    relationship_service = RelationshipService()
    test_user_id = "test_user_004"

    async def run_test():
        # 添加多次互动
        print_info("添加10次互动记录...")
        for i in range(10):
            await relationship_service.record_interaction(
                test_user_id,
                f"今天我们聊的第{i+1}次，我最近压力好大，工作好烦。",
                "唉，我懂这种感觉，慢慢来吧~",
                emotional_context={
                    "user_emotion": {"valence": -0.2, "arousal": 0.3},
                    "ai_emotion": {"valence": -0.1, "arousal": 0.2},
                },
            )

        intimacy = await relationship_service.calculate_intimacy(test_user_id)
        trust = await relationship_service.calculate_trust(test_user_id)

        checks = []

        # 检查亲密度范围
        if 0 < intimacy < 1:
            print_success(f"亲密度计算正确: {intimacy:.3f}")
            checks.append(True)
        else:
            print_error(f"亲密度异常: {intimacy}")
            checks.append(False)

        # 检查信任度范围
        if 0 < trust < 1:
            print_success(f"信任度计算正确: {trust:.3f}")
            checks.append(True)
        else:
            print_error(f"信任度异常: {trust}")
            checks.append(False)

        print_info(f"亲密度与信任度通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) == len(checks)

    return asyncio.run(run_test())


def test_relationship_stage_transition():
    """测试6: 关系阶段跃迁 - 使用实际实现"""
    print_header("测试6: 关系阶段跃迁 - 实际实现")

    profile_service = UserProfileService()
    relationship_service = RelationshipService()
    test_user_id = "test_user_005"

    async def run_test():
        profile = await profile_service.get_or_create_profile(test_user_id)

        # 检查初始阶段
        if profile.relationship.stage == RelationshipStage.STRANGER:
            print_success(f"初始阶段正确: {profile.relationship.stage.value}")
        else:
            print_error(f"初始阶段错误: {profile.relationship.stage.value}")

        # 添加高质量互动
        print_info("添加30次深度互动...")
        for i in range(30):
            await relationship_service.record_interaction(
                test_user_id,
                "我最近遇到了一些感情问题，真的好难过，不知道该怎么办...",
                "啊...怎么了？可以和我说说，我陪着你。",
                emotional_context={
                    "user_emotion": {"valence": -0.7, "arousal": 0.8, "intensity": 0.9},
                    "ai_emotion": {"valence": -0.5, "arousal": 0.6},
                },
            )

        # 更新关系阶段
        new_stage = await relationship_service.update_relationship_stage(test_user_id, profile)

        checks = []

        # 检查关系阶段提升
        expected_stages = [
            RelationshipStage.FRIEND,
            RelationshipStage.CLOSE_FRIEND,
            RelationshipStage.CONFIDANT,
        ]
        if new_stage in expected_stages:
            print_success(f"关系阶段提升成功: {profile.relationship.stage.value}")
            checks.append(True)
        else:
            print_error(f"关系阶段未提升: {profile.relationship.stage.value}")
            checks.append(False)

        # 检查亲密度
        if profile.relationship.intimacy > 0.4:
            print_success(f"亲密度提升: {profile.relationship.intimacy:.3f}")
            checks.append(True)
        else:
            print_error(f"亲密度未达标: {profile.relationship.intimacy:.3f}")
            checks.append(False)

        # 检查信任度
        if profile.relationship.trust > 0.5:
            print_success(f"信任度提升: {profile.relationship.trust:.3f}")
            checks.append(True)
        else:
            print_error(f"信任度未达标: {profile.relationship.trust:.3f}")
            checks.append(False)

        # 检查阶段历史
        if len(profile.relationship.stage_history) >= 1:
            print_success(f"阶段历史记录正确: {len(profile.relationship.stage_history)}条")
            checks.append(True)
        else:
            print_error("阶段历史记录缺失")
            checks.append(False)

        print_info(f"关系阶段跃迁通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.75

    return asyncio.run(run_test())


def test_profile_summary_generation():
    """测试7: 用户画像摘要生成 - 使用实际实现"""
    print_header("测试7: 用户画像摘要生成 - 实际实现")

    profile_service = UserProfileService()
    test_user_id = "test_user_006"

    async def run_test():
        # 先更新用户画像
        await profile_service.update_profile_from_interaction(
            test_user_id,
            "我叫王五，在杭州做产品经理，我喜欢看电影和吃火锅，讨厌开会。",
            "哇，杭州是个好地方啊，我也超喜欢吃火锅的~",
        )

        summary = await profile_service.generate_profile_summary(test_user_id)

        checks = []
        keywords = ["王五", "杭州", "产品经理", "看电影", "吃火锅", "开会"]

        for keyword in keywords:
            if keyword in summary:
                print_success(f"摘要包含关键词: {keyword}")
                checks.append(True)
            else:
                print_error(f"摘要缺少关键词: {keyword}")
                checks.append(False)

        print_info(f"摘要内容:\n{summary[:200]}...")
        print_info(f"摘要生成通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.5

    return asyncio.run(run_test())


def test_prompt_injection():
    """测试8: Prompt注入功能 - 使用实际实现"""
    print_header("测试8: Prompt注入功能 - 实际实现")

    profile_service = UserProfileService()
    relationship_service = RelationshipService()
    prompt_injector = ProfilePromptInjector(profile_service, relationship_service)
    test_user_id = "test_user_007"

    async def run_test():
        # 先更新用户画像
        await profile_service.update_profile_from_interaction(
            test_user_id, "我叫赵六，我喜欢玩游戏和旅游。", "玩什么游戏呀？有机会一起呀~"
        )

        base_prompt = """【系统提示】
你是小花，一个可爱的AI助手。
用户：你好呀
AI："""

        injected_prompt = await prompt_injector.inject_into_prompt(base_prompt, test_user_id)

        checks = []
        required_sections = ["【用户画像】", "赵六", "玩游戏", "【关系状态】", "【行为指导】"]

        for section in required_sections:
            if section in injected_prompt:
                print_success(f"Prompt包含: {section}")
                checks.append(True)
            else:
                print_error(f"Prompt缺少: {section}")
                checks.append(False)

        print_info(f"注入后的Prompt长度: {len(injected_prompt)}字符")
        print_info(f"Prompt注入通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.6

    return asyncio.run(run_test())


def test_relationship_graph():
    """测试9: 关系图分析 - 使用实际实现"""
    print_header("测试9: 关系图分析 - 实际实现")

    profile_service = UserProfileService()
    graph_service = RelationshipGraphService()
    test_user_id = "test_user_008"

    async def run_test():
        # 创建用户画像
        profile = await profile_service.get_or_create_profile(test_user_id)
        profile.extracted_entities = {"PERSON": ["张三", "李四"], "GPE": ["北京"], "ORG": ["腾讯"]}
        profile.preferences["likes"] = ["游戏", "音乐", "旅行"]

        # 构建关系图
        graph_service.build_user_entity_graph(test_user_id, profile)

        checks = []

        # 检查图节点
        expected_nodes = [test_user_id, "张三", "李四", "北京", "腾讯", "游戏", "音乐", "旅行"]
        for node in expected_nodes:
            if node in graph_service.graph:
                print_success(f"图节点存在: {node}")
                checks.append(True)
            else:
                print_error(f"图节点缺失: {node}")
                checks.append(False)

        # 计算中心性
        centrality = graph_service.calculate_centrality(test_user_id)
        if centrality["degree"] > 0:
            print_success(f"中心性计算成功: degree={centrality['degree']}")
            checks.append(True)
        else:
            print_error("中心性计算失败")
            checks.append(False)

        # 推荐话题
        recommendations = graph_service.recommend_topics(test_user_id)
        if isinstance(recommendations, list):
            print_success(f"话题推荐成功: {len(recommendations)}个话题")
            checks.append(True)
        else:
            print_error("话题推荐失败")
            checks.append(False)

        print_info(f"关系图分析通过率: {sum(checks)}/{len(checks)}")
        return sum(checks) >= len(checks) * 0.7

    return asyncio.run(run_test())


def test_disclosure_depth_analysis():
    """测试10: 自我披露深度分析 - 使用实际实现"""
    print_header("测试10: 自我披露深度分析 - 实际实现")

    relationship_service = RelationshipService()

    test_cases = [
        ("今天天气真好啊", 0.0, 0.2, "表层话题"),
        ("我今天工作好累啊", 0.2, 0.4, "一般话题"),
        ("我最近和家里人吵架了，好烦", 0.4, 0.6, "个人话题"),
        ("我最近感情出问题了，真的好难过，不知道该怎么办", 0.6, 0.8, "深层话题"),
        ("我小时候受过很大的创伤，一直走不出来", 0.8, 1.0, "核心话题"),
    ]

    passed = 0
    for text, min_depth, max_depth, desc in test_cases:
        depth = relationship_service._analyze_disclosure_depth(text)

        if min_depth < depth <= max_depth:
            print_success(f"{desc}: '{text[:20]}...' -> 深度={depth:.2f}")
            passed += 1
        else:
            print_error(
                f"{desc}: '{text[:20]}...' -> 期望[{min_depth},{max_depth}], 实际{depth:.2f}"
            )

    print_info(f"披露深度分析通过率: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.6


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 用户画像与关系系统验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("用户画像创建", test_user_profile_creation()))
    except Exception as e:
        print_error(f"用户画像创建测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("用户画像创建", False))

    try:
        results.append(("实体提取", test_entity_extraction()))
    except Exception as e:
        print_error(f"实体提取测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("实体提取", False))

    try:
        results.append(("画像更新", test_profile_update_from_interaction()))
    except Exception as e:
        print_error(f"画像更新测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("画像更新", False))

    try:
        results.append(("互动记录", test_interaction_recording()))
    except Exception as e:
        print_error(f"互动记录测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("互动记录", False))

    try:
        results.append(("亲密度计算", test_intimacy_calculation()))
    except Exception as e:
        print_error(f"亲密度计算测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("亲密度计算", False))

    try:
        results.append(("关系阶段跃迁", test_relationship_stage_transition()))
    except Exception as e:
        print_error(f"关系阶段跃迁测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("关系阶段跃迁", False))

    try:
        results.append(("画像摘要生成", test_profile_summary_generation()))
    except Exception as e:
        print_error(f"画像摘要生成测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("画像摘要生成", False))

    try:
        results.append(("Prompt注入", test_prompt_injection()))
    except Exception as e:
        print_error(f"Prompt注入测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("Prompt注入", False))

    try:
        results.append(("关系图分析", test_relationship_graph()))
    except Exception as e:
        print_error(f"关系图分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("关系图分析", False))

    try:
        results.append(("披露深度分析", test_disclosure_depth_analysis()))
    except Exception as e:
        print_error(f"披露深度分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("披露深度分析", False))

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
        print(f"\n{Colors.GREEN}🎉 所有测试通过！用户画像与关系系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
