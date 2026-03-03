# 数据库设置指南

本指南将帮助您设置AI小花的数据库环境。

## 前置要求

- PostgreSQL 12+ 已安装并运行
- Python 3.8+ 已安装
- 已安装项目依赖 (`pip install -r requirements.txt`)

## 快速开始

### 1. 安装PostgreSQL

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

#### Windows
从 [PostgreSQL官网](https://www.postgresql.org/download/windows/) 下载并安装。

### 2. 创建数据库

```bash
# 切换到postgres用户
sudo -u postgres psql

# 在PostgreSQL命令行中执行
CREATE DATABASE ai_companion_bot;
CREATE USER ai_bot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_companion_bot TO ai_bot_user;
\q
```

### 3. 配置项目

复制配置文件模板：
```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

编辑 `config.yaml`，更新数据库配置：
```yaml
database:
  host: "localhost"
  port: 5432
  database: "ai_companion_bot"
  username: "ai_bot_user"
  password: "your_secure_password"
  pool_size: 10
```

或使用环境变量（编辑 `.env` 文件）：
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_companion_bot
DB_USER=ai_bot_user
DB_PASSWORD=your_secure_password
```

### 4. 生成加密密钥

```bash
python scripts/db_manager.py genkey
```

将生成的密钥添加到 `.env` 文件：
```bash
ENCRYPTION_KEY=your-generated-key-here
```

**重要**: 请妥善保管此密钥！丢失密钥将无法解密已加密的数据。

### 5. 初始化数据库

```bash
# 初始化数据库模式
python scripts/db_manager.py init

# 或使用配置文件路径
python scripts/db_manager.py -c config.yaml init
```

### 6. 验证安装

```bash
# 检查数据库状态
python scripts/db_manager.py check
```

您应该看到类似以下输出：
```
✓ 数据库连接成功
✓ 所有必需的表都存在

数据统计:
  conversations: 0 条记录
  emotion_history: 0 条记录
  personality_profiles: 0 条记录
  ...
```

## 数据库管理工具

项目提供了一个命令行工具来管理数据库：

### 查看帮助
```bash
python scripts/db_manager.py --help
```

### 可用命令

#### 初始化数据库
```bash
# 初始化（保留现有数据）
python scripts/db_manager.py init

# 重置数据库（删除所有表后重新创建）
python scripts/db_manager.py init --reset
```

#### 检查数据库状态
```bash
python scripts/db_manager.py check
```

#### 重置数据库（危险操作）
```bash
# 会提示确认
python scripts/db_manager.py reset

# 跳过确认
python scripts/db_manager.py reset -y
```

#### 生成加密密钥
```bash
# 生成随机密钥
python scripts/db_manager.py genkey

# 从密码生成密钥
python scripts/db_manager.py genkey -p "my-secure-password"
```

#### 备份数据库
```bash
# 备份到默认文件
python scripts/db_manager.py backup

# 指定输出文件
python scripts/db_manager.py backup -o backup_20240101.sql
```

## 数据库模式

系统包含以下数据表：

### 核心表

1. **conversations** - 对话记录
   - 存储所有用户对话消息
   - 支持加密存储（encrypted_content字段）

2. **emotion_history** - 情绪历史
   - 记录用户情绪状态变化

3. **personality_profiles** - 性格配置
   - 存储机器人性格角色配置

4. **slang_database** - 网络用语
   - 存储流行网络用语和梗

5. **emoji_library** - 表情包库
   - 存储表情包文件信息

6. **role_transitions** - 角色转换记录
   - 记录动态角色转换历史

7. **client_sessions** - 客户端会话
   - 管理客户端连接会话

8. **media_cache** - 媒体缓存
   - 缓存富媒体文件

9. **connection_logs** - 连接日志
   - 记录连接事件

详细的表结构请参考 `src/storage/schema.sql`。

## 数据加密

系统使用Fernet对称加密算法加密敏感数据：

- 对话记录存储在 `conversations.encrypted_content` 字段
- API密钥在配置中加密存储
- 平台凭证在配置中加密存储

### 加密密钥管理

1. **首次设置**: 使用 `genkey` 命令生成密钥
2. **保存密钥**: 将密钥保存到 `.env` 文件或环境变量
3. **备份密钥**: 将密钥安全备份到密码管理器或安全存储

**警告**: 丢失加密密钥将导致无法解密已加密的数据！

## 数据库维护

### 定期备份

建议每天备份数据库：

```bash
# 使用项目工具
python scripts/db_manager.py backup -o backup_$(date +%Y%m%d).sql

# 或使用pg_dump
pg_dump -h localhost -U ai_bot_user ai_companion_bot > backup.sql
```

### 恢复备份

```bash
psql -h localhost -U ai_bot_user ai_companion_bot < backup.sql
```

### 清理过期数据

系统会自动清理超过配置天数（默认30天）的对话记录。

手动清理：
```python
from datetime import datetime, timedelta
from src.storage.database import DatabaseManager

# 删除30天前的数据
cutoff_date = datetime.now() - timedelta(days=30)
await db_manager.execute(
    "DELETE FROM conversations WHERE timestamp < $1",
    cutoff_date
)
```

## 性能优化

### 索引优化

所有常用查询字段都已添加索引。如需添加自定义索引：

```sql
CREATE INDEX idx_custom ON table_name(column_name);
```

### 连接池配置

在 `config.yaml` 中调整连接池大小：

```yaml
database:
  pool_size: 20  # 根据并发需求调整
```

### 查询优化

使用 EXPLAIN ANALYZE 分析慢查询：

```sql
EXPLAIN ANALYZE SELECT * FROM conversations WHERE user_id = 'xxx';
```

## 故障排查

### 连接失败

**问题**: 无法连接到数据库

**解决方案**:
1. 检查PostgreSQL服务是否运行: `sudo systemctl status postgresql`
2. 检查配置文件中的连接信息是否正确
3. 检查防火墙设置: `sudo ufw allow 5432/tcp`
4. 检查PostgreSQL配置文件 `pg_hba.conf`

### 权限错误

**问题**: 用户没有权限创建表

**解决方案**:
```sql
GRANT ALL PRIVILEGES ON DATABASE ai_companion_bot TO ai_bot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_bot_user;
```

### 初始化失败

**问题**: 数据库初始化失败

**解决方案**:
1. 查看详细日志: `python scripts/db_manager.py -v init`
2. 检查SQL语法是否正确
3. 确保数据库为空或使用 `--reset` 选项

### 加密错误

**问题**: 加密/解密失败

**解决方案**:
1. 检查 `ENCRYPTION_KEY` 环境变量是否设置
2. 确保使用相同的密钥进行加密和解密
3. 检查密钥格式是否正确（base64编码）

## 开发环境设置

### 使用Docker

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: ai_companion_bot
      POSTGRES_USER: ai_bot_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

启动：
```bash
docker-compose up -d
```

### 测试数据库

建议使用独立的测试数据库：

```bash
# 创建测试数据库
sudo -u postgres psql -c "CREATE DATABASE ai_companion_bot_test;"

# 在测试中使用
export DB_NAME=ai_companion_bot_test
pytest tests/test_database.py
```

## 生产环境建议

1. **使用强密码**: 为数据库用户设置强密码
2. **限制访问**: 配置防火墙只允许应用服务器访问数据库
3. **定期备份**: 设置自动备份任务
4. **监控**: 监控数据库性能和磁盘使用
5. **SSL连接**: 在生产环境使用SSL连接数据库
6. **密钥管理**: 使用密钥管理服务（如AWS KMS）管理加密密钥

## 更多信息

- [PostgreSQL官方文档](https://www.postgresql.org/docs/)
- [asyncpg文档](https://magicstack.github.io/asyncpg/)
- [cryptography文档](https://cryptography.io/)
- 项目存储层文档: `src/storage/README.md`
