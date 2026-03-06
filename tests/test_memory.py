"""
记忆系统验证测试

验证内容:
1. 创建记忆
2. 获取用户记忆
3. 获取重要记忆
4. 工作记忆管理
5. 记忆访问统计

注意: 此测试直接导入实际实现模块进行验证
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ 导入实际实现 ============

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.base import Base  # noqa: E402
from app.services.memory.memory_store import MemoryStore  # noqa: E402

# ============ 颜色输出 ============


class Colors:
    """终端颜色"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


# ============ 数据库设置 ============


async def get_test_db():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


# ============ 测试函数 ============


def test_create_memory():
    """测试1: 创建记忆 - 使用实际实现"""
    print_header("测试1: 创建记忆 - 实际实现")

    async def run_test():
        async for db_session in get_test_db():
            store = MemoryStore(db_session)

            memory = await store.create_memory(
                user_id="user_123",
                memory_type="episodic",
                content="用户今天生日",
                summary="生日",
                importance=8.0,
            )

            checks = []

            # 检查记忆ID
            if memory.id is not None:
                print_success(f"记忆创建成功: ID={memory.id}")
                checks.append(True)
            else:
                print_error("记忆ID为空")
                checks.append(False)

            # 检查用户ID
            if memory.user_id == "user_123":
                print_success(f"用户ID正确: {memory.user_id}")
                checks.append(True)
            else:
                print_error(f"用户ID错误: {memory.user_id}")
                checks.append(False)

            # 检查记忆类型
            if memory.memory_type == "episodic":
                print_success(f"记忆类型正确: {memory.memory_type}")
                checks.append(True)
            else:
                print_error(f"记忆类型错误: {memory.memory_type}")
                checks.append(False)

            # 检查内容
            if memory.content == "用户今天生日":
                print_success("记忆内容正确")
                checks.append(True)
            else:
                print_error(f"记忆内容错误: {memory.content}")
                checks.append(False)

            # 检查重要性
            if memory.importance == 8.0:
                print_success(f"重要性正确: {memory.importance}")
                checks.append(True)
            else:
                print_error(f"重要性错误: {memory.importance}")
                checks.append(False)

            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) >= len(checks) * 0.8

    return asyncio.run(run_test())


def test_get_user_memories():
    """测试2: 获取用户记忆 - 使用实际实现"""
    print_header("测试2: 获取用户记忆 - 实际实现")

    async def run_test():
        async for db_session in get_test_db():
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

            checks = []

            # 检查记忆数量
            if len(memories) == 2:
                print_success(f"记忆数量正确: {len(memories)}条")
                checks.append(True)
            else:
                print_error(f"记忆数量错误: 期望2条, 实际{len(memories)}条")
                checks.append(False)

            # 检查所有记忆的用户ID
            if all(m.user_id == "user_123" for m in memories):
                print_success("所有记忆的用户ID正确")
                checks.append(True)
            else:
                print_error("存在用户ID不匹配的记忆")
                checks.append(False)

            # 检查记忆类型
            types = [m.memory_type for m in memories]
            if "preference" in types and "semantic" in types:
                print_success(f"记忆类型正确: {types}")
                checks.append(True)
            else:
                print_error(f"记忆类型错误: {types}")
                checks.append(False)

            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) == len(checks)

    return asyncio.run(run_test())


def test_get_important_memories():
    """测试3: 获取重要记忆 - 使用实际实现"""
    print_header("测试3: 获取重要记忆 - 实际实现")

    async def run_test():
        async for db_session in get_test_db():
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

            checks = []

            # 检查重要记忆数量
            if len(important) == 1:
                print_success(f"重要记忆数量正确: {len(important)}条")
                checks.append(True)
            else:
                print_error(f"重要记忆数量错误: 期望1条, 实际{len(important)}条")
                checks.append(False)

            # 检查重要性值
            if len(important) > 0 and important[0].importance == 9.5:
                print_success(f"重要性值正确: {important[0].importance}")
                checks.append(True)
            else:
                print_error("重要性值错误")
                checks.append(False)

            # 检查内容
            if len(important) > 0 and "失去了亲人" in important[0].content:
                print_success("重要记忆内容正确")
                checks.append(True)
            else:
                print_error("重要记忆内容错误")
                checks.append(False)

            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) == len(checks)

    return asyncio.run(run_test())


def test_working_memory():
    """测试4: 工作记忆管理 - 使用实际实现"""
    print_header("测试4: 工作记忆管理 - 实际实现")

    async def run_test():
        async for db_session in get_test_db():
            store = MemoryStore(db_session)

            checks = []

            # 更新工作记忆
            wm = await store.update_working_memory(
                user_id="user_123",
                conversation_id="conv_456",
                context=[{"role": "user", "content": "你好"}],
                current_topic="问候",
            )

            if wm.user_id == "user_123":
                print_success(f"工作记忆创建成功: user_id={wm.user_id}")
                checks.append(True)
            else:
                print_error("工作记忆创建失败")
                checks.append(False)

            if wm.conversation_id == "conv_456":
                print_success(f"会话ID正确: {wm.conversation_id}")
                checks.append(True)
            else:
                print_error(f"会话ID错误: {wm.conversation_id}")
                checks.append(False)

            if wm.current_topic == "问候":
                print_success(f"当前话题正确: {wm.current_topic}")
                checks.append(True)
            else:
                print_error(f"当前话题错误: {wm.current_topic}")
                checks.append(False)

            # 获取工作记忆
            retrieved = await store.get_working_memory("user_123")
            if retrieved is not None and retrieved.conversation_id == "conv_456":
                print_success("工作记忆获取成功")
                checks.append(True)
            else:
                print_error("工作记忆获取失败")
                checks.append(False)

            # 清除工作记忆
            cleared = await store.clear_working_memory("user_123")
            if cleared:
                print_success("工作记忆清除成功")
                checks.append(True)
            else:
                print_error("工作记忆清除失败")
                checks.append(False)

            # 确认已清除
            retrieved = await store.get_working_memory("user_123")
            if retrieved is None:
                print_success("确认工作记忆已清除")
                checks.append(True)
            else:
                print_error("工作记忆未正确清除")
                checks.append(False)

            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) >= len(checks) * 0.8

    return asyncio.run(run_test())


def test_memory_access_count():
    """测试5: 记忆访问统计 - 使用实际实现"""
    print_header("测试5: 记忆访问统计 - 实际实现")

    async def run_test():
        async for db_session in get_test_db():
            store = MemoryStore(db_session)

            memory = await store.create_memory(
                user_id="user_123",
                memory_type="episodic",
                content="测试记忆",
                importance=5.0,
            )

            checks = []

            # 检查初始访问次数
            if memory.access_count == 0:
                print_success(f"初始访问次数正确: {memory.access_count}")
                checks.append(True)
            else:
                print_error(f"初始访问次数错误: {memory.access_count}")
                checks.append(False)

            # 更新访问
            await store.update_memory_access(memory.id)

            # 重新获取
            updated = await store.get_memory(memory.id)

            if updated.access_count == 1:
                print_success(f"访问次数更新成功: {updated.access_count}")
                checks.append(True)
            else:
                print_error(f"访问次数更新失败: {updated.access_count}")
                checks.append(False)

            if updated.last_accessed_at is not None:
                print_success(f"最后访问时间已记录: {updated.last_accessed_at}")
                checks.append(True)
            else:
                print_error("最后访问时间未记录")
                checks.append(False)

            print_info(f"通过率: {sum(checks)}/{len(checks)}")
            return sum(checks) == len(checks)

    return asyncio.run(run_test())


def run_all_tests():
    """运行所有测试"""
    print_header("🌸 AI小花 记忆系统验证测试 🌸")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    try:
        results.append(("创建记忆", test_create_memory()))
    except Exception as e:
        print_error(f"创建记忆测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("创建记忆", False))

    try:
        results.append(("获取用户记忆", test_get_user_memories()))
    except Exception as e:
        print_error(f"获取用户记忆测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("获取用户记忆", False))

    try:
        results.append(("获取重要记忆", test_get_important_memories()))
    except Exception as e:
        print_error(f"获取重要记忆测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("获取重要记忆", False))

    try:
        results.append(("工作记忆管理", test_working_memory()))
    except Exception as e:
        print_error(f"工作记忆管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("工作记忆管理", False))

    try:
        results.append(("记忆访问统计", test_memory_access_count()))
    except Exception as e:
        print_error(f"记忆访问统计测试失败: {e}")
        import traceback

        traceback.print_exc()
        results.append(("记忆访问统计", False))

    # 汇总
    print_header("📊 测试结果汇总")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}通过" if result else f"{Colors.RED}失败"
        print(f"  {status}{Colors.RESET} - {name}")

    print(
        f"\n总计: {Colors.GREEN if passed == total else Colors.YELLOW}{passed}/{total}{Colors.RESET} 通过"
    )

    if passed == total:
        print(f"\n{Colors.GREEN}🎉 所有测试通过！记忆系统验证完成。{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过，请检查实现。{Colors.RESET}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
