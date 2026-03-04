# AI小花 - 智能陪伴助手

AI小花是一个基于大模型API的智能陪伴助手，支持多平台接入（微信、QQ、Web），具备长期记忆、情感共鸣、自主学习和表情包回复等能力。

## 特性

- 🤖 多模型支持（DeepSeek、Kimi、GLM、GPT-4o）
- 🧠 长期记忆与关系演进
- 💕 深度情感共鸣
- 🎭 真人化回复（去AI味）
- 😄 表情包回复
- 👥 多账号控制
- 📱 多平台支持（微信、QQ、Web）

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-companion
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 5. 运行应用

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看API文档。

## 项目结构

```
ai-companion/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   ├── api/                 # API路由
│   └── core/                # 核心组件
├── tests/                   # 测试
├── docker/                  # Docker配置
├── docs/                    # 文档
│   └── architecture.md      # 系统架构图
├── data/                    # 数据文件
├── requirements.txt         # 依赖
├── docker-compose.yml       # Docker编排
└── README.md               # 项目说明
```

## 系统架构

详细的系统架构图请查看 [docs/architecture.md](docs/architecture.md)，包含以下内容：

- **整体架构图** - 完整的系统分层架构
- **账号管理架构** - 多账号管理设计
- **对话处理流程** - 消息处理时序图
- **多模型路由架构** - LLM路由器和故障切换
- **记忆系统架构** - 情节/语义/情感记忆
- **人格与情感系统** - 人格维度和情感维度
- **表情包系统架构** - 表情包库和智能选择
- **部署架构** - 生产环境部署方案

## Docker部署

```bash
docker-compose up -d
```

## 开发

### 代码格式化

```bash
black app/
isort app/
```

### 运行测试

```bash
pytest
```

### 预提交钩子

```bash
pre-commit install
pre-commit run --all-files
```

## 配置说明

### AI模型API密钥

在 `.env` 文件中配置以下API密钥：

- `DEEPSEEK_API_KEY` - DeepSeek API密钥
- `KIMI_API_KEY` - Kimi API密钥
- `GLM_API_KEY` - GLM API密钥
- `OPENAI_API_KEY` - OpenAI API密钥（可选）

### 数据库

默认使用SQLite，可通过 `DATABASE_URL` 配置其他数据库。

## 许可证

MIT License
