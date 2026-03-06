"""
强化学习优化服务 - 基于用户反馈的人格参数优化

本模块实现简化的强化学习算法，用于根据用户反馈自主优化AI人格：
1. 用户反馈收集（满意度、点赞/点踩）
2. 奖励函数设计（对话质量、用户满意度）
3. 策略更新机制（基于反馈调整行为）
4. 人格参数渐进式调整

注意：这是简化的RL，不是完整的深度强化学习，而是基于规则的策略优化
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.models.personality import PersonalityConfig
from app.services.learning.continual_learning import ContinualLearningService


class FeedbackType(Enum):
    """反馈类型"""

    THUMBS_UP = "thumbs_up"  # 点赞
    THUMBS_DOWN = "thumbs_down"  # 点踩
    RATING = "rating"  # 评分 (1-5)
    IMPLICIT = "implicit"  # 隐式反馈（对话长度、参与度等）


@dataclass
class UserFeedback:
    """
    用户反馈数据
    """

    id: str
    user_id: str
    conversation_id: str
    message_id: str
    timestamp: datetime

    # 反馈类型和值
    feedback_type: FeedbackType
    feedback_value: float  # 归一化到 0-1

    # 上下文信息
    user_message: str
    ai_response: str
    conversation_length: int  # 对话轮数
    response_time: float  # 响应时间（秒）

    # 情感信息
    user_emotion: Optional[str] = None
    ai_emotion: Optional[str] = None
    emotional_resonance: float = 0.5

    # 人格快照
    personality_snapshot: Dict[str, float] = field(default_factory=dict)

    # 额外元数据
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "feedback_type": self.feedback_type.value,
            "feedback_value": self.feedback_value,
            "user_message": self.user_message,
            "ai_response": self.ai_response,
            "conversation_length": self.conversation_length,
            "response_time": self.response_time,
            "user_emotion": self.user_emotion,
            "ai_emotion": self.ai_emotion,
            "emotional_resonance": self.emotional_resonance,
            "personality_snapshot": self.personality_snapshot,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserFeedback":
        """从字典创建"""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            conversation_id=data["conversation_id"],
            message_id=data["message_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            feedback_type=FeedbackType(data["feedback_type"]),
            feedback_value=data["feedback_value"],
            user_message=data["user_message"],
            ai_response=data["ai_response"],
            conversation_length=data["conversation_length"],
            response_time=data["response_time"],
            user_emotion=data.get("user_emotion"),
            ai_emotion=data.get("ai_emotion"),
            emotional_resonance=data.get("emotional_resonance", 0.5),
            personality_snapshot=data.get("personality_snapshot", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RewardSignal:
    """
    奖励信号
    用于强化学习的奖励计算
    """

    # 基础奖励
    user_satisfaction: float  # 用户满意度 (0-1)
    conversation_quality: float  # 对话质量 (0-1)
    emotional_resonance: float  # 情感共鸣 (0-1)

    # 惩罚项
    response_too_long: float = 0.0  # 回复过长惩罚
    response_too_short: float = 0.0  # 回复过短惩罚
    ai_flavor_penalty: float = 0.0  # AI味惩罚
    inconsistency_penalty: float = 0.0  # 人格不一致惩罚

    # 奖励项
    humor_bonus: float = 0.0  # 幽默奖励
    empathy_bonus: float = 0.0  # 共情奖励
    engagement_bonus: float = 0.0  # 参与度奖励

    def calculate_total_reward(self) -> float:
        """
        计算总奖励
        范围: -1 到 1
        """
        # 基础奖励（权重：0.6）
        base_reward = (
            self.user_satisfaction * 0.3
            + self.conversation_quality * 0.2
            + self.emotional_resonance * 0.1
        )

        # 惩罚项（权重：-0.3）
        penalties = (
            self.response_too_long * 0.1
            + self.response_too_short * 0.05
            + self.ai_flavor_penalty * 0.1
            + self.inconsistency_penalty * 0.05
        )

        # 奖励项（权重：0.1）
        bonuses = self.humor_bonus * 0.03 + self.empathy_bonus * 0.04 + self.engagement_bonus * 0.03

        total = base_reward - penalties + bonuses

        # 限制在 [-1, 1] 范围内
        return max(-1.0, min(1.0, total))


class RewardFunction:
    """
    奖励函数
    根据用户反馈和对话质量计算奖励信号
    """

    def __init__(
        self,
        ideal_response_length: Tuple[int, int] = (50, 200),  # 理想回复长度（字符）
        ai_flavor_keywords: List[str] = None,
    ):
        self.ideal_response_length = ideal_response_length
        self.ai_flavor_keywords = ai_flavor_keywords or [
            "我理解你的感受",
            "作为AI",
            "我建议",
            "非常感谢",
            "很高兴为您服务",
        ]

    def calculate_reward(
        self,
        feedback: UserFeedback,
        previous_personality: Optional[PersonalityConfig] = None,
        current_personality: Optional[PersonalityConfig] = None,
    ) -> RewardSignal:
        """
        计算奖励信号

        Args:
            feedback: 用户反馈
            previous_personality: 上一次的人格配置（用于检测一致性）
            current_personality: 当前人格配置

        Returns:
            RewardSignal对象
        """
        # 1. 用户满意度（来自显式反馈）
        user_satisfaction = feedback.feedback_value

        # 2. 对话质量（基于对话长度和参与度）
        conversation_quality = self._calculate_conversation_quality(feedback)

        # 3. 情感共鸣
        emotional_resonance = feedback.emotional_resonance

        # 4. 惩罚项
        response_too_long = self._check_response_length_penalty(feedback.ai_response, too_long=True)
        response_too_short = self._check_response_length_penalty(
            feedback.ai_response, too_long=False
        )
        ai_flavor_penalty = self._check_ai_flavor(feedback.ai_response)
        inconsistency_penalty = self._check_personality_consistency(
            previous_personality, current_personality
        )

        # 5. 奖励项
        humor_bonus = self._detect_humor_success(feedback)
        empathy_bonus = self._detect_empathy_success(feedback)
        engagement_bonus = self._calculate_engagement_bonus(feedback)

        return RewardSignal(
            user_satisfaction=user_satisfaction,
            conversation_quality=conversation_quality,
            emotional_resonance=emotional_resonance,
            response_too_long=response_too_long,
            response_too_short=response_too_short,
            ai_flavor_penalty=ai_flavor_penalty,
            inconsistency_penalty=inconsistency_penalty,
            humor_bonus=humor_bonus,
            empathy_bonus=empathy_bonus,
            engagement_bonus=engagement_bonus,
        )

    def _calculate_conversation_quality(self, feedback: UserFeedback) -> float:
        """
        计算对话质量
        基于对话长度和响应时间
        """
        # 对话长度奖励（越长越好，但有上限）
        length_score = min(1.0, feedback.conversation_length / 10.0)

        # 响应时间惩罚（太快或太慢都不好）
        if feedback.response_time < 0.5:
            time_score = 0.7  # 太快，可能不够用心
        elif feedback.response_time > 10.0:
            time_score = 0.6  # 太慢，用户可能不耐烦
        else:
            time_score = 1.0

        return length_score * 0.6 + time_score * 0.4

    def _check_response_length_penalty(self, response: str, too_long: bool = True) -> float:
        """
        检查回复长度惩罚
        """
        length = len(response)
        min_len, max_len = self.ideal_response_length

        if too_long and length > max_len:
            # 超出理想长度，惩罚
            excess = length - max_len
            return min(1.0, excess / max_len)
        elif not too_long and length < min_len:
            # 低于理想长度，惩罚
            deficit = min_len - length
            return min(1.0, deficit / min_len)

        return 0.0

    def _check_ai_flavor(self, response: str) -> float:
        """
        检查AI味（使用禁用词汇）
        """
        count = sum(1 for keyword in self.ai_flavor_keywords if keyword in response)
        return min(1.0, count * 0.3)

    def _check_personality_consistency(
        self,
        previous: Optional[PersonalityConfig],
        current: Optional[PersonalityConfig],
    ) -> float:
        """
        检查人格一致性
        同一会话内人格不应该变化太大
        """
        if not previous or not current:
            return 0.0

        # 计算人格参数的变化幅度
        prev_traits = previous.traits.to_dict()
        curr_traits = current.traits.to_dict()

        total_change = 0.0
        for key in prev_traits:
            if key in curr_traits:
                change = abs(curr_traits[key] - prev_traits[key])
                total_change += change

        # 平均变化超过5分，认为不一致
        avg_change = total_change / len(prev_traits)
        if avg_change > 5.0:
            return min(1.0, (avg_change - 5.0) / 10.0)

        return 0.0

    def _detect_humor_success(self, feedback: UserFeedback) -> float:
        """
        检测幽默是否成功
        基于用户反应和情感
        """
        # 简单启发式：如果用户情感是积极的且满意度高
        if feedback.user_emotion in ["happy", "amused", "joyful"]:
            if feedback.feedback_value > 0.7:
                return 1.0
        return 0.0

    def _detect_empathy_success(self, feedback: UserFeedback) -> float:
        """
        检测共情是否成功
        """
        # 情感共鸣度高 + 满意度高 = 共情成功
        if feedback.emotional_resonance > 0.7 and feedback.feedback_value > 0.7:
            return 1.0
        return 0.0

    def _calculate_engagement_bonus(self, feedback: UserFeedback) -> float:
        """
        计算参与度奖励
        对话轮数多 = 用户愿意继续聊
        """
        if feedback.conversation_length > 5:
            return min(1.0, feedback.conversation_length / 20.0)
        return 0.0


class PolicyUpdater:
    """
    策略更新器
    基于奖励信号更新人格参数（策略）
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.1,
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor  # 未来奖励的折扣因子
        self.exploration_rate = exploration_rate  # 探索率（随机调整的概率）

        # 策略历史（用于计算趋势）
        self.policy_history: Dict[str, List[Tuple[datetime, float]]] = {}

    def update_policy(
        self,
        current_personality: PersonalityConfig,
        reward_signal: RewardSignal,
        feedback: UserFeedback,
    ) -> Dict[str, float]:
        """
        基于奖励信号更新策略（人格参数）

        Args:
            current_personality: 当前人格配置
            reward_signal: 奖励信号
            feedback: 用户反馈

        Returns:
            参数调整字典 {param_path: delta}
        """
        total_reward = reward_signal.calculate_total_reward()

        adjustments = {}

        # 1. 基于奖励的调整
        if total_reward > 0:
            # 正向奖励：强化当前策略
            adjustments.update(self._reinforce_current_policy(current_personality, total_reward))
        else:
            # 负向奖励：探索新策略
            adjustments.update(self._explore_new_policy(current_personality, abs(total_reward)))

        # 2. 基于具体反馈的调整
        adjustments.update(self._adjust_based_on_feedback(feedback, reward_signal))

        # 3. 应用学习率
        for key in adjustments:
            adjustments[key] *= self.learning_rate

        return adjustments

    def _reinforce_current_policy(
        self, personality: PersonalityConfig, reward: float
    ) -> Dict[str, float]:
        """
        强化当前策略
        奖励高时，保持当前人格参数不变或微调
        """
        adjustments = {}

        # 微调：向更极端的方向移动（强化特征）
        traits = personality.traits.to_dict()

        for param_name, value in traits.items():
            # 如果参数已经偏向某一端，继续强化
            if value > 60:
                # 高值参数，继续增加
                adjustments[f"traits.{param_name}"] = reward * 2.0
            elif value < 40:
                # 低值参数，继续减少
                adjustments[f"traits.{param_name}"] = -reward * 2.0
            # 中间值不调整

        return adjustments

    def _explore_new_policy(
        self, personality: PersonalityConfig, penalty: float
    ) -> Dict[str, float]:
        """
        探索新策略
        惩罚高时，尝试调整人格参数
        """
        import random

        adjustments = {}

        # 随机选择几个参数进行探索性调整
        traits = personality.traits.to_dict()
        params_to_explore = random.sample(list(traits.keys()), k=min(3, len(traits)))

        for param_name in params_to_explore:
            # 随机调整方向
            direction = random.choice([-1, 1])
            # 调整幅度与惩罚成正比
            magnitude = penalty * 5.0 * direction
            adjustments[f"traits.{param_name}"] = magnitude

        return adjustments

    def _adjust_based_on_feedback(
        self, feedback: UserFeedback, reward_signal: RewardSignal
    ) -> Dict[str, float]:
        """
        基于具体反馈调整
        """
        adjustments = {}

        # 回复过长 -> 减少话痨程度
        if reward_signal.response_too_long > 0.5:
            adjustments["traits.verbosity"] = -5.0

        # 回复过短 -> 增加话痨程度
        if reward_signal.response_too_short > 0.5:
            adjustments["traits.verbosity"] = 5.0

        # AI味重 -> 增加随意度
        if reward_signal.ai_flavor_penalty > 0.5:
            adjustments["traits.casualness"] = 5.0
            adjustments["traits.formality"] = -5.0

        # 幽默成功 -> 增加幽默
        if reward_signal.humor_bonus > 0.5:
            adjustments["traits.humor"] = 3.0

        # 共情成功 -> 增加共情
        if reward_signal.empathy_bonus > 0.5:
            adjustments["traits.empathy"] = 3.0

        # 参与度高 -> 增加外向性
        if reward_signal.engagement_bonus > 0.5:
            adjustments["big_five.extraversion"] = 2.0

        return adjustments


class ReinforcementLearningService:
    """
    强化学习服务
    整合反馈收集、奖励计算和策略更新
    """

    def __init__(
        self,
        continual_learning: ContinualLearningService,
        storage_dir: str = "./data/rl_feedback",
        learning_rate: float = 0.1,
    ):
        self.continual_learning = continual_learning
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 组件
        self.reward_function = RewardFunction()
        self.policy_updater = PolicyUpdater(learning_rate=learning_rate)

        # 反馈存储
        self.feedback_history: List[UserFeedback] = []

        # 加载历史数据
        self._load_feedback_history()

    def collect_explicit_feedback(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        feedback_type: FeedbackType,
        feedback_value: float,
        user_message: str,
        ai_response: str,
        conversation_length: int,
        response_time: float,
        personality: PersonalityConfig,
        user_emotion: Optional[str] = None,
        ai_emotion: Optional[str] = None,
        emotional_resonance: float = 0.5,
    ) -> UserFeedback:
        """
        收集显式反馈（点赞/点踩/评分）

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            message_id: 消息ID
            feedback_type: 反馈类型
            feedback_value: 反馈值（归一化到0-1）
            user_message: 用户消息
            ai_response: AI回复
            conversation_length: 对话轮数
            response_time: 响应时间
            personality: 当前人格配置
            user_emotion: 用户情感
            ai_emotion: AI情感
            emotional_resonance: 情感共鸣度

        Returns:
            UserFeedback对象
        """
        feedback = UserFeedback(
            id=f"feedback_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            timestamp=datetime.now(),
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            user_message=user_message,
            ai_response=ai_response,
            conversation_length=conversation_length,
            response_time=response_time,
            user_emotion=user_emotion,
            ai_emotion=ai_emotion,
            emotional_resonance=emotional_resonance,
            personality_snapshot={
                **personality.big_five.to_dict(),
                **personality.traits.to_dict(),
            },
        )

        self.feedback_history.append(feedback)
        self._save_feedback(feedback)

        return feedback

    def collect_implicit_feedback(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        user_message: str,
        ai_response: str,
        conversation_length: int,
        response_time: float,
        personality: PersonalityConfig,
        user_emotion: Optional[str] = None,
        ai_emotion: Optional[str] = None,
        emotional_resonance: float = 0.5,
    ) -> UserFeedback:
        """
        收集隐式反馈（基于对话行为推断满意度）

        隐式反馈信号：
        - 对话持续时间长 -> 满意度高
        - 用户回复快 -> 参与度高
        - 情感共鸣高 -> 满意度高
        """
        # 计算隐式满意度
        implicit_satisfaction = self._calculate_implicit_satisfaction(
            conversation_length, emotional_resonance
        )

        return self.collect_explicit_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            feedback_type=FeedbackType.IMPLICIT,
            feedback_value=implicit_satisfaction,
            user_message=user_message,
            ai_response=ai_response,
            conversation_length=conversation_length,
            response_time=response_time,
            personality=personality,
            user_emotion=user_emotion,
            ai_emotion=ai_emotion,
            emotional_resonance=emotional_resonance,
        )

    def _calculate_implicit_satisfaction(
        self, conversation_length: int, emotional_resonance: float
    ) -> float:
        """
        计算隐式满意度
        """
        # 对话长度因子（越长越满意，但有上限）
        length_factor = min(1.0, conversation_length / 10.0)

        # 情感共鸣因子
        emotion_factor = emotional_resonance

        # 综合满意度
        satisfaction = length_factor * 0.4 + emotion_factor * 0.6

        return satisfaction

    def optimize_personality(
        self,
        user_id: str,
        current_personality: PersonalityConfig,
        recent_feedback_count: int = 5,
    ) -> PersonalityConfig:
        """
        基于最近的反馈优化人格

        Args:
            user_id: 用户ID
            current_personality: 当前人格配置
            recent_feedback_count: 使用最近N条反馈

        Returns:
            优化后的人格配置
        """
        # 获取最近的反馈
        recent_feedbacks = [
            fb for fb in self.feedback_history[-recent_feedback_count:] if fb.user_id == user_id
        ]

        if not recent_feedbacks:
            return current_personality

        # 计算平均奖励
        total_adjustments: Dict[str, List[float]] = {}

        for feedback in recent_feedbacks:
            # 计算奖励信号
            reward_signal = self.reward_function.calculate_reward(
                feedback, current_personality=current_personality
            )

            # 计算策略调整
            adjustments = self.policy_updater.update_policy(
                current_personality, reward_signal, feedback
            )

            # 累积调整
            for param_path, delta in adjustments.items():
                if param_path not in total_adjustments:
                    total_adjustments[param_path] = []
                total_adjustments[param_path].append(delta)

        # 计算平均调整
        avg_adjustments = {
            param_path: sum(deltas) / len(deltas)
            for param_path, deltas in total_adjustments.items()
        }

        # 转换为反馈信号格式
        feedback_signals = self._convert_adjustments_to_signals(avg_adjustments)

        # 使用持续学习服务应用调整（带防遗忘约束）
        optimized_personality = self.continual_learning.learn_from_feedback(
            user_id, current_personality, feedback_signals
        )

        return optimized_personality

    def _convert_adjustments_to_signals(self, adjustments: Dict[str, float]) -> Dict[str, float]:
        """
        将参数调整转换为反馈信号格式
        """
        signals = {}

        for param_path, delta in adjustments.items():
            # 映射参数路径到反馈信号
            if "humor" in param_path:
                signals["liked_humor"] = delta / 10.0
            elif "empathy" in param_path:
                signals["wanted_more_empathy"] = delta / 10.0
            elif "warmth" in param_path:
                signals["felt_too_cold"] = -delta / 10.0
            elif "verbosity" in param_path:
                if delta < 0:
                    signals["response_too_long"] = abs(delta) / 10.0
            elif "casualness" in param_path:
                signals["liked_casual_tone"] = delta / 10.0

        return signals

    def get_feedback_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        获取反馈统计信息
        """
        feedbacks = self.feedback_history
        if user_id:
            feedbacks = [fb for fb in feedbacks if fb.user_id == user_id]

        if not feedbacks:
            return {
                "total_feedbacks": 0,
                "avg_satisfaction": 0.0,
                "feedback_types": {},
            }

        # 统计
        total = len(feedbacks)
        avg_satisfaction = sum(fb.feedback_value for fb in feedbacks) / total

        feedback_types = {}
        for fb in feedbacks:
            fb_type = fb.feedback_type.value
            if fb_type not in feedback_types:
                feedback_types[fb_type] = 0
            feedback_types[fb_type] += 1

        return {
            "total_feedbacks": total,
            "avg_satisfaction": avg_satisfaction,
            "feedback_types": feedback_types,
            "recent_feedbacks": [fb.to_dict() for fb in feedbacks[-5:]],
        }

    def _save_feedback(self, feedback: UserFeedback):
        """保存反馈到磁盘"""
        feedback_file = self.storage_dir / f"{feedback.user_id}_feedbacks.jsonl"
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback.to_dict(), ensure_ascii=False) + "\n")

    def _load_feedback_history(self):
        """从磁盘加载反馈历史"""
        for feedback_file in self.storage_dir.glob("*_feedbacks.jsonl"):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            feedback = UserFeedback.from_dict(data)
                            self.feedback_history.append(feedback)
            except Exception as e:
                print(f"加载反馈历史失败 {feedback_file}: {e}")


# 全局单例
_rl_service: Optional[ReinforcementLearningService] = None


def get_rl_service(
    continual_learning: Optional[ContinualLearningService] = None,
) -> ReinforcementLearningService:
    """获取强化学习服务单例"""
    global _rl_service
    if _rl_service is None:
        from app.services.learning.continual_learning import get_continual_learning_service

        cl_service = continual_learning or get_continual_learning_service()
        _rl_service = ReinforcementLearningService(cl_service)
    return _rl_service
