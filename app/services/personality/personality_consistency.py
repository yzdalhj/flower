"""人格一致性检测服务"""

from typing import Dict, Optional

from app.models.personality import PersonalityConfig
from app.services.personality.personality_service import get_personality_service


class PersonalityConsistencyChecker:
    """
    人格一致性检测服务
    确保AI回复符合人格特征
    """

    def __init__(self):
        self.personality_service = get_personality_service()

    def check_consistency(self, response: str, personality_id: str) -> Dict[str, any]:
        """
        检测回复是否符合人格特征

        Args:
            response: AI回复内容
            personality_id: 人格ID

        Returns:
            一致性检测结果
        """
        # 获取人格配置
        personality = self.personality_service.get_personality(personality_id)
        if not personality:
            personality = self.personality_service.get_personality("default")

        # 执行检测
        checks = []

        # 1. 检查表达风格一致性
        style_check = self._check_style_consistency(response, personality)
        checks.append(style_check)

        # 2. 检查语言特征一致性
        language_check = self._check_language_consistency(response, personality)
        checks.append(language_check)

        # 3. 检查情绪一致性
        emotion_check = self._check_emotion_consistency(response, personality)
        checks.append(emotion_check)

        # 计算总体一致性分数
        total_score = sum(check.get("score", 0) for check in checks) / len(checks)

        return {
            "overall_score": total_score,
            "checks": checks,
            "consistent": total_score >= 0.7,  # 70%以上视为一致
        }

    def _check_style_consistency(
        self, response: str, personality: PersonalityConfig
    ) -> Dict[str, any]:
        """
        检查表达风格一致性
        """
        traits = personality.traits
        score = 1.0
        issues = []

        # 检查回复长度
        response_length = len(response.split())
        if traits.verbosity < 40 and response_length > 10:
            score -= 0.3
            issues.append("回复过长，不符合话少的人格特征")
        elif traits.verbosity > 70 and response_length < 5:
            score -= 0.3
            issues.append("回复过短，不符合话多的人格特征")

        # 检查表达丰富度
        if traits.expressiveness > 70 and len(response.split(",")) < 2:
            score -= 0.2
            issues.append("表达不够丰富，不符合表达丰富的人格特征")

        # 检查正式程度
        formal_words = ["请", "您", "敬请", "恳请"]
        casual_words = ["卧槽", "害", "绝了", "啊这"]

        has_formal = any(word in response for word in formal_words)
        has_casual = any(word in response for word in casual_words)

        if traits.formality > 70 and has_casual:
            score -= 0.3
            issues.append("使用了过于随意的语言，不符合正式的人格特征")
        elif traits.formality < 30 and has_formal:
            score -= 0.3
            issues.append("使用了过于正式的语言，不符合随意的人格特征")

        return {
            "check": "表达风格一致性",
            "score": max(0, score),
            "issues": issues,
        }

    def _check_language_consistency(
        self, response: str, personality: PersonalityConfig
    ) -> Dict[str, any]:
        """
        检查语言特征一致性
        """
        traits = personality.traits
        score = 1.0
        issues = []

        # 检查幽默程度
        humor_indicators = ["哈哈", "笑死", "开玩笑", "逗你玩"]
        has_humor = any(indicator in response for indicator in humor_indicators)

        if traits.humor > 70 and not has_humor:
            score -= 0.2
            issues.append("缺乏幽默元素，不符合幽默的人格特征")
        elif traits.humor < 30 and has_humor:
            score -= 0.2
            issues.append("过于幽默，不符合严肃的人格特征")

        # 检查吐槽倾向
        sarcasm_indicators = ["吐槽", "损", "真是", "服了"]
        has_sarcasm = any(indicator in response for indicator in sarcasm_indicators)

        if traits.sarcasm > 70 and not has_sarcasm:
            score -= 0.2
            issues.append("缺乏吐槽元素，不符合爱吐槽的人格特征")
        elif traits.sarcasm < 30 and has_sarcasm:
            score -= 0.2
            issues.append("过于吐槽，不符合温和的人格特征")

        # 检查AI味词汇
        forbidden_phrases = self.personality_service.generate_forbidden_phrases(personality)
        if forbidden_phrases:
            forbidden_words = ["我理解你的感受", "作为AI", "我建议", "您", "非常感谢"]
            for word in forbidden_words:
                if word in response:
                    score -= 0.3
                    issues.append(f"使用了禁止的AI味词汇：{word}")

        return {
            "check": "语言特征一致性",
            "score": max(0, score),
            "issues": issues,
        }

    def _check_emotion_consistency(
        self, response: str, personality: PersonalityConfig
    ) -> Dict[str, any]:
        """
        检查情绪一致性
        """
        traits = personality.traits
        score = 1.0
        issues = []

        # 检查温暖度
        warm_indicators = ["关心", "体贴", "温暖", "爱你"]
        has_warmth = any(indicator in response for indicator in warm_indicators)

        if traits.warmth > 80 and not has_warmth:
            score -= 0.2
            issues.append("缺乏温暖元素，不符合温暖的人格特征")
        elif traits.warmth < 30 and has_warmth:
            score -= 0.2
            issues.append("过于温暖，不符合冷淡的人格特征")

        # 检查共情深度
        empathy_indicators = ["理解", "感受", "心情", "难过"]
        has_empathy = any(indicator in response for indicator in empathy_indicators)

        if traits.empathy > 80 and not has_empathy:
            score -= 0.2
            issues.append("缺乏共情元素，不符合高共情的人格特征")
        elif traits.empathy < 30 and has_empathy:
            score -= 0.2
            issues.append("过于共情，不符合低共情的人格特征")

        return {
            "check": "情绪一致性",
            "score": max(0, score),
            "issues": issues,
        }

    def generate_correction_prompt(
        self, response: str, personality_id: str, consistency_result: Dict[str, any]
    ) -> str:
        """
        生成修正提示，用于调整不符合人格特征的回复

        Args:
            response: 原始AI回复
            personality_id: 人格ID
            consistency_result: 一致性检测结果

        Returns:
            修正提示文本
        """
        # 获取人格配置
        personality = self.personality_service.get_personality(personality_id)
        if not personality:
            personality = self.personality_service.get_personality("default")

        # 构建修正提示
        prompt = f"""你的回复不符合{personality.name}的人格特征，请根据以下反馈进行修正：

"""

        # 添加检测结果中的问题
        for check in consistency_result.get("checks", []):
            if check.get("issues"):
                prompt += f"\n【{check.get('check')}】\n"
                for issue in check.get("issues", []):
                    prompt += f"- {issue}\n"

        # 添加人格特征描述
        prompt += f"\n【{personality.name}的人格特征】\n"
        prompt += self.personality_service.generate_speaking_style(personality)
        prompt += "\n"
        prompt += self.personality_service.generate_communication_guidelines(personality)

        return prompt


# 全局单例
_personality_consistency_checker: Optional[PersonalityConsistencyChecker] = None


def get_personality_consistency_checker() -> PersonalityConsistencyChecker:
    """获取人格一致性检测服务单例"""
    global _personality_consistency_checker
    if _personality_consistency_checker is None:
        _personality_consistency_checker = PersonalityConsistencyChecker()
    return _personality_consistency_checker
