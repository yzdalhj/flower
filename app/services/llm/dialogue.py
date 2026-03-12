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
from app.services.sticker.sticker_selector import StickerSelector


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
    sticker: Optional[Dict] = None  # 表情包信息
    sticker_send_mode: str = "no_sticker"  # "only_sticker", "text_with_sticker", "no_sticker"


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
            # source == "llm", response_content 是字符串，需要包装成 LLMResponse
            from app.services.llm.llm_client import LLMResponse

            llm_response = LLMResponse(content=response_content, model="llm", tokens_used=0)

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

        # 6. 智能选择表情包
        sticker_info = None
        sticker_send_mode = "no_sticker"
        try:
            # 分析回复的情绪
            response_emotion = self._analyze_emotion(llm_response.content)

            # 创建表情包选择器
            sticker_selector = StickerSelector(self.session)

            # 提取上下文关键词
            context_keywords = self._extract_keywords(message + " " + llm_response.content)

            # 选择表情包
            sticker, sticker_send_mode = await sticker_selector.select_stickers_for_reply(
                current_emotion=response_emotion,
                personality_type=conversation.personality_id,
                context_keywords=context_keywords,
                is_serious_context=False,  # 可以根据内容判断
            )

            if sticker:
                sticker_info = sticker.to_dict()
        except Exception:
            # 表情包选择失败不影响主流程
            pass

        # 7. 拆分长句并保存AI回复
        # 如果回复太长，拆分成多条短消息
        message_parts = self._split_long_message(llm_response.content)

        for i, part in enumerate(message_parts):
            await self._save_message(
                conversation.id,
                "assistant",
                part,
                model_used=llm_response.model if i == 0 else f"{llm_response.model}-part{i+1}",
                tokens_used=llm_response.tokens_used // len(message_parts) if i == 0 else 0,
            )
            # 添加短暂延迟，模拟真实打字节奏
            if i < len(message_parts) - 1:
                import asyncio

                await asyncio.sleep(0.5)

        # 8. 更新工作记忆（使用完整内容）
        await self._update_working_memory(user_id, conversation.id, message, llm_response.content)

        # 9. 更新人格演化历史
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
            sticker=sticker_info,
            sticker_send_mode=sticker_send_mode,
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

【说话风格 - 必须严格遵守】
1. 简短直接：2-3句话就够了，不要长篇大论
2. 真实情绪：先吐槽再安慰，有真实情绪反应
3. 思维跳跃：不要逻辑太清晰，像真人一样想到哪说到哪
4. 不完美：有错别字也没关系，不要太工整
5. 长句拆分：如果内容多，分成多条短消息发送，每条只表达一个意思
   - 每条消息控制在15-25字以内
   - 像真人打字一样，想到哪说到哪，不要一次性说完
   - 可以分成2-3条消息连续发送，模拟真实聊天节奏

【网络梗使用】
可以适量使用网络流行语和梗，让对话更自然有趣：
- 根据语境自然融入，不要生硬堆砌
- 适度使用，不要每句话都带梗
- 选择符合当下年轻人交流习惯的表达

【表情使用】
用真实表情，不要用官方表情：
- 开心/搞笑：�、🤣、😆、��
- 无奈/无语：�、�、🤦
- 生气：💢、�
- 其他：😏、🤪、👌

【绝对禁止的AI用语】
❌ "我理解你的感受"
❌ "有什么可以帮助您的"
❌ "作为AI"
❌ "很高兴为您服务"
❌ "感谢您的理解"
❌ "我建议"
❌ "让我想想"
❌ "请问"
❌ "您"（用"你"）

【回复示例】
用户：今天工作好累啊
好的回复："卧槽，这么惨😂 我也是，今天差点原地去世"
差的回复："我理解你的感受，工作确实很辛苦。建议您适当休息一下。"

用户：我分手了
好的回复："害，别难过，下一个更乖😏 走，晚上请你喝奶茶"
差的回复："我很抱歉听到这个消息。分手确实是一件令人难过的事情。"
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

    def _analyze_emotion(self, text: str) -> Dict[str, float]:
        """分析文本情绪"""
        # 简单的关键词情绪分析
        emotion_keywords = {
            "happy": ["开心", "高兴", "哈哈", "棒", "赞", "好耶", "太好了", "😊", "😄", "😁"],
            "excited": ["激动", "兴奋", "太棒了", "哇", "厉害", "牛", "冲", "🔥", "💪"],
            "sad": ["难过", "伤心", "哭", "呜呜", "😢", "😭", "😔", "唉", "害"],
            "angry": ["生气", "气死", "哼", "😤", "😠", "💢", "滚", "无语"],
            "surprised": ["惊讶", "震惊", "不会吧", "真的吗", "😲", "😮", "哇哦"],
            "confused": ["困惑", "不懂", "什么", "？", "🤔", "😕", "啊这"],
            "loving": ["喜欢", "爱你", "可爱", "❤️", "😍", "🥰", "比心"],
            "embarrassed": ["尴尬", "害羞", "😅", "😳", "捂脸", "汗"],
            "proud": ["骄傲", "厉害", "得意", "😎", "✌️", "叉腰"],
            "relaxed": ["放松", "悠闲", "😌", "☕", "喝茶", "摸鱼"],
            "silly": ["搞怪", "哈哈", "😂", "🤣", "doge", "狗头"],
            "supportive": ["加油", "没事", "抱抱", "摸摸头", "💪", "🤗"],
        }

        emotions = {}
        text_lower = text.lower()

        for emotion, keywords in emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.3  # 每个关键词增加0.3分
            if score > 0:
                emotions[emotion] = min(1.0, score)

        # 如果没有检测到情绪，默认给一些中性情绪
        if not emotions:
            emotions = {"happy": 0.3, "relaxed": 0.2}

        return emotions

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（实际应用中可以使用NLP工具）
        # 这里使用简单的分词和过滤
        import re

        # 去除标点符号
        text = re.sub(r"[^\w\s]", " ", text)

        # 分词
        words = text.split()

        # 过滤停用词（简单示例）
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
        }

        keywords = []
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)

        # 返回前5个关键词
        return keywords[:5]

    def _split_long_message(self, text: str) -> List[str]:
        """拆分长消息为多条短消息"""
        # 如果消息较短，直接返回
        if len(text) <= 25:
            return [text]

        # 按标点符号拆分
        import re

        # 先按句号、问号、感叹号拆分
        parts = re.split(r"([。！？]+)", text)

        # 合并标点符号到前一句
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if parts[i]:
                sentences.append(parts[i] + (parts[i + 1] if i + 1 < len(parts) else ""))
        if len(parts) % 2 == 1 and parts[-1]:
            sentences.append(parts[-1])

        # 如果没有拆分成功（没有标点），按长度强制拆分
        if not sentences:
            sentences = [text[i : i + 20] for i in range(0, len(text), 20)]

        # 合并短句，确保每条消息不要太短
        result = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= 25:
                current += sentence
            else:
                if current:
                    result.append(current.strip())
                current = sentence
        if current:
            result.append(current.strip())

        # 如果拆分后只有一条且原长度超过40，强制拆分
        if len(result) == 1 and len(text) > 40:
            mid = len(text) // 2
            # 在中间附近找空格或标点
            split_pos = mid
            for i in range(mid - 10, mid + 10):
                if i < len(text) and text[i] in "，。！？ ":
                    split_pos = i + 1
                    break
            result = [text[:split_pos].strip(), text[split_pos:].strip()]

        return result if result else [text]
