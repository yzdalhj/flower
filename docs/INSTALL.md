# 安装指南

## 系统要求

- Python 3.8 或更高版本
- PostgreSQL 12+ 或 MySQL 8+
- Redis 6+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-companion-bot
```

### 2. 创建虚拟环境

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际配置
# 使用你喜欢的编辑器编辑 .env
```

必须配置的环境变量：
- `OPENAI_API_KEY`: OpenAI API密钥
- `DB_PASSWORD`: 数据库密码
- `ENCRYPTION_KEY`: 数据加密密钥（可以使用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成）

### 5. 配置应用

```bash
# 复制配置文件模板
cp config.example.yaml config.yaml

# 编辑 config.yaml 文件
# 根据你的需求修改配置
```

主要配置项：
- AI提供商配置（API密钥、模型等）
- 平台配置（微信、QQ）
- 性格配置
- 数据库配置
- Redis配置

### 6. 初始化数据库

#### PostgreSQL:

```bash
# 创建数据库
createdb ai_companion_bot

# 运行初始化脚本（待实现）
# python scripts/init_db.py
```

#### MySQL:

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE ai_companion_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行初始化脚本（待实现）
# python scripts/init_db.py
```

### 7. 启动Redis

确保Redis服务正在运行：

```bash
# Linux/Mac
redis-server

# Windows (如果使用WSL)
sudo service redis-server start

# 或使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 8. 验证安装

```bash
# 运行测试
pytest tests/

# 检查配置
python main.py --check-config
```

### 9. 启动应用

```bash
python main.py
```

## 客户端控制配置（可选）

如果你想使用客户端控制功能（控制本地微信或QQ客户端），需要额外的配置：

### 微信客户端控制 (Wechaty)

1. 安装Wechaty:
```bash
pip install wechaty
```

2. 在 `config.yaml` 中配置：
```yaml
platforms:
  wechat:
    connection_type: "client_control"
    config:
      puppet: "wechaty-puppet-wechat"
```

3. 启动时会显示二维码，使用微信扫码登录

### QQ客户端控制 (NapCatQQ)

1. 下载并安装 NapCatQQ: https://github.com/NapNeko/NapCatQQ

2. 启动 NapCatQQ 服务

3. 在 `config.yaml` 中配置：
```yaml
platforms:
  qq:
    connection_type: "client_control"
    config:
      host: "localhost"
      port: 3000
      access_token: "your-token"
```

## 故障排查

### 问题：无法连接数据库

**解决方案：**
1. 检查数据库服务是否运行
2. 验证 `.env` 中的数据库配置
3. 确认数据库用户有足够的权限

### 问题：无法连接Redis

**解决方案：**
1. 检查Redis服务是否运行：`redis-cli ping`
2. 验证 `config.yaml` 中的Redis配置
3. 检查防火墙设置

### 问题：AI API调用失败

**解决方案：**
1. 验证API密钥是否正确
2. 检查网络连接
3. 确认API配额是否充足
4. 查看日志文件了解详细错误信息

### 问题：导入模块失败

**解决方案：**
1. 确认虚拟环境已激活
2. 重新安装依赖：`pip install -r requirements.txt`
3. 检查Python版本：`python --version`（需要3.8+）

## 开发环境设置

如果你想参与开发：

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 mypy

# 运行代码格式化
black src/ tests/

# 运行代码检查
flake8 src/ tests/

# 运行类型检查
mypy src/

# 运行测试
pytest tests/ -v
```

## 更新

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行数据库迁移（如果有）
# python scripts/migrate_db.py
```

## 卸载

```bash
# 停止应用
# 按 Ctrl+C 或使用进程管理器

# 删除虚拟环境
deactivate
rm -rf venv/

# 删除数据库（可选）
dropdb ai_companion_bot

# 删除项目文件
cd ..
rm -rf ai-companion-bot/
```

## 获取帮助

如果遇到问题：
1. 查看日志文件：`logs/app.log`
2. 查看文档：`README_CN.md`
3. 提交Issue：<repository-url>/issues
4. 查看常见问题：FAQ.md（待创建）
