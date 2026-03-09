# -*- coding: utf-8 -*-
"""LRU缓存实现"""

import time
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""

    value: str
    timestamp: float
    access_count: int = 0


class LRUCache:
    """
    LRU缓存 - 最近最少使用
    """

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 秒
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def __contains__(self, key: str) -> bool:
        """检查key是否存在且未过期（不更新LRU顺序）"""
        if key not in self.cache:
            return False
        entry = self.cache[key]
        if time.time() - entry.timestamp > self.ttl:
            del self.cache[key]
            return False
        return True

    def __getitem__(self, key: str) -> str:
        """获取缓存值"""
        if key not in self:
            raise KeyError(key)
        entry = self.cache.pop(key)
        entry.access_count += 1
        self.cache[key] = entry  # 移到末尾（最新）
        return entry.value

    def __setitem__(self, key: str, value: str):
        """设置缓存值"""
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # 移除最旧的
            self.cache.popitem(last=False)
        self.cache[key] = CacheEntry(value=value, timestamp=time.time())

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total_access = sum(entry.access_count for entry in self.cache.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_access": total_access,
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()
