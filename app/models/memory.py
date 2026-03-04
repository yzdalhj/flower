"""记忆模型"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Memory(BaseModel):
    """长期记忆"""

    __tablename__ = "memories"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    user: Optional["User"] = relationship("User", back_populates="memories")

    # 记忆类型
    memory_type = Column(String(50), nullable=False)
    # episodic: 情节记忆（具体事件）
    # semantic: 语义记忆（事实信息）
    # emotional: 情感记忆（情感体验）
    # preference: 偏好记忆（喜好厌恶）

    # 记忆内容
    content = Column(Text, nullable=False)
    summary = Column(String(500), nullable=True)

    # 时间信息
    occurred_at = Column(DateTime, nullable=True)  # 事件发生时间
    expires_at = Column(DateTime, nullable=True)  # 过期时间

    # 重要性
    importance = Column(Float, default=1.0)  # 1-10

    # 访问统计
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)

    # 向量ID (用于ChromaDB检索)
    vector_id = Column(String(100), nullable=True, index=True)

    # 元数据
    metadata = Column(Text, nullable=True)  # JSON格式

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.memory_type})>"


class WorkingMemory(BaseModel):
    """工作记忆 - 当前会话上下文"""

    __tablename__ = "working_memories"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # 当前会话ID
    conversation_id = Column(String(36), nullable=True)

    # 短期上下文 (最近N轮对话)
    context = Column(Text, nullable=True)  # JSON格式

    # 当前情感状态
    current_emotion = Column(Text, nullable=True)  # JSON格式

    # 当前话题
    current_topic = Column(String(255), nullable=True)

    # 待处理意图
    pending_intent = Column(String(255), nullable=True)

    # 过期时间
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkingMemory(user_id={self.user_id})>"
