"""统一消息类型定义"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    VOICE_CALL = "voice_call"
    VIDEO_CALL = "video_call"
    STICKER = "sticker"
    LOCATION = "location"
    LINK = "link"
    EVENT = "event"


class PlatformType(str, Enum):
    """平台类型枚举"""

    WECHAT_OFFICIAL = "wechat_official"
    WECHAT_WORK = "wechat_work"
    QQ_GUILD = "qq_guild"
    WECHAT_CLIENT = "wechat_client"


class MessageDirection(str, Enum):
    """消息方向"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SenderInfo(BaseModel):
    """发送者信息"""

    user_id: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChatInfo(BaseModel):
    """聊天信息"""

    chat_id: str
    chat_type: str
    sender: SenderInfo
    extra: Dict[str, Any] = Field(default_factory=dict)


class MessageContent(BaseModel):
    """消息内容"""

    type: MessageType
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class UnifiedMessage(BaseModel):
    """统一消息格式 - 平台无关的消息结构"""

    message_id: str = Field(description="消息唯一ID")
    platform: PlatformType = Field(description="来源平台")
    direction: MessageDirection = Field(description="消息方向")
    chat: ChatInfo = Field(description="聊天信息")
    content: MessageContent = Field(description="消息内容")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="原始数据")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    @property
    def text(self) -> Optional[str]:
        """获取文本内容"""
        return self.content.text

    @property
    def message_type(self) -> MessageType:
        """获取消息类型"""
        return self.content.type

    @property
    def user_id(self) -> str:
        """获取用户ID"""
        return self.chat.sender.user_id

    @property
    def chat_id(self) -> str:
        """获取聊天ID"""
        return self.chat.chat_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def create_inbound(
        cls,
        message_id: str,
        platform: PlatformType,
        chat_id: str,
        chat_type: str,
        user_id: str,
        nickname: Optional[str] = None,
        content_type: MessageType = MessageType.TEXT,
        text: Optional[str] = None,
        media_url: Optional[str] = None,
        media_id: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> "UnifiedMessage":
        """创建入站消息快捷方法"""
        return cls(
            message_id=message_id,
            platform=platform,
            direction=MessageDirection.INBOUND,
            chat=ChatInfo(
                chat_id=chat_id,
                chat_type=chat_type,
                sender=SenderInfo(user_id=user_id, nickname=nickname),
            ),
            content=MessageContent(
                type=content_type,
                text=text,
                media_url=media_url,
                media_id=media_id,
            ),
            raw_data=raw_data or {},
        )


class UnifiedResponse(BaseModel):
    """统一响应格式"""

    message_id: str = Field(description="响应消息ID")
    content: MessageContent = Field(description="响应内容")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展信息")

    @classmethod
    def text_response(cls, text: str) -> "UnifiedResponse":
        """创建文本响应"""
        import uuid

        return cls(
            message_id=str(uuid.uuid4()),
            content=MessageContent(type=MessageType.TEXT, text=text),
        )

    @classmethod
    def image_response(cls, media_url: str, media_id: Optional[str] = None) -> "UnifiedResponse":
        """创建图片响应"""
        import uuid

        return cls(
            message_id=str(uuid.uuid4()),
            content=MessageContent(
                type=MessageType.IMAGE,
                media_url=media_url,
                media_id=media_id,
            ),
        )
