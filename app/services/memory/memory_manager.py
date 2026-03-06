"""
记忆更新管理器
实现记忆冲突处理、过期机制和记忆强化
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class MemoryConflict:
    """记忆冲突"""

    memory_id_1: str
    memory_id_2: str
    conflict_type: str  # contradiction/duplicate/overlap
    description: str
    confidence: float = 0.8
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class MemoryUpdateResult:
    """记忆更新结果"""

    success: bool
    action: str  # created/updated/merged/deleted/skipped
    memory_id: Optional[str] = None
    conflict: Optional[MemoryConflict] = None
    message: str = ""


class MemoryManager:
    """
    记忆管理器
    负责记忆的冲突处理、过期管理和强化
    """

    def __init__(self, memory_store, vector_store=None):
        self.memory_store = memory_store
        self.vector_store = vector_store
        self.conflict_history: List[MemoryConflict] = []

    async def add_or_update_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        summary: Optional[str] = None,
        importance: float = 5.0,
        occurred_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryUpdateResult:
        """
        添加或更新记忆，自动处理冲突

        Args:
            user_id: 用户ID
            memory_type: 记忆类型
            content: 记忆内容
            summary: 摘要
            importance: 重要性
            occurred_at: 发生时间
            metadata: 元数据

        Returns:
            更新结果
        """
        existing = await self._find_similar_memory(user_id, content, memory_type)

        if existing:
            return await self._handle_existing_memory(
                existing, user_id, memory_type, content, summary, importance, occurred_at, metadata
            )
        else:
            return await self._create_new_memory(
                user_id, memory_type, content, summary, importance, occurred_at, metadata
            )

    async def _find_similar_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str,
    ) -> Optional[Any]:
        """查找相似的记忆"""
        memories = await self.memory_store.get_user_memories(
            user_id=user_id, memory_type=memory_type, limit=20
        )

        content_lower = content.lower()

        for mem in memories:
            mem_content_lower = mem.content.lower()

            if self._is_duplicate(content_lower, mem_content_lower):
                return mem

            if self._is_contradiction(content_lower, mem_content_lower):
                return mem

        return None

    def _is_duplicate(self, content1: str, content2: str) -> bool:
        """检查是否是重复内容"""
        if content1 == content2:
            return True

        if len(content1) > 5 and len(content2) > 5:
            similarity = self._simple_similarity(content1, content2)
            return similarity >= 0.7

        return False

    def _is_contradiction(self, content1: str, content2: str) -> bool:
        """检查是否有矛盾"""
        contradiction_pairs = [
            ("喜欢", "讨厌"),
            ("爱", "恨"),
            ("是", "不是"),
            ("有", "没有"),
            ("在", "不在"),
        ]

        for positive, negative in contradiction_pairs:
            if (positive in content1 and negative in content2) or (
                negative in content1 and positive in content2
            ):
                return True

        return False

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算 - 使用字符级n-gram"""
        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        def get_ngrams(text, n=2):
            """获取字符n-gram"""
            text = text.replace(" ", "")
            if len(text) < n:
                return {text}
            return {text[i : i + n] for i in range(len(text) - n + 1)}

        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = ngrams1 & ngrams2
        smaller_set = min(len(ngrams1), len(ngrams2))

        if smaller_set == 0:
            return 0.0

        return len(intersection) / smaller_set

    async def _handle_existing_memory(
        self,
        existing,
        user_id: str,
        memory_type: str,
        content: str,
        summary: Optional[str],
        importance: float,
        occurred_at: Optional[datetime],
        metadata: Optional[Dict[str, Any]],
    ) -> MemoryUpdateResult:
        """处理已存在的记忆"""
        content_lower = content.lower()
        existing_content_lower = existing.content.lower()

        if self._is_duplicate(content_lower, existing_content_lower):
            return await self._handle_duplicate(existing, content, summary, importance, metadata)
        elif self._is_contradiction(content_lower, existing_content_lower):
            return await self._handle_contradiction(
                existing, user_id, memory_type, content, summary, importance, occurred_at, metadata
            )
        else:
            return await self._create_new_memory(
                user_id, memory_type, content, summary, importance, occurred_at, metadata
            )

    async def _handle_duplicate(
        self,
        existing,
        content: str,
        summary: Optional[str],
        importance: float,
        metadata: Optional[Dict[str, Any]],
    ) -> MemoryUpdateResult:
        """处理重复记忆 - 强化"""
        existing.importance = min(10.0, existing.importance + 0.5)
        existing.access_count += 1
        existing.last_accessed_at = datetime.utcnow()

        if summary:
            existing.summary = summary

        await self.memory_store.session.commit()

        if self.vector_store:
            await self.vector_store.update_memory(
                memory_id=existing.id, content=content, metadata=metadata
            )

        return MemoryUpdateResult(
            success=True,
            action="reinforced",
            memory_id=existing.id,
            message="记忆已强化，重要性提升",
        )

    async def _handle_contradiction(
        self,
        existing,
        user_id: str,
        memory_type: str,
        content: str,
        summary: Optional[str],
        importance: float,
        occurred_at: Optional[datetime],
        metadata: Optional[Dict[str, Any]],
    ) -> MemoryUpdateResult:
        """处理矛盾记忆"""
        conflict = MemoryConflict(
            memory_id_1=existing.id,
            memory_id_2="new",
            conflict_type="contradiction",
            description=f"新记忆与已有记忆矛盾: {content[:50]} vs {existing.content[:50]}",
            confidence=0.85,
        )
        self.conflict_history.append(conflict)

        new_occurred = occurred_at or datetime.utcnow()
        old_occurred = existing.occurred_at or existing.created_at

        if new_occurred > old_occurred:
            existing.content = content
            existing.summary = summary
            existing.occurred_at = occurred_at
            existing.importance = importance
            existing.access_count += 1
            existing.last_accessed_at = datetime.utcnow()

            await self.memory_store.session.commit()

            if self.vector_store:
                await self.vector_store.update_memory(
                    memory_id=existing.id, content=content, metadata=metadata
                )

            conflict.resolved = True
            conflict.resolution = "updated_with_newer"

            return MemoryUpdateResult(
                success=True,
                action="updated",
                memory_id=existing.id,
                conflict=conflict,
                message="记忆已用较新的信息更新",
            )
        else:
            return MemoryUpdateResult(
                success=False,
                action="skipped",
                conflict=conflict,
                message="保留了较旧的记忆，新记忆被跳过",
            )

    async def _create_new_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        summary: Optional[str],
        importance: float,
        occurred_at: Optional[datetime],
        metadata: Optional[Dict[str, Any]],
    ) -> MemoryUpdateResult:
        """创建新记忆"""
        memory = await self.memory_store.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            importance=importance,
            occurred_at=occurred_at,
            metadata=metadata,
        )

        if self.vector_store:
            vector_id = await self.vector_store.add_memory(
                memory_id=memory.id, content=content, metadata=metadata
            )
            memory.vector_id = vector_id
            await self.memory_store.session.commit()

        return MemoryUpdateResult(
            success=True, action="created", memory_id=memory.id, message="新记忆已创建"
        )

    async def expire_old_memories(
        self,
        user_id: str,
        max_age_days: int = 90,
        min_importance: float = 3.0,
    ) -> int:
        """
        过期旧记忆

        Args:
            user_id: 用户ID
            max_age_days: 最大保留天数
            min_importance: 最低重要性（低于此值的会被清理）

        Returns:
            清理的记忆数量
        """
        memories = await self.memory_store.get_user_memories(user_id=user_id, limit=1000)

        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        expired_count = 0

        for mem in memories:
            mem_age = mem.created_at or datetime.utcnow()

            if mem_age < cutoff_date and mem.importance < min_importance:
                if self.vector_store:
                    await self.vector_store.delete_memory(mem.id)

                await self.memory_store.delete_memory(mem.id)
                expired_count += 1

        return expired_count

    async def reinforce_memory(
        self,
        memory_id: str,
        boost_amount: float = 0.3,
    ) -> bool:
        """
        强化记忆

        Args:
            memory_id: 记忆ID
            boost_amount: 强化增量

        Returns:
            是否成功
        """
        memory = await self.memory_store.get_memory(memory_id)
        if not memory:
            return False

        memory.importance = min(10.0, memory.importance + boost_amount)
        memory.access_count += 1
        memory.last_accessed_at = datetime.utcnow()

        await self.memory_store.session.commit()
        return True

    def get_conflict_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[MemoryConflict]:
        """获取冲突历史"""
        conflicts = self.conflict_history[-limit:]
        return conflicts


_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(memory_store=None, vector_store=None) -> MemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(memory_store, vector_store)
    return _memory_manager
