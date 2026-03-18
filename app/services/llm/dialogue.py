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
    sticker: Optional[Dict[str, Any]] = None  # 表情包信息
    sticker_send_mode: str = "no_sticker"  # "only_sticker", "text_with_sticker", "no_sticker"
    conversation_id: Optional[str] = None  # 对话ID


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
            messages = await self._build_prompt(context)
            return await llm_router.chat(
                messages=messages,
                temperature=0.7,
                db=self.session,
                user_id=user_id,
                conversation_id=conversation.id,
                operation="dialogue_chat",
            )

        response_content, source = await cost_optimizer.process(
            user_message=message,
            personality_id=conversation.personality_id,
            llm_callback=llm_callback,
        )

        if source == "cache":
            from app.services.llm.llm_client import LLMResponse

            llm_response = LLMResponse(
                content=response_content, model=f"cost-optimizer-{source}", tokens_used=0
            )
        else:
            # source == "llm", response_content 是字符串，需要包装成 LLMResponse
            from app.services.llm.llm_client import LLMResponse

            llm_response = LLMResponse(content=response_content, model="llm", tokens_used=0)

            # 5. 人格一致性检测（对所有回复进行）
            consistency_checker = get_personality_consistency_checker()
            consistency_result = consistency_checker.check_consistency(
                llm_response.content, conversation.personality_id
            )

            # 如果一致性低于阈值，重新生成回复
            if not consistency_result.get("consistent"):
                messages = await self._build_prompt(context)
                correction_prompt = consistency_checker.generate_correction_prompt(
                    llm_response.content, conversation.personality_id, consistency_result
                )
                correction_messages = messages.copy()
                correction_messages.append({"role": "assistant", "content": llm_response.content})
                correction_messages.append({"role": "user", "content": correction_prompt})
                llm_response = await llm_router.chat(
                    messages=correction_messages,
                    temperature=0.7,
                    db=self.session,
                    user_id=user_id,
                    conversation_id=conversation.id,
                    operation="personality_correction",
                )

        # 6. 智能选择网络梗图表情包
        sticker_info = None
        sticker_send_mode = "no_sticker"
        try:
            # 分析回复的情绪
            response_emotion = self._analyze_emotion(llm_response.content)
            print(f"[StickerDebug] 情绪分析结果: {response_emotion}")

            # 智能判断是否需要发送梗图
            should_send = self._should_send_meme(llm_response.content, response_emotion)
            print(f"[StickerDebug] 是否应该发送梗图: {should_send}")

            if not should_send:
                print("[StickerDebug] 根据语境判断不需要发送梗图")
            else:
                print("[StickerDebug] 开始选择梗图...")
                # 创建表情包选择器，强制只选择网络梗图
                sticker_selector = StickerSelector(self.session)

                # 提取上下文关键词
                context_keywords = self._extract_keywords(message + " " + llm_response.content)
                print(f"[StickerDebug] 上下文关键词: {context_keywords}")

                # 选择梗图，强制只选择网络梗图类型
                sticker, sticker_send_mode = await sticker_selector.select_stickers_for_reply(
                    current_emotion=response_emotion,
                    personality_type=conversation.personality_id,
                    context_keywords=context_keywords,
                    is_serious_context=False,
                    sticker_type_filter="meme",
                )

                print(
                    f"[StickerDebug] 选择结果 - sticker: {sticker}, send_mode: {sticker_send_mode}"
                )

                if sticker:
                    sticker_info = sticker.to_dict()
                    print(
                        f"[StickerDebug] 成功获取梗图: {sticker_info.get('name')} - URL: {sticker_info.get('url')}"
                    )
                else:
                    print("[StickerDebug] 未找到合适的梗图")
        except Exception as e:
            # 梗图选择失败不影响主流程
            print(f"[StickerDebug] 梗图选择异常: {e}")
            import traceback

            traceback.print_exc()
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
            # 每个消息保存后立即提交，让前端能读到最新数据
            await self.session.commit()
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

        # 10. 更新会话标题和预览（如果是新会话或消息数较少）
        try:
            await self._update_conversation_title(conversation, message, llm_response.content)
        except Exception as e:
            print(f"[DialogueProcessor] 更新会话标题失败: {e}")

        # 11. 异步提取对话记忆（不阻塞回复）
        # 注意：不在此处执行，避免会话关闭后使用问题
        # 记忆提取由独立调度器处理

        return DialogueResponse(
            content=llm_response.content,
            model_used=llm_response.model,
            tokens_used=llm_response.tokens_used,
            sticker=sticker_info,
            sticker_send_mode=sticker_send_mode,
            conversation_id=conversation.id,
        )

    async def _get_or_create_conversation(
        self,
        user_id: str,
        account_id: str,
        conversation_id: Optional[str] = None,
    ) -> Conversation:
        """获取或创建会话"""
        from sqlalchemy import select

        # 确保用户存在
        await self._ensure_user_exists(user_id, account_id)

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

    async def _ensure_user_exists(self, user_id: str, account_id: str) -> None:
        """确保用户存在，如果不存在则创建"""
        from sqlalchemy import select

        from app.models.user import User

        result = await self.session.execute(select(User).where(User.id == user_id).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            # 创建新用户
            user = User(
                id=user_id,
                account_id=account_id,
                platform_user_id=user_id,
                platform_type="web",
                nickname="用户" + user_id[:6],
            )
            self.session.add(user)
            await self.session.commit()
            print(f"[DialogueProcessor] 创建新用户: {user_id}")

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        sticker_id: Optional[int] = None,
    ) -> Message:
        """保存消息"""
        from sqlalchemy import select

        from app.models.conversation import Conversation

        # 保存消息
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
            sticker_id=sticker_id,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        # 更新会话的消息数和最后消息时间
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.message_count += 1
            conversation.last_message_at = message.created_at
            await self.session.commit()

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

        # 获取用户画像
        from app.services.profile.profile_service import UserProfileService

        profile_service = UserProfileService()
        user_profile = await profile_service.get_profile(user_id)

        # 构建上下文
        context = DialogueContext(
            user_id=user_id,
            account_id=account_id,
            conversation_id=conversation_id,
            user_message=message,
            history=history,
            memories=[m.to_dict() for m in memory_context["long_term_memories"]],
            user_profile=user_profile.to_dict() if user_profile else None,
            personality_id=conversation.personality_id,
        )

        return context

    async def _get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, str]]:
        """获取会话历史"""
        from sqlalchemy import select

        # 获取最近的消息（按时间倒序获取，然后反转保持正序）
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        # 转换为OpenAI格式（反转回正序：从早到晚）
        history = []
        for msg in reversed(list(messages)):
            # 过滤掉内容中的表情包标记，避免AI学习这个模式
            content = self._clean_message_content(msg.content)
            history.append({"role": msg.role, "content": content})

        return history

    async def _build_prompt(self, context: DialogueContext) -> List[Dict[str, str]]:
        """构建Prompt"""
        messages = []

        # 系统提示
        system_prompt = await self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # 历史消息
        messages.extend(context.history)

        # 用户消息
        messages.append({"role": "user", "content": context.user_message})

        return messages

    async def _build_system_prompt(self, context: DialogueContext) -> str:
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

        # 准备模板变量
        variables = {
            "personality_name": personality.name,
            "speaking_style": speaking_style,
            "communication_guidelines": communication_guidelines,
            "forbidden_phrases": forbidden_phrases,
        }

        # 从Prompt模板服务构建Prompt
        from app.services.prompt_template_service import get_prompt_template_service

        prompt_service = await get_prompt_template_service(self.session)
        template_prompt = await prompt_service.build_prompt_for_personality(
            context.personality_id, variables
        )

        # 使用从数据库加载的模板
        prompt = template_prompt

        # 添加用户画像
        if context.user_profile:
            prompt += "\n【用户画像】\n"
            if context.user_profile.get("interests"):
                prompt += f"兴趣爱好: {', '.join(context.user_profile['interests'])}\n"
            if context.user_profile.get("preferences"):
                prefs = context.user_profile["preferences"]
                if isinstance(prefs, dict):
                    for key, value in prefs.items():
                        prompt += f"{key}: {value}\n"

        # 添加记忆上下文
        if context.memories:
            prompt += "\n【你记得关于用户的事】\n"
            for memory in context.memories[:3]:  # 最多3条
                content = memory.get("content", "")
                memory_type = memory.get("memory_type", "")
                # 根据记忆类型添加前缀，帮助AI理解信息来源
                if memory_type in ["ai_promise", "ai_suggestion"]:
                    prefix = "[你之前说过] "
                elif content.startswith("[AI]"):
                    prefix = "[你之前说过] "
                else:
                    prefix = ""
                prompt += f"- {prefix}{content}\n"

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

    async def _update_conversation_title(
        self,
        conversation: Any,
        user_message: str,
        ai_response: str,
    ) -> None:
        """更新会话标题和预览"""
        # 更新最后消息预览
        preview = user_message[:50] + "..." if len(user_message) > 50 else user_message
        conversation.last_message_preview = preview

        # 如果消息数小于4条，生成标题
        if conversation.message_count <= 4 and not conversation.title:
            # 使用LLM生成标题
            title = await self._generate_conversation_title(user_message, ai_response)
            if title:
                conversation.title = title

        await self.session.commit()

    async def _generate_conversation_title(
        self,
        user_message: str,
        ai_response: str,
    ) -> str:
        """使用LLM生成会话标题"""
        prompt = f"""请根据以下对话内容，生成一个简短的会话标题（10个字以内）。

用户: {user_message[:100]}
AI: {ai_response[:100]}

标题要求:
1. 简短精炼，10个字以内
2. 概括对话主题
3. 不要使用标点符号
4. 直接返回标题，不要解释

标题:"""

        try:
            response = await llm_router.chat(
                messages=[
                    {"role": "system", "content": "你是一个标题生成助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                db=self.session,
                operation="generate_conversation_title",
            )

            title = response.content.strip().replace('"', "").replace('"', "")
            # 限制长度
            if len(title) > 15:
                title = title[:15]
            return title

        except Exception as e:
            print(f"[DialogueProcessor] 生成标题失败: {e}")
            return ""

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

    def _clean_message_content(self, content: str) -> str:
        """清理消息内容，移除表情包标记等内部标记

        避免AI从历史消息中学习到 '[表情包：xxx]' 这种标记格式
        """
        import re

        # 移除表情包标记，如：[表情包：xxx.gif] 或 [表情包：xxx.jpg]
        cleaned = re.sub(r"\[表情包：[^\]]+\]\s*", "", content)
        return cleaned.strip()

    def _should_send_meme(self, text: str, emotion: Dict[str, float]) -> bool:
        """智能判断是否应该发送梗图表情包

        只在以下情况发送梗图:
        1. 文本较短（短句适合搭配梗图）
        2. 情绪强度足够高（有明显情绪才需要梗图表达）
        3. 不包含严肃关键词（严肃话题不适合发梗图）
        4. 不是问答/教程类内容
        """
        # 规则1：文本太长 -> 不发（长文通常是正经回答）
        if len(text) > 150:
            return False

        # 规则2：检测严肃关键词 -> 不发
        serious_keywords = [
            "严重",
            "重要",
            "紧急",
            "必须",
            "应该",
            "需要",
            "严肃",
            "认真",
            "正式",
            "官方",
            "法律",
            "规定",
            "通知",
            "公告",
            "警告",
            "提醒",
            "建议",
            "指导",
            "帮助",
            "解决",
            "问题",
            "错误",
            "修复",
            "bug",
            "教程",
            "步骤",
            "方法",
            "如何",
            "怎么",
            "请告诉我",
            "解释",
            "说明",
            "介绍",
            "教学",
            "课程",
        ]
        text_lower = text.lower()
        for keyword in serious_keywords:
            if keyword in text_lower:
                return False

        # 规则3：问答内容 -> 不发
        question_marks = text.count("？") + text.count("?")
        if question_marks >= 2:
            return False

        # 规则4：情绪强度太低 -> 不发
        max_emotion = max(emotion.values()) if emotion else 0
        if max_emotion < 0.3:
            return False

        # 规则5：列表/代码块 -> 不发
        if "\n-" in text or "\n1." in text or "```" in text:
            return False

        # 通过所有规则 -> 可以发送梗图
        return True

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
