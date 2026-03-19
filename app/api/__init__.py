"""API路由模块"""

from app.api.account import router as account_router
from app.api.active_behavior import router as active_behavior_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.llm_usage import router as llm_usage_router
from app.api.memory import router as memory_router
from app.api.personality_config import router as personality_config_router
from app.api.prompt_template import router as prompt_template_router
from app.api.settings import router as settings_router
from app.api.sticker import router as sticker_router
from app.api.user import router as user_router
from app.api.wechat import router as wechat_router

__all__ = [
    "chat_router",
    "active_behavior_router",
    "sticker_router",
    "account_router",
    "prompt_template_router",
    "conversation_router",
    "settings_router",
    "memory_router",
    "user_router",
    "llm_usage_router",
    "auth_router",
    "personality_config_router",
    "wechat_router",
]
