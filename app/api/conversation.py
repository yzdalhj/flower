"""对话管理 API"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter(prefix="/conversations", tags=["对话管理"])


class ConversationListItem(BaseModel):
    """对话列表项"""

    id: str
    user_id: str
    account_id: str
    user_nickname: Optional[str]
    status: str
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """对话列表响应"""

    total: int
    items: List[ConversationListItem]


class MessageItem(BaseModel):
    """消息项"""

    id: str
    role: str
    content: str
    content_type: str
    emotion_valence: Optional[float]
    emotion_arousal: Optional[float]
    model_used: Optional[str]
    tokens_used: Optional[int]
    created_at: datetime


class ConversationDetail(BaseModel):
    """对话详情"""

    id: str
    user_id: str
    account_id: str
    user_nickname: Optional[str]
    status: str
    message_count: int
    last_message_at: Optional[datetime]
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem]


class ConversationFilter(BaseModel):
    """对话筛选条件"""

    account_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    account_id: Optional[str] = Query(None, description="账号ID筛选"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    获取对话列表

    Args:
        page: 页码
        page_size: 每页数量
        account_id: 账号ID筛选
        user_id: 用户ID筛选
        status: 状态筛选
        db: 数据库会话

    Returns:
        对话列表
    """
    # 构建基础查询
    from app.models.account import Account

    base_query = select(Conversation).options(
        selectinload(Conversation.user).selectinload(User.account)
    )
    _ = Account  # 避免 F401 未使用导入警告

    # 应用筛选条件
    if account_id:
        base_query = base_query.where(Conversation.user.has(User.account_id == account_id))
    if user_id:
        base_query = base_query.where(Conversation.user_id == user_id)
    if status:
        base_query = base_query.where(Conversation.status == status)

    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 获取分页数据
    offset = (page - 1) * page_size
    query = base_query.order_by(desc(Conversation.updated_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    conversations = result.scalars().all()

    # 构建响应
    items = []
    for conv in conversations:
        account_name = conv.user.account.name if conv.user and conv.user.account else None
        items.append(
            ConversationListItem(
                id=conv.id,
                user_id=conv.user_id,
                account_id=conv.user.account_id if conv.user else "",
                user_nickname=account_name,
                status=conv.status,
                message_count=conv.message_count,
                last_message_at=conv.last_message_at,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return ConversationListResponse(total=total, items=items)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """
    获取对话详情

    Args:
        conversation_id: 对话ID
        db: 数据库会话

    Returns:
        对话详情
    """
    # 查询对话及其消息
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.user).selectinload(User.account),
            selectinload(Conversation.messages),
        )
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 构建消息列表
    messages = []
    for msg in sorted(conversation.messages, key=lambda m: m.created_at):
        messages.append(
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                content_type=msg.content_type,
                emotion_valence=msg.emotion_valence,
                emotion_arousal=msg.emotion_arousal,
                model_used=msg.model_used,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at,
            )
        )

    account_name = (
        conversation.user.account.name if conversation.user and conversation.user.account else None
    )
    return ConversationDetail(
        id=conversation.id,
        user_id=conversation.user_id,
        account_id=conversation.user.account_id if conversation.user else "",
        user_nickname=account_name,
        status=conversation.status,
        message_count=conversation.message_count,
        last_message_at=conversation.last_message_at,
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除对话

    Args:
        conversation_id: 对话ID
        db: 数据库会话

    Returns:
        删除结果
    """
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    await db.delete(conversation)
    await db.commit()

    return {"success": True, "message": "对话已删除"}


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取对话消息列表（分页）

    Args:
        conversation_id: 对话ID
        page: 页码
        page_size: 每页数量
        db: 数据库会话

    Returns:
        消息列表
    """
    # 检查对话是否存在
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 获取消息总数
    count_result = await db.execute(
        select(func.count()).where(Message.conversation_id == conversation_id)
    )
    total = count_result.scalar() or 0

    # 获取分页消息
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .offset(offset)
        .limit(page_size)
    )
    messages = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "content_type": msg.content_type,
                "emotion_valence": msg.emotion_valence,
                "emotion_arousal": msg.emotion_arousal,
                "model_used": msg.model_used,
                "tokens_used": msg.tokens_used,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(messages)  # 按时间正序返回
        ],
    }
