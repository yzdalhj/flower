"""数据库配置"""

import os
import sys

import app.models  # noqa: F401
import app.services.active_behavior.models  # noqa: F401
from app.core.session import engine
from app.models.base import Base  # 使用模型中定义的Base


async def init_db():
    """初始化数据库

    静默创建表，抑制SQLAlchemy的PRAGMA输出
    """
    # 保存原始stdout，临时重定向来抑制SQLAlchemy的输出
    original_stdout = sys.stdout
    try:
        sys.stdout = open(os.devnull, "w")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout
