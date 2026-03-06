"""记忆存储服务"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, WorkingMemory


class MemoryStore:
    """
    记忆存储服务
    管理长期记忆和工作记忆
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========== 长期记忆操作 ==========

    async def create_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        summary: Optional[str] = None,
        importance: float = 1.0,
        occurred_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        vector_id: Optional[str] = None,
    ) -> Memory:
        """
        创建长期记忆

        Args:
            user_id: 用户ID
            memory_type: 记忆类型 (episodic/semantic/emotional/preference)
            content: 记忆内容
            summary: 摘要
            importance: 重要性 (1-10)
            occurred_at: 事件发生时间
            expires_at: 过期时间
            metadata: 元数据
            vector_id: 向量数据库ID

        Returns:
            创建的记忆对象
        """
        memory = Memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            importance=importance,
            occurred_at=occurred_at or datetime.utcnow(),
            expires_at=expires_at,
            metadata=json.dumps(metadata) if metadata else None,
            vector_id=vector_id,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取单个记忆"""
        result = await self.session.execute(select(Memory).where(Memory.id == memory_id))
        return result.scalar_one_or_none()

    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        """
        获取用户的记忆列表

        Args:
            user_id: 用户ID
            memory_type: 记忆类型筛选
            limit: 数量限制
            offset: 偏移量

        Returns:
            记忆列表
        """
        query = select(Memory).where(Memory.user_id == user_id)

        if memory_type:
            query = query.where(Memory.memory_type == memory_type)

        # 按重要性降序、创建时间降序
        query = query.order_by(Memory.importance.desc(), Memory.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_important_memories(
        self, user_id: str, min_importance: float = 5.0, limit: int = 10
    ) -> List[Memory]:
        """获取重要记忆"""
        result = await self.session.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .where(Memory.importance >= min_importance)
            .order_by(Memory.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_memory_access(self, memory_id: str) -> None:
        """更新记忆访问统计"""
        memory = await self.get_memory(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed_at = datetime.utcnow()
            await self.session.commit()

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = await self.get_memory(memory_id)
        if memory:
            await self.session.delete(memory)
            await self.session.commit()
            return True
        return False

    async def search_memories_by_content(
        self, user_id: str, keyword: str, limit: int = 10
    ) -> List[Memory]:
        """按内容关键词搜索记忆"""
        result = await self.session.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .where(Memory.content.contains(keyword))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ========== 工作记忆操作 ==========

    async def get_working_memory(self, user_id: str) -> Optional[WorkingMemory]:
        """获取用户的工作记忆"""
        result = await self.session.execute(
            select(WorkingMemory).where(WorkingMemory.user_id == user_id)
        )
        wm = result.scalar_one_or_none()

        # 检查是否过期
        if wm and wm.expires_at < datetime.utcnow():
            await self.session.delete(wm)
            await self.session.commit()
            return None

        return wm

    async def update_working_memory(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None,
        current_emotion: Optional[Dict[str, float]] = None,
        current_topic: Optional[str] = None,
        pending_intent: Optional[str] = None,
        expires_minutes: int = 30,
    ) -> WorkingMemory:
        """
        更新工作记忆

        Args:
            user_id: 用户ID
            conversation_id: 当前会话ID
            context: 短期上下文
            current_emotion: 当前情感状态
            current_topic: 当前话题
            pending_intent: 待处理意图
            expires_minutes: 过期时间（分钟）

        Returns:
            更新后的工作记忆
        """
        # 获取或创建工作记忆
        wm = await self.get_working_memory(user_id)

        if not wm:
            wm = WorkingMemory(user_id=user_id)
            self.session.add(wm)

        # 更新字段
        if conversation_id is not None:
            wm.conversation_id = conversation_id

        if context is not None:
            wm.context = json.dumps(context[-20:])  # 保留最近20轮

        if current_emotion is not None:
            wm.current_emotion = json.dumps(current_emotion)

        if current_topic is not None:
            wm.current_topic = current_topic

        if pending_intent is not None:
            wm.pending_intent = pending_intent

        # 更新过期时间
        wm.expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        await self.session.commit()
        await self.session.refresh(wm)
        return wm

    async def clear_working_memory(self, user_id: str) -> bool:
        """清除工作记忆"""
        wm = await self.get_working_memory(user_id)
        if wm:
            await self.session.delete(wm)
            await self.session.commit()
            return True
        return False

    # ========== 记忆检索（用于RAG） ==========

    async def get_memories_for_retrieval(
        self,
        user_id: str,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Memory]:
        """
        获取用于检索增强生成的记忆

        Args:
            user_id: 用户ID
            query: 查询文本（用于关键词匹配）
            memory_types: 记忆类型筛选
            limit: 返回数量

        Returns:
            相关记忆列表
        """
        query_builder = select(Memory).where(Memory.user_id == user_id)

        # 类型筛选
        if memory_types:
            query_builder = query_builder.where(Memory.memory_type.in_(memory_types))

        # 排除过期记忆
        query_builder = query_builder.where(
            (Memory.expires_at.is_(None)) | (Memory.expires_at > datetime.utcnow())
        )

        # 关键词匹配（简单实现）
        if query:
            query_builder = query_builder.where(
                Memory.content.contains(query) | Memory.summary.contains(query)
            )

        # 按重要性、访问次数、时间排序
        query_builder = query_builder.order_by(
            Memory.importance.desc(),
            Memory.access_count.desc(),
            Memory.created_at.desc(),
        )

        query_builder = query_builder.limit(limit)

        result = await self.session.execute(query_builder)
        memories = list(result.scalars().all())

        # 更新访问统计
        for memory in memories:
            await self.update_memory_access(memory.id)

        return memories

    async def get_context_for_prompt(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """
        获取用于构建Prompt的上下文

        Returns:
            包含工作记忆、长期记忆、用户画像的字典
        """
        # 获取工作记忆
        working_memory = await self.get_working_memory(user_id)

        # 获取相关长期记忆
        long_term_memories = await self.get_memories_for_retrieval(
            user_id=user_id,
            query=current_message,
            limit=5,
        )

        # 获取重要记忆（高重要性）
        important_memories = await self.get_important_memories(
            user_id=user_id, min_importance=7.0, limit=3
        )

        return {
            "working_memory": working_memory,
            "long_term_memories": long_term_memories,
            "important_memories": important_memories,
        }
