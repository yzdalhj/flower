# -*- coding: utf-8 -*-
"""对话策略 - 让对话更像真人"""

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ConversationConfig:
    """对话配置"""

    # 主动提问概率（30%概率主动提问，70%不主动）
    proactive_question_probability: float = 0.3

    # 分多条发送概率
    multi_message_probability: float = 0.3

    # 语气词概率
    particle_probability: float = 0.5

    # 吐槽后安慰概率
    roast_then_comfort_probability: float = 0.4


class ConversationStrategy:
    """
    对话策略 - 让AI回复更像真人朋友
    """

    def __init__(self, config: Optional[ConversationConfig] = None):
        self.config = config or ConversationConfig()

        # 语气词列表
        self.particles = ["啊", "呢", "吧", "哦", "呀", "嘛", "啦", "哇", "咯"]

        # 吐槽用语
        self.roast_phrases = [
            "不是吧",
            "真的假的",
            "离谱",
            "服了",
            "救命",
            "笑死",
            "绝了",
            "啊这",
        ]

        # 安慰用语
        self.comfort_phrases = [
            "不过没事的",
            "但是别担心",
            "不过会好起来的",
            "但是我相信你",
            "不过加油",
        ]

    def should_ask_proactive_question(self) -> bool:
        """
        是否应该主动提问
        70%概率不主动提问，30%概率主动提问
        """
        return random.random() < self.config.proactive_question_probability

    def should_send_multi_messages(self) -> bool:
        """
        是否应该分多条发送
        30%概率分多条
        """
        return random.random() < self.config.multi_message_probability

    def split_message(self, text: str) -> List[str]:
        """
        将一条消息分成多条

        Args:
            text: 原始消息

        Returns:
            分条后的消息列表
        """
        # 按句子分割
        sentences = re.split(r"([。！？!?])", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 重新组合句子
        messages = []
        current_msg = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else "。"
            current_msg += sentence + punctuation

            # 随机决定是否在这里分割
            if random.random() < 0.5 and len(messages) < 2:
                messages.append(current_msg)
                current_msg = ""

        if current_msg:
            messages.append(current_msg)

        # 如果只有一条，就不分割了
        if len(messages) == 1:
            return messages

        return messages[:3]  # 最多3条

    def add_particles(self, text: str) -> str:
        """
        随机添加语气词

        Args:
            text: 原始文本

        Returns:
            添加语气词后的文本
        """
        if random.random() > self.config.particle_probability:
            return text

        # 在句末添加语气词
        if text.endswith("。"):
            particle = random.choice(self.particles)
            # 避免重复语气词
            if text[-2] not in self.particles:
                return text[:-1] + particle + "。"
        elif text.endswith("！") or text.endswith("?") or text.endswith("？"):
            particle = random.choice(self.particles)
            if text[-2] not in self.particles:
                return text[:-1] + particle + text[-1]

        return text

    def apply_roast_then_comfort(self, text: str, emotion: Optional[Dict] = None) -> str:
        """
        应用先吐槽再安慰策略

        Args:
            text: 原始文本
            emotion: 情感状态

        Returns:
            处理后的文本
        """
        # 只在消极情感时应用
        if not emotion or emotion.get("valence", 0) >= 0:
            return text

        if random.random() > self.config.roast_then_comfort_probability:
            return text

        roast = random.choice(self.roast_phrases)
        comfort = random.choice(self.comfort_phrases)

        # 构建吐槽+安慰的回复
        return f"{roast}，{text}{comfort}"

    def process(
        self,
        text: str,
        emotion: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """
        应用对话策略

        Args:
            text: 原始回复
            emotion: 情感状态
            context: 对话上下文

        Returns:
            处理后的消息列表
        """
        # 1. 应用先吐槽再安慰策略
        text = self.apply_roast_then_comfort(text, emotion)

        # 2. 添加语气词
        text = self.add_particles(text)

        # 3. 决定是否分多条发送
        if self.should_send_multi_messages():
            messages = self.split_message(text)
        else:
            messages = [text]

        return messages

    def generate_proactive_question(self, context: Optional[Dict] = None) -> Optional[str]:
        """
        生成主动提问

        Args:
            context: 对话上下文

        Returns:
            问题文本，如果不提问则返回None
        """
        if not self.should_ask_proactive_question():
            return None

        questions = [
            "你呢？",
            "你怎么样？",
            "最近咋样？",
            "你呢，最近还好吗？",
            "你呢，有什么新鲜事吗？",
        ]

        return random.choice(questions)


# 全局单例
_conversation_strategy: Optional[ConversationStrategy] = None


def get_conversation_strategy() -> ConversationStrategy:
    """获取对话策略实例（单例）"""
    global _conversation_strategy
    if _conversation_strategy is None:
        _conversation_strategy = ConversationStrategy()
    return _conversation_strategy
