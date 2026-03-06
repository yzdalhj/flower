"""人格演化服务 - 动态人格调整"""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

from app.models.personality import PersonalityConfig, PersonalityDimension


@dataclass
class EvolutionConstraints:
    """人格演化约束配置"""

    # 单次变化限制（百分比）
    max_single_change_percent: float = 5.0  # 单次最大变化 5%

    # 核心特质变化限制（相对初始值的百分比）
    max_core_trait_change_percent: float = 20.0  # 核心特质最大变化 20%

    # 核心特质定义（这些特质变化受限）
    core_traits: Set[str] = None

    # 边界特质定义（这些特质可以自由演化）
    boundary_traits: Set[str] = None

    def __post_init__(self):
        """初始化默认核心和边界特质"""
        if self.core_traits is None:
            # 核心特质：定义人格基础的维度
            self.core_traits = {
                # Big Five 核心维度
                "openness",
                "conscientiousness",
                "extraversion",
                "agreeableness",
                "neuroticism",
                # 关键扩展特质
                "empathy",
                "warmth",
                "emotional_stability",
            }

        if self.boundary_traits is None:
            # 边界特质：可以根据用户偏好调整的维度
            self.boundary_traits = {
                "expressiveness",
                "humor",
                "sarcasm",
                "verbosity",
                "assertiveness",
                "casualness",
                "formality",
            }


@dataclass
class EvolutionRecord:
    """人格演化记录"""

    timestamp: datetime
    trigger: str  # 触发原因（如 "user_feedback", "interaction_analysis"）
    adjustments: Dict[str, Dict[str, float]]  # {category: {trait: change_amount}}
    reason: str  # 调整原因说明
    user_id: Optional[str] = None


class PersonalityEvolutionService:
    """
    人格演化服务
    负责基于交互历史动态调整人格参数
    """

    def __init__(
        self,
        constraints: Optional[EvolutionConstraints] = None,
        storage_dir: str = "./data/personality_evolution",
    ):
        self.constraints = constraints or EvolutionConstraints()
        self.storage_dir = storage_dir

        # 存储初始人格快照（用于计算核心特质变化）
        self._initial_snapshots: Dict[str, PersonalityConfig] = {}

    def register_initial_personality(self, user_id: str, personality: PersonalityConfig):
        """
        注册用户的初始人格配置
        用于后续计算核心特质的变化幅度

        Args:
            user_id: 用户ID
            personality: 初始人格配置
        """
        self._initial_snapshots[user_id] = copy.deepcopy(personality)

    def adjust_personality(
        self,
        current_personality: PersonalityConfig,
        adjustments: Dict[str, float],
        trigger: str = "manual",
        reason: str = "",
        user_id: Optional[str] = None,
    ) -> PersonalityConfig:
        """
        调整人格参数（应用约束）

        Args:
            current_personality: 当前人格配置
            adjustments: 调整量字典 {trait_name: change_amount}
            trigger: 触发原因
            reason: 调整原因说明
            user_id: 用户ID（用于核心特质约束检查）

        Returns:
            调整后的人格配置
        """
        updated = copy.deepcopy(current_personality)
        applied_adjustments = {"big_five": {}, "traits": {}}

        # 获取初始人格快照（如果有）
        initial_personality = None
        if user_id and user_id in self._initial_snapshots:
            initial_personality = self._initial_snapshots[user_id]

        # 应用调整
        for trait_name, change_amount in adjustments.items():
            # 确定特质所属类别
            if hasattr(updated.big_five, trait_name):
                category = "big_five"
                current_value = getattr(updated.big_five, trait_name)
                initial_value = (
                    getattr(initial_personality.big_five, trait_name)
                    if initial_personality
                    else current_value
                )
            elif hasattr(updated.traits, trait_name):
                category = "traits"
                current_value = getattr(updated.traits, trait_name)
                initial_value = (
                    getattr(initial_personality.traits, trait_name)
                    if initial_personality
                    else current_value
                )
            else:
                # 未知特质，跳过
                continue

            # 应用约束
            constrained_change = self._apply_constraints(
                trait_name=trait_name,
                current_value=current_value,
                initial_value=initial_value,
                change_amount=change_amount,
            )

            # 计算新值并限制在 0-100 范围内
            new_value = max(0.0, min(100.0, current_value + constrained_change))

            # 更新值
            if category == "big_five":
                setattr(updated.big_five, trait_name, new_value)
            else:
                setattr(updated.traits, trait_name, new_value)

            # 记录实际应用的调整
            if abs(constrained_change) > 0.01:  # 忽略极小变化
                applied_adjustments[category][trait_name] = constrained_change

        # 更新元数据
        updated.updated_at = datetime.now()
        updated.version += 1

        # 记录演化历史
        if any(applied_adjustments.values()):
            evolution_record = EvolutionRecord(
                timestamp=datetime.now(),
                trigger=trigger,
                adjustments=applied_adjustments,
                reason=reason,
                user_id=user_id,
            )
            updated.evolution_history.append(self._record_to_dict(evolution_record))

        return updated

    def _apply_constraints(
        self,
        trait_name: str,
        current_value: float,
        initial_value: float,
        change_amount: float,
    ) -> float:
        """
        应用演化约束

        Args:
            trait_name: 特质名称
            current_value: 当前值
            initial_value: 初始值
            change_amount: 期望变化量

        Returns:
            约束后的变化量
        """
        # 1. 单次变化限制（5%）
        max_single_change = current_value * (self.constraints.max_single_change_percent / 100.0)
        if abs(change_amount) > max_single_change:
            change_amount = max_single_change if change_amount > 0 else -max_single_change

        # 2. 核心特质变化限制（相对初始值 20%）
        if trait_name in self.constraints.core_traits:
            # 计算相对初始值的总变化
            new_value = current_value + change_amount
            total_change_from_initial = abs(new_value - initial_value)
            max_core_change = initial_value * (
                self.constraints.max_core_trait_change_percent / 100.0
            )

            if total_change_from_initial > max_core_change:
                # 限制总变化不超过 20%
                if new_value > initial_value:
                    # 向上变化
                    allowed_value = initial_value + max_core_change
                    change_amount = allowed_value - current_value
                else:
                    # 向下变化
                    allowed_value = initial_value - max_core_change
                    change_amount = allowed_value - current_value

        return change_amount

    def analyze_interaction_history(
        self,
        interaction_history: List[Dict],
        current_personality: PersonalityConfig,
    ) -> Dict[str, float]:
        """
        分析交互历史，生成人格调整建议

        Args:
            interaction_history: 交互历史列表
                每条记录包含: {
                    "user_message": str,
                    "ai_response": str,
                    "user_satisfaction": float,  # 0-1
                    "feedback_signals": Dict[str, float],  # 反馈信号
                }
            current_personality: 当前人格配置

        Returns:
            调整建议字典 {trait_name: suggested_change}
        """
        if not interaction_history:
            return {}

        adjustments = {}

        # 统计反馈信号
        feedback_counts = {}
        for interaction in interaction_history:
            signals = interaction.get("feedback_signals", {})
            for signal, strength in signals.items():
                if signal not in feedback_counts:
                    feedback_counts[signal] = []
                feedback_counts[signal].append(strength)

        # 根据反馈信号生成调整建议
        for signal, strengths in feedback_counts.items():
            avg_strength = sum(strengths) / len(strengths)

            if signal == "liked_humor" and avg_strength > 0.5:
                # 用户喜欢幽默 -> 增加幽默程度
                adjustments["humor"] = 3.0 * avg_strength

            elif signal == "wanted_more_empathy" and avg_strength > 0.5:
                # 用户希望更多共情 -> 增加共情能力
                adjustments["empathy"] = 2.0 * avg_strength

            elif signal == "felt_too_cold" and avg_strength > 0.5:
                # 用户觉得太冷淡 -> 增加温暖度
                adjustments["warmth"] = 3.0 * avg_strength

            elif signal == "too_verbose" and avg_strength > 0.5:
                # 用户觉得话太多 -> 减少话痨程度
                adjustments["verbosity"] = -3.0 * avg_strength

            elif signal == "too_formal" and avg_strength > 0.5:
                # 用户觉得太正式 -> 增加随意度，减少正式度
                adjustments["casualness"] = 3.0 * avg_strength
                adjustments["formality"] = -3.0 * avg_strength

            elif signal == "liked_sarcasm" and avg_strength > 0.5:
                # 用户喜欢吐槽 -> 增加吐槽倾向
                adjustments["sarcasm"] = 2.5 * avg_strength

            elif signal == "disliked_sarcasm" and avg_strength > 0.5:
                # 用户不喜欢吐槽 -> 减少吐槽倾向
                adjustments["sarcasm"] = -2.5 * avg_strength

        return adjustments

    def get_evolution_summary(
        self, personality: PersonalityConfig, user_id: Optional[str] = None
    ) -> Dict:
        """
        获取人格演化摘要

        Args:
            personality: 当前人格配置
            user_id: 用户ID

        Returns:
            演化摘要字典
        """
        summary = {
            "current_version": personality.version,
            "total_evolutions": len(personality.evolution_history),
            "last_updated": personality.updated_at.isoformat(),
            "evolution_history": personality.evolution_history[-5:],  # 最近5次
        }

        # 如果有初始快照，计算总变化
        if user_id and user_id in self._initial_snapshots:
            initial = self._initial_snapshots[user_id]
            summary["total_changes"] = self._calculate_total_changes(initial, personality)

        return summary

    def _calculate_total_changes(
        self, initial: PersonalityConfig, current: PersonalityConfig
    ) -> Dict[str, Dict[str, float]]:
        """计算总变化量"""
        changes = {"big_five": {}, "traits": {}}

        # Big Five 变化
        for dim in PersonalityDimension:
            trait_name = dim.value
            initial_value = getattr(initial.big_five, trait_name)
            current_value = getattr(current.big_five, trait_name)
            change = current_value - initial_value
            if abs(change) > 0.01:
                changes["big_five"][trait_name] = round(change, 2)

        # 扩展特质变化
        for trait_name in self.constraints.boundary_traits.union(self.constraints.core_traits):
            if hasattr(initial.traits, trait_name):
                initial_value = getattr(initial.traits, trait_name)
                current_value = getattr(current.traits, trait_name)
                change = current_value - initial_value
                if abs(change) > 0.01:
                    changes["traits"][trait_name] = round(change, 2)

        return changes

    def _record_to_dict(self, record: EvolutionRecord) -> Dict:
        """将演化记录转换为字典"""
        return {
            "timestamp": record.timestamp.isoformat(),
            "trigger": record.trigger,
            "adjustments": record.adjustments,
            "reason": record.reason,
            "user_id": record.user_id,
        }

    def validate_personality_consistency(
        self, personality: PersonalityConfig, user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        验证人格一致性

        Args:
            personality: 当前人格配置
            user_id: 用户ID

        Returns:
            验证结果 {
                "is_valid": bool,
                "violations": List[str],  # 违规项
                "warnings": List[str],    # 警告项
            }
        """
        result = {"is_valid": True, "violations": [], "warnings": []}

        # 检查核心特质变化是否超限
        if user_id and user_id in self._initial_snapshots:
            initial = self._initial_snapshots[user_id]

            for trait_name in self.constraints.core_traits:
                # Big Five
                if hasattr(initial.big_five, trait_name):
                    initial_value = getattr(initial.big_five, trait_name)
                    current_value = getattr(personality.big_five, trait_name)
                    change_percent = abs(current_value - initial_value) / initial_value * 100

                    if change_percent > self.constraints.max_core_trait_change_percent:
                        result["is_valid"] = False
                        result["violations"].append(
                            f"核心特质 {trait_name} 变化 {change_percent:.1f}% 超过限制 "
                            f"{self.constraints.max_core_trait_change_percent}%"
                        )
                    elif change_percent > self.constraints.max_core_trait_change_percent * 0.8:
                        result["warnings"].append(
                            f"核心特质 {trait_name} 变化 {change_percent:.1f}% 接近限制"
                        )

                # 扩展特质
                if hasattr(initial.traits, trait_name):
                    initial_value = getattr(initial.traits, trait_name)
                    current_value = getattr(personality.traits, trait_name)
                    change_percent = abs(current_value - initial_value) / initial_value * 100

                    if change_percent > self.constraints.max_core_trait_change_percent:
                        result["is_valid"] = False
                        result["violations"].append(
                            f"核心特质 {trait_name} 变化 {change_percent:.1f}% 超过限制 "
                            f"{self.constraints.max_core_trait_change_percent}%"
                        )
                    elif change_percent > self.constraints.max_core_trait_change_percent * 0.8:
                        result["warnings"].append(
                            f"核心特质 {trait_name} 变化 {change_percent:.1f}% 接近限制"
                        )

        return result


# 全局单例
_evolution_service: Optional[PersonalityEvolutionService] = None


def get_evolution_service() -> PersonalityEvolutionService:
    """获取人格演化服务单例"""
    global _evolution_service
    if _evolution_service is None:
        _evolution_service = PersonalityEvolutionService()
    return _evolution_service
