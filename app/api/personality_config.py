"""人格配置管理 API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_admin_user
from app.core import get_db
from app.models.admin_user import AdminUser
from app.models.personality_config import PersonalityConfigModel

router = APIRouter(prefix="/personality-configs", tags=["人格配置"])


# ============ 请求/响应模型 ============


class CreatePersonalityConfigRequest(BaseModel):
    """创建人格配置请求"""

    name: str = Field(..., description="人格名称", min_length=1, max_length=100)
    description: str | None = Field(None, description="人格描述")
    avatar_url: str | None = Field(None, description="头像URL")
    is_active: bool = Field(True, description="是否启用")

    # Big Five 维度
    openness: float = Field(50.0, description="开放性", ge=0, le=100)
    conscientiousness: float = Field(50.0, description="尽责性", ge=0, le=100)
    extraversion: float = Field(50.0, description="外向性", ge=0, le=100)
    agreeableness: float = Field(50.0, description="宜人性", ge=0, le=100)
    neuroticism: float = Field(50.0, description="神经质", ge=0, le=100)

    # 扩展特质
    expressiveness: float = Field(50.0, description="表达丰富度", ge=0, le=100)
    humor: float = Field(50.0, description="幽默程度", ge=0, le=100)
    sarcasm: float = Field(30.0, description="吐槽倾向", ge=0, le=100)
    verbosity: float = Field(50.0, description="话痨程度", ge=0, le=100)
    empathy: float = Field(70.0, description="共情深度", ge=0, le=100)
    warmth: float = Field(70.0, description="温暖度", ge=0, le=100)
    emotional_stability: float = Field(60.0, description="情绪稳定性", ge=0, le=100)
    assertiveness: float = Field(50.0, description="主动性", ge=0, le=100)
    casualness: float = Field(60.0, description="随意度", ge=0, le=100)
    formality: float = Field(30.0, description="正式程度", ge=0, le=100)

    tags: List[str] = Field(default_factory=list, description="标签")


class UpdatePersonalityConfigRequest(BaseModel):
    """更新人格配置请求"""

    name: str | None = Field(None, description="人格名称", min_length=1, max_length=100)
    description: str | None = Field(None, description="人格描述")
    avatar_url: str | None = Field(None, description="头像URL")
    is_active: bool | None = Field(None, description="是否启用")

    # Big Five 维度
    openness: float | None = Field(None, description="开放性", ge=0, le=100)
    conscientiousness: float | None = Field(None, description="尽责性", ge=0, le=100)
    extraversion: float | None = Field(None, description="外向性", ge=0, le=100)
    agreeableness: float | None = Field(None, description="宜人性", ge=0, le=100)
    neuroticism: float | None = Field(None, description="神经质", ge=0, le=100)

    # 扩展特质
    expressiveness: float | None = Field(None, description="表达丰富度", ge=0, le=100)
    humor: float | None = Field(None, description="幽默程度", ge=0, le=100)
    sarcasm: float | None = Field(None, description="吐槽倾向", ge=0, le=100)
    verbosity: float | None = Field(None, description="话痨程度", ge=0, le=100)
    empathy: float | None = Field(None, description="共情深度", ge=0, le=100)
    warmth: float | None = Field(None, description="温暖度", ge=0, le=100)
    emotional_stability: float | None = Field(None, description="情绪稳定性", ge=0, le=100)
    assertiveness: float | None = Field(None, description="主动性", ge=0, le=100)
    casualness: float | None = Field(None, description="随意度", ge=0, le=100)
    formality: float | None = Field(None, description="正式程度", ge=0, le=100)

    tags: List[str] | None = Field(None, description="标签")


class PersonalityConfigResponse(BaseModel):
    """人格配置响应"""

    id: str
    name: str
    description: str | None
    avatar_url: str | None
    is_active: bool
    is_system: bool
    usage_count: int
    big_five: dict[str, float]
    traits: dict[str, float]
    tags: List[str]
    created_by: str | None
    created_at: str
    updated_at: str


class PersonalityConfigListResponse(BaseModel):
    """人格配置列表响应"""

    total: int
    configs: List[PersonalityConfigResponse]


class PersonalityConfigSimpleResponse(BaseModel):
    """简化的人格配置响应（用于下拉菜单）"""

    id: str
    name: str
    description: str | None
    is_active: bool


# ============ API 端点 ============


@router.get("", response_model=PersonalityConfigListResponse)
async def list_personality_configs(
    is_active: bool | None = Query(None, description="是否启用过滤"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取人格配置列表"""
    query = select(PersonalityConfigModel)

    if is_active is not None:
        query = query.where(PersonalityConfigModel.is_active == is_active)

    query = query.order_by(PersonalityConfigModel.usage_count.desc())

    result = await db.execute(query)
    configs = result.scalars().all()

    return PersonalityConfigListResponse(
        total=len(configs),
        configs=[config.to_dict() for config in configs],
    )


@router.get("/simple", response_model=List[PersonalityConfigSimpleResponse])
async def list_simple_personality_configs(
    is_active: bool = Query(True, description="是否启用过滤"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取简化的人格配置列表（用于下拉菜单）"""
    query = select(PersonalityConfigModel).where(PersonalityConfigModel.is_active == is_active)

    result = await db.execute(query)
    configs = result.scalars().all()

    return [
        {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "is_active": config.is_active,
        }
        for config in configs
    ]


@router.get("/{config_id}", response_model=PersonalityConfigResponse)
async def get_personality_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取人格配置详情"""
    result = await db.execute(
        select(PersonalityConfigModel).where(PersonalityConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail=f"人格配置不存在: {config_id}")

    return config.to_dict()


@router.post("", response_model=PersonalityConfigResponse, status_code=201)
async def create_personality_config(
    request: CreatePersonalityConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建人格配置"""
    # 检查名称是否已存在
    result = await db.execute(
        select(PersonalityConfigModel).where(PersonalityConfigModel.name == request.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"人格名称已存在: {request.name}")

    config = PersonalityConfigModel(
        name=request.name,
        description=request.description,
        avatar_url=request.avatar_url,
        is_active=request.is_active,
        is_system=False,
        created_by=current_admin.id,
        # Big Five
        openness=request.openness,
        conscientiousness=request.conscientiousness,
        extraversion=request.extraversion,
        agreeableness=request.agreeableness,
        neuroticism=request.neuroticism,
        # Traits
        expressiveness=request.expressiveness,
        humor=request.humor,
        sarcasm=request.sarcasm,
        verbosity=request.verbosity,
        empathy=request.empathy,
        warmth=request.warmth,
        emotional_stability=request.emotional_stability,
        assertiveness=request.assertiveness,
        casualness=request.casualness,
        formality=request.formality,
        # Tags
        tags=",".join(request.tags) if request.tags else None,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return config.to_dict()


@router.put("/{config_id}", response_model=PersonalityConfigResponse)
async def update_personality_config(
    config_id: str,
    request: UpdatePersonalityConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新人格配置"""
    result = await db.execute(
        select(PersonalityConfigModel).where(PersonalityConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail=f"人格配置不存在: {config_id}")

    # 系统预设不能修改某些字段
    if config.is_system:
        # 系统预设只能修改 is_active
        if request.is_active is not None:
            config.is_active = request.is_active
    else:
        # 更新字段
        if request.name is not None:
            # 检查新名称是否已存在
            existing = await db.execute(
                select(PersonalityConfigModel).where(
                    PersonalityConfigModel.name == request.name,
                    PersonalityConfigModel.id != config_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"人格名称已存在: {request.name}")
            config.name = request.name

        if request.description is not None:
            config.description = request.description
        if request.avatar_url is not None:
            config.avatar_url = request.avatar_url
        if request.is_active is not None:
            config.is_active = request.is_active

        # Big Five
        if request.openness is not None:
            config.openness = request.openness
        if request.conscientiousness is not None:
            config.conscientiousness = request.conscientiousness
        if request.extraversion is not None:
            config.extraversion = request.extraversion
        if request.agreeableness is not None:
            config.agreeableness = request.agreeableness
        if request.neuroticism is not None:
            config.neuroticism = request.neuroticism

        # Traits
        if request.expressiveness is not None:
            config.expressiveness = request.expressiveness
        if request.humor is not None:
            config.humor = request.humor
        if request.sarcasm is not None:
            config.sarcasm = request.sarcasm
        if request.verbosity is not None:
            config.verbosity = request.verbosity
        if request.empathy is not None:
            config.empathy = request.empathy
        if request.warmth is not None:
            config.warmth = request.warmth
        if request.emotional_stability is not None:
            config.emotional_stability = request.emotional_stability
        if request.assertiveness is not None:
            config.assertiveness = request.assertiveness
        if request.casualness is not None:
            config.casualness = request.casualness
        if request.formality is not None:
            config.formality = request.formality

        # Tags
        if request.tags is not None:
            config.tags = ",".join(request.tags) if request.tags else None

    await db.commit()
    await db.refresh(config)

    return config.to_dict()


@router.delete("/{config_id}")
async def delete_personality_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除人格配置"""
    result = await db.execute(
        select(PersonalityConfigModel).where(PersonalityConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail=f"人格配置不存在: {config_id}")

    # 系统预设不能删除
    if config.is_system:
        raise HTTPException(status_code=403, detail="系统预设不能删除")

    # 如果正在被使用，提示不能删除
    if config.usage_count > 0:
        raise HTTPException(
            status_code=400, detail=f"该人格配置正在被 {config.usage_count} 个账号使用，不能删除"
        )

    await db.delete(config)
    await db.commit()

    return {"message": "人格配置已删除"}


@router.post("/{config_id}/apply")
async def apply_personality_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """应用人格配置到账号（增加使用计数）"""
    result = await db.execute(
        select(PersonalityConfigModel).where(PersonalityConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail=f"人格配置不存在: {config_id}")

    config.usage_count += 1
    await db.commit()

    return {
        "message": "人格配置已应用",
        "personality_config": config.get_personality_config(),
    }
