"""消息网关 - 统一消息路由和分发"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from app.models.account import Account

from .types import PlatformType, UnifiedMessage, UnifiedResponse

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """平台适配器抽象基类"""

    platform_type: PlatformType

    @abstractmethod
    async def parse_message(self, raw_data: Dict[str, Any]) -> Optional[UnifiedMessage]:
        """解析原始消息为统一格式

        Args:
            raw_data: 原始请求数据

        Returns:
            解析后的统一消息，如果无法解析返回 None
        """
        pass

    @abstractmethod
    async def send_response(self, message: UnifiedMessage, response: UnifiedResponse) -> bool:
        """发送响应消息到平台

        Args:
            message: 原始入站消息
            response: 要发送的响应

        Returns:
            发送是否成功
        """
        pass

    @abstractmethod
    async def verify_webhook(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """验证Webhook请求（仅用于首次验证）

        Args:
            raw_data: 原始请求数据

        Returns:
            验证响应内容，如果不需要验证返回 None
        """
        pass


class MessageGateway:
    """消息网关 - 统一消息路由和分发"""

    def __init__(self):
        self._adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._message_handlers: List[Callable[[UnifiedMessage], Optional[UnifiedResponse]]] = []

    def register_adapter(self, adapter: PlatformAdapter) -> None:
        """注册平台适配器"""
        self._adapters[adapter.platform_type] = adapter
        logger.info(f"Registered adapter for platform: {adapter.platform_type}")

    def get_adapter(self, platform_type: PlatformType) -> Optional[PlatformAdapter]:
        """获取平台适配器"""
        return self._adapters.get(platform_type)

    def register_handler(
        self, handler: Callable[[UnifiedMessage], Optional[UnifiedResponse]]
    ) -> None:
        """注册消息处理器"""
        self._message_handlers.append(handler)

    async def process_message(
        self, platform_type: PlatformType, raw_data: Dict[str, Any]
    ) -> Optional[UnifiedResponse]:
        """处理入站消息

        Args:
            platform_type: 平台类型
            raw_data: 原始数据

        Returns:
            处理后的响应，如果不需要立即响应返回 None
        """
        adapter = self.get_adapter(platform_type)
        if not adapter:
            logger.warning(f"No adapter registered for platform: {platform_type}")
            return None

        message = await adapter.parse_message(raw_data)
        if not message:
            logger.warning(f"Failed to parse message from platform: {platform_type}")
            return None

        logger.info(
            f"Processed message: id={message.message_id}, platform={message.platform}, "
            f"type={message.content.type}, user={message.user_id}"
        )

        for handler in self._message_handlers:
            try:
                response = (
                    await handler(message)
                    if asyncio.iscoroutinefunction(handler)
                    else handler(message)
                )
                if response:
                    return response
            except Exception as e:
                logger.error(f"Error in message handler: {e}", exc_info=True)
                continue

        return None

    async def process_webhook_verify(
        self, platform_type: PlatformType, raw_data: Dict[str, Any]
    ) -> Optional[str]:
        """处理Webhook验证"""
        adapter = self.get_adapter(platform_type)
        if not adapter:
            return None
        return await adapter.verify_webhook(raw_data)

    def get_capabilities(self, account: Account) -> Dict[str, bool]:
        """获取账号能力（根据平台类型进行能力分级）

        官方方案能力受限，非官方方案完整能力
        """
        capabilities = {
            "text": account.enable_text,
            "emoji": account.enable_emoji,
            "voice": account.enable_voice,
            "voice_call": account.enable_voice_call,
            "video_call": account.enable_video_call,
            "image": account.enable_image,
            "proactive": account.enable_proactive,
            "learning": account.enable_learning,
        }

        platform = account.platform

        if platform in ["wechat_official", "wechat_work", "qq_guild"]:
            capabilities["proactive"] = False
            capabilities["learning"] = capabilities["learning"] and False
            capabilities["voice_call"] = False
            capabilities["video_call"] = False

        return capabilities


gateway_instance = MessageGateway()


def get_gateway() -> MessageGateway:
    """获取消息网关单例"""
    return gateway_instance
