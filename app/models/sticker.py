"""表情包模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class StickerType(str, Enum):
    """表情包类型"""

    EMOTION = "emotion"  # 情绪类
    REACTION = "reaction"  # 反应类
    MEME = "meme"  # 梗图类
    CUSTOM = "custom"  # 自定义类


class StickerEmotion(str, Enum):
    """表情包关联情绪"""

    HAPPY = "happy"  # 开心、愉悦
    EXCITED = "excited"  # 兴奋、激动
    SAD = "sad"  # 伤心、难过
    ANGRY = "angry"  # 生气、愤怒
    SURPRISED = "surprised"  # 惊讶、惊喜
    CONFUSED = "confused"  # 困惑、疑惑
    LOVING = "loving"  # 喜爱、心动
    EMBARRASSED = "embarrassed"  # 尴尬、害羞
    PROUD = "proud"  # 骄傲、得意
    RELAXED = "relaxed"  # 放松、悠闲
    SILLY = "silly"  # 搞怪、沙雕
    SUPPORTIVE = "supportive"  # 安慰、支持


class StickerPersonalityMatch(str, Enum):
    """适配人格类型"""

    DEFAULT = "default"  # 默认通用
    CHEERFUL = "cheerful"  # 活泼型
    CALM = "calm"  # 沉稳型
    SARCASTIC = "sarcastic"  # 吐槽型
    ALL = "all"  # 所有类型


class Sticker(BaseModel):
    """表情包数据库模型"""

    __tablename__ = "stickers"

    # 基础信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="表情包名称")
    type: Mapped[StickerType] = mapped_column(String(20), nullable=False, comment="表情包类型")
    url: Mapped[str] = mapped_column(String(500), nullable=False, comment="表情包文件URL或路径")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, comment="文件大小（字节）")
    file_format: Mapped[Optional[str]] = mapped_column(
        String(10), comment="文件格式（gif/png/jpg等）"
    )

    # 分类和标签
    emotion: Mapped[Optional[StickerEmotion]] = mapped_column(String(20), comment="关联情绪")
    personality_match: Mapped[StickerPersonalityMatch] = mapped_column(
        String(20), default=StickerPersonalityMatch.ALL, comment="适配人格类型"
    )
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, comment="标签列表")
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list, comment="关键词列表")

    # 元数据
    description: Mapped[Optional[str]] = mapped_column(Text, comment="表情包描述")
    usage_count: Mapped[int] = mapped_column(Integer, default=0, comment="使用次数")
    success_rate: Mapped[float] = mapped_column(Float, default=0.8, comment="用户反馈成功率")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    source: Mapped[Optional[str]] = mapped_column(String(50), comment="来源")

    # 权重配置
    base_weight: Mapped[float] = mapped_column(Float, default=1.0, comment="基础权重")
    emotion_weight: Mapped[float] = mapped_column(Float, default=1.0, comment="情绪匹配权重")
    personality_weight: Mapped[float] = mapped_column(Float, default=1.0, comment="人格匹配权重")
    context_weight: Mapped[float] = mapped_column(Float, default=1.0, comment="上下文匹配权重")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "emotion": self.emotion,
            "personality_match": self.personality_match,
            "tags": self.tags,
            "keywords": self.keywords,
            "description": self.description,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
            "source": self.source,
            "base_weight": self.base_weight,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class StickerSelection:
    """表情包选择结果"""

    sticker: Sticker
    match_score: float
    emotion_match: float
    personality_match: float
    context_match: float
    reason: str = ""


@dataclass
class StickerSendStrategy:
    """表情包发送策略

    注意：发送前的语境过滤已在 dialogue.py 的 _should_send_meme() 中完成，
    这里配置的是通过过滤后的发送概率
    """

    # 发送概率配置（通过 _should_send_meme 过滤后）
    only_sticker_probability: float = 0.2  # 20%概率只发梗图
    text_with_sticker_probability: float = 0.6  # 60%概率图文搭配
    no_sticker_probability: float = 0.2  # 20%概率不发

    # 触发条件
    min_emotion_intensity: float = 0.3  # 最低情绪强度阈值（已在前面过滤，这里放宽）
    max_stickers_per_message: int = 1  # 单条消息最多表情包数量
    use_sticker_in_serious_context: bool = False  # 严肃场景是否使用表情包

    # 人格适配
    personality_adjustment: Dict[str, float] = field(
        default_factory=lambda: {
            "cheerful": 1.3,  # 活泼型人格增加梗图使用概率
            "calm": 0.6,  # 沉稳型人格减少梗图使用概率
            "sarcastic": 1.4,  # 吐槽型人格更适合用梗图
            "default": 1.0,  # 默认
        }
    )
