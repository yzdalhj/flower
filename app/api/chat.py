"""对话API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.services.llm.dialogue import DialogueProcessor

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    """对话请求"""

    user_id: str
    account_id: str
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """对话响应"""

    content: str
    model_used: str
    tokens_used: int
    conversation_id: Optional[str] = None
    sticker_url: Optional[str] = None  # 表情包图片URL
    sticker_name: Optional[str] = None  # 表情包名称


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    发送消息

    Args:
        request: 对话请求
        db: 数据库会话

    Returns:
        对话响应
    """
    processor = DialogueProcessor(db)

    try:
        response = await processor.process(
            user_id=request.user_id,
            account_id=request.account_id,
            message=request.message,
            conversation_id=request.conversation_id,
        )

        # 提取表情包信息
        sticker_url = None
        sticker_name = None
        if response.sticker:
            sticker_url = response.sticker.get("url")
            sticker_name = response.sticker.get("name")
            print(f"[ChatAPI] 返回表情包 - name: {sticker_name}, url: {sticker_url}")
        else:
            print("[ChatAPI] 无表情包返回")

        return ChatResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            conversation_id=response.conversation_id,
            sticker_url=sticker_url,
            sticker_name=sticker_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}")
async def get_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取对话历史"""
    from sqlalchemy import select

    from app.models.conversation import Message

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "sticker_id": msg.sticker_id,
            }
            for msg in messages
        ],
    }


@router.get("/conversations/{account_id}")
async def get_conversations(
    account_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取账号的对话列表"""
    from sqlalchemy import select

    from app.models.conversation import Conversation
    from app.models.user import User

    # 通过 user 表关联查询
    result = await db.execute(
        select(Conversation)
        .join(User, Conversation.user_id == User.id)
        .where(User.account_id == account_id)
        .order_by(Conversation.last_message_at.desc().nullslast())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return {
        "conversations": [
            {
                "id": conv.id,
                "user_id": conv.user_id,
                "account_id": account_id,
                "title": conv.title or f"对话 {conv.id[:8]}",
                "last_message_preview": conv.last_message_preview,
                "message_count": conv.message_count,
                "started_at": conv.started_at.isoformat(),
                "last_message_at": (
                    conv.last_message_at.isoformat() if conv.last_message_at else None
                ),
            }
            for conv in conversations
        ],
    }
