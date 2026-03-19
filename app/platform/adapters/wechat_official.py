"""微信公众号适配器"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional
from urllib.parse import unquote

from app.platform.gateway import PlatformAdapter
from app.platform.types import MessageType, PlatformType, UnifiedMessage, UnifiedResponse

logger = logging.getLogger(__name__)


class WechatOfficialAdapter(PlatformAdapter):
    """微信公众号适配器"""

    platform_type: PlatformType = PlatformType.WECHAT_OFFICIAL

    def __init__(self, token: str, app_id: str = "", app_secret: str = ""):
        self.token = token
        self.app_id = app_id
        self.app_secret = app_secret

    def verify_webhook(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """验证微信服务器配置"""
        signature = raw_data.get("signature", "")
        timestamp = raw_data.get("timestamp", "")
        nonce = raw_data.get("nonce", "")
        echostr = raw_data.get("echostr", "")

        if not all([signature, timestamp, nonce, echostr]):
            return None

        sorted_params = sorted([self.token, timestamp, nonce])
        concatenated = "".join(sorted_params)
        hash_str = hashlib.sha1(concatenated.encode()).hexdigest()

        if hash_str == signature:
            return echostr

        return None

    async def parse_message(self, raw_data: Dict[str, Any]) -> Optional[UnifiedMessage]:
        """解析微信公众号消息"""
        xml_data = raw_data.get("xml")
        if not xml_data:
            logger.warning("No XML data in request")
            return None

        try:
            root = ET.fromstring(xml_data)

            msg_id = root.findtext("MsgId", "")
            from_user = root.findtext("FromUserName", "")
            root.findtext("ToUserName", "")
            msg_type = root.findtext("MsgType", "")
            content = root.findtext("Content", "")
            content = unquote(content) if content else ""

            media_id = root.findtext("MediaId", "")
            pic_url = root.findtext("PicUrl", "")

            unified_msg_type = self._convert_msg_type(msg_type)

            message = UnifiedMessage.create_inbound(
                message_id=msg_id,
                platform=PlatformType.WECHAT_OFFICIAL,
                chat_id=from_user,
                chat_type="single",
                user_id=from_user,
                nickname=None,
                content_type=unified_msg_type,
                text=content if unified_msg_type == MessageType.TEXT else None,
                media_url=pic_url if unified_msg_type == MessageType.IMAGE else None,
                media_id=media_id if media_id else None,
                raw_data=self._xml_to_dict(root),
            )

            return message

        except Exception as e:
            logger.error(f"Failed to parse WeChat message: {e}", exc_info=True)
            return None

    async def send_response(self, message: UnifiedMessage, response: UnifiedResponse) -> bool:
        """发送响应到微信公众号

        微信公众号要求同步返回XML格式响应
        """
        try:
            self._response_to_xml(message, response)
            return True
        except Exception as e:
            logger.error(f"Failed to format WeChat response: {e}", exc_info=True)
            return False

    def _convert_msg_type(self, wechat_type: str) -> MessageType:
        """转换微信消息类型到统一类型"""
        mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "voice": MessageType.VOICE,
            "video": MessageType.VIDEO,
            "shortvideo": MessageType.VIDEO,
            "location": MessageType.LOCATION,
            "link": MessageType.LINK,
            "event": MessageType.EVENT,
        }
        return mapping.get(wechat_type, MessageType.TEXT)

    def _xml_to_dict(self, root: ET.Element) -> Dict[str, Any]:
        """将XML转换为字典"""
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result

    def _response_to_xml(self, incoming: UnifiedMessage, response: UnifiedResponse) -> str:
        """将统一响应转换为微信XML格式"""
        from_user = incoming.user_id
        to_user = incoming.chat.extra.get("ToUserName", "unknown")

        content = response.content.text or ""

        xml_template = f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(incoming.created_at.timestamp())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""

        return xml_template.strip()
