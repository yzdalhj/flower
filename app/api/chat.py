"""对话API"""

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

        return ChatResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
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
            }
            for msg in messages
        ],
    }
