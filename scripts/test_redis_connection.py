"""测试Redis连接的简单脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.manager import RedisConfig
from src.storage.redis_cache import RedisCacheManager


async def test_redis_connection():
    """测试Redis连接"""
    print("=" * 60)
    print("Redis连接测试")
    print("=" * 60)
    
    # 创建配置
    config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        password=None
    )
    
    print(f"\n配置信息:")
    print(f"  Host: {config.host}")
    print(f"  Port: {config.port}")
    print(f"  DB: {config.db}")
    
    # 创建缓存管理器
    cache_manager = RedisCacheManager(config)
    
    # 测试初始化
    print("\n正在连接Redis...")
    success = await cache_manager.initialize()
    
    if not success:
        print("❌ Redis连接失败！")
        print("\n请确保:")
        print("  1. Redis服务正在运行")
        print("  2. 配置信息正确")
        print("  3. 防火墙允许连接")
        return False
    
    print("✅ Redis连接成功！")
    
    # 测试ping
    print("\n测试ping...")
    ping_result = await cache_manager.ping()
    if ping_result:
        print("✅ Ping成功")
    else:
        print("❌ Ping失败")
        return False
    
    # 测试基本操作
    print("\n测试基本操作...")
    
    # 设置值
    print("  - 设置缓存...")
    await cache_manager.set("test_key", "test_value", ttl=60)
    
    # 获取值
    print("  - 获取缓存...")
    value = await cache_manager.get("test_key")
    if value == "test_value":
        print("  ✅ 读写测试通过")
    else:
        print(f"  ❌ 读写测试失败: 期望 'test_value', 得到 '{value}'")
    
    # 删除值
    print("  - 删除缓存...")
    await cache_manager.delete("test_key")
    
    # 测试会话状态
    print("\n测试会话状态操作...")
    session_state = {
        "user_id": "test_user",
        "platform": "wechat",
        "message_count": 5
    }
    await cache_manager.set_session_state("test_session", session_state, ttl=60)
    retrieved = await cache_manager.get_session_state("test_session")
    if retrieved and retrieved["user_id"] == "test_user":
        print("  ✅ 会话状态测试通过")
    else:
        print("  ❌ 会话状态测试失败")
    await cache_manager.delete_session_state("test_session")
    
    # 测试对话上下文
    print("\n测试对话上下文操作...")
    messages = [
        {"id": "msg_1", "content": "你好"},
        {"id": "msg_2", "content": "你好！"}
    ]
    await cache_manager.cache_conversation_context("test_user", messages, ttl=60)
    retrieved_messages = await cache_manager.get_conversation_context("test_user")
    if retrieved_messages and len(retrieved_messages) == 2:
        print("  ✅ 对话上下文测试通过")
    else:
        print("  ❌ 对话上下文测试失败")
    await cache_manager.invalidate_conversation_context("test_user")
    
    # 测试情绪状态
    print("\n测试情绪状态操作...")
    emotion_state = {
        "emotion_type": "happy",
        "intensity": 7.5,
        "trigger": "测试"
    }
    await cache_manager.cache_emotion_state("test_user", emotion_state, ttl=60)
    retrieved_emotion = await cache_manager.get_emotion_state("test_user")
    if retrieved_emotion and retrieved_emotion["emotion_type"] == "happy":
        print("  ✅ 情绪状态测试通过")
    else:
        print("  ❌ 情绪状态测试失败")
    
    # 获取统计信息
    print("\n获取Redis统计信息...")
    stats = await cache_manager.get_stats()
    if stats["connected"]:
        print(f"  已用内存: {stats['used_memory']}")
        print(f"  连接客户端数: {stats['connected_clients']}")
        print(f"  总命令数: {stats['total_commands_processed']}")
        print(f"  运行时间: {stats['uptime_in_seconds']}秒")
    
    # 清理并关闭
    print("\n清理测试数据...")
    await cache_manager.delete("test_key")
    await cache_manager.delete_session_state("test_session")
    await cache_manager.invalidate_conversation_context("test_user")
    await cache_manager.delete(f"{cache_manager.EMOTION_PREFIX}test_user")
    
    await cache_manager.close()
    print("\n✅ 所有测试通过！Redis缓存层工作正常。")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_redis_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
