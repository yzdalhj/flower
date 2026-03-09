# -*- coding: utf-8 -*-
"""带缓存的纯LLM真人化处理器 - 不使用规则，只使用LLM + 缓存"""

from typing import Dict, List, Optional

from app.services.humanize.llm_humanizer import LLMHumanizer
from app.services.humanize.lru_cache import LRUCache


class CachedLLMHumanizer:
    """
    带缓存的纯LLM真人化处理器
    - 100%使用LLM进行真人化（不使用规则）
    - 使用LRU缓存降低成本
    - 支持缓存命中率统计
    """

    def __init__(
        self,
        cache_max_size: int = 10000,
        cache_ttl: int = 3600,
    ):
        """
        初始化带缓存的LLM真人化处理器

        Args:
            cache_max_size: 缓存最大容量
            cache_ttl: 缓存过期时间（秒）
        """
        self.llm_processor = LLMHumanizer()
        self.cache = LRUCache(max_size=cache_max_size, ttl=cache_ttl)

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "llm_calls": 0,
        }

    async def process(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        emotion: Dict[str, float] = None,
        personality_id: str = None,
    ) -> str:
        """
        处理回复（带缓存）

        Args:
            text: 原始AI回复
            conversation_history: 对话历史
            emotion: 当前情感状态
            personality_id: 人格ID

        Returns:
            真人化后的回复
        """
        self.stats["total_requests"] += 1

        # 1. 构建缓存key
        cache_key = self._build_cache_key(text, emotion, personality_id)

        # 2. 检查缓存
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]

        # 3. 缓存未命中，使用LLM
        self.stats["cache_misses"] += 1
        self.stats["llm_calls"] += 1

        try:
            result = await self.llm_processor.process(
                text=text,
                conversation_history=conversation_history,
                emotion=emotion,
                personality_id=personality_id,
            )

            # 4. 缓存结果
            self.cache[cache_key] = result
            return result

        except Exception as e:
            # LLM失败时，返回原始文本（不做处理）
            print(f"LLM真人化失败: {e}")
            return text

    def _build_cache_key(
        self,
        text: str,
        emotion: Dict[str, float] = None,
        personality_id: str = None,
    ) -> str:
        """
        构建缓存key

        Args:
            text: 原始文本
            emotion: 情感状态
            personality_id: 人格ID

        Returns:
            缓存key
        """
        key_parts = [text]
        if emotion:
            # 对emotion进行排序，确保相同的emotion生成相同的key
            sorted_emotion = sorted(emotion.items())
            key_parts.append(f"emotion:{sorted_emotion}")
        if personality_id:
            key_parts.append(f"personality:{personality_id}")
        return "|".join(key_parts)

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        total = self.stats["total_requests"]
        hits = self.stats["cache_hits"]

        hit_rate = hits / total if total > 0 else 0.0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": self.stats["cache_misses"],
            "llm_calls": self.stats["llm_calls"],
            "hit_rate": hit_rate,
            "cache_size": self.cache.get_stats()["size"],
        }

    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        return self.cache.get_stats()

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "llm_calls": 0,
        }


# 全局单例
_cached_llm_humanizer: Optional[CachedLLMHumanizer] = None


def get_cached_llm_humanizer() -> CachedLLMHumanizer:
    """获取带缓存的LLM真人化处理器实例（单例）"""
    global _cached_llm_humanizer
    if _cached_llm_humanizer is None:
        _cached_llm_humanizer = CachedLLMHumanizer()
    return _cached_llm_humanizer
