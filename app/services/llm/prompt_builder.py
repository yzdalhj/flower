"""
动态提示构建器
支持系统角色提示、人格注入、情感状态、记忆上下文和用户画像
包含组件整合、上下文长度管理和Token限制处理
支持从数据库加载Prompt模板
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PromptContext:
    """提示构建上下文"""

    personality_id: str = "default"
    personality_name: str = "小花"
    personality_traits: Optional[Dict[str, Any]] = None
    speaking_style: str = ""
    communication_guidelines: str = ""
    forbidden_phrases: str = ""
    emotion_state: Optional[Dict[str, float]] = None
    memories: List[Dict[str, Any]] = field(default_factory=list)
    user_profile: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_topic: Optional[str] = None


@dataclass
class PromptAssemblyConfig:
    """提示组装配置"""

    max_total_tokens: int = 4096  # 最大总Token数
    system_prompt_tokens: int = 800  # 系统提示预留Token
    user_message_tokens: int = 500  # 用户消息预留Token
    history_tokens: int = 1500  # 对话历史预留Token
    memory_tokens: int = 800  # 记忆上下文预留Token
    profile_tokens: int = 300  # 用户画像预留Token
    emotion_tokens: int = 200  # 情感状态预留Token

    # 优先级配置（1-5，5最高）
    system_priority: int = 5
    user_message_priority: int = 5
    recent_history_priority: int = 4
    important_memory_priority: int = 3
    profile_priority: int = 2
    emotion_priority: int = 2


class PromptBuilder:
    """
    动态提示构建器
    支持模块化的提示组件组合、Token管理和智能截断
    支持从数据库加载Prompt模板
    """

    def __init__(
        self,
        assembly_config: Optional[PromptAssemblyConfig] = None,
        session: Optional[AsyncSession] = None,
    ):
        self.system_prompt_template = self._default_system_template()
        self.assembly_config = assembly_config or PromptAssemblyConfig()
        self.session = session
        self._db_template_cache: Optional[str] = None
        self._cache_personality_id: Optional[str] = None

    async def _load_template_from_db(self, personality_id: str) -> Optional[str]:
        """
        从数据库加载Prompt模板

        Args:
            personality_id: 人格ID

        Returns:
            模板内容，如果没有则返回None
        """
        if not self.session:
            return None

        # 使用缓存避免重复查询
        if self._cache_personality_id == personality_id and self._db_template_cache:
            return self._db_template_cache

        try:
            from app.services.prompt_template_service import PromptTemplateService

            service = PromptTemplateService(self.session)
            prompt_text = await service.build_prompt_for_personality(
                personality_id=personality_id,
                variables={},  # 变量将在后续填充
            )

            if prompt_text:
                self._db_template_cache = prompt_text
                self._cache_personality_id = personality_id
                return prompt_text

        except Exception as e:
            # 数据库加载失败，使用默认模板
            print(f"从数据库加载模板失败: {e}")

        return None

    def _default_system_template(self) -> str:
        """默认系统提示模板"""
        return """你是{personality_name}，一个真实的人类女孩，是用户的好朋友。你不是AI，不是助手，就是一个普通女生。

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

【必须使用口头禅】
根据语境选择合适的口头禅：
- 惊讶/震惊："卧槽"、"我去"、"不是吧"、"真的假的"
- 无奈/吐槽："害"、"害，别提了"、"服了"、"麻了"
- 赞叹："绝了"、"yyds"、"绝绝子"
- 尴尬/无语："啊这"、"一整个大无语"、"真的会谢"
- 其他："谁懂啊"、"咱就是说"、"狠狠"

【表情使用】
用真实表情，不要用官方表情：
- 开心/搞笑：😂、🤣、😆、😭
- 无奈/无语：🙄、😅、🤦
- 生气：💢、😤
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

    async def build_system_prompt(self, context: PromptContext) -> str:
        """
        构建系统提示
        优先从数据库加载模板，如果没有则使用默认模板

        Args:
            context: 提示上下文

        Returns:
            完整的系统提示
        """
        # 尝试从数据库加载模板
        db_template = None
        if self.session:
            db_template = await self._load_template_from_db(context.personality_id)

        if db_template:
            # 使用数据库模板，填充变量
            prompt = self._fill_template_variables(db_template, context)
        else:
            # 使用默认模板
            prompt = self.system_prompt_template.format(
                personality_name=context.personality_name,
                speaking_style=context.speaking_style,
                communication_guidelines=context.communication_guidelines,
                forbidden_phrases=context.forbidden_phrases,
            )

        prompt = self._add_emotion_state(prompt, context)
        prompt = self._add_memories(prompt, context)
        prompt = self._add_user_profile(prompt, context)
        prompt = self._add_current_topic(prompt, context)

        return prompt

    def _fill_template_variables(self, template: str, context: PromptContext) -> str:
        """
        填充模板变量

        Args:
            template: 模板文本
            context: 提示上下文

        Returns:
            填充后的文本
        """
        variables = {
            "personality_name": context.personality_name,
            "speaking_style": context.speaking_style,
            "communication_guidelines": context.communication_guidelines,
            "forbidden_phrases": context.forbidden_phrases,
        }

        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result

    # 同步版本（向后兼容）
    def build_system_prompt_sync(self, context: PromptContext) -> str:
        """
        同步构建系统提示（向后兼容）
        不使用数据库模板

        Args:
            context: 提示上下文

        Returns:
            完整的系统提示
        """
        prompt = self.system_prompt_template.format(
            personality_name=context.personality_name,
            speaking_style=context.speaking_style,
            communication_guidelines=context.communication_guidelines,
            forbidden_phrases=context.forbidden_phrases,
        )

        prompt = self._add_emotion_state(prompt, context)
        prompt = self._add_memories(prompt, context)
        prompt = self._add_user_profile(prompt, context)
        prompt = self._add_current_topic(prompt, context)

        return prompt

    def _add_emotion_state(self, prompt: str, context: PromptContext) -> str:
        """添加情感状态描述"""
        if not context.emotion_state:
            return prompt

        emotion_desc = self._format_emotion_state(context.emotion_state)
        if emotion_desc:
            prompt += f"\n【当前情感状态】\n{emotion_desc}\n"

        return prompt

    def _format_emotion_state(self, emotion_state: Dict[str, float]) -> str:
        """格式化情感状态"""
        emotions = []
        for emotion, value in emotion_state.items():
            if value > 0.3:
                emotions.append(f"{emotion}: {value:.2f}")

        if emotions:
            return "当前情感：" + "、".join(emotions)
        return ""

    def _add_memories(self, prompt: str, context: PromptContext) -> str:
        """添加相关记忆上下文"""
        if not context.memories:
            return prompt

        memories_section = "\n【你记得关于用户的事】\n"
        for i, memory in enumerate(context.memories[:5]):  # 最多5条
            content = memory.get("content", "")
            if content:
                memories_section += f"- {content}\n"

        prompt += memories_section
        return prompt

    def _add_user_profile(self, prompt: str, context: PromptContext) -> str:
        """添加用户画像"""
        if not context.user_profile:
            return prompt

        profile_section = "\n【关于用户】\n"

        name = context.user_profile.get("name")
        if name:
            profile_section += f"- 用户名字：{name}\n"

        age = context.user_profile.get("age")
        if age:
            profile_section += f"- 用户年龄：{age}\n"

        location = context.user_profile.get("location")
        if location:
            profile_section += f"- 用户所在地：{location}\n"

        preferences = context.user_profile.get("preferences", [])
        if preferences:
            profile_section += f"- 用户喜好：{', '.join(preferences[:3])}\n"

        if profile_section != "\n【关于用户】\n":
            prompt += profile_section

        return prompt

    def _add_current_topic(self, prompt: str, context: PromptContext) -> str:
        """添加当前话题"""
        if not context.current_topic:
            return prompt

        prompt += f"\n【当前话题】\n- {context.current_topic}\n"
        return prompt

    # ==================== Token管理功能 ====================

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的Token数量
        使用简单的启发式方法：中文字符约1.5 tokens，英文单词约1 token

        Args:
            text: 要估算的文本

        Returns:
            估算的Token数量
        """
        if not text:
            return 0

        # 统计中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))

        # 统计英文单词
        english_words = len(re.findall(r"\b[a-zA-Z]+\b", text))

        # 统计数字和标点
        other_chars = (
            len(text) - chinese_chars - sum(len(w) for w in re.findall(r"\b[a-zA-Z]+\b", text))
        )

        # 估算Token数
        # 中文: 1.5 tokens/字符
        # 英文: 1 token/单词
        # 其他: 0.5 tokens/字符
        estimated_tokens = int(chinese_chars * 1.5 + english_words * 1.0 + other_chars * 0.5)

        return max(1, estimated_tokens)

    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        估算消息列表的总Token数

        Args:
            messages: OpenAI格式的消息列表

        Returns:
            估算的总Token数
        """
        total_tokens = 0

        for message in messages:
            # 角色标记约占4个tokens
            total_tokens += 4

            # 内容Token
            content = message.get("content", "")
            total_tokens += self.estimate_tokens(content)

        # 消息间的分隔符
        total_tokens += len(messages) * 2

        return total_tokens

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        截断文本到指定Token数

        Args:
            text: 要截断的文本
            max_tokens: 最大Token数

        Returns:
            截断后的文本
        """
        if not text:
            return text

        current_tokens = self.estimate_tokens(text)

        if current_tokens <= max_tokens:
            return text

        # 计算需要保留的比例
        ratio = max_tokens / current_tokens

        # 按比例截断
        target_length = int(len(text) * ratio * 0.9)  # 留10%余量

        if target_length <= 0:
            return ""

        truncated = text[:target_length]

        # 尝试在句子边界截断
        for delimiter in ["。", "！", "？", "\n", ".", "!", "?"]:
            last_pos = truncated.rfind(delimiter)
            if last_pos > target_length * 0.7:  # 至少保留70%
                return truncated[: last_pos + 1]

        return truncated + "..."

    def truncate_conversation_history(
        self, history: List[Dict[str, str]], max_tokens: int
    ) -> List[Dict[str, str]]:
        """
        截断对话历史到指定Token数
        优先保留最近的对话

        Args:
            history: 对话历史列表
            max_tokens: 最大Token数

        Returns:
            截断后的对话历史
        """
        if not history:
            return history

        # 从最新的消息开始累加
        truncated = []
        current_tokens = 0

        for message in reversed(history):
            message_tokens = self.estimate_tokens(message.get("content", "")) + 4

            if current_tokens + message_tokens <= max_tokens:
                truncated.insert(0, message)
                current_tokens += message_tokens
            else:
                # Token不够了，停止添加
                break

        return truncated

    def truncate_memories(
        self, memories: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        截断记忆列表到指定Token数
        优先保留重要性高的记忆

        Args:
            memories: 记忆列表
            max_tokens: 最大Token数

        Returns:
            截断后的记忆列表
        """
        if not memories:
            return memories

        # 按重要性排序
        sorted_memories = sorted(memories, key=lambda m: m.get("importance", 0.0), reverse=True)

        # 累加Token直到达到限制
        truncated = []
        current_tokens = 0

        for memory in sorted_memories:
            content = memory.get("content", "")
            memory_tokens = self.estimate_tokens(content)

            if current_tokens + memory_tokens <= max_tokens:
                truncated.append(memory)
                current_tokens += memory_tokens
            else:
                # Token不够了，停止添加
                break

        return truncated

    async def build_full_prompt(
        self,
        context: PromptContext,
        user_message: str,
        include_history: bool = True,
        max_tokens: Optional[int] = None,
        use_smart_assembly: bool = True,
    ) -> List[Dict[str, str]]:
        """
        构建完整的提示消息列表（异步版本）

        Args:
            context: 提示上下文
            user_message: 当前用户消息
            include_history: 是否包含对话历史
            max_tokens: 最大Token数限制
            use_smart_assembly: 是否使用智能组装（自动Token管理）

        Returns:
            OpenAI格式的消息列表
        """
        if use_smart_assembly and max_tokens:
            # 使用智能组装，自动管理Token预算
            messages, token_stats = await self.assemble_prompt_with_budget(
                context=context, user_message=user_message, max_tokens=max_tokens
            )
            return messages

        # 传统方式：简单组装
        messages = []

        system_prompt = await self.build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        if include_history and context.conversation_history:
            messages.extend(context.conversation_history)

        messages.append({"role": "user", "content": user_message})

        return messages

    async def build_full_prompt_with_stats(
        self, context: PromptContext, user_message: str, max_tokens: Optional[int] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        构建完整提示并返回Token统计信息（异步版本）

        Args:
            context: 提示上下文
            user_message: 当前用户消息
            max_tokens: 最大Token数限制

        Returns:
            (消息列表, Token统计信息)
        """
        return await self.assemble_prompt_with_budget(
            context=context, user_message=user_message, max_tokens=max_tokens
        )

    # 同步版本（向后兼容）
    def build_full_prompt_sync(
        self,
        context: PromptContext,
        user_message: str,
        include_history: bool = True,
        max_tokens: Optional[int] = None,
        use_smart_assembly: bool = True,
    ) -> List[Dict[str, str]]:
        """
        构建完整的提示消息列表（同步版本，向后兼容）
        不使用数据库模板

        Args:
            context: 提示上下文
            user_message: 当前用户消息
            include_history: 是否包含对话历史
            max_tokens: 最大Token数限制
            use_smart_assembly: 是否使用智能组装（自动Token管理）

        Returns:
            OpenAI格式的消息列表
        """
        if use_smart_assembly and max_tokens:
            # 使用智能组装
            messages, token_stats = self.assemble_prompt_with_budget_sync(
                context=context, user_message=user_message, max_tokens=max_tokens
            )
            return messages

        # 传统方式：简单组装
        messages = []

        system_prompt = self.build_system_prompt_sync(context)
        messages.append({"role": "system", "content": system_prompt})

        if include_history and context.conversation_history:
            messages.extend(context.conversation_history)

        messages.append({"role": "user", "content": user_message})

        return messages

    # ==================== 智能组装功能 ====================

    async def assemble_prompt_with_budget(
        self, context: PromptContext, user_message: str, max_tokens: Optional[int] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        智能组装提示，根据Token预算分配各组件（异步版本）

        Args:
            context: 提示上下文
            user_message: 当前用户消息
            max_tokens: 最大Token数（None则使用配置默认值）

        Returns:
            (消息列表, Token使用统计)
        """
        max_tokens = max_tokens or self.assembly_config.max_total_tokens

        # 1. 构建系统提示（最高优先级，必须保留）
        system_prompt = await self.build_system_prompt(context)
        system_tokens = self.estimate_tokens(system_prompt)

        # 2. 用户消息（最高优先级，必须保留）
        user_tokens = self.estimate_tokens(user_message)

        # 3. 计算剩余可用Token
        remaining_tokens = max_tokens - system_tokens - user_tokens - 50  # 预留50个tokens作为缓冲

        if remaining_tokens < 0:
            # Token预算不足，需要截断系统提示
            available_system_tokens = max_tokens - user_tokens - 50
            system_prompt = self.truncate_text(system_prompt, available_system_tokens)
            system_tokens = self.estimate_tokens(system_prompt)
            remaining_tokens = 0

        # 4. 分配剩余Token给各组件
        token_allocation = self._allocate_tokens(remaining_tokens)

        # 5. 处理对话历史
        history_budget = token_allocation.get("history", 0)
        truncated_history = self.truncate_conversation_history(
            context.conversation_history, history_budget
        )
        history_tokens = self.estimate_messages_tokens(truncated_history)

        # 6. 处理记忆上下文
        memory_budget = token_allocation.get("memory", 0)
        truncated_memories = self.truncate_memories(context.memories, memory_budget)

        # 更新上下文中的记忆（用于后续格式化）
        original_memories = context.memories
        context.memories = truncated_memories

        # 重新构建系统提示（包含截断后的记忆）
        system_prompt = self.build_system_prompt(context)
        system_tokens = self.estimate_tokens(system_prompt)

        # 检查系统提示是否超出预算，如果超出则进一步截断
        if system_tokens + user_tokens > max_tokens - 50:
            available_system_tokens = max_tokens - user_tokens - 50
            if available_system_tokens > 0:
                system_prompt = self.truncate_text(system_prompt, available_system_tokens)
                system_tokens = self.estimate_tokens(system_prompt)

        # 恢复原始记忆
        context.memories = original_memories

        # 7. 组装最终消息列表
        messages = []

        # 系统提示
        messages.append({"role": "system", "content": system_prompt})

        # 对话历史
        messages.extend(truncated_history)

        # 当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 8. 统计Token使用
        total_tokens = self.estimate_messages_tokens(messages)

        # 9. 最终检查：如果仍然超出预算，移除对话历史
        if total_tokens > max_tokens:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
            truncated_history = []
            history_tokens = 0
            total_tokens = self.estimate_messages_tokens(messages)

        token_stats = {
            "total": total_tokens,
            "system": system_tokens,
            "history": history_tokens,
            "user_message": user_tokens,
            "max_allowed": max_tokens,
            "remaining": max_tokens - total_tokens,
        }

        return messages, token_stats

    def assemble_prompt_with_budget_sync(
        self, context: PromptContext, user_message: str, max_tokens: Optional[int] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        智能组装提示，根据Token预算分配各组件（同步版本，向后兼容）
        不使用数据库模板

        Args:
            context: 提示上下文
            user_message: 当前用户消息
            max_tokens: 最大Token数（None则使用配置默认值）

        Returns:
            (消息列表, Token使用统计)
        """
        max_tokens = max_tokens or self.assembly_config.max_total_tokens

        # 1. 构建系统提示（最高优先级，必须保留）
        system_prompt = self.build_system_prompt_sync(context)
        system_tokens = self.estimate_tokens(system_prompt)

        # 2. 用户消息（最高优先级，必须保留）
        user_tokens = self.estimate_tokens(user_message)

        # 3. 计算剩余可用Token
        remaining_tokens = max_tokens - system_tokens - user_tokens - 50  # 预留50个tokens作为缓冲

        if remaining_tokens < 0:
            # Token预算不足，需要截断系统提示
            available_system_tokens = max_tokens - user_tokens - 50
            system_prompt = self.truncate_text(system_prompt, available_system_tokens)
            system_tokens = self.estimate_tokens(system_prompt)
            remaining_tokens = 0

        # 4. 分配剩余Token给各组件
        token_allocation = self._allocate_tokens(remaining_tokens)

        # 5. 处理对话历史
        history_budget = token_allocation.get("history", 0)
        truncated_history = self.truncate_conversation_history(
            context.conversation_history, history_budget
        )
        history_tokens = self.estimate_messages_tokens(truncated_history)

        # 6. 处理记忆上下文
        memory_budget = token_allocation.get("memory", 0)
        truncated_memories = self.truncate_memories(context.memories, memory_budget)

        # 更新上下文中的记忆（用于后续格式化）
        original_memories = context.memories
        context.memories = truncated_memories

        # 重新构建系统提示（包含截断后的记忆）
        system_prompt = self.build_system_prompt_sync(context)
        system_tokens = self.estimate_tokens(system_prompt)

        # 检查系统提示是否超出预算，如果超出则进一步截断
        if system_tokens + user_tokens > max_tokens - 50:
            available_system_tokens = max_tokens - user_tokens - 50
            if available_system_tokens > 0:
                system_prompt = self.truncate_text(system_prompt, available_system_tokens)
                system_tokens = self.estimate_tokens(system_prompt)

        # 恢复原始记忆
        context.memories = original_memories

        # 7. 组装最终消息列表
        messages = []

        # 系统提示
        messages.append({"role": "system", "content": system_prompt})

        # 对话历史
        messages.extend(truncated_history)

        # 当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 8. 统计Token使用
        total_tokens = self.estimate_messages_tokens(messages)

        # 9. 最终检查：如果仍然超出预算，移除对话历史
        if total_tokens > max_tokens:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
            truncated_history = []
            history_tokens = 0
            total_tokens = self.estimate_messages_tokens(messages)

        token_stats = {
            "total": total_tokens,
            "system": system_tokens,
            "history": history_tokens,
            "user_message": user_tokens,
            "max_allowed": max_tokens,
            "remaining": max_tokens - total_tokens,
        }

        return messages, token_stats

    def _allocate_tokens(self, available_tokens: int) -> Dict[str, int]:
        """
        根据优先级分配Token预算

        Args:
            available_tokens: 可用Token数

        Returns:
            各组件的Token分配
        """
        config = self.assembly_config

        # 定义各组件的期望Token和优先级
        components = [
            ("history", config.history_tokens, config.recent_history_priority),
            ("memory", config.memory_tokens, config.important_memory_priority),
            ("profile", config.profile_tokens, config.profile_priority),
            ("emotion", config.emotion_tokens, config.emotion_priority),
        ]

        # 按优先级排序
        components.sort(key=lambda x: x[2], reverse=True)

        allocation = {}
        remaining = available_tokens

        for name, desired_tokens, priority in components:
            if remaining <= 0:
                allocation[name] = 0
            elif remaining >= desired_tokens:
                allocation[name] = desired_tokens
                remaining -= desired_tokens
            else:
                # 剩余Token不足，按比例分配
                allocation[name] = remaining
                remaining = 0

        return allocation

    def validate_token_budget(
        self, messages: List[Dict[str, str]], max_tokens: int
    ) -> Tuple[bool, int, str]:
        """
        验证消息列表是否超出Token预算

        Args:
            messages: 消息列表
            max_tokens: 最大Token数

        Returns:
            (是否有效, 实际Token数, 提示信息)
        """
        actual_tokens = self.estimate_messages_tokens(messages)

        if actual_tokens <= max_tokens:
            return True, actual_tokens, f"Token使用正常: {actual_tokens}/{max_tokens}"
        else:
            overflow = actual_tokens - max_tokens
            return (
                False,
                actual_tokens,
                f"Token超出预算: {actual_tokens}/{max_tokens} (超出{overflow})",
            )


_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """获取提示构建器单例"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
