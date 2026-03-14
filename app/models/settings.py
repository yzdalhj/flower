"""系统设置模型"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import BaseModel


class LLMProvider(BaseModel):
    """LLM厂商配置表"""

    __tablename__ = "llm_providers"

    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="厂商名称，如 deepseek、kimi、glm、openai"
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="API基础URL")
    api_key: Mapped[str] = mapped_column(String(500), nullable=False, comment="API密钥")
    default_model: Mapped[str] = mapped_column(String(100), nullable=False, comment="默认模型名称")
    models: Mapped[list] = mapped_column(JSON, default=list, comment="支持的模型列表")

    # 连接配置
    timeout: Mapped[int] = mapped_column(Integer, default=30, comment="超时时间(秒)")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, comment="最大重试次数")

    # 功能开关
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为默认厂商")

    # 优先级（用于故障切换）
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级，数字越大优先级越高")

    # 描述
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self):
        return f"<LLMProvider(name={self.name}, is_enabled={self.is_enabled})>"


class SystemSettings(BaseModel):
    """系统设置表"""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="设置键")
    value: Mapped[Any] = mapped_column(JSON, nullable=True, comment="设置值")
    value_type: Mapped[str] = mapped_column(
        String(20), default="string", comment="值类型: string, int, float, bool, json"
    )
    category: Mapped[str] = mapped_column(String(50), default="general", comment="分类")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self):
        return f"<SystemSettings(key={self.key}, category={self.category})>"


class ModelConfig(BaseModel):
    """模型配置表 - 存储各模型的详细参数"""

    __tablename__ = "model_configs"

    provider_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="关联的厂商ID")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模型名称")
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")

    # 模型参数
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, comment="最大token数")
    temperature: Mapped[float] = mapped_column(Float, default=0.7, comment="温度")
    top_p: Mapped[float] = mapped_column(Float, default=1.0, comment="top_p")

    # 能力配置
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否支持流式")
    supports_functions: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否支持函数调用"
    )
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否支持视觉")
    context_length: Mapped[int] = mapped_column(Integer, default=8192, comment="上下文长度")

    # 成本配置（每1000 tokens）
    input_cost: Mapped[float] = mapped_column(Float, default=0.0, comment="输入成本")
    output_cost: Mapped[float] = mapped_column(Float, default=0.0, comment="输出成本")

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self):
        return f"<ModelConfig(model={self.model_name}, provider={self.provider_id})>"
