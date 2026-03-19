"""账号模型"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser
    from app.models.user import User


class Account(BaseModel):
    """账号模型 - 支持多账号管理"""

    __tablename__ = "accounts"

    # 基本信息
    name: Mapped[str] = Column(String(255), nullable=False)
    platform: Mapped[str] = Column(String(50), nullable=False)  # wechat/qq
    status: Mapped[str] = Column(String(50), default="stopped")  # running/stopped/error

    # 平台配置 (JSON格式存储)
    platform_config: Mapped[str] = Column(Text, nullable=False)

    # 功能开关
    enable_text: Mapped[bool] = Column(Boolean, default=True)
    enable_emoji: Mapped[bool] = Column(Boolean, default=True)
    enable_voice: Mapped[bool] = Column(Boolean, default=False)
    enable_voice_call: Mapped[bool] = Column(Boolean, default=False)
    enable_video_call: Mapped[bool] = Column(Boolean, default=False)
    enable_image: Mapped[bool] = Column(Boolean, default=True)
    enable_proactive: Mapped[bool] = Column(Boolean, default=True)
    enable_learning: Mapped[bool] = Column(Boolean, default=True)

    # 限制配置
    max_daily_messages: Mapped[int] = Column(Integer, default=1000)
    max_daily_cost: Mapped[float] = Column(Float, default=50.0)
    response_rate_limit: Mapped[int] = Column(Integer, default=100)

    # 人格配置 (JSON格式存储)
    personality_config: Mapped[str | None] = Column(Text, nullable=True)

    # 统计 - 今日数据
    today_message_count: Mapped[int] = Column(Integer, default=0)
    today_cost: Mapped[float] = Column(Float, default=0.0)

    # 统计 - 累计数据
    total_message_count: Mapped[int] = Column(Integer, default=0)
    total_cost: Mapped[float] = Column(Float, default=0.0)

    # 统计 - 时间戳
    stats_reset_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime | None] = Column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = Column(DateTime, nullable=True)
    stopped_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # 错误信息
    error_message: Mapped[str | None] = Column(Text, nullable=True)
    error_count: Mapped[int] = Column(Integer, default=0)

    # 关联的用户
    users: Mapped[List["User"]] = relationship("User", back_populates="account")

    # 关联的管理员（多对多）
    admin_users: Mapped[List["AdminUser"]] = relationship(
        "AdminUser",
        secondary="admin_account_associations",
        back_populates="accounts",
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name={self.name}, platform={self.platform})>"

    def is_running(self) -> bool:
        """检查账号是否正在运行"""
        return self.status == "running"

    def is_stopped(self) -> bool:
        """检查账号是否已停止"""
        return self.status == "stopped"

    def is_error(self) -> bool:
        """检查账号是否有错误"""
        return self.status == "error"

    def check_daily_limit(self) -> dict[str, bool]:
        """检查每日限制状态

        Returns:
            限制状态字典
        """
        return {
            "message_limit_reached": self.today_message_count >= self.max_daily_messages,
            "cost_limit_reached": self.today_cost >= self.max_daily_cost,
            "message_remaining": self.max_daily_messages - self.today_message_count,
            "cost_remaining": self.max_daily_cost - self.today_cost,
        }

    def can_send_message(self) -> bool:
        """检查是否可以发送消息"""
        if not self.is_running():
            return False

        limits = self.check_daily_limit()
        return not (limits["message_limit_reached"] or limits["cost_limit_reached"])

    def update_stats(self, message_count: int = 1, cost: float = 0.0) -> None:
        """更新统计数据

        Args:
            message_count: 消息数量
            cost: 成本
        """
        self.today_message_count += message_count
        self.today_cost += cost
        self.total_message_count += message_count
        self.total_cost += cost
        self.last_active_at = datetime.utcnow()

    def reset_daily_stats(self) -> None:
        """重置每日统计"""
        self.today_message_count = 0
        self.today_cost = 0.0
        self.stats_reset_at = datetime.utcnow()

    def set_error(self, message: str) -> None:
        """设置错误状态

        Args:
            message: 错误信息
        """
        self.status = "error"
        self.error_message = message
        self.error_count += 1
        self.stopped_at = datetime.utcnow()

    def start(self) -> None:
        """启动账号"""
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.error_message = None

    def stop(self) -> None:
        """停止账号"""
        self.status = "stopped"
        self.stopped_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict["is_running"] = self.is_running()
        base_dict["is_stopped"] = self.is_stopped()
        base_dict["is_error"] = self.is_error()
        base_dict["limits"] = self.check_daily_limit()
        return base_dict
