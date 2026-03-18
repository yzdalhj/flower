# -*- coding: utf-8 -*-
"""LLM真人化处理器"""

from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.llm_client import llm_router


class LLMHumanizer:
    """
    LLM真人化处理器 - 使用大模型进行深度思考
    """

    def __init__(self):
        self.llm_router = llm_router

    async def process(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        emotion: Dict[str, float] = None,
        personality_id: str = None,
        db: Optional[AsyncSession] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        使用LLM真人化回复

        Args:
            text: 原始AI回复
            conversation_history: 对话历史
            emotion: 当前情感状态
            personality_id: 人格ID
            db: 数据库会话
            user_id: 用户ID
            conversation_id: 对话ID

        Returns:
            真人化后的回复
        """
        # 构建Prompt
        prompt = self._build_humanize_prompt(
            text=text,
            conversation_history=conversation_history,
            emotion=emotion,
            personality_id=personality_id,
        )

        # 调用LLM
        response = await self.llm_router.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=200,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            operation="llm_humanize",
        )

        return response.content

    def _build_humanize_prompt(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        emotion: Dict[str, float] = None,
        personality_id: str = None,
    ) -> str:
        """构建真人化Prompt"""
        prompt_parts = [
            "你是一个真人化专家，负责把AI回复改得像真人说话。",
            "",
            "【要求】",
            "1. 简短，2-3句话就够了",
            "2. 去除AI味，不要说'我理解你的感受'这种话",
            "3. 使用口头禅：'卧槽'、'害'、'绝了'、'啊这'、'真的假的'",
            "4. 替换官方表情",
            "5. 添加合适的语气词：'啊'、'呢'、'吧'、'哦'、'呀'、'嘛'",
            "6. 像朋友一样说话，不要像客服",
            "",
            "【原始回复】",
            text,
        ]

        if emotion:
            prompt_parts.extend(
                [
                    "",
                    "【当前情感】",
                    f"- 愉悦度: {emotion.get('valence', 0)}",
                    f"- 激活度: {emotion.get('arousal', 0)}",
                    "",
                    "请根据当前情感选择合适的语气。",
                ]
            )

        if conversation_history:
            prompt_parts.extend(
                [
                    "",
                    "【对话历史】",
                ]
            )
            for msg in conversation_history[-5:]:
                role = "用户" if msg.get("role") == "user" else "AI"
                prompt_parts.append(f"{role}: {msg.get('content', '')}")

        prompt_parts.extend(
            [
                "",
                "【真人化后的回复】",
                "（只返回改好的回复，不要解释）",
            ]
        )

        return "\n".join(prompt_parts)
