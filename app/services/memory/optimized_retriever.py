"""
优化的记忆检索器
支持语义检索、时序检索、重要性筛选和混合排序
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalQuery:
    """检索查询参数"""

    query_text: str
    user_id: Optional[str] = None
    memory_type: Optional[str] = None
    min_importance: float = 0.0
    max_importance: float = 10.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_range_hours: Optional[int] = None
    n_results: int = 10
    semantic_weight: float = 0.6
    time_weight: float = 0.2
    importance_weight: float = 0.2


@dataclass
class MemoryResult:
    """记忆检索结果"""

    memory_id: str
    content: str
    memory_type: str
    importance: float
    occurred_at: Optional[datetime]
    created_at: datetime
    distance: float = 1.0
    time_score: float = 0.0
    importance_score: float = 0.0
    semantic_score: float = 0.0
    final_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class OptimizedMemoryRetriever:
    """
    优化的记忆检索器
    支持多种检索策略和混合排序
    """

    def __init__(self, vector_store, memory_store):
        self.vector_store = vector_store
        self.memory_store = memory_store

    async def retrieve(self, retrieval_query: RetrievalQuery) -> List[MemoryResult]:
        """
        执行优化的记忆检索

        Args:
            retrieval_query: 检索查询参数

        Returns:
            排序后的记忆结果列表
        """
        all_results = []

        semantic_results = await self._semantic_search(retrieval_query)
        all_results.extend(semantic_results)

        if not all_results and retrieval_query.user_id:
            db_results = await self._database_search(retrieval_query)
            all_results.extend(db_results)

        if all_results:
            all_results = self._deduplicate(all_results)
            all_results = self._calculate_scores(all_results, retrieval_query)
            all_results = self._sort_by_final_score(all_results)
            all_results = all_results[: retrieval_query.n_results]

        return all_results

    async def _semantic_search(self, query: RetrievalQuery) -> List[MemoryResult]:
        """语义检索（向量相似度）"""
        filter_dict = self._build_filter_dict(query)

        vector_results = await self.vector_store.search(
            query=query.query_text, n_results=query.n_results * 2, filter_dict=filter_dict
        )

        results = []
        for vr in vector_results:
            memory_id = vr["id"].replace("memory_", "")

            memory = None
            if self.memory_store:
                memory = await self.memory_store.get_memory(memory_id)

            if memory:
                result = MemoryResult(
                    memory_id=memory_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    importance=memory.importance,
                    occurred_at=memory.occurred_at,
                    created_at=memory.created_at,
                    distance=vr.get("distance", 1.0),
                    semantic_score=self._distance_to_similarity(vr.get("distance", 1.0)),
                    metadata=vr.get("metadata", {}),
                )
                results.append(result)

        return results

    async def _database_search(self, query: RetrievalQuery) -> List[MemoryResult]:
        """数据库检索（作为后备）"""
        if not self.memory_store or not query.user_id:
            return []

        memories = await self.memory_store.get_user_memories(
            user_id=query.user_id, memory_type=query.memory_type, limit=query.n_results * 2
        )

        results = []
        for mem in memories:
            if query.min_importance <= mem.importance <= query.max_importance:
                results.append(
                    MemoryResult(
                        memory_id=mem.id,
                        content=mem.content,
                        memory_type=mem.memory_type,
                        importance=mem.importance,
                        occurred_at=mem.occurred_at,
                        created_at=mem.created_at,
                        distance=1.0,
                        semantic_score=0.5,
                        metadata={},
                    )
                )

        return results

    def _build_filter_dict(self, query: RetrievalQuery) -> Optional[Dict[str, Any]]:
        """构建ChromaDB过滤条件"""
        filter_dict = {}

        if query.user_id:
            filter_dict["user_id"] = query.user_id

        if query.memory_type:
            filter_dict["memory_type"] = query.memory_type

        if query.min_importance > 0:
            filter_dict["importance"] = {"$gte": query.min_importance}

        return filter_dict if filter_dict else None

    def _distance_to_similarity(self, distance: float) -> float:
        """将距离转换为相似度分数 [0, 1]"""
        return max(0.0, min(1.0, 1.0 - distance))

    def _calculate_time_score(self, result: MemoryResult, query: RetrievalQuery) -> float:
        """计算时间分数 [0, 1]"""
        if not result.created_at:
            return 0.5

        now = datetime.utcnow()
        time_diff = now - result.created_at

        if query.time_range_hours:
            max_diff = timedelta(hours=query.time_range_hours)
            if time_diff > max_diff:
                return 0.0

        days_diff = time_diff.total_seconds() / (24 * 3600)
        time_decay = 1.0 / (1.0 + days_diff * 0.1)

        return max(0.0, min(1.0, time_decay))

    def _calculate_importance_score(self, result: MemoryResult, query: RetrievalQuery) -> float:
        """计算重要性分数 [0, 1]"""
        return max(0.0, min(1.0, result.importance / 10.0))

    def _calculate_scores(
        self, results: List[MemoryResult], query: RetrievalQuery
    ) -> List[MemoryResult]:
        """计算所有分数"""
        for result in results:
            result.time_score = self._calculate_time_score(result, query)
            result.importance_score = self._calculate_importance_score(result, query)

            result.final_score = (
                query.semantic_weight * result.semantic_score
                + query.time_weight * result.time_score
                + query.importance_weight * result.importance_score
            )

        return results

    def _deduplicate(self, results: List[MemoryResult]) -> List[MemoryResult]:
        """去重"""
        seen = set()
        unique = []
        for result in results:
            if result.memory_id not in seen:
                seen.add(result.memory_id)
                unique.append(result)
        return unique

    def _sort_by_final_score(self, results: List[MemoryResult]) -> List[MemoryResult]:
        """按最终分数排序"""
        return sorted(results, key=lambda x: x.final_score, reverse=True)

    async def search_by_time_range(
        self,
        user_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        n_results: int = 20,
    ) -> List[MemoryResult]:
        """
        时序检索 - 按时间范围搜索

        Args:
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间（默认为现在）
            n_results: 返回结果数

        Returns:
            记忆结果列表
        """
        if not end_time:
            end_time = datetime.utcnow()

        query = RetrievalQuery(
            query_text="",
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            n_results=n_results,
            semantic_weight=0.0,
            time_weight=0.8,
            importance_weight=0.2,
        )

        results = await self.retrieve(query)

        if self.memory_store:
            all_memories = await self.memory_store.get_user_memories(
                user_id=user_id, limit=n_results * 2
            )

            time_filtered = []
            for mem in all_memories:
                mem_time = mem.occurred_at or mem.created_at
                if start_time <= mem_time <= end_time:
                    time_filtered.append(
                        MemoryResult(
                            memory_id=mem.id,
                            content=mem.content,
                            memory_type=mem.memory_type,
                            importance=mem.importance,
                            occurred_at=mem.occurred_at,
                            created_at=mem.created_at,
                            time_score=1.0,
                            importance_score=mem.importance / 10.0,
                            final_score=0.5 * 1.0 + 0.5 * (mem.importance / 10.0),
                        )
                    )

            time_filtered.sort(key=lambda x: x.final_score, reverse=True)
            results = time_filtered[:n_results]

        return results

    async def search_by_importance(
        self, user_id: str, min_importance: float = 5.0, n_results: int = 10
    ) -> List[MemoryResult]:
        """
        重要性筛选 - 按重要性搜索

        Args:
            user_id: 用户ID
            min_importance: 最低重要性
            n_results: 返回结果数

        Returns:
            记忆结果列表
        """
        query = RetrievalQuery(
            query_text="",
            user_id=user_id,
            min_importance=min_importance,
            n_results=n_results,
            semantic_weight=0.0,
            time_weight=0.2,
            importance_weight=0.8,
        )

        return await self.retrieve(query)


_optimized_retriever: Optional[OptimizedMemoryRetriever] = None


def get_optimized_retriever(vector_store=None, memory_store=None) -> OptimizedMemoryRetriever:
    """获取优化的记忆检索器单例"""
    global _optimized_retriever
    if _optimized_retriever is None:
        _optimized_retriever = OptimizedMemoryRetriever(vector_store, memory_store)
    return _optimized_retriever
