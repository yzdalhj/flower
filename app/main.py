"""FastAPI入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import active_behavior_router, chat_router, sticker_router
from app.config import get_settings
from app.core import init_db
from app.services.active_behavior import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    settings = get_settings()
    print(f"🌸 {settings.APP_NAME} 启动中...")

    # 初始化数据库
    await init_db()
    print("✅ 数据库初始化完成")

    # 初始化向量数据库
    # TODO: 初始化ChromaDB

    # 启动主动行为调度器
    await scheduler.start()
    print("✅ 主动行为系统已启动")

    yield

    # 关闭时
    # 停止主动行为调度器
    await scheduler.stop()
    print("✅ 主动行为系统已停止")

    print(f"🌸 {settings.APP_NAME} 已关闭")


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
app.include_router(chat_router)
app.include_router(active_behavior_router)
app.include_router(sticker_router)
