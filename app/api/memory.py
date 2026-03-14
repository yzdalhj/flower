"""记忆管理 API"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models.memory import Memory
from app.services.memory.memory_store import MemoryStore


def parse_meta_data(meta_data: Optional[str]) -> Optional[Dict[str, Any]]:
    """解析元数据 JSON 字符串"""
    if not meta_data:
        return None
    try:
        return json.loads(meta_data)
    except json.JSONDecodeError:
        return None


router = APIRouter(prefix="/memories", tags=["记忆管理"])


# ========== 请求/响应模型 ==========


class MemoryCreateRequest(BaseModel):
    """创建记忆请求"""

    user_id: str = Field(..., description="用户ID")
    memory_type: str = Field(..., description="记忆类型: episodic/semantic/emotional/preference")
    content: str = Field(..., description="记忆内容")
    summary: Optional[str] = Field(None, description="摘要")
    importance: float = Field(1.0, description="重要性 1-10", ge=1.0, le=10.0)
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""

    content: Optional[str] = Field(None, description="记忆内容")
    summary: Optional[str] = Field(None, description="摘要")
    importance: Optional[float] = Field(None, description="重要性 1-10", ge=1.0, le=10.0)
    memory_type: Optional[str] = Field(None, description="记忆类型")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MemoryResponse(BaseModel):
    """记忆响应"""

    id: str
    user_id: str
    memory_type: str
    content: str
    summary: Optional[str]
    importance: float
    access_count: int
    created_at: str
    updated_at: str
    meta_data: Optional[Dict[str, Any]]


class MemoryListResponse(BaseModel):
    """记忆列表响应"""

    total: int
    items: List[MemoryResponse]


# ========== API 接口 ==========


@router.get("", response_model=MemoryListResponse)
async def get_memories(
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    memory_type: Optional[str] = Query(None, description="记忆类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
) -> MemoryListResponse:
    """
    获取记忆列表
    """
    # 构建查询
    query = select(Memory)

    if user_id:
        query = query.where(Memory.user_id == user_id)

    if memory_type:
        query = query.where(Memory.memory_type == memory_type)

    if keyword:
        query = query.where(Memory.content.contains(keyword) | Memory.summary.contains(keyword))

    # 获取总数
    count_result = await db.execute(
        select(Memory.id).where(Memory.user_id == user_id) if user_id else select(Memory.id)
    )
    total = len(count_result.scalars().all())

    # 获取分页数据
    query = query.order_by(Memory.importance.desc(), Memory.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    memories = result.scalars().all()

    items = [
        MemoryResponse(
            id=m.id,
            user_id=m.user_id,
            memory_type=m.memory_type,
            content=m.content,
            summary=m.summary,
            importance=m.importance,
            access_count=m.access_count,
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else "",
            meta_data=parse_meta_data(m.meta_data),
        )
        for m in memories
    ]

    return MemoryListResponse(total=total, items=items)


@router.post("", response_model=MemoryResponse)
async def create_memory(
    request: MemoryCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    """
    创建记忆
    """
    store = MemoryStore(db)

    memory = await store.create_memory(
        user_id=request.user_id,
        memory_type=request.memory_type,
        content=request.content,
        summary=request.summary,
        importance=request.importance,
        metadata=request.meta_data,
    )

    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        memory_type=memory.memory_type,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        access_count=memory.access_count,
        created_at=memory.created_at.isoformat() if memory.created_at else "",
        updated_at=memory.updated_at.isoformat() if memory.updated_at else "",
        meta_data=parse_meta_data(memory.meta_data),
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    """
    获取单个记忆
    """
    store = MemoryStore(db)
    memory = await store.get_memory(memory_id)

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    # 更新访问统计
    await store.update_memory_access(memory_id)

    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        memory_type=memory.memory_type,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        access_count=memory.access_count,
        created_at=memory.created_at.isoformat() if memory.created_at else "",
        updated_at=memory.updated_at.isoformat() if memory.updated_at else "",
        meta_data=parse_meta_data(memory.meta_data),
    )


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    """
    更新记忆
    """
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    # 更新字段
    update_data = request.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(memory, field, value)

    await db.commit()
    await db.refresh(memory)

    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        memory_type=memory.memory_type,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        access_count=memory.access_count,
        created_at=memory.created_at.isoformat() if memory.created_at else "",
        updated_at=memory.updated_at.isoformat() if memory.updated_at else "",
        meta_data=parse_meta_data(memory.meta_data),
    )


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除记忆
    """
    store = MemoryStore(db)
    success = await store.delete_memory(memory_id)

    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")

    return {"success": True, "message": "记忆已删除"}


@router.get("/{user_id}/important")
async def get_important_memories(
    user_id: str,
    min_importance: float = Query(7.0, ge=1.0, le=10.0, description="最小重要性"),
    limit: int = Query(10, ge=1, le=50, description="数量限制"),
    db: AsyncSession = Depends(get_db),
) -> List[MemoryResponse]:
    """
    获取用户的重要记忆
    """
    store = MemoryStore(db)
    memories = await store.get_important_memories(user_id, min_importance, limit)

    return [
        MemoryResponse(
            id=m.id,
            user_id=m.user_id,
            memory_type=m.memory_type,
            content=m.content,
            summary=m.summary,
            importance=m.importance,
            access_count=m.access_count,
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else "",
            meta_data=m.meta_data,
        )
        for m in memories
    ]


@router.get("/stats/overview")
async def get_memory_stats(
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取记忆统计概览
    """
    from sqlalchemy import func

    query = select(Memory)
    if user_id:
        query = query.where(Memory.user_id == user_id)

    # 总数量
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # 按类型统计
    type_query = select(Memory.memory_type, func.count()).group_by(Memory.memory_type)
    if user_id:
        type_query = type_query.where(Memory.user_id == user_id)
    type_result = await db.execute(type_query)
    by_type = {row[0]: row[1] for row in type_result.all()}

    # 平均重要性
    importance_query = select(func.avg(Memory.importance))
    if user_id:
        importance_query = importance_query.where(Memory.user_id == user_id)
    importance_result = await db.execute(importance_query)
    avg_importance = importance_result.scalar() or 0

    return {
        "total": total,
        "by_type": by_type,
        "avg_importance": round(avg_importance, 2),
    }
