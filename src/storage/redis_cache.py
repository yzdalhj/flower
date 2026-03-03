"""Redis缓存管理器"""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.config.manager import RedisConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCacheManager:
    """Redis缓存管理器"""
    
    # 缓存键前缀
    SESSION_PREFIX = "session:"
    CONTEXT_PREFIX = "context:"
    EMOTION_PREFIX = "emotion:"
    USER_STATE_PREFIX = "user_state:"
    
    # 默认过期时间（秒）
    DEFAULT_SESSION_TTL = 3600  # 1小时
    DEFAULT_CONTEXT_TTL = 1800  # 30分钟
    DEFAULT_EMOTION_TTL = 86400  # 24小时
    
    def __init__(self, config: RedisConfig):
        """
        初始化Redis缓存管理器
        
        Args:
            config: Redis配置
        """
        self.config = config
        self._client: Optional[Redis] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        初始化Redis连接
        
        Returns:
            是否初始化成功
        """
        try:
            async with self._lock:
                if self._client is not None:
                    logger.warning("redis_already_initialized")
                    return True
                
                logger.info(
                    "initializing_redis_connection",
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db
                )
                
                # 创建Redis连接
                self._client = await aioredis.from_url(
                    f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                    password=self.config.password,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                
                # 测试连接
                await self._client.ping()
                logger.info("redis_connected")
                
                return True
                
        except Exception as e:
            logger.error("redis_initialization_error", error=str(e))
            return False
    
    async def close(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("redis_connection_closed")
    
    def _ensure_connected(self) -> None:
        """确保Redis已连接"""
        if not self._client:
            raise RuntimeError("Redis连接未初始化")
    
    # ==================== 会话状态缓存 ====================
    
    async def set_session_state(
        self,
        session_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置会话状态
        
        Args:
            session_id: 会话ID
            state: 会话状态数据
            ttl: 过期时间（秒），None使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            self._ensure_connected()
            key = f"{self.SESSION_PREFIX}{session_id}"
            value = json.dumps(state, ensure_ascii=False)
            ttl = ttl or self.DEFAULT_SESSION_TTL
            
            await self._client.setex(key, ttl, value)
            logger.debug("session_state_cached", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("set_session_state_error", session_id=session_id, error=str(e))
            return False
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态数据，不存在返回None
        """
        try:
            self._ensure_connected()
            key = f"{self.SESSION_PREFIX}{session_id}"
            value = await self._client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error("get_session_state_error", session_id=session_id, error=str(e))
            return None
    
    async def delete_session_state(self, session_id: str) -> bool:
        """
        删除会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            self._ensure_connected()
            key = f"{self.SESSION_PREFIX}{session_id}"
            await self._client.delete(key)
            logger.debug("session_state_deleted", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("delete_session_state_error", session_id=session_id, error=str(e))
            return False
    
    # ==================== 对话上下文缓存 ====================
    
    async def cache_conversation_context(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """
        缓存对话上下文（热数据）
        
        Args:
            user_id: 用户ID
            messages: 消息列表
            ttl: 过期时间（秒），None使用默认值
            
        Returns:
            是否缓存成功
        """
        try:
            self._ensure_connected()
            key = f"{self.CONTEXT_PREFIX}{user_id}"
            value = json.dumps(messages, ensure_ascii=False, default=str)
            ttl = ttl or self.DEFAULT_CONTEXT_TTL
            
            await self._client.setex(key, ttl, value)
            logger.debug("context_cached", user_id=user_id, message_count=len(messages))
            return True
            
        except Exception as e:
            logger.error("cache_context_error", user_id=user_id, error=str(e))
            return False
    
    async def get_conversation_context(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的对话上下文
        
        Args:
            user_id: 用户ID
            
        Returns:
            消息列表，不存在返回None
        """
        try:
            self._ensure_connected()
            key = f"{self.CONTEXT_PREFIX}{user_id}"
            value = await self._client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error("get_context_error", user_id=user_id, error=str(e))
            return None
    
    async def invalidate_conversation_context(self, user_id: str) -> bool:
        """
        使对话上下文缓存失效
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            self._ensure_connected()
            key = f"{self.CONTEXT_PREFIX}{user_id}"
            await self._client.delete(key)
            logger.debug("context_invalidated", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("invalidate_context_error", user_id=user_id, error=str(e))
            return False
    
    # ==================== 情绪状态缓存 ====================
    
    async def cache_emotion_state(
        self,
        user_id: str,
        emotion_state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        缓存用户情绪状态
        
        Args:
            user_id: 用户ID
            emotion_state: 情绪状态数据
            ttl: 过期时间（秒），None使用默认值
            
        Returns:
            是否缓存成功
        """
        try:
            self._ensure_connected()
            key = f"{self.EMOTION_PREFIX}{user_id}"
            value = json.dumps(emotion_state, ensure_ascii=False, default=str)
            ttl = ttl or self.DEFAULT_EMOTION_TTL
            
            await self._client.setex(key, ttl, value)
            logger.debug("emotion_state_cached", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("cache_emotion_error", user_id=user_id, error=str(e))
            return False
    
    async def get_emotion_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的情绪状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            情绪状态数据，不存在返回None
        """
        try:
            self._ensure_connected()
            key = f"{self.EMOTION_PREFIX}{user_id}"
            value = await self._client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error("get_emotion_error", user_id=user_id, error=str(e))
            return None
    
    # ==================== 通用缓存操作 ====================
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值（会自动序列化为JSON）
            ttl: 过期时间（秒），None表示永不过期
            
        Returns:
            是否设置成功
        """
        try:
            self._ensure_connected()
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            elif not isinstance(value, str):
                value = str(value)
            
            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error("set_cache_error", key=key, error=str(e))
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        try:
            self._ensure_connected()
            return await self._client.get(key)
            
        except Exception as e:
            logger.error("get_cache_error", key=key, error=str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            self._ensure_connected()
            await self._client.delete(key)
            return True
            
        except Exception as e:
            logger.error("delete_cache_error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            self._ensure_connected()
            return await self._client.exists(key) > 0
            
        except Exception as e:
            logger.error("exists_cache_error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            self._ensure_connected()
            return await self._client.expire(key, ttl)
            
        except Exception as e:
            logger.error("expire_cache_error", key=key, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        try:
            self._ensure_connected()
            return await self._client.ttl(key)
            
        except Exception as e:
            logger.error("ttl_cache_error", key=key, error=str(e))
            return -2
    
    # ==================== 批量操作 ====================
    
    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        """
        批量获取缓存值
        
        Args:
            keys: 缓存键列表
            
        Returns:
            缓存值列表
        """
        try:
            self._ensure_connected()
            return await self._client.mget(keys)
            
        except Exception as e:
            logger.error("mget_cache_error", error=str(e))
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any]) -> bool:
        """
        批量设置缓存值
        
        Args:
            mapping: 键值对字典
            
        Returns:
            是否设置成功
        """
        try:
            self._ensure_connected()
            
            # 序列化值
            serialized = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized[key] = json.dumps(value, ensure_ascii=False, default=str)
                elif not isinstance(value, str):
                    serialized[key] = str(value)
                else:
                    serialized[key] = value
            
            await self._client.mset(serialized)
            return True
            
        except Exception as e:
            logger.error("mset_cache_error", error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存
        
        Args:
            pattern: 键模式（支持通配符*）
            
        Returns:
            删除的键数量
        """
        try:
            self._ensure_connected()
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._client.delete(*keys)
                logger.info("pattern_deleted", pattern=pattern, count=len(keys))
                return len(keys)
            
            return 0
            
        except Exception as e:
            logger.error("delete_pattern_error", pattern=pattern, error=str(e))
            return 0
    
    # ==================== 统计和监控 ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取Redis统计信息
        
        Returns:
            统计信息字典
        """
        try:
            self._ensure_connected()
            info = await self._client.info()
            
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error("get_stats_error", error=str(e))
            return {"connected": False, "error": str(e)}
    
    async def ping(self) -> bool:
        """
        测试Redis连接
        
        Returns:
            是否连接正常
        """
        try:
            self._ensure_connected()
            await self._client.ping()
            return True
            
        except Exception as e:
            logger.error("ping_error", error=str(e))
            return False
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._client is not None


# 全局缓存管理器实例（可选）
_cache_manager: Optional[RedisCacheManager] = None


async def get_cache_manager(config: Optional[RedisConfig] = None) -> RedisCacheManager:
    """
    获取全局缓存管理器实例
    
    Args:
        config: Redis配置，首次调用时必须提供
        
    Returns:
        RedisCacheManager实例
    """
    global _cache_manager
    
    if _cache_manager is None:
        if config is None:
            raise ValueError("首次调用必须提供Redis配置")
        _cache_manager = RedisCacheManager(config)
        await _cache_manager.initialize()
    
    return _cache_manager
