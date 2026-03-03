# AI Companion Bot - 小花

一个多平台、多AI服务提供商的智能对话系统，支持微信和QQ平台，具备对话记忆、拟人化回复、动态性格转换和情绪系统等核心能力。

## 特性

- 🤖 **多AI服务支持**: 支持OpenAI、Claude、文心一言等多个AI服务提供商
- 💬 **多平台支持**: 统一架构支持微信和QQ平台
- 🎭 **拟人化交互**: 通过延迟、表情、网络用语等手段模拟真人对话
- 🧠 **对话记忆**: 30天对话记忆，支持上下文连贯对话
- 😊 **情绪系统**: 多维度情绪状态管理，动态情绪变化
- 🎨 **性格系统**: 支持多种性格、角色和性别配置
- 🔄 **动态角色转换**: 根据对话场景自动调整角色和性格
- 🗣️ **网络用语**: 理解和使用流行的网络用语和梗
- 📦 **表情包管理**: 智能选择和管理表情包
- 🔒 **安全可靠**: 数据加密、错误容错、隐私保护

## 项目结构

```
ai-companion-bot/
├── src/
│   ├── core/              # 核心模块
│   │   ├── enums.py       # 枚举类型定义
│   │   └── models.py      # 数据模型
│   ├── config/            # 配置管理
│   │   └── manager.py     # 配置管理器
│   ├── storage/           # 数据存储层
│   │   ├── database.py    # 数据库管理器
│   │   ├── encryption.py  # 数据加密工具
│   │   ├── init_db.py     # 数据库初始化
│   │   └── schema.sql     # 数据库模式
│   ├── utils/             # 工具模块
│   │   └── logger.py      # 日志系统
│   ├── adapters/          # 平台适配器（待实现）
│   ├── ai/                # AI服务层（待实现）
│   ├── memory/            # 记忆管理（待实现）
│   ├── personality/       # 性格系统（待实现）
│   ├── emotion/           # 情绪系统（待实现）
│   └── response/          # 回复生成（待实现）
├── scripts/               # 管理脚本
│   └── db_manager.py      # 数据库管理工具
├── docs/                  # 文档
│   └── DATABASE_SETUP.md  # 数据库设置指南
├── config.example.yaml    # 配置文件示例
├── .env.example           # 环境变量示例
├── requirements.txt       # Python依赖
└── README_CN.md          # 项目说明

## 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+ 或 MySQL 8+
- Redis 6+

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

```bash
# 复制配置文件
cp config.example.yaml config.yaml
cp .env.example .env

# 编辑配置文件，填入实际的API密钥和数据库配置
# 编辑 config.yaml 和 .env
```

### 4. 数据库初始化

```bash
# 创建数据库
sudo -u postgres psql -c "CREATE DATABASE ai_companion_bot;"
sudo -u postgres psql -c "CREATE USER ai_bot_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_companion_bot TO ai_bot_user;"

# 生成加密密钥
python scripts/db_manager.py genkey

# 将生成的密钥添加到 .env 文件中的 ENCRYPTION_KEY

# 初始化数据库模式
python scripts/db_manager.py init

# 检查数据库状态
python scripts/db_manager.py check
```

详细的数据库设置指南请参考 [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)

### 5. 运行

```bash
# 启动机器人（待实现）
# python main.py
```

## 配置说明

### AI提供商配置

在 `config.yaml` 中配置AI服务提供商：

```yaml
ai_providers:
  openai:
    api_key: "your-api-key"
    model: "gpt-3.5-turbo"
    parameters:
      temperature: 0.7
```

### 平台配置

支持两种接入方式：

1. **Web API**: 通过官方API接入
2. **客户端控制**: 控制本地客户端（需要安装Wechaty或NapCatQQ）

```yaml
platforms:
  wechat:
    connection_type: "client_control"
    enabled: true
```

### 性格配置

配置机器人的性格、角色和性别：

```yaml
personality_profiles:
  default:
    personality: "lively"  # 活泼
    role: "friend"         # 朋友
    gender: "female"       # 女性
```

## 开发状态

当前项目处于开发初期阶段，已完成：

- ✅ 项目基础架构
- ✅ 核心数据模型和枚举类型
- ✅ 日志系统（structlog）
- ✅ 配置管理模块
- ✅ 数据存储层（数据库管理、数据加密）
- ✅ 数据库初始化脚本和管理工具

待实现功能请参考 `.kiro/specs/ai-companion-bot/tasks.md`

## 技术栈

- **语言**: Python 3.8+
- **异步框架**: asyncio, aiohttp
- **数据库**: PostgreSQL/MySQL + Redis
- **AI服务**: OpenAI API, Anthropic Claude API, 百度文心一言API
- **微信控制**: Wechaty
- **QQ控制**: NapCatQQ
- **配置**: PyYAML
- **日志**: structlog
- **加密**: cryptography

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请提交Issue。
```
