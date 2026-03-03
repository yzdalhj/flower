"""缓存与数据库集成示例"""
from datetime import datetime
from typing import List, Optional

from src.storage.database import DatabaseManager
from src.storage.redis_cache import RedisCacheManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CachedMemoryManager:
    """
    带缓存的记忆管理器示例
    
    展示如何结合Redis缓存和数据库实现高性能的数据访问
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        cache_manager: RedisCacheManager
    ):
        """
        初始化缓存记忆管理器
        
        Args:
            db_manager: 数据库管理器
            cache_manager: 缓存管理器
        """
        self.db = db_manager
        self.cache = cache_manager
    
    async def get_conversation_context(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[dict]:
        """
        获取对话上下文（先查缓存，缓存未命中则查数据库）
        
        Args:
            user_id: 用户ID
            limit: 返回消息数量限制
            
        Returns:
            消息列表
        """
        # 1. 尝试从缓存获取
        cached_messages = await self.cache.get_conversation_context(user_id)
        
        if cached_messages is not None:
            logger.debug("cache_hit", user_id=user_id, count=len(cached_messages))
            return cached_messages[:limit]
        
        # 2. 缓存未命中，从数据库查询
        logger.debug("cache_miss", user_id=user_id)
        
        query = """
            SELECT id, user_id, platform, message_type, content, timestamp, metadata
            FROM conversations
            WHERE user_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        
        rows = await self.db.fetch(query, user_id, limit)
        
        # 3. 转换为字典列表
        messages = []
        for row in rows:
            messages.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "platform": row["platform"],
                "message_type": row["message_type"],
                "content": row["content"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                "metadata": row["metadata"]
            })
        
        # 4. 缓存查询结果
        if messages:
            await self.cache.cache_conversation_context(user_id, messages)
            logger.debug("context_cached", user_id=user_id, count=len(messages))
        
        return messages
    
    async def store_message(
        self,
        user_id: str,
        platform: str,
        message_type: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        存储消息（同时更新数据库和缓存）
        
        Args:
            user_id: 用户ID
            platform: 平台类型
            message_type: 消息类型
            content: 消息内容
            metadata: 元数据
            
        Returns:
            是否存储成功
        """
        import uuid
        
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # 1. 存储到数据库
        query = """
            INSERT INTO conversations (id, user_id, platform, message_type, content, timestamp, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        try:
            await self.db.execute(
                query,
                message_id,
                user_id,
                platform,
                message_type,
                content,
                timestamp,
                metadata
            )
            
            # 2. 使缓存失效，下次查询时会重新加载
            await self.cache.invalidate_conversation_context(user_id)
            
            logger.info(
                "message_stored",
                message_id=message_id,
                user_id=user_id,
                platform=platform
            )
            
            return True
            
        except Exception as e:
            logger.error("store_message_error", user_id=user_id, error=str(e))
            return False
    
    async def get_emotion_state(self, user_id: str) -> Optional[dict]:
        """
        获取用户情绪状态（先查缓存，缓存未命中则查数据库）
        
        Args:
            user_id: 用户ID
            
        Returns:
            情绪状态数据
        """
        # 1. 尝试从缓存获取
        cached_emotion = await self.cache.get_emotion_state(user_id)
        
        if cached_emotion is not None:
            logger.debug("emotion_cache_hit", user_id=user_id)
            return cached_emotion
        
        # 2. 缓存未命中，从数据库查询最新情绪状态
        logger.debug("emotion_cache_miss", user_id=user_id)
        
        query = """
            SELECT emotion_type, intensity, trigger_reason, timestamp
            FROM emotion_history
            WHERE user_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        row = await self.db.fetchrow(query, user_id)
        
        if not row:
            return None
        
        emotion_state = {
            "emotion_type": row["emotion_type"],
            "intensity": float(row["intensity"]),
            "trigger": row["trigger_reason"],
            "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None
        }
        
        # 3. 缓存查询结果
        await self.cache.cache_emotion_state(user_id, emotion_state)
        logger.debug("emotion_cached", user_id=user_id)
        
        return emotion_state
    
    async def update_emotion_state(
        self,
        user_id: str,
        emotion_type: str,
        intensity: float,
        trigger_reason: Optional[str] = None
    ) -> bool:
        """
        更新用户情绪状态（同时更新数据库和缓存）
        
        Args:
            user_id: 用户ID
            emotion_type: 情绪类型
            intensity: 情绪强度
            trigger_reason: 触发原因
            
        Returns:
            是否更新成功
        """
        import uuid
        
        emotion_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # 1. 存储到数据库
        query = """
            INSERT INTO emotion_history (id, user_id, emotion_type, intensity, trigger_reason, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        try:
            await self.db.execute(
                query,
                emotion_id,
                user_id,
                emotion_type,
                intensity,
                trigger_reason,
                timestamp
            )
            
            # 2. 更新缓存
            emotion_state = {
                "emotion_type": emotion_type,
                "intensity": intensity,
                "trigger": trigger_reason,
                "timestamp": timestamp.isoformat()
            }
            
            await self.cache.cache_emotion_state(user_id, emotion_state)
            
            logger.info(
                "emotion_updated",
                user_id=user_id,
                emotion_type=emotion_type,
                intensity=intensity
            )
            
            return True
            
        except Exception as e:
            logger.error("update_emotion_error", user_id=user_id, error=str(e))
            return False


# 使用示例
async def example_usage():
    """使用示例"""
    from src.config.manager import ConfigurationManager, DatabaseConfig, RedisConfig
    
    # 初始化配置
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="ai_companion_bot",
        username="postgres",
        password="your_password"
    )
    
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0
    )
    
    # 初始化管理器
    db_manager = DatabaseManager(db_config)
    await db_manager.initialize()
    
    cache_manager = RedisCacheManager(redis_config)
    await cache_manager.initialize()
    
    # 创建集成管理器
    memory_manager = CachedMemoryManager(db_manager, cache_manager)
    
    # 存储消息
    await memory_manager.store_message(
        user_id="user_001",
        platform="wechat",
        message_type="text",
        content="你好，小花！"
    )
    
    # 获取对话上下文（第一次从数据库，后续从缓存）
    context = await memory_manager.get_conversation_context("user_001", limit=20)
    print(f"获取到 {len(context)} 条消息")
    
    # 更新情绪状态
    await memory_manager.update_emotion_state(
        user_id="user_001",
        emotion_type="happy",
        intensity=8.0,
        trigger_reason="用户友好问候"
    )
    
    # 获取情绪状态（第一次从数据库，后续从缓存）
    emotion = await memory_manager.get_emotion_state("user_001")
    print(f"当前情绪: {emotion}")
    
    # 清理
    await cache_manager.close()
    await db_manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
