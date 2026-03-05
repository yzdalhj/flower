"""账号模型"""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
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
    enable_image: Mapped[bool] = Column(Boolean, default=True)
    enable_proactive: Mapped[bool] = Column(Boolean, default=True)
    enable_learning: Mapped[bool] = Column(Boolean, default=True)

    # 限制配置
    max_daily_messages: Mapped[int] = Column(Integer, default=1000)
    max_daily_cost: Mapped[float] = Column(Float, default=50.0)
    response_rate_limit: Mapped[int] = Column(Integer, default=100)

    # 人格配置 (JSON格式存储)
    personality_config: Mapped[str | None] = Column(Text, nullable=True)

    # 统计
    today_message_count: Mapped[int] = Column(Integer, default=0)
    today_cost: Mapped[float] = Column(Float, default=0.0)

    # 关系
    users: Mapped[List["User"]] = relationship("User", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name={self.name}, platform={self.platform})>"
