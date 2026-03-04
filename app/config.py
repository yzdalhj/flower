"""配置管理"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "AI小花"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # 安全
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/xiaohua.db"

    # 向量数据库
    CHROMA_DB_PATH: str = "./data/chroma_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI模型API密钥
    DEEPSEEK_API_KEY: Optional[str] = None
    KIMI_API_KEY: Optional[str] = None
    GLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # 模型配置
    DEFAULT_MODEL: str = "deepseek"
    FALLBACK_ENABLED: bool = True
    API_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置（缓存）"""
    return Settings()
