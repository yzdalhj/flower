"""记忆系统测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.memory_store import MemoryStore


@pytest.mark.asyncio
async def test_create_memory(db_session: AsyncSession):
    """测试创建记忆"""
    store = MemoryStore(db_session)

    memory = await store.create_memory(
        user_id="user_123",
        memory_type="episodic",
        content="用户今天生日",
        summary="生日",
        importance=8.0,
    )

    assert memory.id is not None
    assert memory.user_id == "user_123"
    assert memory.memory_type == "episodic"
    assert memory.content == "用户今天生日"
    assert memory.importance == 8.0


@pytest.mark.asyncio
async def test_get_user_memories(db_session: AsyncSession):
    """测试获取用户记忆"""
    store = MemoryStore(db_session)

    # 创建多条记忆
    await store.create_memory(
        user_id="user_123",
        memory_type="preference",
        content="用户喜欢猫",
        importance=7.0,
    )
    await store.create_memory(
        user_id="user_123",
        memory_type="semantic",
        content="用户住在上海",
        importance=6.0,
    )

    memories = await store.get_user_memories("user_123")

    assert len(memories) == 2
    assert all(m.user_id == "user_123" for m in memories)


@pytest.mark.asyncio
async def test_get_important_memories(db_session: AsyncSession):
    """测试获取重要记忆"""
    store = MemoryStore(db_session)

    await store.create_memory(
        user_id="user_123",
        memory_type="emotional",
        content="用户失去了亲人",
        importance=9.5,
    )
    await store.create_memory(
        user_id="user_123",
        memory_type="preference",
        content="用户喜欢咖啡",
        importance=3.0,
    )

    important = await store.get_important_memories("user_123", min_importance=7.0)

    assert len(important) == 1
    assert important[0].importance == 9.5


@pytest.mark.asyncio
async def test_working_memory(db_session: AsyncSession):
    """测试工作记忆"""
    store = MemoryStore(db_session)

    # 更新工作记忆
    wm = await store.update_working_memory(
        user_id="user_123",
        conversation_id="conv_456",
        context=[{"role": "user", "content": "你好"}],
        current_topic="问候",
    )

    assert wm.user_id == "user_123"
    assert wm.conversation_id == "conv_456"
    assert wm.current_topic == "问候"

    # 获取工作记忆
    retrieved = await store.get_working_memory("user_123")
    assert retrieved is not None
    assert retrieved.conversation_id == "conv_456"

    # 清除工作记忆
    cleared = await store.clear_working_memory("user_123")
    assert cleared is True

    # 确认已清除
    retrieved = await store.get_working_memory("user_123")
    assert retrieved is None


@pytest.mark.asyncio
async def test_memory_access_count(db_session: AsyncSession):
    """测试记忆访问统计"""
    store = MemoryStore(db_session)

    memory = await store.create_memory(
        user_id="user_123",
        memory_type="episodic",
        content="测试记忆",
        importance=5.0,
    )

    assert memory.access_count == 0

    # 更新访问
    await store.update_memory_access(memory.id)

    # 重新获取
    updated = await store.get_memory(memory.id)
    assert updated.access_count == 1
    assert updated.last_accessed_at is not None
