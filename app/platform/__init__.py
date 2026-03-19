"""双轨接入架构 - 平台接入层"""

from .gateway import MessageGateway, PlatformAdapter, get_gateway
from .service import GatewayService, get_gateway_service
from .types import MessageDirection, MessageType, PlatformType, UnifiedMessage, UnifiedResponse

__all__ = [
    MessageType,
    PlatformType,
    MessageDirection,
    UnifiedMessage,
    UnifiedResponse,
    PlatformAdapter,
    MessageGateway,
    GatewayService,
    get_gateway,
    get_gateway_service,
]
