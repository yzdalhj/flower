"""消息网关服务 - 整合消息网关和核心对话处理"""

import logging
from typing import Optional

from app.models.account import Account
from app.platform.gateway import MessageGateway, get_gateway
from app.platform.types import UnifiedMessage, UnifiedResponse
from app.services.account.account_manager import AccountManager
from app.services.llm.dialogue import DialogueProcessor

logger = logging.getLogger(__name__)


class GatewayService:
    """消息网关服务 - 整合消息网关和核心对话处理"""

    def __init__(self):
        self._gateway = get_gateway()
        self._gateway.register_handler(self._handle_message)

    async def _handle_message(self, message: UnifiedMessage) -> Optional[UnifiedResponse]:
        """处理消息核心逻辑"""
        logger.info(f"Processing message from {message.platform}: {message.message_id}")

        account_id = message.chat.extra.get("account_id")
        if not account_id:
            logger.warning("No account_id in message, skipping processing")
            return None

        from app.core.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            account_manager = AccountManager(session)
            account = await self._get_account(account_manager, account_id)
            if not account:
                logger.warning(f"Account not found: {account_id}")
                return None

            if not account.is_running():
                logger.warning(f"Account not running: {account_id}")
                return None

            if not account.can_send_message():
                logger.warning(f"Account limit reached: {account_id}")
                return None

            capabilities = self._gateway.get_capabilities(account)
            if message.content.type == "text" and not capabilities["text"]:
                logger.warning(f"Text disabled for account: {account_id}")
                return None

            if message.content.type == "image" and not capabilities["image"]:
                logger.warning(f"Image disabled for account: {account_id}")
                return None

            try:
                text = message.text or ""
                processor = DialogueProcessor(session)
                response = await processor.process(
                    user_id=message.user_id,
                    account_id=account_id,
                    message=text,
                )

                account.update_stats(
                    message_count=1,
                    cost=0.0,
                )
                await session.commit()

                return UnifiedResponse.text_response(response.content)

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                return None

    async def _get_account(
        self, account_manager: AccountManager, account_id: str
    ) -> Optional[Account]:
        """获取账号"""
        return await account_manager.get_account(account_id)

    @property
    def gateway(self) -> MessageGateway:
        """获取消息网关实例"""
        return self._gateway


gateway_service = GatewayService()


def get_gateway_service() -> GatewayService:
    """获取网关服务单例"""
    return gateway_service
