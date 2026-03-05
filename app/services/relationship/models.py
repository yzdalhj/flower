import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class InteractionRecord:
    """
    单次互动记录
    用于亲密度和信任度计算
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # 互动内容
    user_message: str = ""
    ai_response: str = ""

    # 情感分析结果
    user_emotion: Dict[str, float] = field(default_factory=dict)  # 用户情感状态
    ai_emotion: Dict[str, float] = field(default_factory=dict)  # AI情感状态
    emotional_resonance: float = 0.0  # 情感共鸣度 (0-1)

    # 自我披露分析
    user_disclosure_depth: float = 0.0  # 用户披露深度 (0-1)
    disclosure_topics: List[str] = field(default_factory=list)  # 披露的话题

    # 互动质量评分
    quality_score: float = 0.0  # 综合质量分 (0-1)
    importance_score: float = 0.0  # 重要性评分 (0-1)

    # 话题标签
    topics: List[str] = field(default_factory=list)
    entities: List[Dict] = field(
        default_factory=list
    )  # 提取的实体 [{"text": "北京", "label": "GPE"}]
