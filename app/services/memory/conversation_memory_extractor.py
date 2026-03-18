"""
对话记忆提取服务
从对话内容中自动提取记忆，增强AI的拟人化回复
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Message
from app.models.memory import Memory
from app.services.llm.llm_client import llm_router


def serialize_meta_data(meta_data: Dict[str, Any]) -> str:
    """将元数据字典序列化为JSON字符串"""
    return json.dumps(meta_data, ensure_ascii=False)


class ConversationMemoryExtractor:
    """
    对话记忆提取器
    分析对话内容，提取有价值的记忆信息
    """

    # 记忆类型定义
    MEMORY_TYPES = {
        "episodic": "事件记忆",  # 具体发生的事情
        "semantic": "语义记忆",  # 事实、知识
        "emotional": "情感记忆",  # 情绪、感受
        "preference": "偏好记忆",  # 喜好、厌恶
        "habit": "习惯记忆",  # 行为习惯
        "relationship": "关系记忆",  # 人际关系
        "ai_promise": "AI承诺",  # AI对用户做出的承诺
        "ai_suggestion": "AI建议",  # AI给用户的建议
        "shared_topic": "共同话题",  # 双方共同讨论的话题
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def extract_from_conversation(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Message],
    ) -> List[Memory]:
        """
        从对话中提取记忆

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            messages: 消息列表

        Returns:
            提取的记忆列表
        """
        if len(messages) < 2:
            return []

        # 构建对话文本
        conversation_text = self._build_conversation_text(messages)

        # 使用LLM分析对话，提取记忆
        extracted_memories = await self._analyze_with_llm(
            conversation_text, user_id, conversation_id
        )

        # 保存记忆
        saved_memories = []
        for memory_data in extracted_memories:
            memory = await self._save_memory(user_id, memory_data, conversation_id)
            if memory:
                saved_memories.append(memory)

        return saved_memories

    def _build_conversation_text(self, messages: List[Message]) -> str:
        """构建对话文本"""
        lines = []
        for msg in messages:
            role = "用户" if msg.role == "user" else "AI"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    async def _analyze_with_llm(
        self, conversation_text: str, user_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """使用LLM分析对话，提取记忆"""
        prompt = f"""请分析以下对话，提取有价值的记忆信息。

对话内容（标注了用户和AI的发言）：
{conversation_text}

请从对话中提取以下类型的记忆（如果没有则不需要提取）：

**用户相关信息：**
1. **事件记忆 (episodic)** - 用户提到的具体事情、经历
   - 例：用户今天去了医院看病
   - 例：用户周末参加了朋友的婚礼

2. **语义记忆 (semantic)** - 用户的事实信息、知识
   - 例：用户是程序员，做后端开发
   - 例：用户住在上海

3. **情感记忆 (emotional)** - 用户的情绪、感受
   - 例：用户最近感到压力很大
   - 例：用户对某件事感到开心/难过

4. **偏好记忆 (preference)** - 用户的喜好、厌恶
   - 例：用户喜欢吃辣
   - 例：用户讨厌下雨天

5. **习惯记忆 (habit)** - 用户的行为习惯
   - 例：用户习惯晚上12点睡觉
   - 例：用户每天早上喝咖啡

6. **关系记忆 (relationship)** - 用户的人际关系
   - 例：用户有个男朋友叫小明
   - 例：用户和同事关系很好

**AI相关信息（重要）：**
7. **AI承诺 (ai_promise)** - AI对用户做出的承诺、约定
   - 例：AI承诺下次提醒用户开会
   - 例：AI答应帮用户查资料

8. **AI建议 (ai_suggestion)** - AI给用户的建议、推荐
   - 例：AI推荐用户试试冥想
   - 例：AI建议用户早点休息

9. **共同话题 (shared_topic)** - 双方共同讨论的话题、约定
   - 例：AI和用户约定周末一起打游戏
   - 例：AI和用户都喜欢某部电影

请以JSON格式返回提取的记忆列表：
[
  {{
    "type": "记忆类型(episodic/semantic/emotional/preference/habit/relationship/ai_promise/ai_suggestion/shared_topic)",
    "content": "记忆内容，简洁明了，如果是AI相关信息请明确标注'AI承诺'、'AI建议'等",
    "summary": "一句话摘要",
    "importance": 重要性评分(1-10),
    "keywords": ["关键词1", "关键词2"],
    "source": "user或ai，表示信息来源"
  }}
]

注意：
- 区分用户和AI的发言，分别提取有价值的信息
- AI的承诺和建议很重要，需要记录以便后续兑现
- 只提取有价值的新信息，不要重复提取已知信息
- 重要性根据信息对了解用户/维护关系的价值判断
- 如果没有新信息，返回空数组 []
"""

        try:
            response = await llm_router.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个对话分析专家，擅长从对话中提取关键信息。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                db=self.session,
                user_id=user_id,
                conversation_id=conversation_id,
                operation="extract_conversation_memory",
            )

            # 解析JSON响应
            content = response.content
            # 提取JSON部分
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                memories = json.loads(json_match.group())
                return memories if isinstance(memories, list) else []
            return []

        except Exception as e:
            print(f"[MemoryExtractor] LLM分析失败: {e}")
            return []

    async def _save_memory(
        self,
        user_id: str,
        memory_data: Dict[str, Any],
        source_conversation_id: str,
    ) -> Optional[Memory]:
        """保存记忆，避免重复"""
        # 检查是否已存在相似记忆
        if await self._is_duplicate_memory(user_id, memory_data["content"]):
            return None

        # 确定信息来源（用户或AI）
        info_source = memory_data.get("source", "user")
        memory_type = memory_data["type"]

        # 根据记忆类型和来源构建更清晰的描述
        content = memory_data["content"]
        if memory_type in ["ai_promise", "ai_suggestion"] and info_source == "ai":
            # 确保AI相关信息有明确标识
            if not content.startswith("AI"):
                content = f"[AI] {content}"
        elif info_source == "ai" and not content.startswith("AI"):
            content = f"[AI] {content}"
        elif info_source == "user" and not content.startswith("用户"):
            # 用户内容可以加上标识以便区分
            pass  # 保持原样，因为用户是默认视角

        # 创建记忆
        memory = Memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            summary=memory_data.get("summary", ""),
            importance=min(max(memory_data.get("importance", 5), 1), 10),
            occurred_at=datetime.utcnow(),
            meta_data=serialize_meta_data(
                {
                    "source": "conversation_extraction",
                    "conversation_id": source_conversation_id,
                    "keywords": memory_data.get("keywords", []),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "info_source": info_source,  # 记录信息来源：user 或 ai
                    "is_ai_generated": info_source == "ai",  # 标记是否为AI生成的内容
                }
            ),
        )

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        source_label = "AI" if info_source == "ai" else "用户"
        print(
            f"[MemoryExtractor] 保存记忆 [{source_label}]: {memory.memory_type} - {memory.content[:50]}..."
        )
        return memory

    async def _is_duplicate_memory(self, user_id: str, content: str) -> bool:
        """检查是否已存在相似记忆"""
        # 简单检查：内容相似度
        result = await self.session.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id, Memory.content.contains(content[:30])  # 检查前30个字符
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_relevant_memories(
        self,
        user_id: str,
        current_message: str,
        limit: int = 5,
    ) -> List[Memory]:
        """
        获取与当前消息相关的记忆

        Args:
            user_id: 用户ID
            current_message: 当前消息内容
            limit: 返回数量限制

        Returns:
            相关记忆列表
        """
        # 提取当前消息的关键词
        keywords = self._extract_keywords(current_message)

        # 查询相关记忆
        memories = []
        for keyword in keywords:
            result = await self.session.execute(
                select(Memory)
                .where(
                    Memory.user_id == user_id,
                    Memory.content.contains(keyword) | Memory.summary.contains(keyword),
                )
                .order_by(Memory.importance.desc())
                .limit(limit)
            )
            memories.extend(result.scalars().all())

        # 去重并按重要性排序
        seen_ids = set()
        unique_memories = []
        for memory in memories:
            if memory.id not in seen_ids:
                seen_ids.add(memory.id)
                unique_memories.append(memory)

        return sorted(unique_memories, key=lambda m: m.importance, reverse=True)[:limit]

    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词（简单实现）"""
        # 移除标点符号
        text = re.sub(r"[^\w\s]", " ", text)
        # 分词并过滤短词
        words = [w for w in text.split() if len(w) >= 2]
        # 返回前5个词作为关键词
        return words[:5]


class MemoryConsolidator:
    """
    记忆整合器
    定期整合零散记忆，生成更完整的用户画像
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.extractor = ConversationMemoryExtractor(session)

    async def consolidate_memories(self, user_id: str) -> Dict[str, Any]:
        """
        整合用户的所有记忆

        Args:
            user_id: 用户ID

        Returns:
            整合后的用户画像
        """
        # 获取用户的所有记忆
        result = await self.session.execute(
            select(Memory).where(Memory.user_id == user_id).order_by(Memory.importance.desc())
        )
        memories = result.scalars().all()

        if not memories:
            return {}

        # 按类型分组
        memories_by_type = {}
        for memory in memories:
            if memory.memory_type not in memories_by_type:
                memories_by_type[memory.memory_type] = []
            memories_by_type[memory.memory_type].append(memory)

        # 生成用户画像摘要
        profile = {
            "memory_count": len(memories),
            "memory_types": {k: len(v) for k, v in memories_by_type.items()},
            "key_memories": [
                {"type": m.memory_type, "content": m.content, "importance": m.importance}
                for m in memories[:10]
            ],
        }

        return profile

    async def generate_user_profile_summary(self, user_id: str) -> str:
        """生成用户画像文本摘要"""
        profile = await self.consolidate_memories(user_id)

        if not profile.get("key_memories"):
            return "暂无足够信息"

        # 构建摘要文本
        summary_parts = []

        for memory_type, memories in profile.get("memory_types", {}).items():
            type_name = ConversationMemoryExtractor.MEMORY_TYPES.get(memory_type, memory_type)
            summary_parts.append(f"{type_name}: {memories}条")

        summary = f"用户画像（共{profile['memory_count']}条记忆）\n"
        summary += "记忆分布: " + ", ".join(summary_parts) + "\n\n"
        summary += "重要记忆:\n"

        for i, memory in enumerate(profile["key_memories"][:5], 1):
            summary += f"{i}. [{memory['type']}] {memory['content']}\n"

        return summary
