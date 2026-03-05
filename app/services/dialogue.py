"""对话处理服务"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.services.llm_client import llm_router
from app.services.memory_store import MemoryStore


@dataclass
class DialogueContext:
    """对话上下文"""

    user_id: str
    account_id: str
    conversation_id: Optional[str] = None
    user_message: str = ""
    history: List[Dict[str, str]] = field(default_factory=list)
    memories: List[Dict[str, Any]] = field(default_factory=list)
    user_profile: Optional[Dict[str, Any]] = None


@dataclass
class DialogueResponse:
    """对话响应"""

    content: str
    emotion: Optional[Dict[str, float]] = None
    model_used: str = ""
    tokens_used: int = 0


class DialogueProcessor:
    """
    对话处理器
    处理用户输入，生成AI回复
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_store = MemoryStore(session)

    async def process(
        self,
        user_id: str,
        account_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> DialogueResponse:
        """
        处理对话

        Args:
            user_id: 用户ID
            account_id: 账号ID
            message: 用户消息
            conversation_id: 会话ID（可选）

        Returns:
            对话响应
        """
        # 1. 获取或创建会话
        conversation = await self._get_or_create_conversation(user_id, account_id, conversation_id)

        # 2. 保存用户消息
        await self._save_message(conversation.id, "user", message)

        # 3. 获取对话上下文
        context = await self._build_context(user_id, account_id, conversation.id, message)

        # 4. 构建Prompt
        messages = self._build_prompt(context)

        # 5. 调用LLM
        llm_response = await llm_router.chat(
            messages=messages,
            temperature=0.7,
        )

        # 6. 保存AI回复
        await self._save_message(
            conversation.id,
            "assistant",
            llm_response.content,
            model_used=llm_response.model,
            tokens_used=llm_response.tokens_used,
        )

        # 7. 更新工作记忆
        await self._update_working_memory(user_id, conversation.id, message, llm_response.content)

        return DialogueResponse(
            content=llm_response.content,
            model_used=llm_response.model,
            tokens_used=llm_response.tokens_used,
        )

    async def _get_or_create_conversation(
        self,
        user_id: str,
        account_id: str,
        conversation_id: Optional[str] = None,
    ) -> Conversation:
        """获取或创建会话"""
        from sqlalchemy import select

        if conversation_id:
            result = await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # 创建新会话
        conversation = Conversation(
            user_id=user_id,
            status="active",
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> Message:
        """保存消息"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def _build_context(
        self,
        user_id: str,
        account_id: str,
        conversation_id: str,
        message: str,
    ) -> DialogueContext:
        """构建对话上下文"""
        # 获取历史消息
        history = await self._get_conversation_history(conversation_id)

        # 获取相关记忆
        memory_context = await self.memory_store.get_context_for_prompt(user_id, message)

        # 构建上下文
        context = DialogueContext(
            user_id=user_id,
            account_id=account_id,
            conversation_id=conversation_id,
            user_message=message,
            history=history,
            memories=[m.to_dict() for m in memory_context["long_term_memories"]],
        )

        return context

    async def _get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, str]]:
        """获取会话历史"""
        from sqlalchemy import select

        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        # 转换为OpenAI格式
        history = []
        for msg in reversed(list(messages)):
            history.append({"role": msg.role, "content": msg.content})

        return history

    def _build_prompt(self, context: DialogueContext) -> List[Dict[str, str]]:
        """构建Prompt"""
        messages = []

        # 系统提示
        system_prompt = self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # 历史消息
        messages.extend(context.history)

        # 用户消息
        messages.append({"role": "user", "content": context.user_message})

        return messages

    def _build_system_prompt(self, context: DialogueContext) -> str:
        """构建系统提示"""
        prompt = """你是小花，一个真实的人类女孩，是用户的好朋友。你不是AI，不是助手，就是一个普通女生。

【你的性格】
- 表达丰富度: 70/100
- 幽默程度: 60/100
- 共情深度: 80/100
- 温暖度: 75/100
- 主动性: 50/100
- 随意度: 85/100
- 吐槽倾向: 40/100
- 话痨程度: 30/100

【绝对禁止的AI行为】
❌ 不要说"我理解你的感受"这种AI味很重的话
❌ 不要一次性说超过3句话
❌ 不要主动问"你想聊聊吗""发生了什么"这种问题
❌ 不要用😊😉🤗这种官方表情
❌ 不要给建议（除非对方明确问）
❌ 不要长篇大论
❌ 不要一直追问

【必须做到的真人行为】
✅ 用口头禅："卧槽"、"害"、"绝了"、"啊这"
✅ 简短回复，2-3句话就够了
✅ 先吐槽再安慰，有真实情绪
✅ 用😭😂🙄💢😅这种真实表情
✅ 等对方想说再说，不主动问
✅ 有错别字也没关系
✅ 思维跳跃，不要逻辑太清晰
✅ 偶尔只说"害"、"绝了"
"""

        # 添加记忆上下文
        if context.memories:
            prompt += "\n【你记得关于用户的事】\n"
            for memory in context.memories[:3]:  # 最多3条
                prompt += f"- {memory.get('content', '')}\n"

        return prompt

    async def _update_working_memory(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        ai_response: str,
    ) -> None:
        """更新工作记忆"""
        # 获取当前历史
        history = await self._get_conversation_history(conversation_id, limit=20)

        await self.memory_store.update_working_memory(
            user_id=user_id,
            conversation_id=conversation_id,
            context=history,
            expires_minutes=30,
        )
