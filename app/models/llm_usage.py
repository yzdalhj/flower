"""LLM Token 使用记录模型"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class LLMUsageRecord(BaseModel):
    """LLM Token 使用记录"""

    __tablename__ = "llm_usage_records"

    # 关联用户（可选，用于统计用户级别的使用量）
    user_id: Mapped[Optional[str]] = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="llm_usage_records")

    # 关联对话（可选，用于追踪具体对话的消耗）
    conversation_id: Mapped[Optional[str]] = Column(
        String(36), ForeignKey("conversations.id"), nullable=True, index=True
    )

    # 使用的厂商和模型
    provider: Mapped[str] = Column(String(50), nullable=False, index=True)
    model: Mapped[str] = Column(String(100), nullable=False)

    # Token 使用量
    prompt_tokens: Mapped[int] = Column(Integer, default=0, nullable=False)  # 输入 token 数
    completion_tokens: Mapped[int] = Column(Integer, default=0, nullable=False)  # 输出 token 数
    total_tokens: Mapped[int] = Column(Integer, default=0, nullable=False)  # 总 token 数

    # 成本估算（可选，单位：美元）
    estimated_cost: Mapped[Optional[float]] = Column(Float, nullable=True)

    # 请求信息
    request_type: Mapped[str] = Column(
        String(50), nullable=False, index=True
    )  # 请求类型：chat, stream, embedding 等
    operation: Mapped[Optional[str]] = Column(
        String(100), nullable=True
    )  # 具体操作：对话、生成标题、提取记忆等

    # 响应信息
    status: Mapped[str] = Column(
        String(20), default="success", nullable=False, index=True
    )  # success, error, timeout
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)  # 错误信息
    latency_ms: Mapped[Optional[int]] = Column(Integer, nullable=True)  # 响应延迟（毫秒）

    # 请求内容摘要（用于调试和分析）
    prompt_summary: Mapped[Optional[str]] = Column(
        String(500), nullable=True
    )  # 输入内容摘要（前100字符）
    response_summary: Mapped[Optional[str]] = Column(
        String(500), nullable=True
    )  # 输出内容摘要（前100字符）

    # 元数据（JSON格式，存储额外信息）
    meta_data: Mapped[Optional[str]] = Column(Text, nullable=True)

    # 复合索引，用于常用查询
    __table_args__ = (
        Index("idx_llm_usage_user_time", "user_id", "created_at"),
        Index("idx_llm_usage_provider_time", "provider", "created_at"),
        Index("idx_llm_usage_conversation", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<LLMUsageRecord(id={self.id}, provider={self.provider}, tokens={self.total_tokens})>"
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "request_type": self.request_type,
            "operation": self.operation,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "prompt_summary": self.prompt_summary,
            "response_summary": self.response_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LLMUsageStatistics(BaseModel):
    """LLM 使用统计（按天聚合）"""

    __tablename__ = "llm_usage_statistics"

    # 用户ID（统计按用户分组）
    user_id: Mapped[Optional[str]] = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    # 统计日期
    stat_date: Mapped[str] = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # 厂商
    provider: Mapped[str] = Column(String(50), nullable=False, index=True)
    model: Mapped[str] = Column(String(100), nullable=False)

    # 聚合数据
    total_requests: Mapped[int] = Column(Integer, default=0)
    total_prompt_tokens: Mapped[int] = Column(Integer, default=0)
    total_completion_tokens: Mapped[int] = Column(Integer, default=0)
    total_tokens: Mapped[int] = Column(Integer, default=0)
    total_cost: Mapped[float] = Column(Float, default=0.0)

    # 成功/失败统计
    success_count: Mapped[int] = Column(Integer, default=0)
    error_count: Mapped[int] = Column(Integer, default=0)

    # 平均延迟
    avg_latency_ms: Mapped[Optional[int]] = Column(Integer, nullable=True)

    # 唯一约束：每天每个用户每个厂商每个模型一条记录
    __table_args__ = (
        Index(
            "idx_llm_stats_user_date_provider",
            "user_id",
            "stat_date",
            "provider",
            "model",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<LLMUsageStatistics(date={self.stat_date}, provider={self.provider}, tokens={self.total_tokens})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stat_date": self.stat_date,
            "provider": self.provider,
            "model": self.model,
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
