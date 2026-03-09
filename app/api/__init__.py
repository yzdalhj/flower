"""API路由模块"""

from app.api.active_behavior import router as active_behavior_router
from app.api.chat import router as chat_router
from app.api.sticker import router as sticker_router

__all__ = ["chat_router", "active_behavior_router", "sticker_router"]
