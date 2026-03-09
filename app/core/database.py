"""数据库配置"""

# 导入所有模型以确保元数据包含它们
import app.models  # noqa: F401
import app.services.active_behavior.models  # noqa: F401
from app.core.session import engine
from app.models.base import Base  # 使用模型中定义的Base


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
