"""用户模型"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.conversation import Conversation
    from app.models.llm_usage import LLMUsageRecord
    from app.models.memory import Memory


class User(BaseModel):
    """用户模型"""

    __tablename__ = "users"

    # 关联账号
    account_id: Mapped[str] = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    account: Mapped["Account"] = relationship("Account", back_populates="users")

    # 平台信息
    platform_user_id: Mapped[str] = Column(String(255), nullable=False)  # 微信openid/QQ号
    platform_type: Mapped[str] = Column(String(50), nullable=False)  # wechat/qq
    nickname: Mapped[str | None] = Column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = Column(String(500), nullable=True)

    # 关系状态
    relationship_stage: Mapped[str] = Column(
        String(50), default="stranger"
    )  # stranger/acquaintance/friend/close
    trust_score: Mapped[float] = Column(Float, default=0.0)  # 0-100
    intimacy_score: Mapped[float] = Column(Float, default=0.0)  # 0-100

    # 统计
    total_messages: Mapped[int] = Column(Integer, default=0)
    last_interaction_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # 关系
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    memories: Mapped[List["Memory"]] = relationship(
        "Memory", back_populates="user", cascade="all, delete-orphan"
    )
    llm_usage_records: Mapped[List["LLMUsageRecord"]] = relationship(
        "LLMUsageRecord", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"


class UserProfile(BaseModel):
    """用户画像"""

    __tablename__ = "user_profiles"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship("User")

    # 基本信息
    age: Mapped[int | None] = Column(Integer, nullable=True)
    gender: Mapped[str | None] = Column(String(10), nullable=True)
    location: Mapped[str | None] = Column(String(255), nullable=True)
    occupation: Mapped[str | None] = Column(String(255), nullable=True)

    # 兴趣爱好
    interests: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    # 重要日期
    birthday: Mapped[datetime | None] = Column(DateTime, nullable=True)
    important_dates: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    # 情感状态
    emotional_state: Mapped[str | None] = Column(String(50), nullable=True)

    # 沟通偏好
    preferred_topics: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式
    disliked_topics: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"
