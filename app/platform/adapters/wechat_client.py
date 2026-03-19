"""微信客户端主控适配器 - 非官方方案

微信客户端主控通过本地HTTP接口接收消息
支持完整能力：主动消息、语音通话等
"""

import logging
from typing import Any, Dict, Optional

import aiohttp

from app.config import get_settings
from app.platform.gateway import PlatformAdapter
from app.platform.types import MessageType, PlatformType, UnifiedMessage, UnifiedResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class WechatClientAdapter(PlatformAdapter):
    """微信客户端主控适配器

    通过HTTP接口与本地微信客户端通信
    支持完整能力，包括主动消息发送
    """

    platform_type: PlatformType = PlatformType.WECHAT_CLIENT

    def __init__(
        self,
        host: str = None,
        port: int = None,
    ):
        self.host = host or settings.WECHAT_CLIENT_HOST
        self.port = port or settings.WECHAT_CLIENT_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def verify_webhook(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """微信客户端不需要Webhook验证"""
        return None

    async def parse_message(self, raw_data: Dict[str, Any]) -> Optional[UnifiedMessage]:
        """解析微信客户端推送的消息"""
        try:
            msg_id = raw_data.get("msg_id", str(hash(str(raw_data)))[:16])
            msg_type = raw_data.get("msg_type", "text")
            from_user = raw_data.get("from_user", "")
            from_nickname = raw_data.get("from_nickname")
            content = raw_data.get("content", "")
            chat_id = raw_data.get("chat_id", from_user)
            chat_type = raw_data.get("chat_type", "single")
            media_url = raw_data.get("media_url")
            media_id = raw_data.get("media_id")

            unified_type = self._convert_msg_type(msg_type)

            message = UnifiedMessage.create_inbound(
                message_id=msg_id,
                platform=PlatformType.WECHAT_CLIENT,
                chat_id=chat_id,
                chat_type=chat_type,
                user_id=from_user,
                nickname=from_nickname,
                content_type=unified_type,
                text=content if unified_type == MessageType.TEXT else None,
                media_url=media_url,
                media_id=media_id,
                raw_data=raw_data,
            )

            return message

        except Exception as e:
            logger.error(f"Failed to parse WeChat Client message: {e}", exc_info=True)
            return None

    async def send_response(self, message: UnifiedMessage, response: UnifiedResponse) -> bool:
        """发送响应到微信客户端"""
        try:
            target = message.chat_id
            payload = self._build_send_payload(target, response)

            url = f"{self.base_url}/send"

            async with self.session.post(url, json=payload) as resp:
                result = await resp.json()
                success = result.get("success", False)
                if not success:
                    logger.error(f"WeChat Client send failed: {result}")
                return success

        except Exception as e:
            logger.error(f"Failed to send to WeChat Client: {e}", exc_info=True)
            return False

    async def send_message(
        self,
        chat_id: str,
        response: UnifiedResponse,
    ) -> bool:
        """主动发送消息（微信客户端完整能力支持）"""
        try:
            payload = self._build_send_payload(chat_id, response)
            url = f"{self.base_url}/send"

            async with self.session.post(url, json=payload) as resp:
                result = await resp.json()
                return result.get("success", False)

        except Exception as e:
            logger.error(f"Failed to send proactive message to WeChat Client: {e}", exc_info=True)
            return False

    def _convert_msg_type(self, wechat_type: str) -> MessageType:
        """转换微信消息类型"""
        mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "voice": MessageType.VOICE,
            "video": MessageType.VIDEO,
            "voice_call": MessageType.VOICE_CALL,
            "video_call": MessageType.VIDEO_CALL,
            "sticker": MessageType.STICKER,
            "location": MessageType.LOCATION,
            "link": MessageType.LINK,
        }
        return mapping.get(wechat_type, MessageType.TEXT)

    def _build_send_payload(self, chat_id: str, response: UnifiedResponse) -> Dict[str, Any]:
        """构建发送payload"""
        return {
            "chat_id": chat_id,
            "msg_type": response.content.type,
            "content": response.content.text,
            "media_url": response.content.media_url,
            "media_id": response.content.media_id,
            "extra": response.extra,
        }

    async def close(self) -> None:
        """关闭HTTP会话"""
        if self._session:
            await self._session.close()
            self._session = None
