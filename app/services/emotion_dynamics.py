"""
情感动力学模块 - 实现情感的自然演化规律

核心概念:
- 自然衰减: 情感随时间自然消退
- 惯性维持: 情感状态倾向于保持
- 刺激响应: 外部刺激对情感的影响
- 情感传染: 群体环境中的情感传播
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional


class AIEmotionalState(Enum):
    """AI情感状态枚举"""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    WORRIED = "worried"
    EXCITED = "excited"
    CALM = "calm"
    CONFUSED = "confused"
    GRATEFUL = "grateful"
    CURIOUS = "curious"


class DecayCurve(Enum):
    """情感衰减曲线类型"""

    EXPONENTIAL = "exponential"  # 指数衰减 (快->慢)
    LINEAR = "linear"  # 线性衰减 (匀速)
    LOGARITHMIC = "logarithmic"  # 对数衰减 (慢->快)
    SIGMOID = "sigmoid"  # S型衰减 (中间快)


@dataclass
class EmotionState:
    """情感状态数据类"""

    valence: float = 0.0  # 愉悦度: -1 ~ 1
    arousal: float = 0.0  # 激活度: 0 ~ 1
    dominance: float = 0.5  # 支配度: 0 ~ 1
    primary_emotion: AIEmotionalState = AIEmotionalState.NEUTRAL
    intensity: float = 0.5  # 情感强度: 0 ~ 1
    confidence: float = 0.8  # 置信度: 0 ~ 1
    secondary_emotions: List[AIEmotionalState] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "initial"  # 来源

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "primary_emotion": self.primary_emotion.value,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "secondary_emotions": [e.value for e in self.secondary_emotions],
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }

    def copy(self) -> "EmotionState":
        """创建副本"""
        return EmotionState(
            valence=self.valence,
            arousal=self.arousal,
            dominance=self.dominance,
            primary_emotion=self.primary_emotion,
            intensity=self.intensity,
            confidence=self.confidence,
            secondary_emotions=self.secondary_emotions.copy(),
            timestamp=self.timestamp,
            source=self.source,
        )


@dataclass
class Stimulus:
    """情感刺激事件"""

    source: str  # 刺激来源
    valence_delta: float  # 愉悦度变化 (-1 to 1)
    arousal_delta: float  # 激活度变化 (-1 to 1)
    dominance_delta: float  # 支配度变化 (-1 to 1)
    intensity: float  # 刺激强度 (0 to 1)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 1.0  # 持续时间(小时)
    decay_curve: DecayCurve = DecayCurve.EXPONENTIAL
    metadata: Dict = field(default_factory=dict)


@dataclass
class EmotionTrajectory:
    """情感轨迹 - 记录情感变化历史"""

    states: List[EmotionState] = field(default_factory=list)
    stimuli: List[Stimulus] = field(default_factory=list)
    max_history: int = 100

    def add_state(self, state: EmotionState):
        """添加情感状态到轨迹"""
        self.states.append(state)
        if len(self.states) > self.max_history:
            self.states.pop(0)

    def add_stimulus(self, stimulus: Stimulus):
        """添加刺激事件到轨迹"""
        self.stimuli.append(stimulus)
        if len(self.stimuli) > self.max_history:
            self.stimuli.pop(0)

    def get_emotional_volatility(self, window: int = 10) -> float:
        """计算情感波动性 (最近N个状态的方差)"""
        if len(self.states) < 2:
            return 0.0

        recent = self.states[-window:]
        valences = [s.valence for s in recent]
        mean_val = sum(valences) / len(valences)
        variance = sum((v - mean_val) ** 2 for v in valences) / len(valences)
        return math.sqrt(variance)

    def get_dominant_emotion(self, window: int = 10) -> Optional[AIEmotionalState]:
        """获取主导情感 (最近N个状态中最频繁的)"""
        if not self.states:
            return None

        recent = self.states[-window:]
        emotion_counts: Dict[AIEmotionalState, int] = {}
        for state in recent:
            emotion_counts[state.primary_emotion] = emotion_counts.get(state.primary_emotion, 0) + 1

        return max(emotion_counts.items(), key=lambda x: x[1])[0]


class EmotionDynamics:
    """
    情感动力学引擎

    实现情感的自然演化规律，包括:
    1. 自然衰减 - 情感随时间消退
    2. 惯性维持 - 情感状态保持
    3. 刺激响应 - 外部事件影响
    4. 情感传染 - 群体情感传播
    """

    # 衰减参数
    DEFAULT_DECAY_RATE = 0.05  # 默认每小时衰减5%
    MIN_DECAY_RATE = 0.01  # 最小衰减率
    MAX_DECAY_RATE = 0.2  # 最大衰减率

    # 惯性参数
    DEFAULT_INERTIA = 0.7  # 默认惯性系数

    # 刺激响应参数
    STIMULUS_THRESHOLD = 0.1  # 刺激阈值
    RESPONSE_SENSITIVITY = 1.2  # 响应敏感度

    def __init__(
        self,
        decay_rate: float = DEFAULT_DECAY_RATE,
        inertia: float = DEFAULT_INERTIA,
        decay_curve: DecayCurve = DecayCurve.EXPONENTIAL,
    ):
        self.decay_rate = max(self.MIN_DECAY_RATE, min(self.MAX_DECAY_RATE, decay_rate))
        self.inertia = inertia
        self.decay_curve = decay_curve
        self.trajectory = EmotionTrajectory()
        self.active_stimuli: List[Stimulus] = []
        self._emotion_hooks: List[Callable] = []  # 情感变化钩子

    def calculate_decay(self, current_value: float, hours_passed: float) -> float:
        """计算衰减后的值"""
        if hours_passed <= 0:
            return current_value

        if self.decay_curve == DecayCurve.EXPONENTIAL:
            return current_value * math.exp(-self.decay_rate * hours_passed)
        elif self.decay_curve == DecayCurve.LINEAR:
            decay_amount = self.decay_rate * hours_passed
            return (
                max(0, current_value - decay_amount)
                if current_value > 0
                else min(0, current_value + decay_amount)
            )
        elif self.decay_curve == DecayCurve.LOGARITHMIC:
            return current_value / (1 + math.log(1 + self.decay_rate * hours_passed))
        elif self.decay_curve == DecayCurve.SIGMOID:
            midpoint = 5.0
            steepness = 0.5
            factor = 1 / (1 + math.exp(steepness * (hours_passed - midpoint)))
            return current_value * factor

        return current_value

    def apply_natural_decay(self, state: EmotionState, hours_passed: float) -> EmotionState:
        """应用自然衰减到情感状态"""
        if hours_passed <= 0:
            return state

        new_valence = self.calculate_decay(state.valence, hours_passed)
        arousal_target = 0.3
        arousal_diff = state.arousal - arousal_target
        new_arousal = arousal_target + self.calculate_decay(arousal_diff, hours_passed)
        dominance_target = 0.5
        dominance_diff = state.dominance - dominance_target
        new_dominance = dominance_target + self.calculate_decay(dominance_diff, hours_passed)
        new_intensity = max(0.1, state.intensity * math.exp(-self.decay_rate * hours_passed))
        new_confidence = max(
            0.3, state.confidence * math.exp(-self.decay_rate * hours_passed * 0.5)
        )

        return EmotionState(
            valence=max(-1.0, min(1.0, new_valence)),
            arousal=max(0.0, min(1.0, new_arousal)),
            dominance=max(0.0, min(1.0, new_dominance)),
            intensity=new_intensity,
            confidence=new_confidence,
            primary_emotion=state.primary_emotion,
            secondary_emotions=state.secondary_emotions,
            timestamp=datetime.utcnow(),
        )

    def apply_inertia(
        self, current_state: EmotionState, target_state: EmotionState
    ) -> EmotionState:
        """应用惯性到情感状态变化"""
        new_valence = current_state.valence * self.inertia + target_state.valence * (
            1 - self.inertia
        )
        new_arousal = current_state.arousal * self.inertia + target_state.arousal * (
            1 - self.inertia
        )
        new_dominance = current_state.dominance * self.inertia + target_state.dominance * (
            1 - self.inertia
        )
        new_intensity = current_state.intensity * self.inertia + target_state.intensity * (
            1 - self.inertia
        )

        return EmotionState(
            valence=max(-1.0, min(1.0, new_valence)),
            arousal=max(0.0, min(1.0, new_arousal)),
            dominance=max(0.0, min(1.0, new_dominance)),
            intensity=new_intensity,
            confidence=target_state.confidence,
            primary_emotion=target_state.primary_emotion,
            secondary_emotions=target_state.secondary_emotions,
            timestamp=datetime.utcnow(),
        )

    def calculate_stimulus_response(
        self, current_state: EmotionState, stimulus: Stimulus
    ) -> EmotionState:
        """计算刺激响应后的情感状态"""
        if stimulus.intensity < self.STIMULUS_THRESHOLD:
            return current_state

        response_factor = stimulus.intensity * self.RESPONSE_SENSITIVITY

        new_valence = max(
            -1.0, min(1.0, current_state.valence + stimulus.valence_delta * response_factor)
        )
        new_arousal = max(
            0.0, min(1.0, current_state.arousal + stimulus.arousal_delta * response_factor)
        )
        new_dominance = max(
            0.0, min(1.0, current_state.dominance + stimulus.dominance_delta * response_factor)
        )
        intensity_boost = stimulus.intensity * 0.3
        new_intensity = min(1.0, current_state.intensity + intensity_boost)

        self.active_stimuli.append(stimulus)
        self.trajectory.add_stimulus(stimulus)

        return EmotionState(
            valence=new_valence,
            arousal=new_arousal,
            dominance=new_dominance,
            intensity=new_intensity,
            confidence=min(1.0, current_state.confidence + 0.1),
            primary_emotion=current_state.primary_emotion,
            secondary_emotions=current_state.secondary_emotions,
            timestamp=datetime.utcnow(),
        )

    def update_stimuli(self, current_time: Optional[datetime] = None) -> List[Stimulus]:
        """更新活跃刺激列表，移除过期刺激"""
        if current_time is None:
            current_time = datetime.utcnow()

        expired = []
        remaining = []

        for stimulus in self.active_stimuli:
            hours_since = (current_time - stimulus.timestamp).total_seconds() / 3600
            if hours_since > stimulus.duration:
                expired.append(stimulus)
            else:
                remaining.append(stimulus)

        self.active_stimuli = remaining
        return expired

    def calculate_active_stimulus_effect(self) -> Optional[Stimulus]:
        """计算所有活跃刺激的复合效果"""
        if not self.active_stimuli:
            return None

        total_valence = 0.0
        total_arousal = 0.0
        total_dominance = 0.0
        total_intensity = 0.0

        for stimulus in self.active_stimuli:
            hours_since = (datetime.utcnow() - stimulus.timestamp).total_seconds() / 3600
            remaining_factor = max(0, 1 - hours_since / stimulus.duration)

            total_valence += stimulus.valence_delta * stimulus.intensity * remaining_factor
            total_arousal += stimulus.arousal_delta * stimulus.intensity * remaining_factor
            total_dominance += stimulus.dominance_delta * stimulus.intensity * remaining_factor
            total_intensity += stimulus.intensity * remaining_factor

        count = len(self.active_stimuli)
        return Stimulus(
            source="composite",
            valence_delta=total_valence / count,
            arousal_delta=total_arousal / count,
            dominance_delta=total_dominance / count,
            intensity=min(1.0, total_intensity / count),
        )

    def evolve_state(
        self,
        current_state: EmotionState,
        hours_passed: float = 1.0,
        new_stimulus: Optional[Stimulus] = None,
    ) -> EmotionState:
        """演化情感状态 - 综合自然衰减、惯性和刺激响应"""
        decayed_state = self.apply_natural_decay(current_state, hours_passed)
        self.update_stimuli()
        composite_stimulus = self.calculate_active_stimulus_effect()
        if composite_stimulus:
            decayed_state = self.calculate_stimulus_response(decayed_state, composite_stimulus)
        if new_stimulus:
            decayed_state = self.calculate_stimulus_response(decayed_state, new_stimulus)
        self.trajectory.add_state(decayed_state)
        self._trigger_hooks(current_state, decayed_state)
        return decayed_state

    def add_emotion_hook(self, hook: Callable[[EmotionState, EmotionState], None]):
        """添加情感变化钩子函数"""
        self._emotion_hooks.append(hook)

    def _trigger_hooks(self, old_state: EmotionState, new_state: EmotionState):
        """触发所有情感变化钩子"""
        for hook in self._emotion_hooks:
            try:
                hook(old_state, new_state)
            except Exception:
                pass

    def get_emotional_momentum(self) -> Dict[str, float]:
        """获取情感动量(变化趋势)"""
        if len(self.trajectory.states) < 3:
            return {"valence": 0, "arousal": 0, "dominance": 0}

        recent = self.trajectory.states[-5:]

        def calc_trend(values: List[float]) -> float:
            if len(values) < 2:
                return 0.0
            n = len(values)
            sum_x = sum(range(n))
            sum_y = sum(values)
            sum_xy = sum(i * v for i, v in enumerate(values))
            sum_x2 = sum(i * i for i in range(n))

            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                return 0.0

            slope = (n * sum_xy - sum_x * sum_y) / denominator
            return slope

        valences = [s.valence for s in recent]
        arousals = [s.arousal for s in recent]
        dominances = [s.dominance for s in recent]

        return {
            "valence": calc_trend(valences),
            "arousal": calc_trend(arousals),
            "dominance": calc_trend(dominances),
        }

    def predict_future_state(
        self, current_state: EmotionState, hours_ahead: float = 1.0
    ) -> EmotionState:
        """预测未来情感状态(不考虑新刺激)"""
        momentum = self.get_emotional_momentum()

        predicted_valence = max(
            -1.0, min(1.0, current_state.valence + momentum["valence"] * hours_ahead)
        )
        predicted_arousal = max(
            0.0, min(1.0, current_state.arousal + momentum["arousal"] * hours_ahead)
        )
        predicted_dominance = max(
            0.0, min(1.0, current_state.dominance + momentum["dominance"] * hours_ahead)
        )

        temp_state = EmotionState(
            valence=predicted_valence,
            arousal=predicted_arousal,
            dominance=predicted_dominance,
            intensity=current_state.intensity,
            confidence=current_state.confidence * 0.9,
            primary_emotion=current_state.primary_emotion,
            secondary_emotions=current_state.secondary_emotions,
            timestamp=datetime.utcnow() + timedelta(hours=hours_ahead),
        )

        return self.apply_natural_decay(temp_state, hours_ahead)

    def calculate_emotional_contagion(
        self, my_state: EmotionState, other_state: EmotionState, intimacy: float = 0.5
    ) -> Stimulus:
        """计算情感传染效果"""
        contagion_factor = intimacy * 0.5

        valence_diff = other_state.valence - my_state.valence
        arousal_diff = other_state.arousal - my_state.arousal
        dominance_diff = other_state.dominance - my_state.dominance

        if abs(valence_diff) < 0.2 and abs(arousal_diff) < 0.2:
            return Stimulus(
                source="contagion", valence_delta=0, arousal_delta=0, dominance_delta=0, intensity=0
            )

        return Stimulus(
            source="contagion",
            valence_delta=valence_diff * contagion_factor,
            arousal_delta=arousal_diff * contagion_factor,
            dominance_delta=dominance_diff * contagion_factor,
            intensity=other_state.intensity * contagion_factor,
            metadata={"intimacy": intimacy, "source_emotion": other_state.primary_emotion.value},
        )


# 便捷函数
def create_positive_stimulus(
    source: str, intensity: float = 0.5, excitement: bool = False
) -> Stimulus:
    """创建积极刺激"""
    return Stimulus(
        source=source,
        valence_delta=0.3 + intensity * 0.4,
        arousal_delta=0.2 + (0.3 if excitement else 0),
        dominance_delta=0.1,
        intensity=intensity,
        decay_curve=DecayCurve.EXPONENTIAL,
    )


def create_negative_stimulus(source: str, intensity: float = 0.5, anger: bool = False) -> Stimulus:
    """创建消极刺激"""
    return Stimulus(
        source=source,
        valence_delta=-(0.3 + intensity * 0.4),
        arousal_delta=0.2 + (0.3 if anger else 0),
        dominance_delta=-0.1 if not anger else 0.2,
        intensity=intensity,
        decay_curve=DecayCurve.EXPONENTIAL,
    )


def create_surprise_stimulus(source: str, intensity: float = 0.6) -> Stimulus:
    """创建惊讶刺激"""
    return Stimulus(
        source=source,
        valence_delta=0,
        arousal_delta=0.5 + intensity * 0.3,
        dominance_delta=-0.1,
        intensity=intensity,
        decay_curve=DecayCurve.SIGMOID,
    )
