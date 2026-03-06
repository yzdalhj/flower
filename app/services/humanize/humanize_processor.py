# -*- coding: utf-8 -*-
"""真人化回复处理器 - 去除AI味，让回复像真人"""

import random
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HumanizeConfig:
    """真人化配置"""

    max_sentences: int = 3
    min_sentences: int = 2
    add_catchphrase_probability: float = 0.4
    replace_emoji_probability: float = 0.7


class HumanizeProcessor:
    """真人化回复处理器"""

    def __init__(self, config: Optional[HumanizeConfig] = None):
        self.config = config or HumanizeConfig()

        # AI味词汇替换表（按长度降序排序，优先替换长词）
        self.ai_word_replacements = {
            "我理解你的感受": "我懂你",
            "有什么可以帮助您的": "咋了",
            "有什么我可以帮您": "咋了",
            "感谢您的理解": "懂的都懂",
            "很高兴为您服务": "",
            "作为AI": "",
            "我理解": "我懂",
            "我建议": "不如",
            "让我想想": "容我琢磨琢磨",
            "让我看看": "我瞅瞅",
            "非常感谢": "谢啦",
            "好的，没问题": "行，ok",
            "好的": "行",
            "没问题": "ok",
            "明白了": "懂了",
            "您": "你",
            "请问": "",
            "敬请": "",
            "恳请": "",
            "务必": "",
        }

        # 官方表情替换为更真实的表情
        self.emoji_replacements = {
            "😊": ["😭", "😂", "🙄", "😅", "🤣"],
            "😉": ["😏", "🤪", "😜"],
            "🤗": ["👋", "🤝", "🤞"],
            "🙂": ["😐", "😑", "🙄"],
            "😃": ["😂", "🤣", "😆"],
            "😄": ["😆", "🤣", "😂"],
            "🙏": ["😅", "🤦", "摊手"],
            "👍": ["👌", "👏", "🎉"],
            "❤️": ["💕", "💖", "💗"],
        }

        # 按情感分类的口头禅库
        self.emotion_catchphrases = {
            "joy": [
                "绝了",
                "yyds",
                "绝绝子",
                "笑不活了",
                "狠狠爱住",
                "太棒了",
                "太赞了",
                "我去",
                "不是吧",
                "真的假的",
                "谁懂啊",
                "咱就是说",
            ],
            "sadness": [
                "害",
                "害，别提了",
                "害，说多了都是泪",
                "破防了",
                "麻了",
                "绷不住了",
                "狠狠破防",
                "服了",
                "服了服了",
                "真的会谢",
                "一整个大无语",
                "emmm",
                "emm",
            ],
            "anger": [
                "卧槽",
                "我去",
                "不是吧",
                "离谱",
                "服了",
                "服了服了",
                "真的会谢",
                "麻了",
                "一整个大无语",
            ],
            "fear": [
                "我去",
                "不是吧",
                "真的假的",
                "救命",
                "救命啊",
                "我的天",
                "我天",
                "离谱",
            ],
            "surprise": [
                "我去",
                "不是吧",
                "真的假的",
                "卧槽",
                "绝了",
                "我的天",
                "我天",
                "离谱",
                "啊这",
            ],
            "neutral": [
                "害",
                "啊这",
                "咱就是说",
                "一整个",
                "狠狠",
                "emmm",
                "emm",
            ],
        }

        # 通用口头禅库（向后兼容）
        self.catchphrases = [
            "卧槽",
            "害",
            "绝了",
            "啊这",
            "我去",
            "不是吧",
            "真的假的",
            "离谱",
            "服了",
            "救命",
            "笑不活了",
            "破防了",
            "麻了",
            "绷不住了",
            "谁懂啊",
            "咱就是说",
            "一整个",
            "狠狠",
            "狠狠爱住",
            "狠狠破防",
            "救命啊",
            "我的天",
            "我天",
            "绝绝子",
            "yyds",
            "emmm",
            "emm",
            "害，别提了",
            "害，说多了都是泪",
            "服了服了",
            "真的会谢",
            "一整个大无语",
        ]

        # 情感关键词映射（用于简单的情感检测）
        self.emotion_keywords = {
            "joy": [
                "开心",
                "高兴",
                "快乐",
                "幸福",
                "满足",
                "喜欢",
                "优秀",
                "完美",
                "舒服",
                "嘻嘻",
                "哈哈",
                "棒",
                "赞",
                "爽",
                "爱",
                "好",
                "不错",
                "太棒了",
                "太赞了",
                "yyds",
                "绝绝子",
                "笑",
                "开心死了",
            ],
            "sadness": [
                "难过",
                "伤心",
                "失望",
                "痛苦",
                "悲伤",
                "绝望",
                "沮丧",
                "郁闷",
                "难受",
                "委屈",
                "失落",
                "无助",
                "哭",
                "emo",
                "难过死了",
                "破防",
                "麻了",
                "绷不住",
            ],
            "anger": [
                "生气",
                "愤怒",
                "烦",
                "讨厌",
                "滚",
                "火大",
                "气死",
                "暴躁",
                "恼火",
                "恨",
                "恶心",
                "不爽",
                "离谱",
                "服了",
            ],
            "fear": [
                "害怕",
                "担心",
                "焦虑",
                "紧张",
                "慌",
                "恐惧",
                "不安",
                "忐忑",
                "怕",
                "吓",
                "可怕",
                "恐怖",
            ],
            "surprise": [
                "惊讶",
                "震惊",
                "没想到",
                "哇",
                "天哪",
                "居然",
                "竟然",
                "神奇",
                "不可思议",
                "我的天",
                "我天",
            ],
        }

        # 句末语气词
        self.modal_particles = ["啊", "呢", "吧", "哦", "呀", "嘛", "啦", "哇", "咯", "嘞"]

    def process(self, text: str) -> str:
        """
        处理文本，去除AI味

        Args:
            text: 原始文本

        Returns:
            真人化后的文本
        """
        if not text or not text.strip():
            return text

        result = text

        # 1. 替换AI味词汇
        result = self._replace_ai_words(result)

        # 2. 截断长句
        result = self._truncate_sentences(result)

        # 3. 替换官方表情
        result = self._replace_emojis(result)

        # 4. 添加口头禅（语境感知）
        result = self._add_catchphrase(result)

        # 5. 添加随机语气词
        result = self._add_modal_particles(result)

        return result

    def _cleanup_punctuation(self, text: str) -> str:
        """清理多余的标点符号"""
        original_text = text
        # 清理开头的标点
        text = re.sub(r"^[，。！？!?、；;,]+", "", text)
        # 清理连续的中文逗号
        text = re.sub(r"，+", "，", text)
        # 清理连续的英文逗号
        text = re.sub(r",+", ",", text)
        # 清理逗号后面直接跟句号的情况
        text = re.sub(r"，。", "。", text)
        # 清理"，我"这种情况在句末
        text = re.sub(r"，([\u4e00-\u9fa5a-zA-Z])$", r"", text)
        # 清理多余的空格
        text = re.sub(r"\s+", " ", text)
        # 清理句末的逗号
        text = text.rstrip("，")
        # 如果结果为空或太短，返回原始文本（避免清理过度）
        if len(text.strip()) < 2:
            return original_text
        return text.strip()

    def _detect_emotion(self, text: str) -> str:
        """
        简单的情感检测（基于关键词）

        Args:
            text: 输入文本

        Returns:
            情感类别: joy, sadness, anger, fear, surprise, neutral
        """
        emotion_scores = {
            "joy": 0,
            "sadness": 0,
            "anger": 0,
            "fear": 0,
            "surprise": 0,
        }

        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_scores[emotion] += 1

        # 找出得分最高的情感
        max_score = max(emotion_scores.values())
        if max_score > 0:
            for emotion, score in emotion_scores.items():
                if score == max_score:
                    return emotion

        return "neutral"

    def _replace_ai_words(self, text: str) -> str:
        """替换AI味词汇"""
        original_text = text
        result = text

        # 先处理特殊情况：删除整个包含"作为AI"或"很高兴为您服务"的句子
        # 使用捕获分组来保存标点符号
        parts = re.split(r"([。！？!?])", result)
        cleaned_parts = []

        i = 0
        while i < len(parts):
            sentence = parts[i].strip()
            punctuation = parts[i + 1] if i + 1 < len(parts) else ""

            # 检查是否包含需要删除整个句子的关键词
            skip = False
            keywords_to_remove = ["作为AI", "很高兴为您服务"]
            for keyword in keywords_to_remove:
                if keyword in sentence:
                    skip = True
                    break

            if not skip and sentence:
                cleaned_parts.append(sentence + punctuation)
            i += 2

        # 重新组合
        if cleaned_parts:
            result = "".join(cleaned_parts)
        else:
            result = original_text

        # 然后再替换其他AI味词汇
        # 按长度降序替换，避免短词先替换导致长词无法匹配
        sorted_replacements = sorted(
            self.ai_word_replacements.items(), key=lambda x: len(x[0]), reverse=True
        )
        # 排除已经处理过的关键词
        exclude_words = ["作为AI", "很高兴为您服务"]
        for old_word, new_word in sorted_replacements:
            if old_word not in exclude_words:
                result = result.replace(old_word, new_word)

        # 清理多余的标点
        result = self._cleanup_punctuation(result)
        return result

    def _truncate_sentences(self, text: str) -> str:
        """截断长句，限制在2-3句话"""
        # 分割句子（支持中文和英文标点）
        sentences = re.split(r"[。！？!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= self.config.max_sentences:
            return text

        # 随机保留2-3句话
        num_sentences = random.randint(self.config.min_sentences, self.config.max_sentences)
        selected_sentences = sentences[:num_sentences]

        # 重新组合
        result = "。".join(selected_sentences) + "。"

        return result

    def _replace_emojis(self, text: str) -> str:
        """替换官方表情为更真实的表情"""
        if random.random() > self.config.replace_emoji_probability:
            return text

        result = text
        for official_emoji, real_emojis in self.emoji_replacements.items():
            if official_emoji in result:
                real_emoji = random.choice(real_emojis)
                result = result.replace(official_emoji, real_emoji)

        return result

    def _add_catchphrase(self, text: str) -> str:
        """添加口头禅（语境感知）"""
        if random.random() > self.config.add_catchphrase_probability:
            return text

        # 检测文本情感
        emotion = self._detect_emotion(text)

        # 根据情感选择合适的口头禅
        if emotion in self.emotion_catchphrases:
            catchphrases = self.emotion_catchphrases[emotion]
        else:
            catchphrases = self.emotion_catchphrases["neutral"]

        if not catchphrases:
            return text

        catchphrase = random.choice(catchphrases)
        position = random.random()

        if position < 0.3:
            # 添加在开头
            text_stripped = text.lstrip()
            if text_stripped:
                # 检查第一个字符是否是标点，如果是则不需要额外逗号
                first_char = text_stripped[0]
                if first_char in "，。！？!?、；;,":
                    result = f"{catchphrase}{text_stripped}"
                else:
                    result = f"{catchphrase}，{text_stripped}"
            else:
                result = catchphrase
        elif position < 0.7:
            # 添加在中间（随机位置）- 只在有多个句子时才添加在中间
            sentences = re.split(r"[。！？!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) >= 2:
                insert_idx = random.randint(1, len(sentences) - 1)
                sentences.insert(insert_idx, catchphrase)
                result = "。".join(sentences) + "。"
            else:
                # 短句直接加在结尾
                text_no_punc = text.rstrip("。！？!?")
                result = f"{text_no_punc}，{catchphrase}。"
        else:
            # 添加在结尾
            text_no_punc = text.rstrip("。！？!?")
            result = f"{text_no_punc}，{catchphrase}。"

        # 清理多余的标点
        result = self._cleanup_punctuation(result)
        return result

    def _add_modal_particles(self, text: str) -> str:
        """添加随机语气词"""
        # 只在50%的情况下添加
        if random.random() > 0.5:
            return text

        # 更保守的语气词列表，避免奇怪组合
        safe_particles = ["啊", "呢", "吧", "哦", "呀", "嘛"]

        # 在句末添加语气词
        if text.endswith("。"):
            particle = random.choice(safe_particles)
            # 避免"救命哇"这种奇怪的组合，检查最后一个词
            text_no_punc = text[:-1]
            words = text_no_punc.split("，")
            last_word = words[-1] if words else ""
            # 如果最后一个词本身已经是感叹词或已经以语气词结尾，就不添加
            excluded_words = ["救命", "绝了", "卧槽", "我的天", "我天", "害", "谁懂啊", "咱就是说"]
            if last_word in excluded_words:
                return text
            if any(last_word.endswith(p) for p in self.modal_particles):
                return text
            # 避免"啊哇"这种连续语气词
            if text_no_punc and text_no_punc[-1] in self.modal_particles:
                return text
            return f"{text_no_punc}{particle}。"
        elif text.endswith("！") or text.endswith("?") or text.endswith("？"):
            particle = random.choice(safe_particles)
            text_no_punc = text[:-1]
            words = text_no_punc.split("，")
            last_word = words[-1] if words else ""
            excluded_words = ["救命", "绝了", "卧槽", "我的天", "我天", "害", "谁懂啊", "咱就是说"]
            if last_word in excluded_words:
                return text
            if any(last_word.endswith(p) for p in self.modal_particles):
                return text
            if text_no_punc and text_no_punc[-1] in self.modal_particles:
                return text
            return f"{text_no_punc}{particle}{text[-1]}"

        return text

    def update_catchphrases(
        self, new_catchphrases: List[str], emotion: Optional[str] = None
    ) -> None:
        """
        更新口头禅库（用于实时获取网络梗）

        Args:
            new_catchphrases: 新的口头禅列表
            emotion: 情感类别，如果为None则添加到通用库
        """
        if emotion and emotion in self.emotion_catchphrases:
            self.emotion_catchphrases[emotion].extend(new_catchphrases)
            # 去重
            self.emotion_catchphrases[emotion] = list(set(self.emotion_catchphrases[emotion]))
        else:
            self.catchphrases.extend(new_catchphrases)
            # 去重
            self.catchphrases = list(set(self.catchphrases))


# 全局单例
_humanize_processor: Optional[HumanizeProcessor] = None


def get_humanize_processor() -> HumanizeProcessor:
    """获取真人化处理器实例（单例）"""
    global _humanize_processor
    if _humanize_processor is None:
        _humanize_processor = HumanizeProcessor()
    return _humanize_processor
