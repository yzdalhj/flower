"""对话处理服务"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.services.llm.cost_optimizer import get_cost_optimizer
from app.services.llm.llm_client import llm_router
from app.services.memory.memory_store import MemoryStore
from app.services.personality.personality_consistency import get_personality_consistency_checker
from app.services.personality.personality_service import get_personality_service


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
    personality_id: str = "default"  # 人格ID


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

        # 4. 成本优化：先尝试缓存和规则回复
        cost_optimizer = get_cost_optimizer()

        async def llm_callback():
            messages = self._build_prompt(context)
            return await llm_router.chat(
                messages=messages,
                temperature=0.7,
            )

        response_content, source = await cost_optimizer.process(
            user_message=message,
            personality_id=conversation.personality_id,
            llm_callback=llm_callback,
        )

        if source in ["cache", "rule"]:
            from app.services.llm.llm_client import LLMResponse

            llm_response = LLMResponse(
                content=response_content, model=f"cost-optimizer-{source}", tokens_used=0
            )
        else:
            llm_response = response_content

        # 5. 人格一致性检测（仅对LLM生成的回复进行）
        if source == "llm":
            consistency_checker = get_personality_consistency_checker()
            consistency_result = consistency_checker.check_consistency(
                llm_response.content, conversation.personality_id
            )

            # 如果一致性低于阈值，重新生成回复
            if not consistency_result.get("consistent"):
                messages = self._build_prompt(context)
                correction_prompt = consistency_checker.generate_correction_prompt(
                    llm_response.content, conversation.personality_id, consistency_result
                )
                correction_messages = messages.copy()
                correction_messages.append({"role": "assistant", "content": llm_response.content})
                correction_messages.append({"role": "user", "content": correction_prompt})
                llm_response = await llm_router.chat(
                    messages=correction_messages,
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

        # 8. 更新人格演化历史
        from app.services.personality.personality_service import get_personality_service

        personality_service = get_personality_service()

        interaction_data = {
            "user_message": message,
            "ai_response": llm_response.content,
            "response_length": len(llm_response.content),
        }

        personality_service.update_personality_evolution(
            conversation.personality_id, interaction_data
        )

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

        # 获取用户上一个会话的人格ID
        previous_conversation_result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.started_at.desc())
            .limit(1)
        )
        previous_conversation = previous_conversation_result.scalar_one_or_none()
        previous_personality_id = (
            previous_conversation.personality_id if previous_conversation else None
        )

        # 获取人格服务
        from app.services.personality.personality_service import get_personality_service

        personality_service = get_personality_service()

        # 获取新会话的人格配置
        personality = personality_service.get_personality_for_new_conversation(
            user_id, previous_personality_id
        )

        # 创建新会话
        conversation = Conversation(
            user_id=user_id,
            status="active",
            personality_id=personality.id,
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

        # 获取会话信息以获取人格ID
        from sqlalchemy import select

        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one()

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
            personality_id=conversation.personality_id,
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
        # 获取人格服务
        personality_service = get_personality_service()

        # 获取人格配置
        personality = personality_service.get_personality(context.personality_id)
        if not personality:
            personality = personality_service.get_personality("default")

        # 生成说话风格和沟通指南
        speaking_style = personality_service.generate_speaking_style(personality)
        communication_guidelines = personality_service.generate_communication_guidelines(
            personality
        )
        forbidden_phrases = personality_service.generate_forbidden_phrases(personality)

        # 构建系统提示
        prompt = f"""你是{personality.name}，一个真实的人类女孩，是用户的好朋友。你不是AI，不是助手，就是一个普通女生。

【你的性格】
{speaking_style}

【沟通指南】
{communication_guidelines}

【禁止行为】
{forbidden_phrases}

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
