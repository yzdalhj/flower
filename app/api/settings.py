"""系统设置 API"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/settings", tags=["系统设置"])


# 设置项模型
class SettingsItem(BaseModel):
    """设置项"""

    key: str
    value: Any
    category: str = "general"
    description: Optional[str] = None


# 系统设置响应
class SettingsResponse(BaseModel):
    """系统设置响应"""

    deepseek_api_key: Optional[str] = Field(None, description="DeepSeek API Key")
    kimi_api_key: Optional[str] = Field(None, description="Kimi API Key")
    glm_api_key: Optional[str] = Field(None, description="GLM API Key")
    emotion_analysis_enabled: bool = Field(True, description="情感分析开关")
    memory_enabled: bool = Field(True, description="记忆功能开关")
    proactive_enabled: bool = Field(True, description="主动行为开关")
    sticker_enabled: bool = Field(True, description="表情包开关")
    daily_message_limit: int = Field(1000, description="每日消息限制")
    daily_cost_limit: float = Field(50.0, description="每日成本限制")


# 更新设置请求
class UpdateSettingsRequest(BaseModel):
    """更新设置请求"""

    deepseek_api_key: Optional[str] = None
    kimi_api_key: Optional[str] = None
    glm_api_key: Optional[str] = None
    emotion_analysis_enabled: Optional[bool] = None
    memory_enabled: Optional[bool] = None
    proactive_enabled: Optional[bool] = None
    sticker_enabled: Optional[bool] = None
    daily_message_limit: Optional[int] = None
    daily_cost_limit: Optional[float] = None


# 内存中的设置缓存（实际应用应该使用数据库或Redis）
_settings_cache: Dict[str, Any] = {
    "deepseek_api_key": "",
    "kimi_api_key": "",
    "glm_api_key": "",
    "emotion_analysis_enabled": True,
    "memory_enabled": True,
    "proactive_enabled": True,
    "sticker_enabled": True,
    "daily_message_limit": 1000,
    "daily_cost_limit": 50.0,
}


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """
    获取系统设置

    Returns:
        系统设置
    """
    return SettingsResponse(**_settings_cache)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
) -> SettingsResponse:
    """
    更新系统设置

    Args:
        request: 更新设置请求

    Returns:
        更新后的系统设置
    """
    global _settings_cache

    # 只更新非 None 的字段
    update_data = request.model_dump(exclude_none=True)
    _settings_cache.update(update_data)

    return SettingsResponse(**_settings_cache)


@router.post("/reset")
async def reset_settings() -> SettingsResponse:
    """
    重置系统设置为默认值

    Returns:
        重置后的系统设置
    """
    global _settings_cache

    _settings_cache = {
        "deepseek_api_key": "",
        "kimi_api_key": "",
        "glm_api_key": "",
        "emotion_analysis_enabled": True,
        "memory_enabled": True,
        "proactive_enabled": True,
        "sticker_enabled": True,
        "daily_message_limit": 1000,
        "daily_cost_limit": 50.0,
    }

    return SettingsResponse(**_settings_cache)


@router.get("/{key}")
async def get_setting_by_key(key: str) -> Dict[str, Any]:
    """
    获取指定设置项

    Args:
        key: 设置项键名

    Returns:
        设置项值
    """
    if key not in _settings_cache:
        raise HTTPException(status_code=404, detail=f"设置项 {key} 不存在")

    return {"key": key, "value": _settings_cache[key]}


@router.put("/{key}")
async def update_setting_by_key(
    key: str,
    value: Any,
) -> Dict[str, Any]:
    """
    更新指定设置项

    Args:
        key: 设置项键名
        value: 设置项值

    Returns:
        更新后的设置项
    """
    if key not in _settings_cache:
        raise HTTPException(status_code=404, detail=f"设置项 {key} 不存在")

    _settings_cache[key] = value

    return {"key": key, "value": value}
