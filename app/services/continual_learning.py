"""
持续学习服务 - 人格参数的渐进式学习与防遗忘机制

在基于API的系统中，持续学习主要体现在：
1. 经验重放缓冲区 - 存储历史交互经验
2. 防遗忘机制 - 保护重要人格参数不被过度修改
3. 增量学习策略 - 基于反馈渐进式调整人格
4. 记忆巩固 - 定期重放旧经验以巩固人格特征

注意：这不是深度学习模型的持续学习，而是人格参数的动态优化
"""

import json
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.models.personality import PersonalityConfig, PersonalityTraits, BigFiveScores


@dataclass
class Experience:
    """
    单次交互经验
    用于经验重放
    """

    id: str
    user_id: str
    timestamp: datetime

    # 交互内容
    user_message: str
    ai_response: str

    # 反馈信号
    user_satisfaction: float  # 用户满意度 (0-1)
    conversation_length: int  # 对话持续轮数
    emotional_resonance: float  # 情感共鸣度 (0-1)

    # 人格快照（交互时的人格状态）
    personality_snapshot: Dict[str, float]

    # 重要性评分
    importance: float = 1.0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "user_message": self.user_message,
            "ai_response": self.ai_response,
            "user_satisfaction": self.user_satisfaction,
            "conversation_length": self.conversation_length,
            "emotional_resonance": self.emotional_resonance,
            "personality_snapshot": self.personality_snapshot,
            "importance": self.importance,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Experience":
        """从字典创建"""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_message=data["user_message"],
            ai_response=data["ai_response"],
            user_satisfaction=data["user_satisfaction"],
            conversation_length=data["conversation_length"],
            emotional_resonance=data["emotional_resonance"],
            personality_snapshot=data["personality_snapshot"],
            importance=data.get("importance", 1.0),
        )


@dataclass
class ParameterImportance:
    """
    参数重要性权重
    用于防遗忘机制（类似EWC的Fisher信息矩阵）
    """

    parameter_name: str
    importance: float  # 重要性权重 (0-1)
    last_updated: datetime
    update_count: int = 0

    # 历史值（用于检测稳定性）
    value_history: List[float] = field(default_factory=list)

    def update_importance(self, new_value: float):
        """
        更新重要性
        基于参数的稳定性和使用频率
        """
        self.value_history.append(new_value)
        if len(self.value_history) > 20:
            self.value_history.pop(0)

        # 计算稳定性（方差越小越稳定）
        if len(self.value_history) >= 3:
            mean = sum(self.value_history) / len(self.value_history)
            variance = sum((x - mean) ** 2 for x in self.value_history) / len(
                self.value_history
            )
            stability = 1.0 / (1.0 + variance)  # 稳定性越高，重要性越高

            # 更新重要性（结合稳定性和更新频率）
            frequency_factor = min(1.0, self.update_count / 10.0)
            self.importance = 0.7 * stability + 0.3 * frequency_factor

        self.update_count += 1
        self.last_updated = datetime.now()


class ReplayBuffer:
    """
    经验重放缓冲区
    存储历史交互经验，用于定期重放和学习
    """

    def __init__(self, max_size: int = 1000, storage_dir: str = "./data/replay_buffer"):
        self.max_size = max_size
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 使用deque实现固定大小的缓冲区
        self.buffer: deque = deque(maxlen=max_size)

        # 按用户分组的索引
        self.user_index: Dict[str, List[str]] = {}

        # 加载已有数据
        self._load_from_disk()

    def add_experience(self, experience: Experience):
        """
        添加经验到缓冲区
        """
        self.buffer.append(experience)

        # 更新用户索引
        if experience.user_id not in self.user_index:
            self.user_index[experience.user_id] = []
        self.user_index[experience.user_id].append(experience.id)

        # 定期持久化
        if len(self.buffer) % 10 == 0:
            self._save_to_disk()

    def sample_experiences(
        self, n: int, user_id: Optional[str] = None, importance_weighted: bool = True
    ) -> List[Experience]:
        """
        从缓冲区采样经验

        Args:
            n: 采样数量
            user_id: 指定用户ID（可选）
            importance_weighted: 是否按重要性加权采样

        Returns:
            采样的经验列表
        """
        # 筛选经验
        if user_id:
            experiences = [
                exp for exp in self.buffer if exp.user_id == user_id
            ]
        else:
            experiences = list(self.buffer)

        if not experiences:
            return []

        # 限制采样数量
        n = min(n, len(experiences))

        if importance_weighted:
            # 按重要性加权采样
            import random

            weights = [exp.importance for exp in experiences]
            total_weight = sum(weights)
            if total_weight > 0:
                probabilities = [w / total_weight for w in weights]
                sampled = random.choices(experiences, weights=probabilities, k=n)
            else:
                sampled = random.sample(experiences, n)
        else:
            # 均匀采样
            import random

            sampled = random.sample(experiences, n)

        return sampled

    def get_recent_experiences(
        self, n: int, user_id: Optional[str] = None
    ) -> List[Experience]:
        """
        获取最近的N条经验
        """
        if user_id:
            experiences = [
                exp for exp in self.buffer if exp.user_id == user_id
            ]
        else:
            experiences = list(self.buffer)

        # 按时间排序，返回最近的N条
        experiences.sort(key=lambda x: x.timestamp, reverse=True)
        return experiences[:n]

    def get_high_quality_experiences(
        self, n: int, user_id: Optional[str] = None, min_satisfaction: float = 0.7
    ) -> List[Experience]:
        """
        获取高质量经验（用于正向强化）
        """
        if user_id:
            experiences = [
                exp
                for exp in self.buffer
                if exp.user_id == user_id and exp.user_satisfaction >= min_satisfaction
            ]
        else:
            experiences = [
                exp for exp in self.buffer if exp.user_satisfaction >= min_satisfaction
            ]

        # 按满意度排序
        experiences.sort(key=lambda x: x.user_satisfaction, reverse=True)
        return experiences[:n]

    def _save_to_disk(self):
        """持久化到磁盘"""
        buffer_file = self.storage_dir / "replay_buffer.json"
        data = {
            "experiences": [exp.to_dict() for exp in self.buffer],
            "user_index": self.user_index,
        }
        with open(buffer_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self):
        """从磁盘加载"""
        buffer_file = self.storage_dir / "replay_buffer.json"
        if buffer_file.exists():
            try:
                with open(buffer_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.buffer = deque(
                        [Experience.from_dict(exp) for exp in data["experiences"]],
                        maxlen=self.max_size,
                    )
                    self.user_index = data.get("user_index", {})
            except Exception as e:
                print(f"加载经验缓冲区失败: {e}")

    def get_buffer_stats(self) -> Dict:
        """获取缓冲区统计信息"""
        if not self.buffer:
            return {
                "total_experiences": 0,
                "unique_users": 0,
                "avg_satisfaction": 0.0,
                "avg_importance": 0.0,
            }

        return {
            "total_experiences": len(self.buffer),
            "unique_users": len(self.user_index),
            "avg_satisfaction": sum(exp.user_satisfaction for exp in self.buffer)
            / len(self.buffer),
            "avg_importance": sum(exp.importance for exp in self.buffer)
            / len(self.buffer),
            "oldest_experience": min(exp.timestamp for exp in self.buffer).isoformat(),
            "newest_experience": max(exp.timestamp for exp in self.buffer).isoformat(),
        }


class AntiForgetMechanism:
    """
    防遗忘机制
    类似EWC (Elastic Weight Consolidation)，但适用于人格参数

    核心思想：
    - 重要的人格参数（稳定且有效的）应该被保护，不轻易修改
    - 不重要的参数可以更自由地调整
    """

    def __init__(self, storage_dir: str = "./data/parameter_importance"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 参数重要性映射
        self.importance_map: Dict[str, ParameterImportance] = {}

        # 加载已有数据
        self._load_from_disk()

    def update_parameter_importance(self, parameter_name: str, current_value: float):
        """
        更新参数重要性
        """
        if parameter_name not in self.importance_map:
            self.importance_map[parameter_name] = ParameterImportance(
                parameter_name=parameter_name,
                importance=0.5,  # 初始中等重要性
                last_updated=datetime.now(),
            )

        self.importance_map[parameter_name].update_importance(current_value)

    def get_parameter_importance(self, parameter_name: str) -> float:
        """
        获取参数重要性
        """
        if parameter_name in self.importance_map:
            return self.importance_map[parameter_name].importance
        return 0.5  # 默认中等重要性

    def calculate_update_constraint(
        self, parameter_name: str, old_value: float, new_value: float
    ) -> float:
        """
        计算更新约束
        返回实际应该更新的值（考虑重要性约束）

        Args:
            parameter_name: 参数名
            old_value: 旧值
            new_value: 新值（未约束）

        Returns:
            约束后的新值
        """
        importance = self.get_parameter_importance(parameter_name)

        # 重要性越高，变化越小
        # importance = 0.0 -> 完全自由更新
        # importance = 1.0 -> 几乎不更新
        constraint_factor = 1.0 - importance * 0.8  # 最多保留20%的变化

        # 计算约束后的值
        delta = new_value - old_value
        constrained_delta = delta * constraint_factor
        constrained_value = old_value + constrained_delta

        return constrained_value

    def _save_to_disk(self):
        """持久化到磁盘"""
        importance_file = self.storage_dir / "parameter_importance.json"
        data = {
            param_name: {
                "importance": param.importance,
                "last_updated": param.last_updated.isoformat(),
                "update_count": param.update_count,
                "value_history": param.value_history,
            }
            for param_name, param in self.importance_map.items()
        }
        with open(importance_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self):
        """从磁盘加载"""
        importance_file = self.storage_dir / "parameter_importance.json"
        if importance_file.exists():
            try:
                with open(importance_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for param_name, param_data in data.items():
                        self.importance_map[param_name] = ParameterImportance(
                            parameter_name=param_name,
                            importance=param_data["importance"],
                            last_updated=datetime.fromisoformat(
                                param_data["last_updated"]
                            ),
                            update_count=param_data["update_count"],
                            value_history=param_data["value_history"],
                        )
            except Exception as e:
                print(f"加载参数重要性失败: {e}")


class ContinualLearningService:
    """
    持续学习服务
    整合经验重放、防遗忘机制和增量学习策略
    """

    def __init__(
        self,
        replay_buffer: Optional[ReplayBuffer] = None,
        anti_forget: Optional[AntiForgetMechanism] = None,
        learning_rate: float = 0.1,
        consolidation_interval_hours: int = 24,
    ):
        self.replay_buffer = replay_buffer or ReplayBuffer()
        self.anti_forget = anti_forget or AntiForgetMechanism()
        self.learning_rate = learning_rate
        self.consolidation_interval = timedelta(hours=consolidation_interval_hours)

        # 上次巩固时间
        self.last_consolidation: Dict[str, datetime] = {}

    def record_interaction(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        personality: PersonalityConfig,
        user_satisfaction: float,
        conversation_length: int,
        emotional_resonance: float,
    ) -> Experience:
        """
        记录交互经验

        Args:
            user_id: 用户ID
            user_message: 用户消息
            ai_response: AI回复
            personality: 当前人格配置
            user_satisfaction: 用户满意度 (0-1)
            conversation_length: 对话轮数
            emotional_resonance: 情感共鸣度 (0-1)

        Returns:
            Experience对象
        """
        # 创建人格快照
        personality_snapshot = {
            **personality.big_five.to_dict(),
            **personality.traits.to_dict(),
        }

        # 计算重要性（基于满意度和共鸣度）
        importance = (user_satisfaction * 0.6 + emotional_resonance * 0.4) * (
            1.0 + math.log(conversation_length + 1) / 10.0
        )

        experience = Experience(
            id=f"exp_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            user_message=user_message,
            ai_response=ai_response,
            user_satisfaction=user_satisfaction,
            conversation_length=conversation_length,
            emotional_resonance=emotional_resonance,
            personality_snapshot=personality_snapshot,
            importance=min(1.0, importance),
        )

        self.replay_buffer.add_experience(experience)
        return experience

    def learn_from_feedback(
        self,
        user_id: str,
        current_personality: PersonalityConfig,
        feedback_signals: Dict[str, float],
    ) -> PersonalityConfig:
        """
        基于反馈信号学习并更新人格

        Args:
            user_id: 用户ID
            current_personality: 当前人格配置
            feedback_signals: 反馈信号字典
                例如: {
                    "liked_humor": 0.8,
                    "wanted_more_empathy": 0.6,
                    "response_too_long": -0.5,
                }

        Returns:
            更新后的人格配置
        """
        # 创建新的人格配置（避免修改原对象）
        new_personality = PersonalityConfig.from_dict(current_personality.to_dict())

        # 根据反馈调整人格参数
        adjustments = self._calculate_adjustments(feedback_signals)

        # 应用调整（带防遗忘约束）
        for param_name, delta in adjustments.items():
            self._apply_adjustment(new_personality, param_name, delta)

        # 记录演化历史
        new_personality.evolution_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "feedback_signals": feedback_signals,
                "adjustments": adjustments,
            }
        )

        new_personality.updated_at = datetime.now()
        new_personality.version += 1

        return new_personality

    def _calculate_adjustments(
        self, feedback_signals: Dict[str, float]
    ) -> Dict[str, float]:
        """
        根据反馈信号计算参数调整量
        """
        adjustments = {}

        # 映射反馈信号到人格参数
        signal_to_param = {
            "liked_humor": ("traits.humor", 1.0),
            "wanted_more_empathy": ("traits.empathy", 1.0),
            "felt_too_cold": ("traits.warmth", 1.0),
            "response_too_long": ("traits.verbosity", -1.0),
            "felt_too_robotic": ("traits.casualness", 1.0),
            "liked_casual_tone": ("traits.casualness", 1.0),
            "wanted_more_structure": ("big_five.conscientiousness", 1.0),
            "liked_openness": ("big_five.openness", 1.0),
        }

        for signal, value in feedback_signals.items():
            if signal in signal_to_param:
                param_name, direction = signal_to_param[signal]
                # 调整量 = 反馈强度 × 方向 × 学习率
                adjustment = value * direction * self.learning_rate * 10.0
                adjustments[param_name] = adjustment

        return adjustments

    def _apply_adjustment(
        self, personality: PersonalityConfig, param_path: str, delta: float
    ):
        """
        应用参数调整（带防遗忘约束）

        Args:
            personality: 人格配置对象
            param_path: 参数路径（如 "traits.humor" 或 "big_five.openness"）
            delta: 调整量
        """
        # 解析参数路径
        parts = param_path.split(".")
        if len(parts) != 2:
            return

        category, param_name = parts

        # 获取当前值
        if category == "traits":
            obj = personality.traits
        elif category == "big_five":
            obj = personality.big_five
        else:
            return

        old_value = getattr(obj, param_name, 50.0)

        # 计算新值（未约束）
        unconstrained_new_value = old_value + delta

        # 应用防遗忘约束
        constrained_new_value = self.anti_forget.calculate_update_constraint(
            param_path, old_value, unconstrained_new_value
        )

        # 限制在有效范围内
        constrained_new_value = max(0.0, min(100.0, constrained_new_value))

        # 更新参数
        setattr(obj, param_name, constrained_new_value)

        # 更新参数重要性
        self.anti_forget.update_parameter_importance(param_path, constrained_new_value)

    def consolidate_memory(self, user_id: str, current_personality: PersonalityConfig):
        """
        记忆巩固 - 定期重放旧经验以巩固人格特征

        Args:
            user_id: 用户ID
            current_personality: 当前人格配置
        """
        # 检查是否需要巩固
        if user_id in self.last_consolidation:
            time_since_last = datetime.now() - self.last_consolidation[user_id]
            if time_since_last < self.consolidation_interval:
                return  # 还不需要巩固

        # 采样高质量经验
        high_quality_exp = self.replay_buffer.get_high_quality_experiences(
            n=20, user_id=user_id, min_satisfaction=0.7
        )

        if not high_quality_exp:
            return

        # 分析高质量经验中的人格特征
        consolidated_traits = self._analyze_successful_traits(high_quality_exp)

        # 微调当前人格，使其更接近成功的人格特征
        for param_path, target_value in consolidated_traits.items():
            parts = param_path.split(".")
            if len(parts) != 2:
                continue

            category, param_name = parts
            if category == "traits":
                obj = current_personality.traits
            elif category == "big_five":
                obj = current_personality.big_five
            else:
                continue

            current_value = getattr(obj, param_name, 50.0)

            # 缓慢向目标值移动（巩固效应）
            delta = (target_value - current_value) * 0.1
            new_value = current_value + delta
            new_value = max(0.0, min(100.0, new_value))

            setattr(obj, param_name, new_value)

        # 更新巩固时间
        self.last_consolidation[user_id] = datetime.now()

    def _analyze_successful_traits(
        self, experiences: List[Experience]
    ) -> Dict[str, float]:
        """
        分析成功经验中的人格特征
        返回平均的成功人格参数
        """
        if not experiences:
            return {}

        # 收集所有参数值
        param_values: Dict[str, List[float]] = {}

        for exp in experiences:
            for param_name, value in exp.personality_snapshot.items():
                if param_name not in param_values:
                    param_values[param_name] = []
                # 按满意度加权
                param_values[param_name].append(value * exp.user_satisfaction)

        # 计算加权平均
        consolidated = {}
        for param_name, values in param_values.items():
            if values:
                # 映射到标准参数路径
                if param_name in [
                    "openness",
                    "conscientiousness",
                    "extraversion",
                    "agreeableness",
                    "neuroticism",
                ]:
                    param_path = f"big_five.{param_name}"
                else:
                    param_path = f"traits.{param_name}"

                consolidated[param_path] = sum(values) / len(values)

        return consolidated

    def get_learning_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        获取学习统计信息
        """
        buffer_stats = self.replay_buffer.get_buffer_stats()

        stats = {
            "replay_buffer": buffer_stats,
            "parameter_importance_count": len(self.anti_forget.importance_map),
            "learning_rate": self.learning_rate,
        }

        if user_id and user_id in self.last_consolidation:
            stats["last_consolidation"] = self.last_consolidation[
                user_id
            ].isoformat()
            stats["time_since_consolidation"] = (
                datetime.now() - self.last_consolidation[user_id]
            ).total_seconds() / 3600.0  # 小时

        return stats


# 全局单例
_continual_learning_service: Optional[ContinualLearningService] = None


def get_continual_learning_service() -> ContinualLearningService:
    """获取持续学习服务单例"""
    global _continual_learning_service
    if _continual_learning_service is None:
        _continual_learning_service = ContinualLearningService()
    return _continual_learning_service
