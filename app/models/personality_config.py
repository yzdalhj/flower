"""人格配置模型 - 用于后台管理"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import Mapped

from app.models.base import BaseModel


class PersonalityConfigModel(BaseModel):
    """人格配置模型

    用于后台管理人格模板，账号可以通过下拉菜单选择使用
    """

    __tablename__ = "personality_configs"

    # 基本信息
    name: Mapped[str] = Column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = Column(Text, nullable=True)
    avatar_url: Mapped[str | None] = Column(String(500), nullable=True)

    # 是否启用
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # 是否系统预设（系统预设不可删除）
    is_system: Mapped[bool] = Column(Boolean, default=False)

    # 使用次数统计
    usage_count: Mapped[int] = Column(Integer, default=0)

    # Big Five 维度 (0-100)
    openness: Mapped[float] = Column(Float, default=50.0)
    conscientiousness: Mapped[float] = Column(Float, default=50.0)
    extraversion: Mapped[float] = Column(Float, default=50.0)
    agreeableness: Mapped[float] = Column(Float, default=50.0)
    neuroticism: Mapped[float] = Column(Float, default=50.0)

    # 扩展特质 (0-100)
    expressiveness: Mapped[float] = Column(Float, default=50.0)  # 表达丰富度
    humor: Mapped[float] = Column(Float, default=50.0)  # 幽默程度
    sarcasm: Mapped[float] = Column(Float, default=30.0)  # 吐槽倾向
    verbosity: Mapped[float] = Column(Float, default=50.0)  # 话痨程度
    empathy: Mapped[float] = Column(Float, default=70.0)  # 共情深度
    warmth: Mapped[float] = Column(Float, default=70.0)  # 温暖度
    emotional_stability: Mapped[float] = Column(Float, default=60.0)  # 情绪稳定性
    assertiveness: Mapped[float] = Column(Float, default=50.0)  # 主动性
    casualness: Mapped[float] = Column(Float, default=60.0)  # 随意度
    formality: Mapped[float] = Column(Float, default=30.0)  # 正式程度

    # 标签（逗号分隔）
    tags: Mapped[str | None] = Column(String(255), nullable=True)

    # 创建者
    created_by: Mapped[str | None] = Column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<PersonalityConfig(id={self.id}, name={self.name})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "usage_count": self.usage_count,
            "big_five": {
                "openness": self.openness,
                "conscientiousness": self.conscientiousness,
                "extraversion": self.extraversion,
                "agreeableness": self.agreeableness,
                "neuroticism": self.neuroticism,
            },
            "traits": {
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
            },
            "tags": self.tags.split(",") if self.tags else [],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_personality_config(self) -> dict:
        """获取 personality_config 格式的字典（用于账号配置）"""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "traits": {
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
            },
        }
