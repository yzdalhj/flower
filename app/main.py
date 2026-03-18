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
)
from app.config import get_settings
from app.core import init_db, init_default_admin
from app.core.init_prompt_template import init_default_prompt_template, init_prompt_variables
from app.core.session import AsyncSessionLocal
from app.services.active_behavior import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # 启动时
    print("╔" + "═" * 50)
    print(f"║  🌸 {settings.APP_NAME} v{app.version}")
    print("╠" + "═" * 50)

    # 初始化数据库
    print("║  📦 正在初始化数据库...", end=" ")
    await init_db()
    print("✓")

    # 初始化默认管理员账号
    print("║  👤 正在初始化管理员账号...", end=" ")
    async with AsyncSessionLocal() as db:
        await init_default_admin(db)
    print("✓")

    # 初始化默认Prompt模板
    print("║  📝 正在初始化Prompt模板...", end=" ")
    async with AsyncSessionLocal() as db:
        await init_prompt_variables(db)
        await init_default_prompt_template(db)
    print("✓")

    # 初始化向量数据库
    # TODO: 初始化ChromaDB

    # 启动主动行为调度器
    print("║  ⏰ 正在启动主动行为调度器...", end=" ")
    await scheduler.start()
    print("✓")

    # 启动记忆调度器
    print("║  🧠 正在启动记忆调度器...", end=" ")
    from app.services.memory.memory_scheduler import get_memory_scheduler

    memory_scheduler = get_memory_scheduler()
    await memory_scheduler.start()
    print("✓")

    print("╚" + "═" * 50)
    print("✨ 服务已启动，访问 http://localhost:8000/docs 查看文档")
    print()

    yield

    # 关闭时
    print()
    print("╔" + "═" * 50)
    print(f"║  🛑 {settings.APP_NAME} 正在关闭...")
    print("╠" + "═" * 50)

    print("║  ⏰ 正在停止主动行为调度器...", end=" ")
    await scheduler.stop()
    print("✓")

    print("║  🧠 正在停止记忆调度器...", end=" ")
    await memory_scheduler.stop()
    print("✓")

    print("╚" + "═" * 50)
    print(f"👋 感谢使用 {settings.APP_NAME}！")


app = FastAPI(
    title="AI小花 API",
    description="智能陪伴助手 API",
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
