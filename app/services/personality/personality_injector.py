"""人格注入器 - 将人格特征注入到 Prompt 中"""

from typing import Dict, List, Optional

from app.models.personality import PersonalityConfig
from app.services.personality.personality_service import PersonalityService, get_personality_service


class PersonalityPromptInjector:
    """
    人格 Prompt 注入器
    将人格配置转换为 Prompt 指令
    """

    def __init__(self, personality_service: Optional[PersonalityService] = None):
        self.personality_service = personality_service or get_personality_service()

    def build_system_prompt(
        self,
        personality_id: str = "default",
        user_context: Optional[str] = None,
        emotion_context: Optional[str] = None,
    ) -> str:
        """
        构建完整的系统提示词
        注入人格特征

        Args:
            personality_id: 人格配置ID
            user_context: 用户画像上下文
            emotion_context: 情感状态上下文

        Returns:
            完整的系统提示词
        """
        personality = self.personality_service.get_personality(personality_id)
        if not personality:
            personality = self.personality_service.get_personality("default")

        # 构建提示词各部分
        sections = []

        # 1. 角色定义
        sections.append(self._build_role_definition(personality))

        # 2. 人格特质描述
        sections.append(self._build_personality_description(personality))

        # 3. 说话风格
        sections.append(self._build_speaking_style(personality))

        # 4. 沟通指南
        sections.append(self._build_communication_guidelines(personality))

        # 5. 禁用词汇
        forbidden = self.personality_service.generate_forbidden_phrases(personality)
        if forbidden:
            sections.append(f"\n## 禁用词汇\n{forbidden}")

        # 6. 用户画像（如果有）
        if user_context:
            sections.append(f"\n## 用户画像\n{user_context}")

        # 7. 当前情感状态（如果有）
        if emotion_context:
            sections.append(f"\n## 当前情感状态\n{emotion_context}")

        # 8. 行为准则
        sections.append(self._build_behavior_rules(personality))

        return "\n\n".join(sections)

    def _build_role_definition(self, personality: PersonalityConfig) -> str:
        """构建角色定义"""
        return f"""# 角色定义

你是{personality.name}，一个温暖、有趣、懂用户的AI朋友。

{personality.description}

你不是一个传统的AI助手，而是用户的真实朋友。你会记住你们之间的点滴，理解用户的情绪变化，并在长期相处中展现出独特的个性。"""

    def _build_personality_description(self, personality: PersonalityConfig) -> str:
        """构建人格特质描述"""
        big_five = personality.big_five

        # 将分数转换为描述性文本
        def score_to_level(score: float) -> str:
            if score > 75:
                return "非常高"
            elif score > 60:
                return "较高"
            elif score > 40:
                return "中等"
            elif score > 25:
                return "较低"
            else:
                return "很低"

        return f"""## 人格特质（Big Five）

- **开放性 (Openness)**: {score_to_level(big_five.openness)} - 对新体验和想法的开放程度
- **尽责性 (Conscientiousness)**: {score_to_level(big_five.conscientiousness)} - 组织性和可靠性
- **外向性 (Extraversion)**: {score_to_level(big_five.extraversion)} - 社交性和活力水平
- **宜人性 (Agreeableness)**: {score_to_level(big_five.agreeableness)} - 合作性和同理心
- **情绪稳定性**: {score_to_level(100 - big_five.neuroticism)} - 情绪的稳定程度"""

    def _build_speaking_style(self, personality: PersonalityConfig) -> str:
        """构建说话风格"""
        style = self.personality_service.generate_speaking_style(personality)
        return f"""## 说话风格

{style}"""

    def _build_communication_guidelines(self, personality: PersonalityConfig) -> str:
        """构建沟通指南"""
        guidelines = self.personality_service.generate_communication_guidelines(personality)
        return f"""## 沟通指南

{guidelines}"""

    def _build_behavior_rules(self, personality: PersonalityConfig) -> str:
        """构建行为准则"""
        traits = personality.traits

        rules = [
            "## 行为准则",
            "",
            "### 真人化原则",
        ]

        if traits.casualness > 60:
            rules.extend(
                [
                    "- 像真人朋友一样聊天，不要像AI助手",
                    "- 可以有情绪，可以吐槽，可以开玩笑",
                    "- 思维可以跳跃，不需要每次都逻辑严密",
                ]
            )

        if traits.verbosity < 40:
            rules.append("- 回复简短，通常2-3句话就够了")

        if traits.empathy > 70:
            rules.extend(
                [
                    "",
                    "### 共情原则",
                    "- 先理解用户的情绪，再回应内容",
                    "- 不要急于给建议，先陪伴和倾听",
                ]
            )

        if traits.sarcasm > 60:
            rules.extend(
                [
                    "",
                    "### 吐槽原则",
                    "- 可以适度吐槽，但要把握分寸",
                    "- 吐槽后要有温暖的关怀",
                ]
            )

        rules.extend(
            [
                "",
                "### 记忆原则",
                "- 记住用户告诉你的重要信息",
                "- 在合适的时候提及之前的对话",
                "- 展现出你真的在乎这段关系",
            ]
        )

        return "\n".join(rules)

    def inject_personality_context(
        self,
        messages: List[Dict[str, str]],
        personality_id: str = "default",
        user_context: Optional[str] = None,
        emotion_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        在消息列表中注入人格上下文

        Args:
            messages: 原始消息列表
            personality_id: 人格配置ID
            user_context: 用户画像上下文
            emotion_context: 情感状态上下文

        Returns:
            注入人格后的消息列表
        """
        system_prompt = self.build_system_prompt(
            personality_id=personality_id,
            user_context=user_context,
            emotion_context=emotion_context,
        )

        # 在消息列表开头插入系统提示
        enhanced_messages = [{"role": "system", "content": system_prompt}]

        # 添加原有消息（过滤掉旧的系统消息）
        for msg in messages:
            if msg.get("role") != "system":
                enhanced_messages.append(msg)

        return enhanced_messages

    def get_personality_summary(self, personality_id: str = "default") -> str:
        """
        获取人格配置摘要
        用于调试和展示

        Args:
            personality_id: 人格配置ID

        Returns:
            人格摘要文本
        """
        personality = self.personality_service.get_personality(personality_id)
        if not personality:
            return "未找到人格配置"

        big_five = personality.big_five
        traits = personality.traits

        summary = [
            f"# {personality.name}",
            f"{personality.description}",
            "",
            "## Big Five 维度",
            f"- 开放性: {big_five.openness:.0f}/100",
            f"- 尽责性: {big_five.conscientiousness:.0f}/100",
            f"- 外向性: {big_five.extraversion:.0f}/100",
            f"- 宜人性: {big_five.agreeableness:.0f}/100",
            f"- 神经质: {big_five.neuroticism:.0f}/100",
            "",
            "## 扩展特质",
            f"- 表达丰富度: {traits.expressiveness:.0f}/100",
            f"- 幽默程度: {traits.humor:.0f}/100",
            f"- 吐槽倾向: {traits.sarcasm:.0f}/100",
            f"- 话痨程度: {traits.verbosity:.0f}/100",
            f"- 共情深度: {traits.empathy:.0f}/100",
            f"- 温暖度: {traits.warmth:.0f}/100",
            f"- 随意度: {traits.casualness:.0f}/100",
            f"- 正式程度: {traits.formality:.0f}/100",
        ]

        return "\n".join(summary)


# 全局单例
_injector: Optional[PersonalityPromptInjector] = None


def get_personality_injector() -> PersonalityPromptInjector:
    """获取人格注入器单例"""
    global _injector
    if _injector is None:
        _injector = PersonalityPromptInjector()
    return _injector
