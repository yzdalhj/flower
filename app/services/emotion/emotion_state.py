"""AI情感状态管理 - 集成情感动力学"""

from datetime import datetime
from typing import Dict, List, Optional

# 避免循环导入，使用局部导入
# from app.services.emotion_analyzer import EmotionResult
from app.services.emotion.emotion_dynamics import (
    AIEmotionalState,
    DecayCurve,
    EmotionDynamics,
    EmotionState,
    Stimulus,
    create_negative_stimulus,
    create_positive_stimulus,
)


class AIEmotionManager:
    """AI情感状态管理器 - 集成情感动力学"""

    # 共情系数：AI情感向用户情感靠近的程度
    EMPATHY_FACTOR = 0.6

    # 情感惯性：保持当前情感的倾向
    INERTIA = 0.7

    # 状态映射表：PAD到离散状态 (使用0-1范围的激活度)
    PAD_TO_STATE = [
        # (状态, 愉悦度范围, 激活度范围)
        (AIEmotionalState.EXCITED, (0.5, 1.0), (0.7, 1.0)),
        (AIEmotionalState.HAPPY, (0.3, 1.0), (0.4, 0.7)),
        (AIEmotionalState.GRATEFUL, (0.3, 0.8), (0.3, 0.5)),
        (AIEmotionalState.CALM, (0.0, 0.3), (0.2, 0.4)),
        (AIEmotionalState.CURIOUS, (0.0, 0.5), (0.4, 0.6)),
        (AIEmotionalState.NEUTRAL, (-0.2, 0.2), (0.3, 0.5)),
        (AIEmotionalState.CONFUSED, (-0.2, 0.2), (0.4, 0.6)),
        (AIEmotionalState.WORRIED, (-0.5, 0.0), (0.4, 0.6)),
        (AIEmotionalState.SAD, (-0.8, -0.3), (0.2, 0.5)),
        (AIEmotionalState.ANGRY, (-0.8, 0.0), (0.7, 1.0)),
    ]

    def __init__(
        self,
        user_id: str,
        decay_rate: float = 0.05,
        inertia: float = 0.7,
        decay_curve: DecayCurve = DecayCurve.EXPONENTIAL,
    ):
        self.user_id = user_id
        self.current_state = EmotionState()
        self.history: List[EmotionState] = []
        self.last_update = datetime.utcnow()

        # 初始化情感动力学引擎
        self.dynamics = EmotionDynamics(
            decay_rate=decay_rate, inertia=inertia, decay_curve=decay_curve
        )

        # 注册情感变化钩子
        self.dynamics.add_emotion_hook(self._on_emotion_change)

    def get_current_state(self) -> EmotionState:
        """获取当前情感状态（自动应用衰减）"""
        # 计算自上次更新经过的时间
        hours_passed = (datetime.utcnow() - self.last_update).total_seconds() / 3600
        if hours_passed > 0.1:  # 超过6分钟才更新
            self._evolve_state(hours_passed)
        return self.current_state

    def _evolve_state(self, hours_passed: float, new_stimulus: Optional[Stimulus] = None):
        """使用情感动力学演化状态"""
        evolved = self.dynamics.evolve_state(
            self.current_state, hours_passed=hours_passed, new_stimulus=new_stimulus
        )
        self._save_state(evolved)

    def _on_emotion_change(self, old_state: EmotionState, new_state: EmotionState):
        """情感变化钩子 - 更新离散状态"""
        # 当PAD值变化时，重新计算离散状态
        new_discrete = self._pad_to_state(new_state.valence, new_state.arousal)
        if new_discrete != new_state.primary_emotion:
            new_state.primary_emotion = new_discrete

    def update_from_user_emotion(
        self, user_emotion, context: Optional[Dict] = None
    ) -> EmotionState:
        """
        根据用户情感更新AI情感（共情反应）- 使用情感动力学

        Args:
            user_emotion: 用户情感分析结果
            context: 上下文信息（可选）

        Returns:
            更新后的AI情感状态
        """
        # 先应用时间衰减
        hours_passed = (datetime.utcnow() - self.last_update).total_seconds() / 3600

        # 计算共情刺激
        intimacy = context.get("intimacy", 0.5) if context else 0.5
        empathy_intensity = self.EMPATHY_FACTOR * (1 + intimacy * 0.2)

        # 将用户情感转换为刺激（支持字典或对象）
        valence = (
            user_emotion.get("valence", 0)
            if isinstance(user_emotion, dict)
            else getattr(user_emotion, "valence", 0)
        )
        arousal = (
            user_emotion.get("arousal", 0)
            if isinstance(user_emotion, dict)
            else getattr(user_emotion, "arousal", 0)
        )
        intensity = (
            user_emotion.get("intensity", 0.5)
            if isinstance(user_emotion, dict)
            else getattr(user_emotion, "intensity", 0.5)
        )
        label = (
            user_emotion.get("label", "neutral")
            if isinstance(user_emotion, dict)
            else getattr(user_emotion, "label", "neutral")
        )

        stimulus = Stimulus(
            source="user_empathy",
            valence_delta=valence * empathy_intensity,
            arousal_delta=max(0, arousal * empathy_intensity),  # 转为正值
            dominance_delta=0.0,
            intensity=intensity * empathy_intensity,
            metadata={"user_emotion": label},
        )

        # 使用动力学演化状态
        self._evolve_state(hours_passed, stimulus)

        return self.current_state

    def update_from_event(self, event_type: str, intensity: float = 0.5) -> EmotionState:
        """
        根据事件更新情感 - 使用情感动力学

        Args:
            event_type: 事件类型
            intensity: 事件强度 0-1

        Returns:
            更新后的情感状态
        """
        # 事件到刺激的映射
        event_stimulus_map = {
            "user_greeting": lambda i: create_positive_stimulus("greeting", i),
            "user_thanks": lambda i: create_positive_stimulus("thanks", i * 0.8),
            "user_anger": lambda i: create_negative_stimulus("anger", i, anger=True),
            "user_sadness": lambda i: create_negative_stimulus("sadness", i),
            "user_compliment": lambda i: create_positive_stimulus("compliment", i, excitement=True),
            "user_criticism": lambda i: create_negative_stimulus("criticism", i),
            "long_silence": lambda i: Stimulus(
                source="silence",
                valence_delta=0,
                arousal_delta=-0.2 * i,
                dominance_delta=0,
                intensity=i,
            ),
            "shared_secret": lambda i: Stimulus(
                source="secret",
                valence_delta=0.2 * i,
                arousal_delta=0.1 * i,
                dominance_delta=0.1 * i,
                intensity=i,
            ),
        }

        if event_type not in event_stimulus_map:
            return self.current_state

        # 先应用时间衰减
        hours_passed = (datetime.utcnow() - self.last_update).total_seconds() / 3600

        # 创建刺激
        stimulus = event_stimulus_map[event_type](intensity)
        stimulus.metadata["event_type"] = event_type

        # 使用动力学演化状态
        self._evolve_state(hours_passed, stimulus)

        return self.current_state

    def apply_stimulus(self, stimulus: Stimulus) -> EmotionState:
        """
        直接应用刺激到情感状态

        Args:
            stimulus: 情感刺激

        Returns:
            更新后的情感状态
        """
        hours_passed = (datetime.utcnow() - self.last_update).total_seconds() / 3600
        self._evolve_state(hours_passed, stimulus)
        return self.current_state

    def apply_decay(self, hours_passed: float) -> EmotionState:
        """
        应用情感衰减 - 使用情感动力学

        Args:
            hours_passed: 经过的小时数

        Returns:
            衰减后的情感状态
        """
        self._evolve_state(hours_passed)
        return self.current_state

    def get_emotional_momentum(self) -> Dict[str, float]:
        """获取情感动量（变化趋势）"""
        return self.dynamics.get_emotional_momentum()

    def predict_future_state(self, hours_ahead: float = 1.0) -> EmotionState:
        """预测未来情感状态"""
        return self.dynamics.predict_future_state(self.current_state, hours_ahead)

    def get_emotional_trajectory(self) -> List[EmotionState]:
        """获取情感轨迹历史"""
        return self.dynamics.trajectory.states

    def _save_state(self, state: EmotionState):
        """保存情感状态到历史"""
        self.current_state = state
        self.history.append(state)
        self.last_update = datetime.utcnow()

        # 限制历史记录长度
        if len(self.history) > 1000:
            self.history = self.history[-500:]

    def _pad_to_state(self, valence: float, arousal: float) -> AIEmotionalState:
        """
        将PAD值映射到离散情感状态

        Args:
            valence: 愉悦度 (-1 to 1)
            arousal: 激活度 (0 to 1)

        Returns:
            离散情感状态
        """
        for state, (v_min, v_max), (a_min, a_max) in self.PAD_TO_STATE:
            if v_min <= valence <= v_max and a_min <= arousal <= a_max:
                return state

        # 默认返回中性
        return AIEmotionalState.NEUTRAL

    def get_emotion_description(self) -> str:
        """
        获取当前情感的描述文本

        Returns:
            情感描述字符串
        """
        descriptions = {
            AIEmotionalState.HAPPY: "感到开心",
            AIEmotionalState.SAD: "感到难过",
            AIEmotionalState.ANGRY: "感到生气",
            AIEmotionalState.WORRIED: "感到担心",
            AIEmotionalState.EXCITED: "感到兴奋",
            AIEmotionalState.CALM: "感到平静",
            AIEmotionalState.CONFUSED: "感到困惑",
            AIEmotionalState.GRATEFUL: "感到感激",
            AIEmotionalState.CURIOUS: "感到好奇",
            AIEmotionalState.NEUTRAL: "心情平静",
        }

        base_desc = descriptions.get(self.current_state.primary_emotion, "心情平静")

        # 根据强度调整描述
        if self.current_state.intensity > 0.8:
            return f"非常{base_desc}"
        elif self.current_state.intensity > 0.5:
            return base_desc
        else:
            return f"有点{base_desc}"


# 全局管理器存储
_emotion_managers: Dict[str, AIEmotionManager] = {}


def get_emotion_manager(user_id: str) -> AIEmotionManager:
    """
    获取或创建情感管理器

    Args:
        user_id: 用户ID

    Returns:
        AIEmotionManager实例
    """
    if user_id not in _emotion_managers:
        _emotion_managers[user_id] = AIEmotionManager(user_id)
    return _emotion_managers[user_id]


def remove_emotion_manager(user_id: str):
    """移除情感管理器"""
    if user_id in _emotion_managers:
        del _emotion_managers[user_id]
