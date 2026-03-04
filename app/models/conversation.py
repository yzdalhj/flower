"""对话模型"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(BaseModel):
    """对话会话"""

    __tablename__ = "conversations"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    user: Optional["User"] = relationship("User", back_populates="conversations")

    # 会话状态
    status = Column(String(50), default="active")  # active/paused/ended
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # 会话统计
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)

    # 关系
    messages: List["Message"] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"


class Message(BaseModel):
    """消息记录"""

    __tablename__ = "messages"

    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    conversation: Optional["Conversation"] = relationship("Conversation", back_populates="messages")

    # 消息信息
    role = Column(String(50), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # text/emoji/image/voice

    # 情感分析
    emotion_valence = Column(Float, nullable=True)  # 愉悦度 -1~1
    emotion_arousal = Column(Float, nullable=True)  # 激活度 -1~1

    # 元数据
    metadata = Column(Text, nullable=True)  # JSON格式

    # 使用的模型
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"
