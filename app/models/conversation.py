"""对话模型"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(BaseModel):
    """对话会话"""

    __tablename__ = "conversations"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="conversations")

    # 会话状态
    status: Mapped[str] = Column(String(50), default="active")  # active/paused/ended
    started_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # 会话统计
    message_count: Mapped[int] = Column(Integer, default=0)
    last_message_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # 人格配置
    personality_id: Mapped[str] = Column(String(50), default="default")  # 关联的人格ID

    # 关系
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"


class Message(BaseModel):
    """消息记录"""

    __tablename__ = "messages"

    conversation_id: Mapped[str] = Column(
        String(36), ForeignKey("conversations.id"), nullable=False
    )
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # 消息信息
    role: Mapped[str] = Column(String(50), nullable=False)  # user/assistant/system
    content: Mapped[str] = Column(Text, nullable=False)
    content_type: Mapped[str] = Column(String(50), default="text")  # text/emoji/image/voice

    # 情感分析
    emotion_valence: Mapped[float | None] = Column(Float, nullable=True)  # 愉悦度 -1~1
    emotion_arousal: Mapped[float | None] = Column(Float, nullable=True)  # 激活度 -1~1

    # 元数据
    meta_data: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    # 使用的模型
    model_used: Mapped[str | None] = Column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"
