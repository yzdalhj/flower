"""Prompt模板服务 - 提供CRUD操作和模板管理"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_template import PromptSection, PromptTemplate, PromptVariable


class PromptTemplateService:
    """Prompt模板服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Prompt模板操作 ====================

    async def create_template(
        self,
        name: str,
        description: Optional[str] = None,
        personality_id: Optional[str] = None,
        is_default: bool = False,
        sections_data: Optional[List[Dict]] = None,
    ) -> PromptTemplate:
        """
        创建Prompt模板

        Args:
            name: 模板名称
            description: 模板描述
            personality_id: 关联的人格ID
            is_default: 是否为默认模板
            sections_data: 区块数据列表

        Returns:
            创建的模板
        """
        # 如果设置为默认，先取消其他默认模板
        if is_default:
            await self._clear_default_template(personality_id)

        template = PromptTemplate(
            name=name,
            description=description,
            personality_id=personality_id,
            is_default=is_default,
            is_active=True,
            version=1,
        )
        self.session.add(template)
        await self.session.flush()  # 获取template.id

        # 创建区块
        if sections_data:
            for idx, section_data in enumerate(sections_data):
                section = PromptSection(
                    template_id=template.id,
                    name=section_data["name"],
                    section_type=section_data.get("section_type", "custom"),
                    title=section_data.get("title"),
                    content=section_data["content"],
                    sort_order=section_data.get("sort_order", idx),
                    is_active=section_data.get("is_active", True),
                    is_reusable=section_data.get("is_reusable", False),
                )
                self.session.add(section)

        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板详情"""
        result = await self.session.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_template_by_personality(self, personality_id: str) -> Optional[PromptTemplate]:
        """获取人格关联的默认模板"""
        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.personality_id == personality_id,
                PromptTemplate.is_default.is_(True),
                PromptTemplate.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_default_template(self) -> Optional[PromptTemplate]:
        """获取系统默认模板"""
        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.is_default.is_(True),
                PromptTemplate.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        personality_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PromptTemplate]:
        """列出模板"""
        query = select(PromptTemplate)

        if personality_id is not None:
            query = query.where(PromptTemplate.personality_id == personality_id)
        if is_active is not None:
            query = query.where(PromptTemplate.is_active == is_active)

        query = query.order_by(PromptTemplate.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[PromptTemplate]:
        """更新模板基本信息"""
        template = await self.get_template(template_id)
        if not template:
            return None

        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if is_active is not None:
            template.is_active = is_active
        if is_default is not None:
            if is_default:
                await self._clear_default_template(template.personality_id)
            template.is_default = is_default

        template.version += 1
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        template = await self.get_template(template_id)
        if not template:
            return False

        await self.session.delete(template)
        await self.session.commit()
        return True

    async def _clear_default_template(self, personality_id: Optional[str]) -> None:
        """清除指定人格的默认模板标记"""
        query = select(PromptTemplate).where(PromptTemplate.is_default.is_(True))
        if personality_id:
            query = query.where(PromptTemplate.personality_id == personality_id)
        else:
            query = query.where(PromptTemplate.personality_id.is_(None))

        result = await self.session.execute(query)
        templates = result.scalars().all()
        for template in templates:
            template.is_default = False

    # ==================== 区块操作 ====================

    async def add_section(
        self,
        template_id: str,
        name: str,
        section_type: str,
        content: str,
        title: Optional[str] = None,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> PromptSection:
        """添加区块到模板"""
        section = PromptSection(
            template_id=template_id,
            name=name,
            section_type=section_type,
            title=title,
            content=content,
            sort_order=sort_order,
            is_active=is_active,
        )
        self.session.add(section)
        await self.session.commit()
        await self.session.refresh(section)
        return section

    async def update_section(
        self,
        section_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[PromptSection]:
        """更新区块"""
        result = await self.session.execute(
            select(PromptSection).where(PromptSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            return None

        if name is not None:
            section.name = name
        if title is not None:
            section.title = title
        if content is not None:
            section.content = content
        if sort_order is not None:
            section.sort_order = sort_order
        if is_active is not None:
            section.is_active = is_active

        await self.session.commit()
        await self.session.refresh(section)
        return section

    async def delete_section(self, section_id: str) -> bool:
        """删除区块"""
        result = await self.session.execute(
            select(PromptSection).where(PromptSection.id == section_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            return False

        await self.session.delete(section)
        await self.session.commit()
        return True

    async def reorder_sections(
        self, template_id: str, section_orders: List[Dict[str, Any]]
    ) -> bool:
        """
        重新排序区块

        Args:
            template_id: 模板ID
            section_orders: [{"section_id": "xxx", "sort_order": 0}, ...]
        """
        for item in section_orders:
            section_id = item.get("section_id")
            sort_order = item.get("sort_order")

            result = await self.session.execute(
                select(PromptSection).where(
                    PromptSection.id == section_id,
                    PromptSection.template_id == template_id,
                )
            )
            section = result.scalar_one_or_none()
            if section:
                section.sort_order = sort_order

        await self.session.commit()
        return True

    # ==================== 变量操作 ====================

    async def create_variable(
        self,
        name: str,
        description: str,
        var_type: str = "string",
        default_value: Optional[str] = None,
        is_required: bool = True,
        example: Optional[str] = None,
    ) -> PromptVariable:
        """创建变量定义"""
        variable = PromptVariable(
            name=name,
            description=description,
            var_type=var_type,
            default_value=default_value,
            is_required=is_required,
            example=example,
        )
        self.session.add(variable)
        await self.session.commit()
        await self.session.refresh(variable)
        return variable

    async def get_variable(self, variable_id: str) -> Optional[PromptVariable]:
        """获取变量定义"""
        result = await self.session.execute(
            select(PromptVariable).where(PromptVariable.id == variable_id)
        )
        return result.scalar_one_or_none()

    async def get_variable_by_name(self, name: str) -> Optional[PromptVariable]:
        """通过名称获取变量定义"""
        result = await self.session.execute(
            select(PromptVariable).where(PromptVariable.name == name)
        )
        return result.scalar_one_or_none()

    async def list_variables(self) -> List[PromptVariable]:
        """列出所有变量定义"""
        result = await self.session.execute(select(PromptVariable))
        return list(result.scalars().all())

    async def update_variable(
        self,
        variable_id: str,
        description: Optional[str] = None,
        default_value: Optional[str] = None,
        is_required: Optional[bool] = None,
        example: Optional[str] = None,
    ) -> Optional[PromptVariable]:
        """更新变量定义"""
        variable = await self.get_variable(variable_id)
        if not variable:
            return None

        if description is not None:
            variable.description = description
        if default_value is not None:
            variable.default_value = default_value
        if is_required is not None:
            variable.is_required = is_required
        if example is not None:
            variable.example = example

        await self.session.commit()
        await self.session.refresh(variable)
        return variable

    async def delete_variable(self, variable_id: str) -> bool:
        """删除变量定义"""
        variable = await self.get_variable(variable_id)
        if not variable:
            return False

        await self.session.delete(variable)
        await self.session.commit()
        return True

    # ==================== 模板构建 ====================

    async def build_prompt(self, template_id: str, variables: Dict[str, str]) -> Optional[str]:
        """
        构建Prompt

        Args:
            template_id: 模板ID
            variables: 模板变量值

        Returns:
            构建后的Prompt文本
        """
        template = await self.get_template(template_id)
        if not template:
            return None

        return template.build_prompt(variables)

    async def build_prompt_for_personality(
        self,
        personality_id: str,
        variables: Dict[str, str],
    ) -> Optional[str]:
        """
        为人格构建Prompt

        Args:
            personality_id: 人格ID
            variables: 模板变量值

        Returns:
            构建后的Prompt文本
        """
        # 先查找人格特定的模板
        template = await self.get_template_by_personality(personality_id)

        # 如果没有，使用系统默认模板
        if not template:
            template = await self.get_default_template()

        if not template:
            return None

        return template.build_prompt(variables)


# 便捷函数
async def get_prompt_template_service(
    session: AsyncSession,
) -> PromptTemplateService:
    """获取Prompt模板服务实例"""
    return PromptTemplateService(session)
