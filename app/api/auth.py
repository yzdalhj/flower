"""认证 API

提供登录、登出、获取当前管理员用户等认证相关接口
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import create_access_token, get_password_hash, security, verify_password
from app.core.session import get_db
from app.models.admin_user import AdminUser

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class AdminUserInfoResponse(BaseModel):
    """管理员用户信息响应"""

    id: str
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    last_login_at: Optional[str] = None
    login_count: int


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str
    new_password: str


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """获取当前管理员用户

    从请求中的 JWT Token 解析并获取当前管理员用户
    """
    from jose import JWTError, jwt

    from app.config import get_settings

    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 检查是否提供了认证凭证
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    try:
        # 解码 JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 查询管理员用户
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id, AdminUser.is_active)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        raise credentials_exception

    return admin


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """管理员登录

    验证用户名密码，返回 JWT Token
    """
    # 查找管理员用户
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == request.username, AdminUser.is_active)
    )
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证密码
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 记录登录信息
    client_ip = http_request.client.host if http_request.client else None
    admin.record_login(client_ip)
    await db.commit()

    # 创建访问令牌
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={
            "sub": admin.id,
            "username": admin.username,
            "role": admin.role,
        },
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24小时
        user=admin.to_dict(),
    )


@router.get("/me", response_model=AdminUserInfoResponse)
async def get_me(current_admin: AdminUser = Depends(get_current_admin_user)):
    """获取当前登录管理员信息"""
    return AdminUserInfoResponse(
        id=current_admin.id,
        username=current_admin.username,
        nickname=current_admin.nickname,
        email=current_admin.email,
        avatar_url=current_admin.avatar_url,
        role=current_admin.role,
        is_active=current_admin.is_active,
        last_login_at=(
            current_admin.last_login_at.isoformat() if current_admin.last_login_at else None
        ),
        login_count=current_admin.login_count,
    )


@router.post("/logout")
async def logout(current_admin: AdminUser = Depends(get_current_admin_user)):
    """管理员登出

    前端需要清除本地存储的 token
    """
    # JWT 是无状态的，服务端不需要做特殊处理
    # 如果需要实现 token 黑名单，可以在这里将 token 加入黑名单
    return {"message": "登出成功"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(request.old_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

    # 更新为新密码哈希
    current_admin.password_hash = get_password_hash(request.new_password)
    await db.commit()

    return {"message": "密码修改成功"}


@router.post("/refresh")
async def refresh_token(current_admin: AdminUser = Depends(get_current_admin_user)):
    """刷新访问令牌"""
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={
            "sub": current_admin.id,
            "username": current_admin.username,
            "role": current_admin.role,
        },
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,
    }


# 管理员管理接口（仅超级管理员可用）
class CreateAdminRequest(BaseModel):
    """创建管理员请求"""

    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: str = "admin"  # super_admin / admin / viewer


@router.post("/admins")
async def create_admin(
    request: CreateAdminRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新管理员（仅超级管理员）"""
    if not current_admin.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建管理员账号",
        )

    # 检查用户名是否已存在
    result = await db.execute(select(AdminUser).where(AdminUser.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建新管理员
    new_admin = AdminUser(
        username=request.username,
        password_hash=get_password_hash(request.password),
        nickname=request.nickname,
        email=request.email,
        role=request.role,
        is_active=True,
    )
    db.add(new_admin)
    await db.commit()

    return {"message": "管理员创建成功", "id": new_admin.id}


@router.get("/admins")
async def list_admins(
    current_admin: AdminUser = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    """获取管理员列表（仅超级管理员）"""
    if not current_admin.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以查看管理员列表",
        )

    result = await db.execute(select(AdminUser))
    admins = result.scalars().all()

    return {
        "data": [admin.to_dict() for admin in admins],
        "total": len(admins),
    }
