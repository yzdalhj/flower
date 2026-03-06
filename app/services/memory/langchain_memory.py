"""LangChain 记忆系统集成"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.services.memory.memory_store import MemoryStore
from app.services.memory.vector_store import HybridMemoryRetriever, VectorStore


class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """
    基于数据库的聊天历史记录
    实现 LangChain 的 BaseChatMessageHistory 接口
    """

    def __init__(self, user_id: str, memory_store: MemoryStore, session_id: Optional[str] = None):
        self.user_id = user_id
        self.memory_store = memory_store
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._messages: List[BaseMessage] = []

    async def aadd_message(self, message: BaseMessage) -> None:
        """异步添加消息"""
        self._messages.append(message)

        # 保存到数据库
        content = message.content
        role = "user" if message.type == "human" else "assistant"

        await self.memory_store.create_memory(
            user_id=self.user_id,
            memory_type="episodic",
            content=f"{role}: {content}",
            summary=content[:100] if len(content) > 100 else content,
            importance=3.0,
            metadata={
                "session_id": self.session_id,
                "role": role,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def add_message(self, message: BaseMessage) -> None:
        """同步添加消息（不推荐使用）"""
        self._messages.append(message)

    async def aget_messages(self) -> List[BaseMessage]:
        """异步获取消息历史"""
        return self._messages

    def get_messages(self) -> List[BaseMessage]:
        """同步获取消息历史"""
        return self._messages

    async def aclear(self) -> None:
        """异步清空历史"""
        self._messages.clear()

    def clear(self) -> None:
        """同步清空历史"""
        self._messages.clear()


class LangChainMemoryService:
    """
    LangChain 记忆服务
    集成 ConversationBufferMemory 和向量检索
    """

    def __init__(
        self,
        memory_store: MemoryStore,
        vector_store: VectorStore,
        user_id: str,
        memory_type: str = "buffer",  # buffer 或 summary
        max_token_limit: int = 2000,
    ):
        self.memory_store = memory_store
        self.vector_store = vector_store
        self.user_id = user_id
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit

        # 创建聊天历史
        self.chat_history = DatabaseChatMessageHistory(user_id=user_id, memory_store=memory_store)

        # 创建混合检索器
        self.retriever = HybridMemoryRetriever(vector_store)

    async def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        await self.chat_history.aadd_message(HumanMessage(content=message))

    async def add_ai_message(self, message: str) -> None:
        """添加 AI 消息"""
        await self.chat_history.aadd_message(AIMessage(content=message))

    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        获取对话历史

        Returns:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        messages = await self.chat_history.aget_messages()

        history = []
        for msg in messages[-limit:]:
            role = "user" if msg.type == "human" else "assistant"
            history.append({"role": role, "content": msg.content})

        return history

    async def retrieve_relevant_memories(
        self, query: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆

        Args:
            query: 查询文本
            n_results: 返回结果数

        Returns:
            相关记忆列表
        """
        return await self.retriever.retrieve(query=query, user_id=self.user_id, n_results=n_results)

    async def build_context_for_prompt(
        self,
        current_message: str,
        include_conversation: bool = True,
        include_long_term: bool = True,
        conversation_limit: int = 10,
        memory_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        构建用于 Prompt 的完整上下文

        Args:
            current_message: 当前用户消息
            include_conversation: 是否包含对话历史
            include_long_term: 是否包含长期记忆
            conversation_limit: 对话历史条数
            memory_limit: 长期记忆条数

        Returns:
            包含所有上下文的字典
        """
        context = {
            "current_message": current_message,
            "conversation_history": [],
            "relevant_memories": [],
            "working_memory": None,
        }

        # 1. 获取对话历史
        if include_conversation:
            context["conversation_history"] = await self.get_conversation_history(
                limit=conversation_limit
            )

        # 2. 检索相关长期记忆
        if include_long_term:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query=current_message, n_results=memory_limit
            )

        # 3. 获取工作记忆
        working_memory = await self.memory_store.get_working_memory(self.user_id)
        if working_memory:
            context["working_memory"] = {
                "current_topic": working_memory.current_topic,
                "current_emotion": (
                    json.loads(working_memory.current_emotion)
                    if working_memory.current_emotion
                    else None
                ),
                "pending_intent": working_memory.pending_intent,
            }

        return context

    async def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """
        将上下文格式化为 LLM 可读的文本

        Args:
            context: build_context_for_prompt 返回的上下文

        Returns:
            格式化的上下文文本
        """
        parts = []

        # 1. 对话历史
        if context.get("conversation_history"):
            parts.append("## 最近对话历史")
            for msg in context["conversation_history"]:
                role_name = "用户" if msg["role"] == "user" else "小花"
                parts.append(f"{role_name}: {msg['content']}")
            parts.append("")

        # 2. 相关记忆
        if context.get("relevant_memories"):
            parts.append("## 相关记忆")
            for i, memory in enumerate(context["relevant_memories"], 1):
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                parts.append(f"{i}. {content}")
                if metadata.get("occurred_at"):
                    parts.append(f"   时间: {metadata['occurred_at']}")
            parts.append("")

        # 3. 工作记忆
        if context.get("working_memory"):
            wm = context["working_memory"]
            parts.append("## 当前状态")
            if wm.get("current_topic"):
                parts.append(f"当前话题: {wm['current_topic']}")
            if wm.get("current_emotion"):
                emotion = wm["current_emotion"]
                parts.append(f"当前情感: {emotion}")
            parts.append("")

        return "\n".join(parts)

    async def save_interaction(
        self,
        user_message: str,
        ai_response: str,
        importance: float = 3.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        保存完整的交互到记忆系统

        Args:
            user_message: 用户消息
            ai_response: AI 回复
            importance: 重要性评分
            metadata: 额外元数据
        """
        # 1. 添加到对话历史
        await self.add_user_message(user_message)
        await self.add_ai_message(ai_response)

        # 2. 保存到向量数据库
        interaction_text = f"用户: {user_message}\n小花: {ai_response}"

        # 创建长期记忆
        memory = await self.memory_store.create_memory(
            user_id=self.user_id,
            memory_type="episodic",
            content=interaction_text,
            summary=user_message[:100],
            importance=importance,
            metadata=metadata or {},
        )

        # 添加到向量数据库
        await self.vector_store.add_memory(
            memory_id=memory.id,
            content=interaction_text,
            metadata={
                "user_id": self.user_id,
                "memory_type": "episodic",
                "importance": importance,
                "created_at": memory.created_at.isoformat(),
            },
        )

    async def clear_conversation_history(self) -> None:
        """清空对话历史"""
        await self.chat_history.aclear()

    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        # 获取数据库记忆数量
        db_memories = await self.memory_store.get_user_memories(user_id=self.user_id, limit=1000)

        # 获取向量数据库记忆数量
        vector_count = await self.vector_store.get_memory_count()

        # 获取对话历史长度
        conversation_history = await self.get_conversation_history(limit=1000)

        return {
            "total_memories": len(db_memories),
            "vector_memories": vector_count,
            "conversation_length": len(conversation_history),
            "memory_types": self._count_memory_types(db_memories),
        }

    def _count_memory_types(self, memories: List) -> Dict[str, int]:
        """统计记忆类型分布"""
        type_counts = {}
        for memory in memories:
            memory_type = memory.memory_type
            type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
        return type_counts


class MemoryContextInjector:
    """
    记忆上下文注入器
    用于将记忆上下文注入到 LLM Prompt 中
    """

    def __init__(self, langchain_memory: LangChainMemoryService):
        self.memory = langchain_memory

    async def inject_context(
        self,
        base_prompt: str,
        current_message: str,
        include_conversation: bool = True,
        include_memories: bool = True,
    ) -> str:
        """
        将记忆上下文注入到基础 Prompt 中

        Args:
            base_prompt: 基础系统提示
            current_message: 当前用户消息
            include_conversation: 是否包含对话历史
            include_memories: 是否包含长期记忆

        Returns:
            注入上下文后的完整 Prompt
        """
        # 构建上下文
        context = await self.memory.build_context_for_prompt(
            current_message=current_message,
            include_conversation=include_conversation,
            include_long_term=include_memories,
        )

        # 格式化上下文
        context_text = await self.memory.format_context_for_llm(context)

        # 组装完整 Prompt
        full_prompt = f"""{base_prompt}

{context_text}

## 当前用户消息
{current_message}

请根据以上上下文和历史记忆，以小花的身份回复用户。
"""

        return full_prompt

    async def inject_context_for_chat(
        self, system_prompt: str, current_message: str, max_history: int = 10
    ) -> List[Dict[str, str]]:
        """
        为聊天 API 格式注入上下文

        Returns:
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
                ...
            ]
        """
        messages = []

        # 1. 系统提示
        messages.append({"role": "system", "content": system_prompt})

        # 2. 获取相关记忆并注入到系统提示
        relevant_memories = await self.memory.retrieve_relevant_memories(
            query=current_message, n_results=3
        )

        if relevant_memories:
            memory_context = "## 相关记忆\n"
            for memory in relevant_memories:
                memory_context += f"- {memory.get('content', '')}\n"

            messages.append({"role": "system", "content": memory_context})

        # 3. 对话历史
        conversation_history = await self.memory.get_conversation_history(limit=max_history)
        messages.extend(conversation_history)

        # 4. 当前消息
        messages.append({"role": "user", "content": current_message})

        return messages
