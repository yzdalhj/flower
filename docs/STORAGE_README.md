# 数据存储层

本目录包含AI小花的数据存储层实现，包括数据库管理、数据加密和数据库初始化功能。

## 文件说明

- `database.py` - 数据库连接管理器，支持PostgreSQL
- `encryption.py` - 数据加密工具类，使用cryptography库
- `init_db.py` - 数据库初始化模块
- `schema.sql` - 数据库模式定义（SQL脚本）

## 数据库模式

系统使用PostgreSQL数据库，包含以下表：

### 核心表

1. **conversations** - 对话记录表
   - 存储所有用户对话消息
   - 支持加密存储敏感内容
   - 索引：user_id + timestamp, platform

2. **emotion_history** - 情绪历史表
   - 记录用户情绪状态变化
   - 索引：user_id + timestamp, emotion_type

3. **personality_profiles** - 性格配置表
   - 存储机器人性格角色配置
   - 索引：name

4. **slang_database** - 网络用语数据库
   - 存储流行网络用语和梗
   - 索引：popularity, last_updated, is_outdated

5. **emoji_library** - 表情包库
   - 存储表情包文件信息
   - 索引：usage_count

6. **role_transitions** - 角色转换记录表
   - 记录动态角色转换历史
   - 索引：user_id + timestamp, scene_type

7. **client_sessions** - 客户端会话表
   - 管理客户端连接会话
   - 索引：platform, status, last_heartbeat

8. **media_cache** - 媒体缓存表
   - 缓存富媒体文件
   - 索引：expires_at, media_type

9. **connection_logs** - 连接日志表
   - 记录连接事件
   - 索引：session_id + timestamp, event_type

## 使用方法

### 1. 配置数据库

在 `config.yaml` 中配置数据库连接信息：

```yaml
database:
  host: localhost
  port: 5432
  database: ai_companion_bot
  username: postgres
  password: your-password
  pool_size: 10
```

或使用环境变量：

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ai_companion_bot
export DB_USER=postgres
export DB_PASSWORD=your-password
```

### 2. 初始化数据库

使用命令行工具初始化数据库：

```bash
# 初始化数据库（保留现有数据）
python -m src.storage.init_db config.yaml

# 重置数据库（删除所有表后重新创建）
python -m src.storage.init_db config.yaml --reset
```

或在代码中使用：

```python
from src.config.manager import ConfigurationManager
from src.storage.init_db import init_database

# 加载配置
config_manager = ConfigurationManager()
config = config_manager.load_config("config.yaml")

# 初始化数据库
success = await init_database(config.database, reset=False)
```

### 3. 使用数据库管理器

```python
from src.storage.database import DatabaseManager
from src.config.manager import DatabaseConfig

# 创建数据库管理器
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="ai_companion_bot",
    username="postgres",
    password="your-password"
)
db_manager = DatabaseManager(config)

# 初始化连接池
await db_manager.initialize()

# 执行查询
result = await db_manager.fetchval("SELECT COUNT(*) FROM conversations")

# 插入数据
await db_manager.execute(
    "INSERT INTO conversations (id, user_id, platform, message_type, content, timestamp) VALUES ($1, $2, $3, $4, $5, $6)",
    conversation_id, user_id, platform, message_type, content, timestamp
)

# 查询多行
rows = await db_manager.fetch(
    "SELECT * FROM conversations WHERE user_id = $1 ORDER BY timestamp DESC LIMIT 20",
    user_id
)

# 关闭连接池
await db_manager.close()
```

### 4. 使用加密管理器

```python
from src.storage.encryption import EncryptionManager

# 创建加密管理器（自动从环境变量读取密钥）
encryption_manager = EncryptionManager()

# 或使用指定密钥
encryption_manager = EncryptionManager(encryption_key="your-base64-key")

# 加密数据
original_text = "敏感对话内容"
encrypted_data = encryption_manager.encrypt(original_text)

# 解密数据
decrypted_text = encryption_manager.decrypt(encrypted_data)

# 生成新密钥
new_key = EncryptionManager.generate_new_key()
print(f"新密钥: {new_key}")

# 从密码生成密钥
key_from_password = EncryptionManager.generate_key_from_password("my-password")
```

### 5. 加密存储对话记录

```python
from src.storage.encryption import EncryptionManager
from src.storage.database import DatabaseManager

encryption_manager = EncryptionManager()
db_manager = DatabaseManager(config)

# 加密对话内容
original_content = "用户的敏感对话"
encrypted_content = encryption_manager.encrypt(original_content)

# 存储到数据库
await db_manager.execute(
    """
    INSERT INTO conversations 
    (id, user_id, platform, message_type, content, encrypted_content, timestamp)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    """,
    conversation_id,
    user_id,
    "wechat",
    "text",
    "[加密]",  # 明文字段存储占位符
    encrypted_content,
    datetime.now()
)

# 读取并解密
row = await db_manager.fetchrow(
    "SELECT * FROM conversations WHERE id = $1",
    conversation_id
)
decrypted_content = encryption_manager.decrypt(bytes(row['encrypted_content']))
```

## 数据加密

系统使用 `cryptography` 库的 Fernet 对称加密算法来加密敏感数据：

- **对话记录**: 存储在 `conversations.encrypted_content` 字段
- **API密钥**: 在配置管理器中加密存储
- **平台凭证**: 在配置管理器中加密存储

### 加密密钥管理

1. **生成密钥**:
   ```python
   from src.storage.encryption import EncryptionManager
   key = EncryptionManager.generate_new_key()
   print(f"请将此密钥保存到环境变量 ENCRYPTION_KEY: {key}")
   ```

2. **设置环境变量**:
   ```bash
   export ENCRYPTION_KEY="your-generated-key"
   ```

3. **或在 .env 文件中**:
   ```
   ENCRYPTION_KEY=your-generated-key
   ```

**重要**: 请妥善保管加密密钥，丢失密钥将无法解密已加密的数据！

## 数据库维护

### 备份数据库

```bash
pg_dump -h localhost -U postgres ai_companion_bot > backup.sql
```

### 恢复数据库

```bash
psql -h localhost -U postgres ai_companion_bot < backup.sql
```

### 清理过期数据

系统会自动清理超过配置天数的对话记录（默认30天）。也可以手动清理：

```python
from datetime import datetime, timedelta

# 删除30天前的对话记录
cutoff_date = datetime.now() - timedelta(days=30)
await db_manager.execute(
    "DELETE FROM conversations WHERE timestamp < $1",
    cutoff_date
)
```

## 性能优化

1. **索引**: 所有常用查询字段都已添加索引
2. **连接池**: 使用连接池管理数据库连接，避免频繁创建连接
3. **批量操作**: 使用 `execute_many` 进行批量插入
4. **JSONB**: 使用PostgreSQL的JSONB类型存储元数据，支持高效查询

## 故障排查

### 连接失败

1. 检查PostgreSQL服务是否运行
2. 检查数据库配置是否正确
3. 检查防火墙设置
4. 检查PostgreSQL的 `pg_hba.conf` 配置

### 初始化失败

1. 检查数据库用户是否有创建表的权限
2. 检查SQL语法是否正确
3. 查看详细错误日志

### 加密/解密失败

1. 检查 ENCRYPTION_KEY 环境变量是否设置
2. 确保使用相同的密钥进行加密和解密
3. 检查加密数据是否完整

## 测试

运行数据库测试：

```bash
# 运行所有数据库测试
pytest tests/test_database.py -v

# 运行特定测试
pytest tests/test_database.py::TestDatabaseManager::test_connection -v
```

**注意**: 测试需要一个可用的PostgreSQL数据库实例。建议使用独立的测试数据库。
