"""业务逻辑模块

重组后的目录结构：
- emotion/     - 情感分析与动力学
- personality/ - 人格系统
- memory/      - 记忆存储与检索
- learning/    - 持续学习与强化学习
- llm/         - LLM 客户端与对话处理
- profile/     - 用户画像
- relationship/- 关系图谱
"""

# 向后兼容的导入
from app.services.emotion import EmotionResult, MultilingualEmotionAnalyzer, get_emotion_analyzer
from app.services.llm import DialogueProcessor, DialogueResponse, LLMRouter, llm_router
from app.services.memory import (
    DatabaseChatMessageHistory,
    EmbeddingService,
    HybridMemoryRetriever,
    LangChainMemoryService,
    MemoryContextInjector,
    MemoryStore,
    VectorStore,
)
from app.services.personality import (
    PersonalityPromptInjector,
    PersonalityService,
    get_personality_injector,
    get_personality_service,
)

__all__ = [
    # memory
    "MemoryStore",
    "VectorStore",
    "EmbeddingService",
    "HybridMemoryRetriever",
    "LangChainMemoryService",
    "MemoryContextInjector",
    "DatabaseChatMessageHistory",
    # llm
    "LLMRouter",
    "llm_router",
    "DialogueProcessor",
    "DialogueResponse",
    # emotion
    "MultilingualEmotionAnalyzer",
    "EmotionResult",
    "get_emotion_analyzer",
    # personality
    "PersonalityService",
    "get_personality_service",
    "PersonalityPromptInjector",
    "get_personality_injector",
]
