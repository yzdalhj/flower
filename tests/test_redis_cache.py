"""Redis缓存管理器测试"""
import asyncio
import json
from datetime import datetime

import pytest

from src.config.manager import RedisConfig
from src.storage.redis_cache import RedisCacheManager


@pytest.fixture
async def redis_config():
    """Redis配置fixture"""
    return RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        password=None
    )


@pytest.fixture
async def cache_manager(redis_config):
    """缓存管理器fixture"""
    manager = RedisCacheManager(redis_config)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_redis_initialization(redis_config):
    """测试Redis初始化"""
    manager = RedisCacheManager(redis_config)
    
    # 测试初始化
    result = await manager.initialize()
    assert result is True
    assert manager.is_connected is True
    
    # 测试ping
    ping_result = await manager.ping()
    assert ping_result is True
    
    await manager.close()


@pytest.mark.asyncio
async def test_session_state_operations(cache_manager):
    """测试会话状态操作"""
    session_id = "test_session_123"
    state = {
        "user_id": "user_001",
        "platform": "wechat",
        "last_message_time": datetime.now().isoformat(),
        "message_count": 5
    }
    
    # 设置会话状态
    result = await cache_manager.set_session_state(session_id, state, ttl=60)
    assert result is True
    
    # 获取会话状态
    retrieved_state = await cache_manager.get_session_state(session_id)
    assert retrieved_state is not None
    assert retrieved_state["user_id"] == state["user_id"]
    assert retrieved_state["platform"] == state["platform"]
    assert retrieved_state["message_count"] == state["message_count"]
    
    # 删除会话状态
    delete_result = await cache_manager.delete_session_state(session_id)
    assert delete_result is True
    
    # 验证已删除
    retrieved_state = await cache_manager.get_session_state(session_id)
    assert retrieved_state is None


@pytest.mark.asyncio
async def test_conversation_context_operations(cache_manager):
    """测试对话上下文操作"""
    user_id = "user_001"
    messages = [
        {
            "id": "msg_1",
            "content": "你好",
            "timestamp": datetime.now().isoformat(),
            "sender": "user"
        },
        {
            "id": "msg_2",
            "content": "你好！有什么可以帮你的吗？",
            "timestamp": datetime.now().isoformat(),
            "sender": "bot"
        }
    ]
    
    # 缓存对话上下文
    result = await cache_manager.cache_conversation_context(user_id, messages, ttl=120)
    assert result is True
    
    # 获取对话上下文
    retrieved_messages = await cache_manager.get_conversation_context(user_id)
    assert retrieved_messages is not None
    assert len(retrieved_messages) == 2
    assert retrieved_messages[0]["content"] == "你好"
    assert retrieved_messages[1]["sender"] == "bot"
    
    # 使缓存失效
    invalidate_result = await cache_manager.invalidate_conversation_context(user_id)
    assert invalidate_result is True
    
    # 验证已失效
    retrieved_messages = await cache_manager.get_conversation_context(user_id)
    assert retrieved_messages is None


@pytest.mark.asyncio
async def test_emotion_state_operations(cache_manager):
    """测试情绪状态操作"""
    user_id = "user_001"
    emotion_state = {
        "emotion_type": "happy",
        "intensity": 7.5,
        "timestamp": datetime.now().isoformat(),
        "trigger": "用户表达感谢"
    }
    
    # 缓存情绪状态
    result = await cache_manager.cache_emotion_state(user_id, emotion_state, ttl=300)
    assert result is True
    
    # 获取情绪状态
    retrieved_emotion = await cache_manager.get_emotion_state(user_id)
    assert retrieved_emotion is not None
    assert retrieved_emotion["emotion_type"] == "happy"
    assert retrieved_emotion["intensity"] == 7.5
    assert retrieved_emotion["trigger"] == "用户表达感谢"


@pytest.mark.asyncio
async def test_generic_cache_operations(cache_manager):
    """测试通用缓存操作"""
    # 测试字符串值
    await cache_manager.set("test_key_1", "test_value", ttl=60)
    value = await cache_manager.get("test_key_1")
    assert value == "test_value"
    
    # 测试字典值
    dict_value = {"name": "小花", "age": 18}
    await cache_manager.set("test_key_2", dict_value, ttl=60)
    retrieved = await cache_manager.get("test_key_2")
    assert retrieved is not None
    parsed = json.loads(retrieved)
    assert parsed["name"] == "小花"
    
    # 测试exists
    exists = await cache_manager.exists("test_key_1")
    assert exists is True
    
    # 测试ttl
    ttl = await cache_manager.ttl("test_key_1")
    assert ttl > 0 and ttl <= 60
    
    # 测试delete
    await cache_manager.delete("test_key_1")
    exists = await cache_manager.exists("test_key_1")
    assert exists is False


@pytest.mark.asyncio
async def test_batch_operations(cache_manager):
    """测试批量操作"""
    # 批量设置
    mapping = {
        "batch_key_1": "value1",
        "batch_key_2": "value2",
        "batch_key_3": {"data": "value3"}
    }
    result = await cache_manager.mset(mapping)
    assert result is True
    
    # 批量获取
    keys = ["batch_key_1", "batch_key_2", "batch_key_3"]
    values = await cache_manager.mget(keys)
    assert len(values) == 3
    assert values[0] == "value1"
    assert values[1] == "value2"
    
    # 清理
    for key in keys:
        await cache_manager.delete(key)


@pytest.mark.asyncio
async def test_pattern_deletion(cache_manager):
    """测试模式删除"""
    # 创建多个测试键
    await cache_manager.set("pattern_test:1", "value1")
    await cache_manager.set("pattern_test:2", "value2")
    await cache_manager.set("pattern_test:3", "value3")
    await cache_manager.set("other_key", "other_value")
    
    # 删除匹配模式的键
    count = await cache_manager.delete_pattern("pattern_test:*")
    assert count == 3
    
    # 验证其他键未被删除
    exists = await cache_manager.exists("other_key")
    assert exists is True
    
    # 清理
    await cache_manager.delete("other_key")


@pytest.mark.asyncio
async def test_expire_operations(cache_manager):
    """测试过期时间操作"""
    # 设置无过期时间的键
    await cache_manager.set("expire_test", "value")
    
    # 设置过期时间
    result = await cache_manager.expire("expire_test", 10)
    assert result is True
    
    # 检查TTL
    ttl = await cache_manager.ttl("expire_test")
    assert ttl > 0 and ttl <= 10
    
    # 清理
    await cache_manager.delete("expire_test")


@pytest.mark.asyncio
async def test_stats(cache_manager):
    """测试统计信息"""
    stats = await cache_manager.get_stats()
    
    assert stats is not None
    assert stats["connected"] is True
    assert "used_memory" in stats
    assert "connected_clients" in stats
    assert "total_commands_processed" in stats


@pytest.mark.asyncio
async def test_cache_performance(cache_manager):
    """测试缓存性能（满足需求9.2：1秒内返回）"""
    import time
    
    user_id = "perf_test_user"
    messages = [
        {
            "id": f"msg_{i}",
            "content": f"测试消息 {i}",
            "timestamp": datetime.now().isoformat()
        }
        for i in range(20)  # 20条消息
    ]
    
    # 测试写入性能
    start_time = time.time()
    await cache_manager.cache_conversation_context(user_id, messages)
    write_time = time.time() - start_time
    
    # 测试读取性能
    start_time = time.time()
    retrieved = await cache_manager.get_conversation_context(user_id)
    read_time = time.time() - start_time
    
    # 验证性能要求（应该远小于1秒）
    assert write_time < 0.1, f"写入时间过长: {write_time}秒"
    assert read_time < 0.1, f"读取时间过长: {read_time}秒"
    assert len(retrieved) == 20
    
    # 清理
    await cache_manager.invalidate_conversation_context(user_id)


@pytest.mark.asyncio
async def test_concurrent_operations(cache_manager):
    """测试并发操作"""
    async def set_and_get(index: int):
        key = f"concurrent_test_{index}"
        value = f"value_{index}"
        
        await cache_manager.set(key, value, ttl=60)
        retrieved = await cache_manager.get(key)
        await cache_manager.delete(key)
        
        return retrieved == value
    
    # 并发执行10个操作
    tasks = [set_and_get(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    # 验证所有操作都成功
    assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
