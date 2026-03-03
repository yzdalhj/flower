# Redis缓存层实现文档

## 概述

Redis缓存层为小花AI伴侣机器人提供高性能的数据缓存能力，满足需求9.2中"1秒内返回对话历史"的性能要求。通过Redis缓存热数据，显著减少数据库查询压力，提升系统响应速度。

## 架构设计

### 缓存策略

采用**Cache-Aside（旁路缓存）**模式：

1. **读取流程**：
   - 先查询Redis缓存
   - 缓存命中：直接返回数据
   - 缓存未命中：查询数据库，并将结果写入缓存

2. **写入流程**：
   - 先写入数据库
   - 使相关缓存失效（或更新缓存）
   - 下次读取时重新加载

### 缓存数据类型

#### 1. 会话状态缓存 (Session State)
- **键格式**: `session:{session_id}`
- **数据内容**: 客户端会话状态、连接信息
- **过期时间**: 1小时（可配置）
- **用途**: 快速获取会话状态，避免频繁查询数据库

#### 2. 对话上下文缓存 (Conversation Context)
- **键格式**: `context:{user_id}`
- **数据内容**: 用户最近的对话消息列表（通常20条）
- **过期时间**: 30分钟（可配置）
- **用途**: 快速检索对话历史，满足1秒内返回的性能要求

#### 3. 情绪状态缓存 (Emotion State)
- **键格式**: `emotion:{user_id}`
- **数据内容**: 用户当前情绪状态
- **过期时间**: 24小时（可配置）
- **用途**: 快速获取用户情绪，支持情绪系统

#### 4. 用户状态缓存 (User State)
- **键格式**: `user_state:{user_id}`
- **数据内容**: 用户性格配置、角色设定等
- **过期时间**: 根据需要配置
- **用途**: 减少配置查询次数

## 核心功能

### RedisCacheManager 类

主要的Redis缓存管理器，提供以下功能：

#### 初始化和连接管理
```python
from src.config.manager import RedisConfig
from src.storage.redis_cache import RedisCacheManager

# 创建配置
config = RedisConfig(
    host="localhost",
    port=6379,
    db=0,
    password=None
)

# 初始化管理器
cache_manager = RedisCacheManager(config)
await cache_manager.initialize()

# 测试连接
is_connected = await cache_manager.ping()

# 关闭连接
await cache_manager.close()
```

#### 会话状态操作
```python
# 设置会话状态
session_state = {
    "user_id": "user_001",
    "platform": "wechat",
    "last_message_time": "2024-01-01T12:00:00",
    "message_count": 5
}
await cache_manager.set_session_state("session_123", session_state, ttl=3600)

# 获取会话状态
state = await cache_manager.get_session_state("session_123")

# 删除会话状态
await cache_manager.delete_session_state("session_123")
```

#### 对话上下文操作
```python
# 缓存对话上下文
messages = [
    {"id": "msg_1", "content": "你好", "timestamp": "2024-01-01T12:00:00"},
    {"id": "msg_2", "content": "你好！", "timestamp": "2024-01-01T12:00:05"}
]
await cache_manager.cache_conversation_context("user_001", messages, ttl=1800)

# 获取对话上下文
context = await cache_manager.get_conversation_context("user_001")

# 使缓存失效
await cache_manager.invalidate_conversation_context("user_001")
```

#### 情绪状态操作
```python
# 缓存情绪状态
emotion_state = {
    "emotion_type": "happy",
    "intensity": 7.5,
    "timestamp": "2024-01-01T12:00:00",
    "trigger": "用户表达感谢"
}
await cache_manager.cache_emotion_state("user_001", emotion_state, ttl=86400)

# 获取情绪状态
emotion = await cache_manager.get_emotion_state("user_001")
```

#### 通用缓存操作
```python
# 设置缓存
await cache_manager.set("my_key", "my_value", ttl=60)
await cache_manager.set("my_dict", {"name": "小花", "age": 18}, ttl=60)

# 获取缓存
value = await cache_manager.get("my_key")

# 检查存在
exists = await cache_manager.exists("my_key")

# 获取TTL
ttl = await cache_manager.ttl("my_key")

# 设置过期时间
await cache_manager.expire("my_key", 120)

# 删除缓存
await cache_manager.delete("my_key")
```

#### 批量操作
```python
# 批量设置
mapping = {
    "key1": "value1",
    "key2": "value2",
    "key3": {"data": "value3"}
}
await cache_manager.mset(mapping)

# 批量获取
keys = ["key1", "key2", "key3"]
values = await cache_manager.mget(keys)

# 模式删除
count = await cache_manager.delete_pattern("session:*")
```

#### 统计和监控
```python
# 获取统计信息
stats = await cache_manager.get_stats()
print(f"已用内存: {stats['used_memory']}")
print(f"连接客户端数: {stats['connected_clients']}")
print(f"命中次数: {stats['keyspace_hits']}")
print(f"未命中次数: {stats['keyspace_misses']}")
```

## 与数据库集成

### CachedMemoryManager 示例

`cache_integration.py` 提供了一个完整的集成示例，展示如何结合Redis缓存和PostgreSQL数据库：

```python
from src.storage.cache_integration import CachedMemoryManager

# 创建集成管理器
memory_manager = CachedMemoryManager(db_manager, cache_manager)

# 获取对话上下文（自动处理缓存）
context = await memory_manager.get_conversation_context("user_001", limit=20)

# 存储消息（自动更新缓存）
await memory_manager.store_message(
    user_id="user_001",
    platform="wechat",
    message_type="text",
    content="你好，小花！"
)

# 获取情绪状态（自动处理缓存）
emotion = await memory_manager.get_emotion_state("user_001")

# 更新情绪状态（自动更新缓存）
await memory_manager.update_emotion_state(
    user_id="user_001",
    emotion_type="happy",
    intensity=8.0,
    trigger_reason="用户友好问候"
)
```

## 性能优化

### 1. 连接池配置
Redis客户端使用连接池，自动管理连接复用：
- 支持健康检查（每30秒）
- 自动重连机制
- 连接超时设置（5秒）

### 2. 数据序列化
- 使用JSON序列化复杂数据结构
- 自动处理datetime等特殊类型
- 支持中文（ensure_ascii=False）

### 3. 过期策略
- 会话状态：1小时
- 对话上下文：30分钟
- 情绪状态：24小时
- 可根据实际需求调整

### 4. 缓存失效策略
- 写入数据时主动失效相关缓存
- 避免缓存与数据库不一致
- 支持模式匹配批量失效

## 配置说明

### config.yaml 配置
```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null  # 如果Redis设置了密码，在此填写
```

### 环境变量配置
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## 测试

### 运行测试
```bash
# 确保Redis服务运行中
redis-server

# 运行测试
pytest tests/test_redis_cache.py -v
```

### 测试覆盖
- ✅ Redis初始化和连接
- ✅ 会话状态操作
- ✅ 对话上下文操作
- ✅ 情绪状态操作
- ✅ 通用缓存操作
- ✅ 批量操作
- ✅ 模式删除
- ✅ 过期时间操作
- ✅ 性能测试（满足1秒内返回要求）
- ✅ 并发操作测试

## 性能指标

根据测试结果：
- **写入性能**: < 100ms（20条消息）
- **读取性能**: < 100ms（20条消息）
- **并发支持**: 10+并发操作无问题
- **满足需求**: ✅ 远超需求9.2的1秒内返回要求

## 故障处理

### 常见问题

#### 1. 无法连接Redis
```
错误: redis_initialization_error
解决: 
- 检查Redis服务是否运行: redis-cli ping
- 验证配置中的host和port
- 检查防火墙设置
```

#### 2. 连接超时
```
错误: socket_connect_timeout
解决:
- 增加连接超时时间
- 检查网络连接
- 验证Redis服务状态
```

#### 3. 内存不足
```
错误: OOM command not allowed
解决:
- 增加Redis最大内存配置
- 调整过期策略
- 清理不必要的缓存
```

### 监控建议

1. **定期检查统计信息**
   ```python
   stats = await cache_manager.get_stats()
   # 监控内存使用、命中率等
   ```

2. **设置告警**
   - 内存使用超过80%
   - 命中率低于50%
   - 连接数异常增长

3. **日志记录**
   - 所有缓存操作都有日志记录
   - 使用structlog结构化日志
   - 便于问题排查

## 最佳实践

### 1. 合理设置TTL
- 根据数据更新频率设置过期时间
- 避免缓存过期导致的雪崩效应
- 考虑使用随机TTL避免同时过期

### 2. 缓存预热
- 系统启动时预加载热数据
- 避免冷启动时大量缓存未命中

### 3. 缓存降级
- 当Redis不可用时，直接查询数据库
- 记录降级事件，便于监控

### 4. 数据一致性
- 写入数据库后立即失效缓存
- 避免使用更新缓存策略（容易不一致）

### 5. 键命名规范
- 使用有意义的前缀
- 包含版本号便于升级
- 避免过长的键名

## 未来扩展

### 1. 分布式缓存
- 支持Redis Cluster
- 实现缓存分片

### 2. 缓存预热
- 自动识别热数据
- 定期预加载

### 3. 缓存统计
- 详细的命中率统计
- 性能分析报告

### 4. 智能过期
- 基于访问频率动态调整TTL
- LRU策略优化

## 相关文档

- [数据库设计文档](./README.md)
- [系统架构设计](../../.kiro/specs/ai-companion-bot/design.md)
- [需求文档](../../.kiro/specs/ai-companion-bot/requirements.md)

## 维护者

- 开发团队
- 最后更新: 2024-01-01
