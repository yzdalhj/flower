# -*- coding: utf-8 -*-
"""混合真人化处理器 - 规则 + LLM + 缓存"""

import random
from typing import Dict, List, Optional

from app.services.humanize.humanize_processor import HumanizeProcessor as RuleHumanizeProcessor
from app.services.humanize.llm_humanizer import LLMHumanizer
from app.services.humanize.lru_cache import LRUCache


class HybridHumanizer:
    """
    混合真人化处理器 - 规则 + LLM + 缓存
    """

    def __init__(
        self,
        llm_probability: float = 0.3,
        cache_max_size: int = 10000,
        cache_ttl: int = 3600,
    ):
        """
        初始化混合真人化处理器

        Args:
            llm_probability: 使用LLM的概率（0-1）
            cache_max_size: 缓存最大容量
            cache_ttl: 缓存过期时间（秒）
        """
        self.rule_processor = RuleHumanizeProcessor()
        self.llm_processor = LLMHumanizer()
        self.cache = LRUCache(max_size=cache_max_size, ttl=cache_ttl)
        self.llm_probability = llm_probability

    async def process(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        emotion: Dict[str, float] = None,
        personality_id: str = None,
        use_llm: bool = None,
    ) -> str:
        """
        混合处理回复

        Args:
            text: 原始AI回复
            conversation_history: 对话历史
            emotion: 当前情感状态
            personality_id: 人格ID
            use_llm: 是否强制使用LLM（None则自动决定）

        Returns:
            真人化后的回复
        """
        # 1. 检查缓存
        cache_key = self._build_cache_key(text, emotion, personality_id)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 2. 决定使用规则还是LLM
        if use_llm is None:
            use_llm = random.random() < self.llm_probability

        if use_llm:
            # 3. 使用LLM真人化
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
                # LLM失败时回退到规则
                print(f"LLM真人化失败，回退到规则: {e}")

        # 5. 使用规则处理
        result = self.rule_processor.process(text)
        return result

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

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        return self.cache.get_stats()

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 全局单例
_hybrid_humanizer: Optional[HybridHumanizer] = None


def get_hybrid_humanizer() -> HybridHumanizer:
    """获取混合真人化处理器实例（单例）"""
    global _hybrid_humanizer
    if _hybrid_humanizer is None:
        _hybrid_humanizer = HybridHumanizer()
    return _hybrid_humanizer
