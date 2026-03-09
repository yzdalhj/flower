"""后台管理 - Prompt模板管理API"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.services.prompt_template_service import PromptTemplateService

router = APIRouter(prefix="/admin/prompt-templates", tags=["admin-prompt-templates"])


# ==================== 请求/响应模型 ====================


class PromptSectionCreate(BaseModel):
    """创建区块请求"""

    name: str = Field(..., description="区块名称")
    section_type: str = Field(..., description="区块类型")
    content: str = Field(..., description="区块内容")
    title: Optional[str] = Field(None, description="区块标题")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否启用")


class PromptSectionUpdate(BaseModel):
    """更新区块请求"""

    name: Optional[str] = Field(None, description="区块名称")
    title: Optional[str] = Field(None, description="区块标题")
    content: Optional[str] = Field(None, description="区块内容")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PromptTemplateCreate(BaseModel):
    """创建模板请求"""

    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    personality_id: Optional[str] = Field(None, description="关联的人格ID")
    is_default: bool = Field(False, description="是否为默认模板")
    sections: Optional[List[PromptSectionCreate]] = Field(None, description="区块列表")


class PromptTemplateUpdate(BaseModel):
    """更新模板请求"""

    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    is_default: Optional[bool] = Field(None, description="是否为默认模板")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PromptVariableCreate(BaseModel):
    """创建变量请求"""

    name: str = Field(..., description="变量名")
    description: str = Field(..., description="变量描述")
    var_type: str = Field("string", description="变量类型")
    default_value: Optional[str] = Field(None, description="默认值")
    is_required: bool = Field(True, description="是否必需")
    example: Optional[str] = Field(None, description="示例值")


class PromptVariableUpdate(BaseModel):
    """更新变量请求"""

    description: Optional[str] = Field(None, description="变量描述")
    default_value: Optional[str] = Field(None, description="默认值")
    is_required: Optional[bool] = Field(None, description="是否必需")
    example: Optional[str] = Field(None, description="示例值")


class ReorderSectionsRequest(BaseModel):
    """重新排序区块请求"""

    section_orders: List[Dict[str, Any]] = Field(
        ..., description='区块排序列表 [{"section_id": "xxx", "sort_order": 0}, ...]'
    )


class BuildPromptRequest(BaseModel):
    """构建Prompt请求"""

    variables: Dict[str, str] = Field(default_factory=dict, description="模板变量值")


# ==================== API路由 ====================


@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    personality_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """列出所有Prompt模板"""
    service = PromptTemplateService(db)
    templates = await service.list_templates(
        personality_id=personality_id, is_active=is_active, skip=skip, limit=limit
    )
    return [template.to_dict() for template in templates]


@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    request: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建Prompt模板"""
    service = PromptTemplateService(db)

    # 转换区块数据
    sections_data = []
    if request.sections:
        for section in request.sections:
            sections_data.append(section.model_dump())

    template = await service.create_template(
        name=request.name,
        description=request.description,
        personality_id=request.personality_id,
        is_default=request.is_default,
        sections_data=sections_data,
    )
    return template.to_dict()


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取模板详情"""
    service = PromptTemplateService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template.to_dict()


@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: str,
    request: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新模板"""
    service = PromptTemplateService(db)

    template = await service.update_template(
        template_id=template_id,
        name=request.name,
        description=request.description,
        is_default=request.is_default,
        is_active=request.is_active,
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除模板"""
    service = PromptTemplateService(db)
    success = await service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"message": "删除成功"}


@router.post("/templates/{template_id}/build", response_model=Dict[str, str])
async def build_prompt(
    template_id: str,
    request: BuildPromptRequest,
    db: AsyncSession = Depends(get_db),
):
    """构建Prompt"""
    service = PromptTemplateService(db)
    prompt_text = await service.build_prompt(template_id, request.variables)
    if prompt_text is None:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"prompt": prompt_text}


# ==================== 区块管理 ====================


@router.post("/templates/{template_id}/sections", response_model=Dict[str, Any])
async def add_section(
    template_id: str,
    request: PromptSectionCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加区块到模板"""
    service = PromptTemplateService(db)

    # 检查模板是否存在
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    section = await service.add_section(
        template_id=template_id,
        name=request.name,
        section_type=request.section_type,
        content=request.content,
        title=request.title,
        sort_order=request.sort_order,
        is_active=request.is_active,
    )
    return section.to_dict()


@router.put("/sections/{section_id}", response_model=Dict[str, Any])
async def update_section(
    section_id: str,
    request: PromptSectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新区块"""
    service = PromptTemplateService(db)

    section = await service.update_section(
        section_id=section_id,
        name=request.name,
        title=request.title,
        content=request.content,
        sort_order=request.sort_order,
        is_active=request.is_active,
    )
    if not section:
        raise HTTPException(status_code=404, detail="区块不存在")
    return section.to_dict()


@router.delete("/sections/{section_id}")
async def delete_section(
    section_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除区块"""
    service = PromptTemplateService(db)
    success = await service.delete_section(section_id)
    if not success:
        raise HTTPException(status_code=404, detail="区块不存在")
    return {"message": "删除成功"}


@router.post("/templates/{template_id}/reorder", response_model=Dict[str, str])
async def reorder_sections(
    template_id: str,
    request: ReorderSectionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """重新排序区块"""
    service = PromptTemplateService(db)

    # 检查模板是否存在
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await service.reorder_sections(template_id, request.section_orders)
    return {"message": "排序成功"}


# ==================== 变量管理 ====================


@router.get("/variables", response_model=List[Dict[str, Any]])
async def list_variables(
    db: AsyncSession = Depends(get_db),
):
    """列出所有变量定义"""
    service = PromptTemplateService(db)
    variables = await service.list_variables()
    return [variable.to_dict() for variable in variables]


@router.post("/variables", response_model=Dict[str, Any])
async def create_variable(
    request: PromptVariableCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建变量定义"""
    service = PromptTemplateService(db)
    variable = await service.create_variable(
        name=request.name,
        description=request.description,
        var_type=request.var_type,
        default_value=request.default_value,
        is_required=request.is_required,
        example=request.example,
    )
    return variable.to_dict()


@router.get("/variables/{variable_id}", response_model=Dict[str, Any])
async def get_variable(
    variable_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取变量定义"""
    service = PromptTemplateService(db)
    variable = await service.get_variable(variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="变量不存在")
    return variable.to_dict()


@router.put("/variables/{variable_id}", response_model=Dict[str, Any])
async def update_variable(
    variable_id: str,
    request: PromptVariableUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新变量定义"""
    service = PromptTemplateService(db)
    variable = await service.update_variable(
        variable_id=variable_id,
        description=request.description,
        default_value=request.default_value,
        is_required=request.is_required,
        example=request.example,
    )
    if not variable:
        raise HTTPException(status_code=404, detail="变量不存在")
    return variable.to_dict()


@router.delete("/variables/{variable_id}")
async def delete_variable(
    variable_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除变量定义"""
    service = PromptTemplateService(db)
    success = await service.delete_variable(variable_id)
    if not success:
        raise HTTPException(status_code=404, detail="变量不存在")
    return {"message": "删除成功"}


# ==================== 便捷接口 ====================


@router.get("/by-personality/{personality_id}", response_model=Optional[Dict[str, Any]])
async def get_template_by_personality(
    personality_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取人格关联的默认模板"""
    service = PromptTemplateService(db)
    template = await service.get_template_by_personality(personality_id)
    if template:
        return template.to_dict()
    return None


@router.post("/by-personality/{personality_id}/build", response_model=Dict[str, str])
async def build_prompt_for_personality(
    personality_id: str,
    request: BuildPromptRequest,
    db: AsyncSession = Depends(get_db),
):
    """为人格构建Prompt"""
    service = PromptTemplateService(db)
    prompt_text = await service.build_prompt_for_personality(
        personality_id=personality_id, variables=request.variables
    )
    if prompt_text is None:
        raise HTTPException(status_code=404, detail="未找到可用的模板")
    return {"prompt": prompt_text}
