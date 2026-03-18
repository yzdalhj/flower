"""管理员用户模型"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.account import Account


# 管理员与账号的关联表
admin_account_association = Table(
    "admin_account_associations",
    BaseModel.metadata,
    Column("admin_user_id", String(36), ForeignKey("admin_users.id"), primary_key=True),
    Column("account_id", String(36), ForeignKey("accounts.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class AdminUser(BaseModel):
    """管理员用户模型

    用于登录后台管理系统的运营人员
    """

    __tablename__ = "admin_users"

    # 登录信息
    username: Mapped[str] = Column(String(100), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = Column(String(255), nullable=False)

    # 个人信息
    nickname: Mapped[str | None] = Column(String(100), nullable=True)
    email: Mapped[str | None] = Column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = Column(String(500), nullable=True)

    # 角色权限
    role: Mapped[str] = Column(String(50), default="admin")  # super_admin / admin / viewer
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # 安全相关
    last_login_at: Mapped[datetime | None] = Column(DateTime, nullable=True)
    last_login_ip: Mapped[str | None] = Column(String(50), nullable=True)
    login_count: Mapped[int] = Column(Integer, default=0)

    # 可管理的账号（多对多）
    accounts: Mapped[List["Account"]] = relationship(
        "Account",
        secondary=admin_account_association,
        back_populates="admin_users",
    )

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username={self.username}, role={self.role})>"

    def is_super_admin(self) -> bool:
        """检查是否为超级管理员"""
        return self.role == "super_admin"

    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role in ("super_admin", "admin")

    def is_viewer(self) -> bool:
        """检查是否为只读用户"""
        return self.role == "viewer"

    def can_manage_account(self, account_id: str) -> bool:
        """检查是否可以管理指定账号

        Args:
            account_id: 账号ID

        Returns:
            是否有权限
        """
        if self.is_super_admin():
            return True
        return any(acc.id == account_id for acc in self.accounts)

    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限

        Args:
            permission: 权限名称

        Returns:
            是否有权限
        """
        permissions_map = {
            "super_admin": ["*"],  # 所有权限
            "admin": [
                "account:read",
                "account:write",
                "user:read",
                "user:write",
                "conversation:read",
                "conversation:write",
                "memory:read",
                "memory:write",
                "settings:read",
                "settings:write",
                "llm_usage:read",
            ],
            "viewer": [
                "account:read",
                "user:read",
                "conversation:read",
                "memory:read",
                "settings:read",
                "llm_usage:read",
            ],
        }

        user_permissions = permissions_map.get(self.role, [])
        return "*" in user_permissions or permission in user_permissions

    def record_login(self, ip: str | None = None) -> None:
        """记录登录信息

        Args:
            ip: 登录IP地址
        """
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip
        self.login_count += 1

    def to_dict(self) -> dict:
        """转换为字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
