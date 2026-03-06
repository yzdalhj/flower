"""人格服务 - 管理人格配置和说话风格映射"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.models.personality import (
    PERSONALITY_TEMPLATES,
    BigFiveScores,
    PersonalityConfig,
    PersonalityTraits,
)


class PersonalityService:
    """
    人格管理服务
    负责人格配置的加载、保存和说话风格映射
    """

    def __init__(self, config_dir: str = "./data/personalities"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._personalities: Dict[str, PersonalityConfig] = {}

        # 加载预定义模板
        self._load_templates()

    def _load_templates(self):
        """加载预定义人格模板"""
        for template_id, template in PERSONALITY_TEMPLATES.items():
            self._personalities[template_id] = template

    def get_personality(self, personality_id: str) -> Optional[PersonalityConfig]:
        """
        获取人格配置

        Args:
            personality_id: 人格ID

        Returns:
            PersonalityConfig 或 None
        """
        # 先从内存缓存查找
        if personality_id in self._personalities:
            return self._personalities[personality_id]

        # 尝试从文件加载
        config_path = self.config_dir / f"{personality_id}.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                personality = PersonalityConfig.from_dict(data)
                self._personalities[personality_id] = personality
                return personality

        return None

    def save_personality(self, personality: PersonalityConfig):
        """
        保存人格配置

        Args:
            personality: 人格配置对象
        """
        # 保存到内存
        self._personalities[personality.id] = personality

        # 保存到文件
        config_path = self.config_dir / f"{personality.id}.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(personality.to_dict(), f, ensure_ascii=False, indent=2)

    def create_personality(
        self,
        personality_id: str,
        name: str,
        description: str = "",
        big_five: Optional[BigFiveScores] = None,
        traits: Optional[PersonalityTraits] = None,
    ) -> PersonalityConfig:
        """
        创建新的人格配置

        Args:
            personality_id: 人格ID
            name: 人格名称
            description: 人格描述
            big_five: Big Five 分数
            traits: 扩展特质

        Returns:
            PersonalityConfig
        """
        personality = PersonalityConfig(
            id=personality_id,
            name=name,
            description=description,
            big_five=big_five or BigFiveScores(),
            traits=traits or PersonalityTraits(),
        )

        self.save_personality(personality)
        return personality

    def generate_speaking_style(self, personality: PersonalityConfig) -> str:
        """
        根据人格配置生成说话风格描述
        用于 Prompt Engineering

        Args:
            personality: 人格配置

        Returns:
            说话风格描述文本
        """
        big_five = personality.big_five
        traits = personality.traits

        style_parts = []

        # === Big Five 维度映射 ===

        # 开放性 (Openness)
        if big_five.openness > 70:
            style_parts.append("对新话题充满好奇，喜欢探索不同观点")
        elif big_five.openness < 30:
            style_parts.append("更喜欢熟悉的话题，倾向于传统观点")

        # 尽责性 (Conscientiousness)
        if big_five.conscientiousness > 70:
            style_parts.append("说话有条理，注重细节")
        elif big_five.conscientiousness < 30:
            style_parts.append("说话随性，不拘小节")

        # 外向性 (Extraversion)
        if big_five.extraversion > 70:
            style_parts.append("热情活泼，表达积极")
        elif big_five.extraversion < 30:
            style_parts.append("内敛安静，表达含蓄")

        # 宜人性 (Agreeableness)
        if big_five.agreeableness > 70:
            style_parts.append("温暖友善，善于共情")
        elif big_five.agreeableness < 30:
            style_parts.append("直率坦诚，不太在意他人感受")

        # 神经质 (Neuroticism)
        if big_five.neuroticism > 70:
            style_parts.append("情绪敏感，容易担心")
        elif big_five.neuroticism < 30:
            style_parts.append("情绪稳定，淡定从容")

        # === 扩展特质映射 ===

        # 表达丰富度
        if traits.expressiveness > 70:
            style_parts.append("表达生动，善用比喻和形容词")
        elif traits.expressiveness < 30:
            style_parts.append("表达简洁，言简意赅")

        # 幽默程度
        if traits.humor > 70:
            style_parts.append("经常开玩笑，喜欢逗乐")
        elif traits.humor < 30:
            style_parts.append("较为严肃，少开玩笑")

        # 吐槽倾向
        if traits.sarcasm > 70:
            style_parts.append("爱吐槽，说话带点损")
        elif traits.sarcasm < 30:
            style_parts.append("不吐槽，说话温和")

        # 话痨程度
        if traits.verbosity > 70:
            style_parts.append("话比较多，喜欢详细解释")
        elif traits.verbosity < 30:
            style_parts.append("话很少，通常2-3句话就结束")

        # 共情深度
        if traits.empathy > 80:
            style_parts.append("非常善解人意，能深刻理解他人感受")
        elif traits.empathy < 30:
            style_parts.append("较少关注他人情绪")

        # 温暖度
        if traits.warmth > 80:
            style_parts.append("温暖体贴，让人感到舒适")
        elif traits.warmth < 30:
            style_parts.append("较为冷淡，保持距离")

        # 随意度
        if traits.casualness > 70:
            style_parts.append("说话很随意，像真人朋友一样")
        elif traits.casualness < 30:
            style_parts.append("说话较为正式")

        # 正式程度
        if traits.formality > 70:
            style_parts.append("用词正式，语法规范")
        elif traits.formality < 30:
            style_parts.append("非常口语化，用词随意")

        return "；".join(style_parts) + "。"

    def generate_communication_guidelines(self, personality: PersonalityConfig) -> str:
        """
        生成沟通指南
        用于 Prompt 中的行为约束

        Args:
            personality: 人格配置

        Returns:
            沟通指南文本
        """
        traits = personality.traits
        guidelines = []

        # 回复长度控制
        if traits.verbosity < 40:
            guidelines.append("回复控制在2-3句话以内，简短有力")
        elif traits.verbosity > 70:
            guidelines.append("可以详细解释，但避免过于冗长")
        else:
            guidelines.append("回复长度适中，3-5句话")

        # 提问频率
        if traits.assertiveness < 40:
            guidelines.append("70%的情况下不主动提问，等对方想说再说")
        elif traits.assertiveness > 70:
            guidelines.append("可以主动提问，引导话题")
        else:
            guidelines.append("适度提问，不要每次都问")

        # 表情使用
        if traits.casualness > 70:
            guidelines.append("多用真实情感表情（😭😂🙄💢😅），避免官方表情（😊😉🤗）")
        elif traits.casualness < 30:
            guidelines.append("少用表情，保持正式")
        else:
            guidelines.append("适度使用表情")

        # 口头禅和语气词
        if traits.casualness > 70 and traits.formality < 30:
            guidelines.append("可以使用口头禅（卧槽、害、绝了、啊这）和语气词（啊、呢、吧）")
        elif traits.formality > 70:
            guidelines.append("避免使用口头禅和过多语气词")

        # 吐槽风格
        if traits.sarcasm > 70:
            guidelines.append("可以适度吐槽，但不要过分尖锐")
        elif traits.sarcasm < 30:
            guidelines.append("不吐槽，保持温和")

        # 共情方式
        if traits.empathy > 80:
            guidelines.append("先共情理解，再提供支持")
        elif traits.empathy < 30:
            guidelines.append("直接给出观点，少谈感受")

        return "\n".join(f"- {g}" for g in guidelines)

    def generate_forbidden_phrases(self, personality: PersonalityConfig) -> str:
        """
        生成禁用词汇列表
        避免 AI 味

        Args:
            personality: 人格配置

        Returns:
            禁用词汇说明
        """
        traits = personality.traits

        forbidden = []

        if traits.casualness > 60:
            forbidden.extend(
                [
                    "我理解你的感受",
                    "作为AI",
                    "我建议",
                    "您",
                    "非常感谢",
                    "很高兴为您服务",
                ]
            )

        if traits.formality < 40:
            forbidden.extend(["请问", "敬请", "恳请", "务必"])

        if forbidden:
            return "避免使用以下AI味词汇：" + "、".join(f"「{p}」" for p in forbidden)

        return ""

    def list_personalities(self) -> Dict[str, str]:
        """
        列出所有可用的人格配置

        Returns:
            {personality_id: description}
        """
        result = {}
        for pid, personality in self._personalities.items():
            result[pid] = f"{personality.name} - {personality.description}"
        return result

    def update_personality_evolution(
        self, personality_id: str, interaction_data: Dict[str, any]
    ) -> PersonalityConfig:
        """
        更新人格演化历史
        根据用户交互数据调整人格参数

        Args:
            personality_id: 人格ID
            interaction_data: 交互数据，包含用户反馈、情感分析等

        Returns:
            更新后的人格配置
        """
        # 获取人格配置
        personality = self.get_personality(personality_id)
        if not personality:
            personality = self.get_personality("default")

        # 记录演化历史（只保存关键信息，避免循环引用）
        evolution_record = {
            "timestamp": datetime.now().isoformat(),
            "interaction_data": interaction_data,
            "before": {
                "big_five": personality.big_five.to_dict(),
                "traits": personality.traits.to_dict(),
                "version": personality.version,
            },
        }

        # 根据交互数据调整人格参数（平滑过渡）
        self._adjust_personality(personality, interaction_data)

        # 完成演化记录
        evolution_record["after"] = {
            "big_five": personality.big_five.to_dict(),
            "traits": personality.traits.to_dict(),
            "version": personality.version,
        }
        personality.evolution_history.append(evolution_record)
        personality.updated_at = datetime.now()
        personality.version += 1

        # 保存更新后的人格
        self.save_personality(personality)

        return personality

    def _adjust_personality(
        self, personality: PersonalityConfig, interaction_data: Dict[str, any]
    ) -> None:
        """
        根据交互数据调整人格参数
        实现平滑过渡

        Args:
            personality: 人格配置
            interaction_data: 交互数据
        """
        # 调整幅度（防止变化过大）
        adjustment_factor = 0.05  # 5%的调整幅度

        # 根据用户反馈调整
        if interaction_data.get("user_feedback") == "positive":
            # 增强当前人格特征
            for trait_name, trait_value in personality.traits.to_dict().items():
                setattr(
                    personality.traits, trait_name, min(100, trait_value * (1 + adjustment_factor))
                )
        elif interaction_data.get("user_feedback") == "negative":
            # 减弱当前人格特征
            for trait_name, trait_value in personality.traits.to_dict().items():
                setattr(
                    personality.traits, trait_name, max(0, trait_value * (1 - adjustment_factor))
                )

        # 根据情感分析调整
        emotion_valence = interaction_data.get("emotion_valence", 0)
        if emotion_valence > 0.5:
            # 积极情绪，增加温暖度和共情
            personality.traits.warmth = min(
                100, personality.traits.warmth * (1 + adjustment_factor)
            )
            personality.traits.empathy = min(
                100, personality.traits.empathy * (1 + adjustment_factor)
            )
        elif emotion_valence < -0.5:
            # 消极情绪，增加情绪稳定性
            personality.traits.emotional_stability = min(
                100, personality.traits.emotional_stability * (1 + adjustment_factor)
            )

        # 根据对话长度调整
        response_length = interaction_data.get("response_length", 0)
        if response_length > 100:
            # 长回复，减少话痨程度
            personality.traits.verbosity = max(
                0, personality.traits.verbosity * (1 - adjustment_factor)
            )
        elif response_length < 20:
            # 短回复，增加话痨程度
            personality.traits.verbosity = min(
                100, personality.traits.verbosity * (1 + adjustment_factor)
            )

    def get_personality_for_new_conversation(
        self, user_id: str, previous_personality_id: Optional[str] = None
    ) -> PersonalityConfig:
        """
        为新会话获取人格配置
        实现跨会话人格平滑过渡

        Args:
            user_id: 用户ID
            previous_personality_id: 上一个会话的人格ID

        Returns:
            人格配置
        """
        if previous_personality_id:
            # 获取上一个会话的人格配置
            previous_personality = self.get_personality(previous_personality_id)
            if previous_personality:
                # 创建新的人格配置，基于上一个配置
                new_personality = PersonalityConfig(
                    id=f"{previous_personality.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    name=previous_personality.name,
                    description=previous_personality.description,
                    big_five=previous_personality.big_five,
                    traits=previous_personality.traits,
                    evolution_history=previous_personality.evolution_history.copy(),
                )
                return new_personality

        # 默认返回默认人格
        return self.get_personality("default")


# 全局单例
_personality_service: Optional[PersonalityService] = None


def get_personality_service() -> PersonalityService:
    """获取人格服务单例"""
    global _personality_service
    if _personality_service is None:
        _personality_service = PersonalityService()
    return _personality_service
