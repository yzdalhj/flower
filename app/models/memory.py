"""记忆模型"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Memory(BaseModel):
    """长期记忆"""

    __tablename__ = "memories"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="memories")

    # 记忆类型
    memory_type: Mapped[str] = Column(String(50), nullable=False)
    # episodic: 情节记忆（具体事件）
    # semantic: 语义记忆（事实信息）
    # emotional: 情感记忆（情感体验）
    # preference: 偏好记忆（喜好厌恶）

    # 记忆内容
    content: Mapped[str] = Column(Text, nullable=False)
    summary: Mapped[str | None] = Column(String(500), nullable=True)

    # 时间信息
    occurred_at: Mapped[datetime | None] = Column(DateTime, nullable=True)  # 事件发生时间
    expires_at: Mapped[datetime | None] = Column(DateTime, nullable=True)  # 过期时间

    # 重要性
    importance: Mapped[float] = Column(Float, default=1.0)  # 1-10

    # 访问统计
    access_count: Mapped[int] = Column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # 向量ID (用于ChromaDB检索)
    vector_id: Mapped[str | None] = Column(String(100), nullable=True, index=True)

    # 元数据
    meta_data: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.memory_type})>"


class WorkingMemory(BaseModel):
    """工作记忆 - 当前会话上下文"""

    __tablename__ = "working_memories"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # 当前会话ID
    conversation_id: Mapped[str | None] = Column(String(36), nullable=True)

    # 短期上下文 (最近N轮对话)
    context: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    # 当前情感状态
    current_emotion: Mapped[str | None] = Column(Text, nullable=True)  # JSON格式

    # 当前话题
    current_topic: Mapped[str | None] = Column(String(255), nullable=True)

    # 待处理意图
    pending_intent: Mapped[str | None] = Column(String(255), nullable=True)

    # 过期时间
    expires_at: Mapped[datetime] = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkingMemory(user_id={self.user_id})>"
