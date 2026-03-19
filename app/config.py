"""配置管理"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "AI小花"
    DEBUG: bool = True
    LOG_LEVEL: str = "ERROR"

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
    DEEPSEEK_API_KEY: str = "sk-xxx"
    KIMI_API_KEY: Optional[str] = None
    GLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: str = "xxxx"

    # 模型配置
    DEFAULT_MODEL: str = "openai"
    FALLBACK_ENABLED: bool = True
    API_TIMEOUT: int = 30

    # 微信公众号配置
    WECHAT_OFFICIAL_TOKEN: str = ""
    WECHAT_OFFICIAL_APP_ID: str = ""
    WECHAT_OFFICIAL_APP_SECRET: str = ""

    # 企业微信配置
    WECHAT_WORK_CORPID: str = ""
    WECHAT_WORK_AGENTID: str = ""
    WECHAT_WORK_SECRET: str = ""

    # 微信客户端主控配置（非官方方案）
    WECHAT_CLIENT_ENABLED: bool = False
    WECHAT_CLIENT_HOST: str = "127.0.0.1"
    WECHAT_CLIENT_PORT: int = 5555

    # 初始化开关
    INIT_ADMIN: bool = False
    INIT_PROMPT_TEMPLATES: bool = False
    INIT_STICKERS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置（缓存）"""
    return Settings()
