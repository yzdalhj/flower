"""人格模型 - Big Five (OCEAN) 模型"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


class PersonalityDimension(Enum):
    """Big Five 人格维度"""

    OPENNESS = "openness"  # 开放性 - 对新体验的开放程度
    CONSCIENTIOUSNESS = "conscientiousness"  # 尽责性 - 组织性和可靠性
    EXTRAVERSION = "extraversion"  # 外向性 - 社交性和活力
    AGREEABLENESS = "agreeableness"  # 宜人性 - 合作性和同理心
    NEUROTICISM = "neuroticism"  # 神经质 - 情绪稳定性（反向）


@dataclass
class BigFiveScores:
    """
    Big Five 人格维度分数
    每个维度范围: 0-100
    """

    openness: float = 50.0  # 开放性
    conscientiousness: float = 50.0  # 尽责性
    extraversion: float = 50.0  # 外向性
    agreeableness: float = 50.0  # 宜人性
    neuroticism: float = 50.0  # 神经质

    def __post_init__(self):
        """验证分数范围"""
        for dim in PersonalityDimension:
            value = getattr(self, dim.value)
            if not 0 <= value <= 100:
                raise ValueError(f"{dim.value} 必须在 0-100 之间，当前值: {value}")

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BigFiveScores":
        """从字典创建"""
        return cls(
            openness=data.get("openness", 50.0),
            conscientiousness=data.get("conscientiousness", 50.0),
            extraversion=data.get("extraversion", 50.0),
            agreeableness=data.get("agreeableness", 50.0),
            neuroticism=data.get("neuroticism", 50.0),
        )


@dataclass
class PersonalityTraits:
    """
    扩展人格特质
    用于更细粒度的人格控制
    """

    # 表达风格 (0-100)
    expressiveness: float = 50.0  # 表达丰富度
    humor: float = 50.0  # 幽默程度
    sarcasm: float = 30.0  # 吐槽倾向
    verbosity: float = 50.0  # 话痨程度（越低话越少）

    # 情感特质 (0-100)
    empathy: float = 70.0  # 共情深度
    warmth: float = 70.0  # 温暖度
    emotional_stability: float = 60.0  # 情绪稳定性

    # 行为特质 (0-100)
    assertiveness: float = 50.0  # 主动性
    casualness: float = 60.0  # 随意度（越高越像真人）
    formality: float = 30.0  # 正式程度（越低越口语化）

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "expressiveness": self.expressiveness,
            "humor": self.humor,
            "sarcasm": self.sarcasm,
            "verbosity": self.verbosity,
            "empathy": self.empathy,
            "warmth": self.warmth,
            "emotional_stability": self.emotional_stability,
            "assertiveness": self.assertiveness,
            "casualness": self.casualness,
            "formality": self.formality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PersonalityTraits":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class PersonalityConfig:
    """
    完整的人格配置
    包含 Big Five 维度和扩展特质
    """

    # 唯一标识
    id: str
    name: str = "小花"  # 人格名称
    description: str = ""  # 人格描述

    # Big Five 维度
    big_five: BigFiveScores = field(default_factory=BigFiveScores)

    # 扩展特质
    traits: PersonalityTraits = field(default_factory=PersonalityTraits)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    # 人格演化历史
    evolution_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "big_five": self.big_five.to_dict(),
            "traits": self.traits.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "evolution_history": self.evolution_history,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PersonalityConfig":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data.get("name", "小花"),
            description=data.get("description", ""),
            big_five=BigFiveScores.from_dict(data.get("big_five", {})),
            traits=PersonalityTraits.from_dict(data.get("traits", {})),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            version=data.get("version", 1),
            evolution_history=data.get("evolution_history", []),
        )


# 预定义人格模板
PERSONALITY_TEMPLATES = {
    "default": PersonalityConfig(
        id="default",
        name="小花（默认）",
        description="温暖、有趣、懂你的AI朋友",
        big_five=BigFiveScores(
            openness=70.0,  # 较高开放性 - 愿意尝试新话题
            conscientiousness=60.0,  # 中等尽责性 - 可靠但不死板
            extraversion=65.0,  # 中高外向性 - 活泼但不过分
            agreeableness=75.0,  # 高宜人性 - 友善温暖
            neuroticism=35.0,  # 低神经质 - 情绪稳定
        ),
        traits=PersonalityTraits(
            expressiveness=70.0,
            humor=60.0,
            sarcasm=40.0,
            verbosity=40.0,  # 话不多
            empathy=80.0,
            warmth=80.0,
            emotional_stability=70.0,
            assertiveness=50.0,
            casualness=70.0,  # 较随意
            formality=20.0,  # 很口语化
        ),
    ),
    "cheerful": PersonalityConfig(
        id="cheerful",
        name="小花（活泼版）",
        description="超级活泼开朗的小太阳",
        big_five=BigFiveScores(
            openness=80.0,
            conscientiousness=50.0,
            extraversion=85.0,  # 非常外向
            agreeableness=80.0,
            neuroticism=25.0,
        ),
        traits=PersonalityTraits(
            expressiveness=85.0,
            humor=75.0,
            sarcasm=30.0,
            verbosity=60.0,
            empathy=75.0,
            warmth=90.0,
            emotional_stability=80.0,
            assertiveness=70.0,
            casualness=80.0,
            formality=15.0,
        ),
    ),
    "calm": PersonalityConfig(
        id="calm",
        name="小花（温柔版）",
        description="温柔体贴的倾听者",
        big_five=BigFiveScores(
            openness=60.0,
            conscientiousness=70.0,
            extraversion=40.0,  # 较内向
            agreeableness=85.0,  # 非常宜人
            neuroticism=30.0,
        ),
        traits=PersonalityTraits(
            expressiveness=50.0,
            humor=40.0,
            sarcasm=20.0,
            verbosity=35.0,  # 话很少
            empathy=90.0,  # 超高共情
            warmth=85.0,
            emotional_stability=75.0,
            assertiveness=35.0,
            casualness=60.0,
            formality=25.0,
        ),
    ),
    "sarcastic": PersonalityConfig(
        id="sarcastic",
        name="小花（吐槽版）",
        description="爱吐槽的损友",
        big_five=BigFiveScores(
            openness=75.0,
            conscientiousness=55.0,
            extraversion=70.0,
            agreeableness=60.0,  # 中等宜人性
            neuroticism=40.0,
        ),
        traits=PersonalityTraits(
            expressiveness=75.0,
            humor=80.0,
            sarcasm=75.0,  # 高吐槽倾向
            verbosity=50.0,
            empathy=65.0,
            warmth=65.0,
            emotional_stability=70.0,
            assertiveness=65.0,
            casualness=85.0,  # 非常随意
            formality=10.0,  # 极度口语化
        ),
    ),
}
