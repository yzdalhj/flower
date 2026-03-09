"""主动行为系统数据模型"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped

from app.models.base import BaseModel


class ActiveMessageType(str, Enum):
    """主动消息类型"""

    CARE = "care"  # 关怀消息
    TOPIC = "topic"  # 话题发起
    REMINDER = "reminder"  # 提醒
    GREETING = "greeting"  # 问候
    ANNIVERSARY = "anniversary"  # 纪念日祝福


class ActiveMessageStatus(str, Enum):
    """主动消息状态"""

    PENDING = "pending"  # 待发送
    SENT = "sent"  # 已发送
    FAILED = "failed"  # 发送失败
    CANCELLED = "cancelled"  # 已取消


class ScheduledTaskType(str, Enum):
    """定时任务类型"""

    IMPORTANT_DATE = "important_date"  # 重要日期检测
    LONG_TIME_NO_CONTACT = "long_time_no_contact"  # 长时间未联系检测
    FREQUENCY_CONTROL = "frequency_control"  # 频率控制
    DAILY_CHECK = "daily_check"  # 每日检查


class ActiveMessageRecord(BaseModel):
    """主动消息发送记录"""

    __tablename__ = "active_message_records"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False)
    message_type: Mapped[ActiveMessageType] = Column(String(50), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    scheduled_send_time: Mapped[datetime] = Column(DateTime, nullable=False)
    actual_send_time: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    status: Mapped[ActiveMessageStatus] = Column(String(50), default=ActiveMessageStatus.PENDING)

    # 用户反馈
    user_feedback: Mapped[Optional[str]] = Column(
        String(50), nullable=True
    )  # positive/negative/neutral
    user_response_time: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)

    # 元数据
    trigger_reason: Mapped[str] = Column(String(255), nullable=False)  # 触发原因
    priority: Mapped[int] = Column(Integer, default=5)  # 优先级 1-10，越高越优先
    meta_data: Mapped[Optional[str]] = Column(Text, nullable=True)  # JSON格式的扩展数据

    def __repr__(self) -> str:
        return (
            f"<ActiveMessageRecord(id={self.id}, user_id={self.user_id}, type={self.message_type})>"
        )


class UserActivePreference(BaseModel):
    """用户主动消息偏好设置"""

    __tablename__ = "user_active_preferences"

    user_id: Mapped[str] = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # 频率控制
    max_messages_per_day: Mapped[int] = Column(Integer, default=2)  # 每天最多发送条数
    quiet_hours_start: Mapped[Optional[int]] = Column(
        Integer, nullable=True
    )  # 免打扰开始时间（小时）
    quiet_hours_end: Mapped[Optional[int]] = Column(
        Integer, nullable=True
    )  # 免打扰结束时间（小时）

    # 偏好设置
    enabled_message_types: Mapped[str] = Column(
        Text, default='["care", "topic", "greeting", "anniversary"]'
    )  # JSON数组
    preferred_send_time_start: Mapped[int] = Column(Integer, default=9)  # 偏好发送开始时间（小时）
    preferred_send_time_end: Mapped[int] = Column(Integer, default=22)  # 偏好发送结束时间（小时）

    # 统计数据
    total_sent: Mapped[int] = Column(Integer, default=0)
    positive_feedback_count: Mapped[int] = Column(Integer, default=0)
    negative_feedback_count: Mapped[int] = Column(Integer, default=0)
    last_message_sent_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UserActivePreference(user_id={self.user_id})>"


class ScheduledTaskLog(BaseModel):
    """定时任务执行日志"""

    __tablename__ = "scheduled_task_logs"

    task_type: Mapped[ScheduledTaskType] = Column(String(50), nullable=False)
    started_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    status: Mapped[str] = Column(String(50), default="running")  # running/success/failed
    message_count: Mapped[int] = Column(Integer, default=0)
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ScheduledTaskLog(id={self.id}, type={self.task_type}, status={self.status})>"
