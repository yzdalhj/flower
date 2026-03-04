# AI小花系统架构图

## 1. 整体架构图

```mermaid
graph TB
    subgraph 用户层
        U1[微信用户]
        U2[QQ用户]
        U3[Web用户]
    end

    subgraph 接入层
        W1[微信账号#1]
        W2[微信账号#2]
        Q1[QQ账号#1]
        Q2[QQ账号#2]
        WEB[Web界面]
    end

    subgraph API层
        API[FastAPI网关]
        AUTH[认证模块]
        ROUTER[路由分发]
    end

    subgraph 业务层
        AM[账号管理器]
        DP[对话处理器]
        EH[情感处理]
        MS[记忆系统]
        PS[人格系统]
        ES[表情包系统]
    end

    subgraph AI层
        LLM[LLM路由器]
        DSK[DeepSeek]
        KIMI[Kimi]
        GLM[GLM]
        GPT[GPT-4o]
    end

    subgraph 数据层
        DB[(SQLite/PostgreSQL)]
        VDB[(ChromaDB)]
        REDIS[(Redis)]
        S3[文件存储]
    end

    U1 --> W1
    U1 --> W2
    U2 --> Q1
    U2 --> Q2
    U3 --> WEB

    W1 --> API
    W2 --> API
    Q1 --> API
    Q2 --> API
    WEB --> API

    API --> AUTH
    AUTH --> ROUTER

    ROUTER --> AM
    AM --> DP
    DP --> EH
    DP --> MS
    DP --> PS
    DP --> ES

    DP --> LLM
    LLM --> DSK
    LLM --> KIMI
    LLM --> GLM
    LLM --> GPT

    AM --> DB
    MS --> DB
    MS --> VDB
    AM --> REDIS
    ES --> S3
```

## 2. 账号管理架构

```mermaid
graph TB
    subgraph 账号管理层
        AM[AccountManager]
        AC[AccountConfig]
    end

    subgraph 账号实例层
        AI1[AccountInstance<br/>微信#1]
        AI2[AccountInstance<br/>微信#2]
        AI3[AccountInstance<br/>QQ#1]
    end

    subgraph 独立组件
        subgraph 微信#1
            MH1[MessageHandler]
            MP1[MemoryStore]
            DP1[DialogueProcessor]
            PE1[Personality]
        end

        subgraph 微信#2
            MH2[MessageHandler]
            MP2[MemoryStore]
            DP2[DialogueProcessor]
            PE2[Personality]
        end

        subgraph QQ#1
            MH3[MessageHandler]
            MP3[MemoryStore]
            DP3[DialogueProcessor]
            PE3[Personality]
        end
    end

    subgraph 数据隔离
        DB1[(account_001_*)]
        DB2[(account_002_*)]
        DB3[(account_003_*)]
    end

    AM --> AI1
    AM --> AI2
    AM --> AI3

    AI1 --> MH1
    AI1 --> MP1
    AI1 --> DP1
    AI1 --> PE1

    AI2 --> MH2
    AI2 --> MP2
    AI2 --> DP2
    AI2 --> PE2

    AI3 --> MH3
    AI3 --> MP3
    AI3 --> DP3
    AI3 --> PE3

    MP1 --> DB1
    MP2 --> DB2
    MP3 --> DB3
```

## 3. 对话处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Handler as MessageHandler
    participant DP as DialogueProcessor
    participant MS as MemorySystem
    participant ES as EmotionSystem
    participant LLM as LLMRouter
    participant Post as PostProcessor

    User->>Handler: 发送消息
    Handler->>DP: process(message)

    DP->>MS: 检索相关记忆
    MS-->>DP: 返回记忆

    DP->>ES: 分析情感
    ES-->>DP: 返回情感状态

    DP->>DP: 构建Prompt
    DP->>LLM: 调用模型
    LLM-->>DP: 返回回复

    DP->>Post: 后处理
    Post-->>DP: 真人化回复

    DP->>MS: 保存对话
    DP-->>Handler: 返回回复
    Handler-->>User: 发送回复
```

## 4. 多模型路由架构

```mermaid
graph LR
    subgraph 请求
        REQ[对话请求]
    end

    subgraph 智能路由
        ROUTER[LLMRouter]
        STRAT[路由策略]
    end

    subgraph 模型池
        DSK[DeepSeek-V3.2<br/>推理强/中文优]
        KIMI[Kimi-K2.5<br/>长上下文256K]
        GLM[GLM-5<br/>中文理解强/速度快]
        GPT[GPT-4o<br/>多模态能力]
    end

    subgraph 故障处理
        FB[故障检测]
        CB[断路器]
        RETRY[重试机制]
    end

    REQ --> ROUTER
    ROUTER --> STRAT

    STRAT -->|深度思考| DSK
    STRAT -->|长对话| KIMI
    STRAT -->|快速响应| GLM
    STRAT -->|多模态| GPT

    DSK -.->|失败| FB
    FB --> CB
    CB -->|切换| GLM

    RETRY -.-> DSK
```

## 5. 记忆系统架构

```mermaid
graph TB
    subgraph 记忆输入
        MSG[新消息]
        RSP[AI回复]
    end

    subgraph 记忆处理
        EP[EpisodicProcessor<br/>情节记忆]
        SEM[SemanticProcessor<br/>语义记忆]
        EM[EmotionProcessor<br/>情感记忆]
    end

    subgraph 向量存储
        VDB[(ChromaDB)]
        EMB[Embedding模型<br/>BAAI/bge-large-zh]
    end

    subgraph 关系存储
        DB[(SQLite)]
    end

    subgraph 记忆检索
        RET[记忆检索器]
        WORK[工作记忆<br/>最近20轮]
        LONG[长期记忆<br/>Top-K相关]
        REL[关系记忆<br/>用户画像]
    end

    MSG --> EP
    MSG --> SEM
    MSG --> EM
    RSP --> EP

    EP --> EMB
    SEM --> EMB
    EM --> EMB

    EMB --> VDB
    EP --> DB
    SEM --> DB
    EM --> DB

    RET --> WORK
    RET --> VDB
    RET --> DB

    WORK --> RET
    VDB --> LONG
    DB --> REL
```

## 6. 人格与情感系统

```mermaid
graph TB
    subgraph 人格配置
        PE[PersonalityEngine]
        CONF[人格配置]
        EVO[人格演化]
    end

    subgraph 人格维度
        EXP[表达丰富度]
        HUM[幽默程度]
        EMP[共情深度]
        WARM[温暖度]
        CAS[随意度]
        SAR[吐槽倾向]
        VER[话痨程度]
    end

    subgraph 情感系统
        ES[EmotionSystem]
        CUR[当前情感]
        HIS[情感历史]
    end

    subgraph 情感维度
        VAL[愉悦度]
        ARO[激活度]
        TRU[信任度]
        INT[亲密感]
        SEC[安全感]
    end

    PE --> CONF
    PE --> EVO

    CONF --> EXP
    CONF --> HUM
    CONF --> EMP
    CONF --> WARM
    CONF --> CAS
    CONF --> SAR
    CONF --> VER

    ES --> CUR
    ES --> HIS

    CUR --> VAL
    CUR --> ARO
    CUR --> TRU
    CUR --> INT
    CUR --> SEC
```

## 7. 表情包系统架构

```mermaid
graph TB
    subgraph 表情包库
        EMO[EmojiLibrary]
        EM1[情绪类<br/>开心/难过/生气]
        EM2[反应类<br/>赞同/反对/无语]
        EM3[梗图类<br/>经典/流行]
        EM4[贴纸类<br/>可爱/酷/搞笑]
    end

    subgraph 智能选择
        SEL[EmojiSelector]
        SENT[情感分析]
        PERS[人格匹配]
        STRAT[发送策略]
    end

    subgraph 发送方式
        ONLY[只发表情包<br/>30%]
        COMB[文字+表情包<br/>50%]
        TEXT[只发文字<br/>20%]
    end

    subgraph 平台适配
        WECHAT[微信表情]
        QQ[QQ表情]
        WEB[Web图片]
    end

    EMO --> EM1
    EMO --> EM2
    EMO --> EM3
    EMO --> EM4

    SEL --> SENT
    SEL --> PERS
    SEL --> STRAT

    STRAT --> ONLY
    STRAT --> COMB
    STRAT --> TEXT

    ONLY --> WECHAT
    ONLY --> QQ
    ONLY --> WEB

    COMB --> WECHAT
    COMB --> QQ
    COMB --> WEB
```

## 8. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI | 高性能异步Web框架 |
| **数据库** | SQLAlchemy + SQLite/PostgreSQL | ORM + 关系数据库 |
| **向量数据库** | ChromaDB | 向量相似度搜索 |
| **缓存** | Redis | 会话缓存、任务队列 |
| **任务队列** | Celery | 异步任务处理 |
| **AI模型** | DeepSeek/Kimi/GLM/GPT-4o | 大语言模型API |
| **嵌入模型** | BAAI/bge-large-zh-v1.5 | 中文文本嵌入 |
| **部署** | Docker + Docker Compose | 容器化部署 |
| **代码质量** | Black + isort + flake8 + mypy | 代码格式化和类型检查 |

## 9. 数据流图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Platform as 平台层
    participant API as API层
    participant Service as 业务层
    participant AI as AI层
    participant DB as 数据层

    User->>Platform: 发送消息
    Platform->>API: HTTP请求
    API->>Service: 调用服务

    Service->>DB: 检索记忆
    DB-->>Service: 返回记忆

    Service->>Service: 构建Prompt
    Service->>AI: 调用模型
    AI-->>Service: 返回回复

    Service->>DB: 保存对话
    Service-->>API: 返回结果
    API-->>Platform: HTTP响应
    Platform-->>User: 显示回复
```

## 10. 部署架构

```mermaid
graph TB
    subgraph 用户
        U1[微信用户]
        U2[QQ用户]
        U3[Web用户]
    end

    subgraph 负载均衡
        LB[Nginx/Traefik]
    end

    subgraph 应用集群
        APP1[FastAPI实例1]
        APP2[FastAPI实例2]
        APP3[FastAPI实例3]
    end

    subgraph 数据层
        PG[(PostgreSQL主库)]
        PGR[(PostgreSQL从库)]
        REDIS[(Redis集群)]
        CHROMA[(ChromaDB集群)]
    end

    subgraph 任务队列
        CELERY[Celery Worker]
        FLOWER[Flower监控]
    end

    U1 --> LB
    U2 --> LB
    U3 --> LB

    LB --> APP1
    LB --> APP2
    LB --> APP3

    APP1 --> PG
    APP2 --> PG
    APP3 --> PG

    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS

    APP1 --> CHROMA
    APP2 --> CHROMA
    APP3 --> CHROMA

    CELERY --> REDIS
    FLOWER --> REDIS

    PG -.-> PGR
```

---

这些架构图展示了AI小花的完整技术架构，包括多账号管理、智能路由、记忆系统、人格情感、表情包回复等核心功能的设计。