"""账号管理API"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.services.account import AccountLimiter, AccountManager

router = APIRouter(prefix="/accounts", tags=["账号管理"])


# ============ 请求/响应模型 ============


class CreateAccountRequest(BaseModel):
    """创建账号请求"""

    name: str = Field(..., description="账号名称", min_length=1, max_length=255)
    platform: str = Field(..., description="平台类型", pattern="^(wechat|qq)$")
    platform_config: dict[str, Any] = Field(..., description="平台配置")
    personality_config: dict[str, Any] | None = Field(None, description="人格配置")
    max_daily_messages: int = Field(1000, description="每日最大消息数", ge=1)
    max_daily_cost: float = Field(50.0, description="每日最大成本", ge=0)
    enable_text: bool = Field(True, description="启用文本")
    enable_emoji: bool = Field(True, description="启用表情")
    enable_voice: bool = Field(False, description="启用语音")
    enable_image: bool = Field(True, description="启用图片")
    enable_proactive: bool = Field(True, description="启用主动行为")
    enable_learning: bool = Field(True, description="启用学习")


class UpdateAccountRequest(BaseModel):
    """更新账号请求"""

    name: str | None = Field(None, description="账号名称", min_length=1, max_length=255)
    platform_config: dict[str, Any] | None = Field(None, description="平台配置")
    personality_config: dict[str, Any] | None = Field(None, description="人格配置")
    max_daily_messages: int | None = Field(None, description="每日最大消息数", ge=1)
    max_daily_cost: float | None = Field(None, description="每日最大成本", ge=0)
    enable_text: bool | None = Field(None, description="启用文本")
    enable_emoji: bool | None = Field(None, description="启用表情")
    enable_voice: bool | None = Field(None, description="启用语音")
    enable_image: bool | None = Field(None, description="启用图片")
    enable_proactive: bool | None = Field(None, description="启用主动行为")
    enable_learning: bool | None = Field(None, description="启用学习")


class AccountResponse(BaseModel):
    """账号响应"""

    id: str
    name: str
    platform: str
    status: str
    enable_text: bool
    enable_emoji: bool
    enable_voice: bool
    enable_image: bool
    enable_proactive: bool
    enable_learning: bool
    max_daily_messages: int
    max_daily_cost: float
    today_message_count: int
    today_cost: float
    total_message_count: int
    total_cost: float
    created_at: str
    updated_at: str


class AccountListResponse(BaseModel):
    """账号列表响应"""

    total: int
    accounts: list[AccountResponse]


class AccountStatsResponse(BaseModel):
    """账号统计响应"""

    account_id: str
    name: str
    platform: str
    status: str
    today: dict[str, Any]
    total: dict[str, Any]
    limits: dict[str, Any]
    timestamps: dict[str, Any]
    error: dict[str, Any] | None


class LimitStatusResponse(BaseModel):
    """限制状态响应"""

    account_id: str
    status: str
    daily_limits: dict[str, Any]
    rate_limit: dict[str, Any]
    can_send: bool


class AlertResponse(BaseModel):
    """告警响应"""

    alerts: list[dict[str, Any]]


class MessageResponse(BaseModel):
    """通用消息响应"""

    message: str


# ============ API端点 ============


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    request: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    """创建新账号"""
    manager = AccountManager(db)

    try:
        account = await manager.create_account(
            name=request.name,
            platform=request.platform,
            platform_config=request.platform_config,
            personality_config=request.personality_config,
            max_daily_messages=request.max_daily_messages,
            max_daily_cost=request.max_daily_cost,
            enable_text=request.enable_text,
            enable_emoji=request.enable_emoji,
            enable_voice=request.enable_voice,
            enable_image=request.enable_image,
            enable_proactive=request.enable_proactive,
            enable_learning=request.enable_learning,
        )

        return AccountResponse(
            id=account.id,
            name=account.name,
            platform=account.platform,
            status=account.status,
            enable_text=account.enable_text,
            enable_emoji=account.enable_emoji,
            enable_voice=account.enable_voice,
            enable_image=account.enable_image,
            enable_proactive=account.enable_proactive,
            enable_learning=account.enable_learning,
            max_daily_messages=account.max_daily_messages,
            max_daily_cost=account.max_daily_cost,
            today_message_count=account.today_message_count,
            today_cost=account.today_cost,
            total_message_count=account.total_message_count,
            total_cost=account.total_cost,
            created_at=account.created_at.isoformat() if account.created_at else "",
            updated_at=account.updated_at.isoformat() if account.updated_at else "",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    platform: str | None = Query(None, description="平台过滤"),
    status: str | None = Query(None, description="状态过滤"),
    limit: int = Query(100, description="数量限制", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
    db: AsyncSession = Depends(get_db),
) -> AccountListResponse:
    """获取账号列表"""
    manager = AccountManager(db)

    accounts = await manager.list_accounts(
        platform=platform,
        status=status,
        limit=limit,
        offset=offset,
    )

    return AccountListResponse(
        total=len(accounts),
        accounts=[
            AccountResponse(
                id=account.id,
                name=account.name,
                platform=account.platform,
                status=account.status,
                enable_text=account.enable_text,
                enable_emoji=account.enable_emoji,
                enable_voice=account.enable_voice,
                enable_image=account.enable_image,
                enable_proactive=account.enable_proactive,
                enable_learning=account.enable_learning,
                max_daily_messages=account.max_daily_messages,
                max_daily_cost=account.max_daily_cost,
                today_message_count=account.today_message_count,
                today_cost=account.today_cost,
                total_message_count=account.total_message_count,
                total_cost=account.total_cost,
                created_at=account.created_at.isoformat() if account.created_at else "",
                updated_at=account.updated_at.isoformat() if account.updated_at else "",
            )
            for account in accounts
        ],
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    """获取账号详情"""
    manager = AccountManager(db)

    account = await manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"账号不存在: {account_id}")

    return AccountResponse(
        id=account.id,
        name=account.name,
        platform=account.platform,
        status=account.status,
        enable_text=account.enable_text,
        enable_emoji=account.enable_emoji,
        enable_voice=account.enable_voice,
        enable_image=account.enable_image,
        enable_proactive=account.enable_proactive,
        enable_learning=account.enable_learning,
        max_daily_messages=account.max_daily_messages,
        max_daily_cost=account.max_daily_cost,
        today_message_count=account.today_message_count,
        today_cost=account.today_cost,
        total_message_count=account.total_message_count,
        total_cost=account.total_cost,
        created_at=account.created_at.isoformat() if account.created_at else "",
        updated_at=account.updated_at.isoformat() if account.updated_at else "",
    )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    """更新账号配置"""
    manager = AccountManager(db)

    try:
        account = await manager.update_account(
            account_id=account_id,
            name=request.name,
            platform_config=request.platform_config,
            personality_config=request.personality_config,
            max_daily_messages=request.max_daily_messages,
            max_daily_cost=request.max_daily_cost,
            enable_text=request.enable_text,
            enable_emoji=request.enable_emoji,
            enable_voice=request.enable_voice,
            enable_image=request.enable_image,
            enable_proactive=request.enable_proactive,
            enable_learning=request.enable_learning,
        )

        return AccountResponse(
            id=account.id,
            name=account.name,
            platform=account.platform,
            status=account.status,
            enable_text=account.enable_text,
            enable_emoji=account.enable_emoji,
            enable_voice=account.enable_voice,
            enable_image=account.enable_image,
            enable_proactive=account.enable_proactive,
            enable_learning=account.enable_learning,
            max_daily_messages=account.max_daily_messages,
            max_daily_cost=account.max_daily_cost,
            today_message_count=account.today_message_count,
            today_cost=account.today_cost,
            total_message_count=account.total_message_count,
            total_cost=account.total_cost,
            created_at=account.created_at.isoformat() if account.created_at else "",
            updated_at=account.updated_at.isoformat() if account.updated_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """删除账号"""
    manager = AccountManager(db)

    try:
        await manager.delete_account(account_id)
        return MessageResponse(message=f"账号 {account_id} 已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{account_id}/start", response_model=AccountResponse)
async def start_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    """启动账号"""
    manager = AccountManager(db)

    try:
        account = await manager.start_account(account_id)

        return AccountResponse(
            id=account.id,
            name=account.name,
            platform=account.platform,
            status=account.status,
            enable_text=account.enable_text,
            enable_emoji=account.enable_emoji,
            enable_voice=account.enable_voice,
            enable_image=account.enable_image,
            enable_proactive=account.enable_proactive,
            enable_learning=account.enable_learning,
            max_daily_messages=account.max_daily_messages,
            max_daily_cost=account.max_daily_cost,
            today_message_count=account.today_message_count,
            today_cost=account.today_cost,
            total_message_count=account.total_message_count,
            total_cost=account.total_cost,
            created_at=account.created_at.isoformat() if account.created_at else "",
            updated_at=account.updated_at.isoformat() if account.updated_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{account_id}/stop", response_model=AccountResponse)
async def stop_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    """停止账号"""
    manager = AccountManager(db)

    try:
        account = await manager.stop_account(account_id)

        return AccountResponse(
            id=account.id,
            name=account.name,
            platform=account.platform,
            status=account.status,
            enable_text=account.enable_text,
            enable_emoji=account.enable_emoji,
            enable_voice=account.enable_voice,
            enable_image=account.enable_image,
            enable_proactive=account.enable_proactive,
            enable_learning=account.enable_learning,
            max_daily_messages=account.max_daily_messages,
            max_daily_cost=account.max_daily_cost,
            today_message_count=account.today_message_count,
            today_cost=account.today_cost,
            total_message_count=account.total_message_count,
            total_cost=account.total_cost,
            created_at=account.created_at.isoformat() if account.created_at else "",
            updated_at=account.updated_at.isoformat() if account.updated_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{account_id}/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> AccountStatsResponse:
    """获取账号统计"""
    manager = AccountManager(db)

    try:
        stats = await manager.get_account_stats(account_id)
        return AccountStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/limits", response_model=LimitStatusResponse)
async def get_limit_status(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> LimitStatusResponse:
    """获取限制状态"""
    limiter = AccountLimiter(db)

    try:
        status = await limiter.get_limit_status(account_id)
        return LimitStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/alerts", response_model=AlertResponse)
async def get_account_alerts(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """获取账号告警"""
    limiter = AccountLimiter(db)

    try:
        alerts = await limiter.check_alert_thresholds(account_id)
        return AlertResponse(alerts=alerts)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{account_id}/reset-stats", response_model=MessageResponse)
async def reset_daily_stats(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """重置账号每日统计"""
    manager = AccountManager(db)

    try:
        await manager.reset_daily_stats(account_id)
        return MessageResponse(message=f"账号 {account_id} 的每日统计已重置")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reset-all-stats", response_model=MessageResponse)
async def reset_all_daily_stats(
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """重置所有账号的每日统计"""
    manager = AccountManager(db)

    count = await manager.reset_all_daily_stats()
    return MessageResponse(message=f"已重置 {count} 个账号的每日统计")


@router.get("/limits/all", response_model=list[LimitStatusResponse])
async def get_all_limit_status(
    db: AsyncSession = Depends(get_db),
) -> list[LimitStatusResponse]:
    """获取所有账号的限制状态"""
    limiter = AccountLimiter(db)

    statuses = await limiter.get_all_limit_status()
    return [LimitStatusResponse(**status) for status in statuses]
