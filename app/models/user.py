"""用户模型"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.conversation import Conversation
    from app.models.memory import Memory


class User(BaseModel):
    """用户模型"""

    __tablename__ = "users"

    # 关联账号
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    account: Optional["Account"] = relationship("Account", back_populates="users")

    # 平台信息
    platform_user_id = Column(String(255), nullable=False)  # 微信openid/QQ号
    platform_type = Column(String(50), nullable=False)  # wechat/qq
    nickname = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # 关系状态
    relationship_stage = Column(
        String(50), default="stranger"
    )  # stranger/acquaintance/friend/close
    trust_score = Column(Float, default=0.0)  # 0-100
    intimacy_score = Column(Float, default=0.0)  # 0-100

    # 统计
    total_messages = Column(Integer, default=0)
    last_interaction_at = Column(DateTime, nullable=True)

    # 关系
    conversations: List["Conversation"] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    memories: List["Memory"] = relationship(
        "Memory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"


class UserProfile(BaseModel):
    """用户画像"""

    __tablename__ = "user_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    user: Optional["User"] = relationship("User")

    # 基本信息
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    location = Column(String(255), nullable=True)
    occupation = Column(String(255), nullable=True)

    # 兴趣爱好
    interests = Column(Text, nullable=True)  # JSON格式

    # 重要日期
    birthday = Column(DateTime, nullable=True)
    important_dates = Column(Text, nullable=True)  # JSON格式

    # 情感状态
    emotional_state = Column(String(50), nullable=True)

    # 沟通偏好
    preferred_topics = Column(Text, nullable=True)  # JSON格式
    disliked_topics = Column(Text, nullable=True)  # JSON格式

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"
