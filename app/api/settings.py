"""系统设置 API"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models.settings import LLMProvider, SystemSettings

router = APIRouter(prefix="/settings", tags=["系统设置"])


# ========== LLM 厂商配置 ==========


class LLMProviderCreate(BaseModel):
    """创建LLM厂商请求"""

    name: str = Field(..., description="厂商名称，如 deepseek、kimi")
    display_name: str = Field(..., description="显示名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    default_model: str = Field(..., description="默认模型名称")
    models: List[str] = Field(default=[], description="支持的模型列表")
    timeout: int = Field(default=30, description="超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    is_enabled: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认厂商")
    priority: int = Field(default=0, description="优先级")
    description: Optional[str] = Field(None, description="描述")


class LLMProviderResponse(BaseModel):
    """LLM厂商响应"""

    id: str
    name: str
    display_name: str
    base_url: str
    api_key: str
    default_model: str
    models: List[str]
    timeout: int
    max_retries: int
    is_enabled: bool
    is_default: bool
    priority: int
    description: Optional[str]


class LLMProviderUpdate(BaseModel):
    """更新LLM厂商请求"""

    display_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    models: Optional[List[str]] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None


# ========== 模型配置 ==========


class ModelConfigCreate(BaseModel):
    """创建模型配置请求"""

    provider_id: str = Field(..., description="厂商ID")
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.7, description="温度")
    top_p: float = Field(default=1.0, description="top_p")
    supports_streaming: bool = Field(default=True, description="是否支持流式")
    supports_functions: bool = Field(default=False, description="是否支持函数调用")
    supports_vision: bool = Field(default=False, description="是否支持视觉")
    context_length: int = Field(default=8192, description="上下文长度")
    input_cost: float = Field(default=0.0, description="输入成本")
    output_cost: float = Field(default=0.0, description="输出成本")
    is_enabled: bool = Field(default=True, description="是否启用")


class ModelConfigResponse(BaseModel):
    """模型配置响应"""

    id: str
    provider_id: str
    model_name: str
    display_name: str
    max_tokens: int
    temperature: float
    top_p: float
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool
    context_length: int
    input_cost: float
    output_cost: float
    is_enabled: bool


# ========== 系统设置 ==========


class SettingsResponse(BaseModel):
    """系统设置响应"""

    emotion_analysis_enabled: bool = Field(True, description="情感分析开关")
    memory_enabled: bool = Field(True, description="记忆功能开关")
    proactive_enabled: bool = Field(True, description="主动行为开关")
    sticker_enabled: bool = Field(True, description="表情包开关")
    daily_message_limit: int = Field(1000, description="每日消息限制")
    daily_cost_limit: float = Field(50.0, description="每日成本限制")
    fallback_enabled: bool = Field(True, description="故障切换开关")
    deep_thinking_enabled: bool = Field(False, description="深度思考开关")


class UpdateSettingsRequest(BaseModel):
    """更新设置请求"""

    emotion_analysis_enabled: Optional[bool] = None
    memory_enabled: Optional[bool] = None
    proactive_enabled: Optional[bool] = None
    sticker_enabled: Optional[bool] = None
    daily_message_limit: Optional[int] = None
    daily_cost_limit: Optional[float] = None
    fallback_enabled: Optional[bool] = None
    deep_thinking_enabled: Optional[bool] = None


# 默认系统设置
DEFAULT_SETTINGS = {
    "emotion_analysis_enabled": True,
    "memory_enabled": True,
    "proactive_enabled": True,
    "sticker_enabled": True,
    "daily_message_limit": 1000,
    "daily_cost_limit": 50.0,
    "fallback_enabled": True,
    "deep_thinking_enabled": False,
}


# ========== 辅助函数 ==========


async def get_or_create_setting(
    db: AsyncSession,
    key: str,
    default_value: Any,
    value_type: str = "string",
    category: str = "general",
    description: str = "",
) -> SystemSettings:
    """获取或创建设置项"""
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        setting = SystemSettings(
            key=key,
            value=default_value,
            value_type=value_type,
            category=category,
            description=description,
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return setting


async def get_settings_dict(db: AsyncSession) -> Dict[str, Any]:
    """获取所有设置的字典"""
    # 确保所有默认设置都存在
    for key, value in DEFAULT_SETTINGS.items():
        value_type = type(value).__name__
        if value_type == "bool":
            value_type = "bool"
        elif value_type == "int":
            value_type = "int"
        elif value_type == "float":
            value_type = "float"
        else:
            value_type = "string"

        await get_or_create_setting(
            db,
            key,
            value,
            value_type,
            category="features" if "enabled" in key else "limits",
            description=f"设置项: {key}",
        )

    # 获取所有设置
    result = await db.execute(select(SystemSettings))
    settings = result.scalars().all()

    return {s.key: s.value for s in settings}


# ========== LLM 厂商 API ==========


@router.get("/providers", response_model=List[LLMProviderResponse])
async def get_providers(
    db: AsyncSession = Depends(get_db), enabled_only: bool = False
) -> List[LLMProviderResponse]:
    """获取所有LLM厂商配置"""
    query = select(LLMProvider)
    if enabled_only:
        query = query.where(LLMProvider.is_enabled.is_(True))
    query = query.order_by(LLMProvider.priority.desc())

    result = await db.execute(query)
    providers = result.scalars().all()

    return [
        LLMProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            base_url=p.base_url,
            api_key=p.api_key,
            default_model=p.default_model,
            models=p.models or [],
            timeout=p.timeout,
            max_retries=p.max_retries,
            is_enabled=p.is_enabled,
            is_default=p.is_default,
            priority=p.priority,
            description=p.description,
        )
        for p in providers
    ]


@router.post("/providers", response_model=LLMProviderResponse)
async def create_provider(
    request: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    """创建LLM厂商配置"""
    # 检查名称是否已存在
    result = await db.execute(select(LLMProvider).where(LLMProvider.name == request.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"厂商 {request.name} 已存在")

    # 如果设置为默认，取消其他默认
    if request.is_default:
        await db.execute(select(LLMProvider).where(LLMProvider.is_default.is_(True)))
        result = await db.execute(select(LLMProvider).where(LLMProvider.is_default.is_(True)))
        for provider in result.scalars().all():
            provider.is_default = False

    provider = LLMProvider(
        name=request.name,
        display_name=request.display_name,
        base_url=request.base_url,
        api_key=request.api_key,
        default_model=request.default_model,
        models=request.models,
        timeout=request.timeout,
        max_retries=request.max_retries,
        is_enabled=request.is_enabled,
        is_default=request.is_default,
        priority=request.priority,
        description=request.description,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        base_url=provider.base_url,
        api_key=provider.api_key,
        default_model=provider.default_model,
        models=provider.models or [],
        timeout=provider.timeout,
        max_retries=provider.max_retries,
        is_enabled=provider.is_enabled,
        is_default=provider.is_default,
        priority=provider.priority,
        description=provider.description,
    )


@router.put("/providers/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: str,
    request: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    """更新LLM厂商配置"""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="厂商不存在")

    # 如果设置为默认，取消其他默认
    if request.is_default:
        result = await db.execute(select(LLMProvider).where(LLMProvider.is_default.is_(True)))
        for p in result.scalars().all():
            if p.id != provider_id:
                p.is_default = False

    # 更新字段
    update_data = request.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        base_url=provider.base_url,
        api_key=provider.api_key,
        default_model=provider.default_model,
        models=provider.models or [],
        timeout=provider.timeout,
        max_retries=provider.max_retries,
        is_enabled=provider.is_enabled,
        is_default=provider.is_default,
        priority=provider.priority,
        description=provider.description,
    )


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """删除LLM厂商配置"""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="厂商不存在")

    await db.delete(provider)
    await db.commit()

    return {"success": True, "message": f"厂商 {provider.name} 已删除"}


# ========== 系统设置 API ==========


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)) -> SettingsResponse:
    """获取系统设置"""
    settings_dict = await get_settings_dict(db)

    # 填充默认值
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings_dict:
            settings_dict[key] = value

    return SettingsResponse(**settings_dict)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """更新系统设置"""
    update_data = request.model_dump(exclude_none=True)

    for key, value in update_data.items():
        value_type = type(value).__name__
        if value_type == "bool":
            value_type = "bool"
        elif value_type == "int":
            value_type = "int"
        elif value_type == "float":
            value_type = "float"
        else:
            value_type = "string"

        setting = await get_or_create_setting(
            db,
            key,
            value,
            value_type,
            category="features" if "enabled" in key else "limits",
            description=f"设置项: {key}",
        )

        setting.value = value
        setting.value_type = value_type

    await db.commit()

    return await get_settings(db)


@router.post("/reset")
async def reset_settings(db: AsyncSession = Depends(get_db)) -> SettingsResponse:
    """重置系统设置为默认值"""
    result = await db.execute(select(SystemSettings))
    settings = result.scalars().all()

    for setting in settings:
        await db.delete(setting)

    await db.commit()

    return await get_settings(db)


# ========== 初始化默认厂商 ==========


@router.post("/providers/init-defaults")
async def init_default_providers(db: AsyncSession = Depends(get_db)) -> List[LLMProviderResponse]:
    """初始化默认LLM厂商配置"""
    default_providers = [
        {
            "name": "deepseek",
            "display_name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "",
            "default_model": "deepseek-chat",
            "models": ["deepseek-chat", "deepseek-coder"],
            "is_enabled": True,
            "priority": 10,
        },
        {
            "name": "kimi",
            "display_name": "Kimi (Moonshot)",
            "base_url": "https://api.moonshot.cn/v1",
            "api_key": "",
            "default_model": "moonshot-v1-8k",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            "is_enabled": True,
            "priority": 20,
        },
        {
            "name": "glm",
            "display_name": "智谱 GLM",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "",
            "default_model": "glm-4",
            "models": ["glm-4", "glm-4-flash", "glm-3-turbo"],
            "is_enabled": True,
            "priority": 5,
        },
        {
            "name": "openai",
            "display_name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "default_model": "gpt-3.5-turbo",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            "is_enabled": False,
            "priority": 0,
        },
    ]

    created_providers = []

    for provider_data in default_providers:
        # 检查是否已存在
        result = await db.execute(
            select(LLMProvider).where(LLMProvider.name == provider_data["name"])
        )
        if not result.scalar_one_or_none():
            provider = LLMProvider(**provider_data)
            db.add(provider)
            await db.commit()
            await db.refresh(provider)
            created_providers.append(provider)

    return [
        LLMProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            base_url=p.base_url,
            api_key=p.api_key,
            default_model=p.default_model,
            models=p.models or [],
            timeout=p.timeout,
            max_retries=p.max_retries,
            is_enabled=p.is_enabled,
            is_default=p.is_default,
            priority=p.priority,
            description=p.description,
        )
        for p in created_providers
    ]
