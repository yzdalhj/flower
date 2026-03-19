"""数据库会话管理 - 独立模块避免循环导入"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

# 创建异步引擎
echo_sql = settings.LOG_LEVEL in ["DEBUG", "INFO"]
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=echo_sql,
    future=True,
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
