# Redis缓存层安装和配置指南

## 概述

本文档说明如何安装和配置Redis缓存层，以支持小花AI伴侣机器人的高性能数据访问。

## 前置要求

- Python 3.8+
- Redis 6.0+

## 安装步骤

### 1. 安装Redis服务

#### Windows

**方法1: 使用WSL2（推荐）**
```bash
# 在WSL2中安装Redis
sudo apt update
sudo apt install redis-server

# 启动Redis
sudo service redis-server start

# 测试连接
redis-cli ping
# 应该返回: PONG
```

**方法2: 使用Docker**
```bash
# 拉取Redis镜像
docker pull redis:latest

# 运行Redis容器
docker run -d --name redis -p 6379:6379 redis:latest

# 测试连接
docker exec -it redis redis-cli ping
# 应该返回: PONG
```

**方法3: 使用Memurai（Windows原生）**
```bash
# 下载并安装Memurai（Redis的Windows版本）
# https://www.memurai.com/get-memurai

# 安装后自动启动服务
# 测试连接
memurai-cli ping
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# 启动Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 测试连接
redis-cli ping
```

#### macOS

```bash
# 使用Homebrew安装
brew install redis

# 启动Redis
brew services start redis

# 测试连接
redis-cli ping
```

### 2. 安装Python依赖

```bash
# 确保在项目虚拟环境中
pip install redis==5.0.1
```

### 3. 配置Redis连接

编辑 `config.yaml` 文件：

```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null  # 如果设置了密码，在此填写
```

或使用环境变量（`.env` 文件）：

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## 验证安装

### 方法1: 使用测试脚本

```bash
# 运行Redis连接测试
python scripts/test_redis_connection.py
```

成功输出示例：
```
============================================================
Redis连接测试
============================================================

配置信息:
  Host: localhost
  Port: 6379
  DB: 0

正在连接Redis...
✅ Redis连接成功！

测试ping...
✅ Ping成功

测试基本操作...
  - 设置缓存...
  - 获取缓存...
  ✅ 读写测试通过
  - 删除缓存...

测试会话状态操作...
  ✅ 会话状态测试通过

测试对话上下文操作...
  ✅ 对话上下文测试通过

测试情绪状态操作...
  ✅ 情绪状态测试通过

获取Redis统计信息...
  已用内存: 1.23M
  连接客户端数: 2
  总命令数: 1234
  运行时间: 3600秒

清理测试数据...

✅ 所有测试通过！Redis缓存层工作正常。

============================================================
测试完成
============================================================
```

### 方法2: 使用pytest

```bash
# 运行完整测试套件
pytest tests/test_redis_cache.py -v
```

### 方法3: 手动测试

```bash
# 启动Python交互式环境
python

# 执行以下代码
import asyncio
from src.config.manager import RedisConfig
from src.storage.redis_cache import RedisCacheManager

async def test():
    config = RedisConfig(host="localhost", port=6379, db=0)
    cache = RedisCacheManager(config)
    await cache.initialize()
    
    # 测试基本操作
    await cache.set("test", "hello", ttl=60)
    value = await cache.get("test")
    print(f"Value: {value}")
    
    # 获取统计信息
    stats = await cache.get_stats()
    print(f"Stats: {stats}")
    
    await cache.close()

asyncio.run(test())
```

## Redis配置优化

### 基本配置

编辑Redis配置文件（通常在 `/etc/redis/redis.conf`）：

```conf
# 最大内存限制（根据实际情况调整）
maxmemory 256mb

# 内存淘汰策略（推荐使用allkeys-lru）
maxmemory-policy allkeys-lru

# 持久化配置（根据需要启用）
save 900 1
save 300 10
save 60 10000

# AOF持久化（可选）
appendonly yes
appendfsync everysec

# 日志级别
loglevel notice

# 绑定地址（生产环境建议限制）
bind 127.0.0.1

# 保护模式
protected-mode yes
```

### 性能优化

```conf
# TCP backlog
tcp-backlog 511

# TCP keepalive
tcp-keepalive 300

# 超时设置
timeout 0

# 数据库数量
databases 16

# 慢查询日志
slowlog-log-slower-than 10000
slowlog-max-len 128
```

## 常见问题

### 1. 无法连接Redis

**问题**: `redis_initialization_error` 或连接超时

**解决方案**:
```bash
# 检查Redis是否运行
redis-cli ping

# 检查端口是否监听
netstat -an | grep 6379

# 检查防火墙
sudo ufw allow 6379

# 查看Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

### 2. 连接被拒绝

**问题**: `Connection refused`

**解决方案**:
- 确认Redis服务正在运行
- 检查 `redis.conf` 中的 `bind` 配置
- 如果使用Docker，确保端口映射正确

### 3. 认证失败

**问题**: `NOAUTH Authentication required`

**解决方案**:
- 在配置中设置正确的密码
- 或在 `redis.conf` 中注释掉 `requirepass`

### 4. 内存不足

**问题**: `OOM command not allowed when used memory > 'maxmemory'`

**解决方案**:
```bash
# 增加最大内存限制
redis-cli CONFIG SET maxmemory 512mb

# 或修改redis.conf
maxmemory 512mb
```

### 5. 性能问题

**问题**: 缓存操作缓慢

**解决方案**:
- 检查网络延迟
- 优化数据结构
- 使用批量操作（mget/mset）
- 检查慢查询日志

## 监控和维护

### 监控命令

```bash
# 查看Redis信息
redis-cli INFO

# 查看内存使用
redis-cli INFO memory

# 查看统计信息
redis-cli INFO stats

# 查看客户端连接
redis-cli CLIENT LIST

# 查看慢查询
redis-cli SLOWLOG GET 10

# 实时监控命令
redis-cli MONITOR
```

### 定期维护

```bash
# 备份数据
redis-cli SAVE

# 清理过期键
redis-cli --scan --pattern "expired:*" | xargs redis-cli DEL

# 检查内存碎片
redis-cli INFO memory | grep fragmentation
```

## 生产环境建议

### 安全配置

1. **设置密码**
   ```conf
   requirepass your_strong_password_here
   ```

2. **限制访问**
   ```conf
   bind 127.0.0.1
   protected-mode yes
   ```

3. **禁用危险命令**
   ```conf
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   rename-command CONFIG ""
   ```

### 高可用配置

1. **主从复制**
   ```conf
   # 从节点配置
   replicaof master_ip master_port
   masterauth master_password
   ```

2. **Redis Sentinel**（监控和自动故障转移）

3. **Redis Cluster**（分布式部署）

### 监控告警

- 内存使用率 > 80%
- 连接数异常增长
- 慢查询数量增加
- 主从同步延迟
- 缓存命中率 < 50%

## 相关文档

- [Redis缓存层实现文档](../src/storage/REDIS_CACHE.md)
- [数据库设计文档](../src/storage/README.md)
- [系统架构设计](../.kiro/specs/ai-companion-bot/design.md)

## 技术支持

如遇到问题，请：
1. 查看Redis日志
2. 运行测试脚本诊断
3. 查阅Redis官方文档: https://redis.io/documentation
4. 联系开发团队

---

最后更新: 2024-01-01
