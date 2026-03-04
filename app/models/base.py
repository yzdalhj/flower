"""基础模型"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


class BaseModel(Base):
    """基础模型类"""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
