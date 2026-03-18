"""LLM 使用统计 API"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_admin_user
from app.core.session import get_db
from app.models.admin_user import AdminUser
from app.services.llm.llm_usage_service import LLMUsageService

router = APIRouter(prefix="/llm-usage", tags=["LLM Usage"])


@router.get("/statistics/daily")
async def get_daily_statistics(
    days: int = Query(30, ge=1, le=365),
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取每日使用统计"""
    service = LLMUsageService(db)
    stats = await service.get_daily_statistics(days=days, provider=provider)
    return {
        "success": True,
        "data": stats,
    }


@router.get("/statistics/providers")
async def get_provider_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """按厂商统计使用情况"""
    service = LLMUsageService(db)

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    stats = await service.get_provider_statistics(start_date=start_date, end_date=end_date)
    return {
        "success": True,
        "data": stats,
    }


@router.get("/statistics/operations")
async def get_operation_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """按操作类型统计使用情况"""
    service = LLMUsageService(db)

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    stats = await service.get_operation_statistics(start_date=start_date, end_date=end_date)
    return {
        "success": True,
        "data": stats,
    }


@router.get("/statistics/user")
async def get_user_usage_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取当前用户的使用统计"""
    service = LLMUsageService(db)

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    stats = await service.get_user_usage(
        user_id=current_admin.id,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "success": True,
        "data": stats,
    }


@router.get("/records")
async def get_usage_records(
    limit: int = Query(100, ge=1, le=1000),
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取使用记录列表"""
    service = LLMUsageService(db)
    records = await service.get_recent_records(
        limit=limit,
        user_id=current_admin.id,
        provider=provider,
    )
    return {
        "success": True,
        "data": records,
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation_usage(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取特定对话的 Token 消耗"""
    service = LLMUsageService(db)
    stats = await service.get_conversation_usage(conversation_id)
    return {
        "success": True,
        "data": stats,
    }


@router.get("/dashboard")
async def get_usage_dashboard(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取使用仪表盘数据（汇总）"""
    from sqlalchemy import func, select

    from app.models.llm_usage import LLMUsageRecord

    service = LLMUsageService(db)
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    # 用户统计
    user_stats = await service.get_user_usage(
        user_id=current_admin.id,
        start_date=start_date,
        end_date=end_date,
    )

    # 每日统计（从原始记录表按日期分组聚合，确保总有数据）
    result = await db.execute(
        select(
            func.date(LLMUsageRecord.created_at).label("stat_date"),
            func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
            func.sum(LLMUsageRecord.estimated_cost).label("total_cost"),
        )
        .where(LLMUsageRecord.created_at >= start_date)
        .group_by(func.date(LLMUsageRecord.created_at))
        .order_by(func.date(LLMUsageRecord.created_at))
    )

    daily_stats = [
        {
            "stat_date": str(row.stat_date),
            "total_tokens": row.total_tokens or 0,
            "total_cost": float(row.total_cost) if row.total_cost is not None else 0,
        }
        for row in result.all()
    ]

    # 厂商统计
    provider_stats = await service.get_provider_statistics(
        start_date=start_date,
        end_date=end_date,
    )

    # 操作统计
    operation_stats = await service.get_operation_statistics(
        start_date=start_date,
        end_date=end_date,
    )

    # 最近记录（管理员查看所有用户的最近记录）
    recent_records = await service.get_recent_records(
        limit=10,
    )

    return {
        "success": True,
        "data": {
            "period_days": days,
            "user_summary": user_stats,
            "daily": daily_stats,
            "provider_breakdown": provider_stats,
            "operation_breakdown": operation_stats,
            "recent_records": recent_records,
        },
    }
