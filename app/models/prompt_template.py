"""Prompt模板模型 - 支持后台管理系统维护"""

from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PromptTemplate(BaseModel):
    """Prompt模板主表"""

    __tablename__ = "prompt_templates"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="模板描述")
    personality_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="关联的人格ID"
    )

    # 是否默认模板
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否为默认模板"
    )

    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )

    # 版本号
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="版本号")

    # 关联的模板区块（按顺序组合）
    sections: Mapped[List["PromptSection"]] = relationship(
        "PromptSection",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="PromptSection.sort_order",
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality_id": self.personality_id,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sections": [section.to_dict() for section in self.sections] if self.sections else [],
        }

    def build_prompt(self, variables: Dict[str, str]) -> str:
        """
        构建完整的Prompt

        Args:
            variables: 模板变量，如 {personality_name}, {speaking_style} 等

        Returns:
            完整的Prompt文本
        """
        parts = []
        for section in self.sections:
            if section.is_active:
                section_content = section.build_content(variables)
                if section_content.strip():
                    parts.append(section_content)
        return "\n\n".join(parts)


class PromptSection(BaseModel):
    """Prompt模板区块 - 可复用的Prompt片段"""

    __tablename__ = "prompt_sections"

    # 区块名称
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="区块名称")

    # 区块类型
    section_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="区块类型: identity(身份)/style(风格)/guidelines(指南)/forbidden(禁止)/examples(示例)/custom(自定义)",
    )

    # 区块标题（显示在Prompt中）
    title: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="区块标题，如'说话风格'、'口头禅'等"
    )

    # 区块内容（支持模板变量）
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="区块内容，支持{variable}格式的模板变量",
    )

    # 排序顺序
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序顺序")

    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )

    # 是否可复用（作为公共区块）
    is_reusable: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否可作为公共区块被其他模板引用"
    )

    # 关联的模板ID
    template_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属的模板ID",
    )

    # 关联的模板
    template: Mapped[Optional["PromptTemplate"]] = relationship(
        "PromptTemplate", back_populates="sections"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "section_type": self.section_type,
            "title": self.title,
            "content": self.content,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "is_reusable": self.is_reusable,
            "template_id": self.template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def build_content(self, variables: Dict[str, str]) -> str:
        """
        构建区块内容

        Args:
            variables: 模板变量

        Returns:
            填充变量后的区块内容
        """
        content = self.content
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))

        # 如果有标题，添加标题
        if self.title:
            return f"【{self.title}】\n{content}"
        return content


class PromptVariable(BaseModel):
    """Prompt模板变量定义 - 用于后台管理界面提示"""

    __tablename__ = "prompt_variables"

    # 变量名（不含花括号）
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="变量名")

    # 变量描述
    description: Mapped[str] = mapped_column(String(500), nullable=False, comment="变量描述")

    # 变量类型
    var_type: Mapped[str] = mapped_column(
        String(50),
        default="string",
        nullable=False,
        comment="变量类型: string/text/int/float/boolean/json",
    )

    # 默认值
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="默认值")

    # 是否必需
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否必需"
    )

    # 示例值
    example: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="示例值")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "var_type": self.var_type,
            "default_value": self.default_value,
            "is_required": self.is_required,
            "example": self.example,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
