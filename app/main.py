"""FastAPI入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    account_router,
    active_behavior_router,
    auth_router,
    chat_router,
    conversation_router,
    llm_usage_router,
    memory_router,
    personality_config_router,
    prompt_template_router,
    settings_router,
    sticker_router,
    user_router,
    wechat_router,
)
from app.config import get_settings
from app.core import init_db, init_default_admin
from app.core.banner import (
    print_banner,
    print_info,
    print_platforms,
    print_ready,
    print_schedulers_started,
    print_shutdown,
    print_success,
)
from app.core.init_prompt_template import init_default_prompt_template, init_prompt_variables
from app.core.session import AsyncSessionLocal
from app.platform.adapters.wechat_client import WechatClientAdapter
from app.platform.adapters.wechat_official import WechatOfficialAdapter
from app.platform.gateway import get_gateway
from app.services.active_behavior import scheduler
from app.services.sticker import init_default_stickers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    print_banner(settings.APP_NAME, "0.1.0")

    await init_db()
    print_success("Database initialized")

    init_steps = []
    async with AsyncSessionLocal() as db:
        if settings.INIT_ADMIN:
            await init_default_admin(db)
            init_steps.append("admin")
        if settings.INIT_PROMPT_TEMPLATES:
            await init_prompt_variables(db)
            await init_default_prompt_template(db)
            init_steps.append("prompt templates")
        if settings.INIT_STICKERS:
            await init_default_stickers(db)
            init_steps.append("stickers")

    if init_steps:
        print_success(f"Core data initialized: {', '.join(init_steps)}")
    else:
        print_info("Core data init skipped")

    await scheduler.start()
    from app.services.memory.memory_scheduler import get_memory_scheduler

    memory_scheduler = get_memory_scheduler()
    await memory_scheduler.start()
    print_schedulers_started(["Active Behavior", "Memory"])

    gateway = get_gateway()

    platforms = []
    if settings.WECHAT_OFFICIAL_TOKEN:
        adapter = WechatOfficialAdapter(
            token=settings.WECHAT_OFFICIAL_TOKEN,
            app_id=settings.WECHAT_OFFICIAL_APP_ID,
            app_secret=settings.WECHAT_OFFICIAL_APP_SECRET,
        )
        gateway.register_adapter(adapter)
        platforms.append("WeChat Official")

    if settings.WECHAT_CLIENT_ENABLED:
        client_adapter = WechatClientAdapter(
            host=settings.WECHAT_CLIENT_HOST,
            port=settings.WECHAT_CLIENT_PORT,
        )
        gateway.register_adapter(client_adapter)
        platforms.append(
            f"WeChat Client ({settings.WECHAT_CLIENT_HOST}:{settings.WECHAT_CLIENT_PORT})"
        )

    print_platforms(platforms)

    extra_info = {}
    if platforms:
        extra_info["平台"] = ", ".join(platforms)

    print_ready(port=8000, docs_url="/docs", extra_info=extra_info)

    yield

    # 关闭时
    print_shutdown(settings.APP_NAME)
    await scheduler.stop()
    await memory_scheduler.stop()


app = FastAPI(
    title="AI小花 API",
    description="智能助手 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI小花",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(active_behavior_router)
app.include_router(sticker_router)
app.include_router(account_router)
app.include_router(prompt_template_router)
app.include_router(conversation_router)
app.include_router(settings_router)
app.include_router(memory_router)
app.include_router(user_router)
app.include_router(llm_usage_router)
app.include_router(personality_config_router)
app.include_router(wechat_router)
