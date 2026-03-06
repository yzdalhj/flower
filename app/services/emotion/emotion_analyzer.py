"""情感分析服务 - 多语言支持（中文优先）"""

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from langdetect import detect


@dataclass
class EmotionResult:
    """情感分析结果"""

    valence: float  # 愉悦度: -1 (痛苦) ~ +1 (快乐)
    arousal: float  # 激活度: -1 (平静) ~ +1 (兴奋)
    dominance: float  # 支配度: -1 (被控制) ~ +1 (掌控)
    primary_emotion: str  # 主要情绪
    emotion_scores: Dict[str, float]  # 各情绪得分
    language: str  # 检测到的语言
    confidence: float  # 置信度


class ChineseEmotionLexicon:
    """中文情感词典"""

    # 基础情绪词典 - 按优先级排序（长的优先匹配）
    EMOTION_WORDS = {
        "joy": [
            "开心",
            "高兴",
            "太好了",
            "不错",
            "幸福",
            "满足",
            "快乐",
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
        ],
        "trust": [
            "相信",
            "信任",
            "依赖",
            "放心",
            "靠谱",
            "踏实",
            "安心",
            "可靠",
        ],
        "anticipation": [
            "期待",
            "希望",
            "想",
            "等",
            "盼望",
            "憧憬",
            "渴望",
            "向往",
        ],
        "disgust": [
            "恶心",
            "反感",
            "嫌弃",
            "厌恶",
            "受不了",
            "讨厌",
            "鄙视",
        ],
    }

    # 语气词情感权重
    MODAL_PARTICLES = {
        "呢": 0.05,
        "吧": 0.05,
        "啊": 0.1,
        "呀": 0.1,
        "哇": 0.15,
        "哦": 0.05,
        "嗯": 0.05,
        "哼": -0.15,
        "唉": -0.2,
        "呵呵": -0.25,
        "嘿嘿": 0.1,
        "哈哈": 0.2,
    }

    # 网络用语情感映射
    INTERNET_SLANG = {
        "yyds": ("joy", 0.8),
        "绝绝子": ("joy", 0.7),
        "emo": ("sadness", 0.6),
        "躺平": ("sadness", 0.4),
        "内卷": ("anger", 0.3),
        "破防": ("sadness", 0.7),
        "社死": ("sadness", 0.6),
        "真香": ("joy", 0.6),
        "打脸": ("surprise", 0.4),
        "翻车": ("sadness", 0.5),
        "锦鲤": ("joy", 0.5),
        "佛系": ("calm", 0.3),
        "杠精": ("anger", 0.5),
        "舔狗": ("sadness", 0.4),
        "绿茶": ("disgust", 0.4),
        "渣男": ("disgust", 0.5),
        "渣女": ("disgust", 0.5),
    }

    # 否定词 - 用于反转情感
    NEGATION_WORDS = [
        "不",
        "没",
        "无",
        "非",
        "莫",
        "勿",
        "不是",
        "没有",
        "不太",
        "不怎么",
    ]

    # 程度副词 - 用于增强或减弱情感
    INTENSIFIERS = {
        "很": 1.3,
        "非常": 1.5,
        "特别": 1.5,
        "十分": 1.5,
        "超级": 1.6,
        "太": 1.4,
        "极其": 1.7,
        "有点": 0.7,
        "稍微": 0.6,
        "略": 0.7,
        "比较": 0.9,
    }

    # 表情包Unicode情感映射
    EMOJI_SENTIMENT = {
        # 正面情绪
        "😊": (0.6, 0.2),
        "😄": (0.7, 0.3),
        "😃": (0.7, 0.4),
        "😁": (0.6, 0.4),
        "😆": (0.8, 0.5),
        "😂": (0.7, 0.6),
        "🤣": (0.8, 0.7),
        "😍": (0.9, 0.6),
        "🥰": (0.9, 0.5),
        "😘": (0.8, 0.4),
        "😗": (0.6, 0.2),
        "😙": (0.6, 0.2),
        "😚": (0.7, 0.3),
        "☺️": (0.5, 0.1),
        "🙂": (0.3, 0.1),
        "🤗": (0.6, 0.3),
        "🤩": (0.8, 0.7),
        "🥳": (0.9, 0.8),
        "😎": (0.6, 0.3),
        "👍": (0.5, 0.2),
        "👏": (0.6, 0.4),
        "🙏": (0.3, 0.2),
        "❤️": (0.8, 0.3),
        "💖": (0.9, 0.4),
        "💕": (0.8, 0.3),
        "💓": (0.7, 0.4),
        "✨": (0.6, 0.3),
        "🎉": (0.9, 0.7),
        # 负面情绪
        "😔": (-0.5, -0.2),
        "😟": (-0.4, 0.2),
        "😕": (-0.3, 0.0),
        "🙁": (-0.4, -0.1),
        "☹️": (-0.5, -0.2),
        "😣": (-0.6, 0.3),
        "😖": (-0.6, 0.4),
        "😫": (-0.7, 0.5),
        "😩": (-0.7, 0.4),
        "😢": (-0.7, -0.1),
        "😭": (-0.8, 0.2),
        "😤": (-0.5, 0.8),
        "😠": (-0.7, 0.7),
        "😡": (-0.8, 0.9),
        "🤬": (-0.9, 0.9),
        "🤯": (-0.3, 0.9),
        "😳": (-0.2, 0.6),
        "🥵": (-0.3, 0.7),
        "🥶": (-0.4, 0.2),
        "😱": (-0.7, 0.9),
        "😨": (-0.6, 0.7),
        "😰": (-0.6, 0.6),
        "😥": (-0.5, 0.3),
        "😓": (-0.4, 0.3),
        "🤔": (0.0, 0.3),
        "🤭": (0.2, 0.3),
        "🤫": (0.0, 0.1),
        "🤥": (-0.3, 0.2),
        "😶": (-0.1, -0.2),
        "😐": (0.0, 0.0),
        "😑": (-0.2, -0.1),
        "😬": (-0.3, 0.4),
        "🙄": (-0.4, 0.2),
        "😯": (0.1, 0.5),
        "😦": (-0.2, 0.4),
        "😧": (-0.3, 0.4),
        "😮": (0.1, 0.5),
        "😲": (0.2, 0.6),
        "🥱": (-0.3, -0.3),
        "😴": (-0.2, -0.5),
        "🤤": (0.3, -0.2),
        "😪": (-0.4, -0.3),
        "😵": (-0.3, 0.2),
        "🤐": (-0.1, 0.0),
        "🥴": (-0.3, 0.3),
        "🤢": (-0.7, 0.3),
        "🤮": (-0.8, 0.4),
        "🤧": (-0.4, 0.1),
        "😷": (-0.3, 0.0),
        "🤒": (-0.5, -0.1),
        "🤕": (-0.5, -0.1),
        "🤑": (0.2, 0.3),
        "🤠": (0.4, 0.3),
        "😈": (-0.2, 0.4),
        "👿": (-0.6, 0.6),
        "👹": (-0.4, 0.5),
        "👺": (-0.4, 0.4),
        "🤡": (-0.3, 0.3),
        "💩": (-0.4, 0.2),
        "👻": (0.1, 0.3),
        "💀": (-0.2, 0.2),
        "☠️": (-0.3, 0.2),
        "👽": (0.0, 0.1),
        "👾": (0.1, 0.2),
        "🤖": (0.0, 0.1),
        "🎃": (0.2, 0.3),
        "😺": (0.4, 0.2),
        "😸": (0.5, 0.3),
        "😹": (0.4, 0.4),
        "😻": (0.8, 0.5),
        "😼": (0.2, 0.3),
        "😽": (0.5, 0.2),
        "🙀": (-0.5, 0.7),
        "😿": (-0.6, 0.1),
        "😾": (-0.5, 0.5),
    }

    # 反讽模式 - 更严格的匹配，避免误判正常赞美
    IRONY_PATTERNS = [
        r"真[的]*(?:不错|好|棒|优秀|厉害)[呢|啊|哦|哟]",
        r"(?:太|真|多).*(?:恶心|差|糟|烂|烦|讨厌)",
        r"(?:呵呵|哈哈).*(?:不错|好|棒)",
        r"(?:不错|好|棒).*(?:呵呵|哈哈)",
        r"^呵呵$",
        r"^哈哈$",
    ]

    def get_emotion(self, word: str) -> tuple:
        """
        获取词语的情感类别和强度

        Args:
            word: 输入词语

        Returns:
            (情感类别, 强度) 元组，如果没有找到则返回 (None, 0.0)
        """
        # 检查网络用语
        if word in self.INTERNET_SLANG:
            return self.INTERNET_SLANG[word]

        # 检查情感词典
        for emotion, words in self.EMOTION_WORDS.items():
            if word in words:
                # 根据词在列表中的位置计算强度（越靠前强度越高）
                idx = words.index(word)
                intensity = max(0.5, 1.0 - idx * 0.05)
                return (emotion, intensity)

        return (None, 0.0)


class MultilingualEmotionAnalyzer:
    """多语言情感分析器（中文优先）"""

    def __init__(self):
        self.lexicon = ChineseEmotionLexicon()
        self._deep_model = None  # 延迟加载深度学习模型

    def detect_language(self, text: str) -> str:
        """检测语言（优先识别中文）"""
        # 快速检测中文字符
        if any("\u4e00" <= char <= "\u9fff" for char in text):
            return "zh"

        try:
            return detect(text)
        except Exception:
            return "zh"  # 默认中文

    def analyze(self, text: str, use_deep: bool = False) -> EmotionResult:
        """
        分析文本情感

        Args:
            text: 输入文本
            use_deep: 是否使用深度学习模型

        Returns:
            情感分析结果
        """
        if not text or not text.strip():
            return EmotionResult(
                valence=0.0,
                arousal=0.0,
                dominance=0.5,
                primary_emotion="neutral",
                emotion_scores={},
                language="unknown",
                confidence=0.0,
            )

        # 检测语言
        language = self.detect_language(text)

        # 根据语言选择分析方式
        if language == "zh":
            return self._analyze_chinese(text)
        else:
            return self._analyze_other(text, language)

    def _analyze_chinese(self, text: str) -> EmotionResult:
        """中文情感分析"""
        emotion_scores = {emotion: 0.0 for emotion in self.lexicon.EMOTION_WORDS}

        # 1. 关键词匹配 - 优先匹配长词
        all_words = []
        for emotion, words in self.lexicon.EMOTION_WORDS.items():
            for word in words:
                all_words.append((word, emotion))
        # 按长度降序排序，优先匹配长词
        all_words.sort(key=lambda x: len(x[0]), reverse=True)

        matched_positions = set()  # 记录已匹配的位置

        for word, emotion in all_words:
            pos = text.find(word)
            while pos != -1:
                # 检查该位置是否已被匹配
                if pos not in matched_positions:
                    # 检查前面是否有否定词（在词前3个字符内）
                    negation = self._check_negation(text, pos)
                    # 检查前面是否有程度副词
                    intensifier = self._check_intensifier(text, pos)

                    # 根据词频和长度加权
                    count = text.count(word)
                    weight = min(count * len(word) / 10, 1.0)

                    # 应用程度修饰
                    weight *= intensifier

                    # 应用否定修饰（反转情感或减弱）
                    if negation:
                        # 否定词会反转情感或减弱
                        weight *= -0.8

                    emotion_scores[emotion] += weight

                    # 标记已匹配的位置
                    for i in range(pos, pos + len(word)):
                        matched_positions.add(i)

                pos = text.find(word, pos + 1)

        # 2. 网络用语分析
        for slang, (emotion, intensity) in self.lexicon.INTERNET_SLANG.items():
            if slang in text:
                emotion_scores[emotion] += intensity

        # 3. 语气词分析
        modal_score = 0.0
        for particle, weight in self.lexicon.MODAL_PARTICLES.items():
            if particle in text:
                modal_score += weight

        # 4. 表情包分析
        emoji_valence, emoji_arousal = self._analyze_emoji(text)

        # 5. 反讽检测
        is_irony = self._detect_irony(text)
        if is_irony:
            # 反讽时反转主要情感
            for emotion in emotion_scores:
                if emotion in ["joy", "trust", "anticipation"]:
                    emotion_scores[emotion] *= -0.5
                elif emotion in ["sadness", "anger", "fear", "disgust"]:
                    emotion_scores[emotion] *= 0.5

        # 6. 标点符号分析
        punct_arousal = self._analyze_punctuation(text)

        # 7. 归一化并计算主要情绪
        total_score = sum(abs(score) for score in emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v / total_score for k, v in emotion_scores.items()}

        primary_emotion = max(emotion_scores, key=emotion_scores.get)

        # 8. 计算PAD值
        valence, arousal, dominance = self._calculate_pad(
            emotion_scores, modal_score, emoji_valence, emoji_arousal, punct_arousal
        )

        return EmotionResult(
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            primary_emotion=primary_emotion,
            emotion_scores=emotion_scores,
            language="zh",
            confidence=min(total_score, 1.0),
        )

    def _analyze_other(self, text: str, language: str) -> EmotionResult:
        """其他语言情感分析（简化版）"""
        # 使用简单的情感词典方法
        positive_words = [
            "good",
            "great",
            "excellent",
            "happy",
            "joy",
            "love",
            "like",
            "wonderful",
            "amazing",
            "awesome",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "sad",
            "angry",
            "hate",
            "dislike",
            "horrible",
            "disgusting",
            "worst",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            valence = 0.0
            primary_emotion = "neutral"
        else:
            valence = (positive_count - negative_count) / total
            primary_emotion = "joy" if valence > 0 else "sadness"

        # 分析表情符号
        emoji_valence, emoji_arousal = self._analyze_emoji(text)

        # 融合表情符号情感
        valence = valence * 0.7 + emoji_valence * 0.3

        return EmotionResult(
            valence=valence,
            arousal=emoji_arousal,
            dominance=0.5,
            primary_emotion=primary_emotion,
            emotion_scores={primary_emotion: abs(valence), "neutral": 1 - abs(valence)},
            language=language,
            confidence=min(total / 5, 1.0),
        )

    def _analyze_emoji(self, text: str) -> Tuple[float, float]:
        """分析表情包情感"""
        total_valence = 0.0
        total_arousal = 0.0
        count = 0

        for emoji, (valence, arousal) in self.lexicon.EMOJI_SENTIMENT.items():
            if emoji in text:
                total_valence += valence
                total_arousal += arousal
                count += 1

        if count == 0:
            return 0.0, 0.0

        return total_valence / count, total_arousal / count

    def _check_negation(self, text: str, pos: int) -> bool:
        """检查位置前是否有否定词"""
        # 检查前5个字符
        start = max(0, pos - 5)
        context = text[start:pos]
        for neg_word in self.lexicon.NEGATION_WORDS:
            if neg_word in context:
                return True
        return False

    def _check_intensifier(self, text: str, pos: int) -> float:
        """检查位置前是否有程度副词，返回强度系数"""
        # 检查前4个字符
        start = max(0, pos - 4)
        context = text[start:pos]
        for intensifier, factor in self.lexicon.INTENSIFIERS.items():
            if intensifier in context:
                return factor
        return 1.0

    def _detect_irony(self, text: str) -> bool:
        """检测反讽"""
        for pattern in self.lexicon.IRONY_PATTERNS:
            if re.search(pattern, text):
                # 结合上下文判断
                # 如果前面有负面情绪词，后面有正面评价，可能是反讽
                return True
        return False

    def _analyze_punctuation(self, text: str) -> float:
        """分析标点符号情感"""
        arousal = 0.0

        # 多个感叹号 = 强烈情感
        if "！！" in text or "!!" in text:
            arousal += 0.3

        # 多个问号 = 困惑/质疑
        if "？？" in text or "??" in text:
            arousal += 0.2

        # 省略号 = 犹豫/无语
        if "……" in text or "..." in text:
            arousal -= 0.2

        # 波浪号 = 轻松/撒娇
        if "~" in text:
            arousal -= 0.1

        return arousal

    def _calculate_pad(
        self,
        emotion_scores: Dict[str, float],
        modal_score: float,
        emoji_valence: float,
        emoji_arousal: float,
        punct_arousal: float,
    ) -> Tuple[float, float, float]:
        """计算PAD三维情感值"""
        # PAD映射表
        emotion_to_pad = {
            "joy": (0.8, 0.6, 0.4),
            "sadness": (-0.8, -0.4, -0.6),
            "anger": (-0.6, 0.8, 0.4),
            "fear": (-0.7, 0.7, -0.6),
            "trust": (0.6, 0.2, 0.3),
            "anticipation": (0.4, 0.4, 0.2),
            "surprise": (0.2, 0.8, 0.1),
            "disgust": (-0.7, 0.3, -0.2),
        }

        # 加权计算PAD
        p, a, d = 0.0, 0.0, 0.0
        total_weight = 0.0

        for emotion, score in emotion_scores.items():
            if emotion in emotion_to_pad:
                ep, ea, ed = emotion_to_pad[emotion]
                p += ep * score
                a += ea * score
                d += ed * score
                total_weight += abs(score)

        if total_weight > 0:
            p /= total_weight
            a /= total_weight
            d /= total_weight

        # 融合其他特征
        p = p * 0.6 + emoji_valence * 0.3 + modal_score * 0.1
        a = a * 0.6 + emoji_arousal * 0.3 + punct_arousal * 0.1
        d = d * 0.8 + 0.5 * 0.2  # 支配度相对稳定

        # 限制范围
        p = max(-1.0, min(1.0, p))
        a = max(-1.0, min(1.0, a))
        d = max(-1.0, min(1.0, d))

        return p, a, d

    def analyze_sticker(self, description: str) -> EmotionResult:
        """
        分析表情包/贴图描述

        Args:
            description: 表情包描述文本，如"用户发送了一个[大笑]表情包"

        Returns:
            情感分析结果
        """
        # 表情包关键词映射
        sticker_keywords = {
            "大笑": "joy",
            "开心": "joy",
            "高兴": "joy",
            "笑": "joy",
            "哭泣": "sadness",
            "难过": "sadness",
            "伤心": "sadness",
            "哭": "sadness",
            "生气": "anger",
            "愤怒": "anger",
            "怒": "anger",
            "惊讶": "surprise",
            "震惊": "surprise",
            "惊": "surprise",
            "害怕": "fear",
            "恐惧": "fear",
            "吓": "fear",
        }

        # 提取方括号中的关键词
        import re

        match = re.search(r"\[(.*?)\]", description)
        if match:
            keyword = match.group(1)
            for k, emotion in sticker_keywords.items():
                if k in keyword:
                    return self._create_emotion_result(emotion, 0.8, "zh")

        # 如果没有匹配到关键词，尝试分析整个描述
        for keyword, emotion in sticker_keywords.items():
            if keyword in description:
                return self._create_emotion_result(emotion, 0.7, "zh")

        # 默认返回中性
        return self._create_emotion_result("neutral", 0.5, "zh")

    def _create_emotion_result(
        self, emotion: str, confidence: float, language: str
    ) -> EmotionResult:
        """创建情感结果"""
        emotion_to_pad = {
            "joy": (0.8, 0.6, 0.4),
            "sadness": (-0.8, -0.4, -0.6),
            "anger": (-0.6, 0.8, 0.4),
            "fear": (-0.7, 0.7, -0.6),
            "trust": (0.6, 0.2, 0.3),
            "anticipation": (0.4, 0.4, 0.2),
            "surprise": (0.2, 0.8, 0.1),
            "disgust": (-0.7, 0.3, -0.2),
            "neutral": (0.0, 0.3, 0.5),
        }

        v, a, d = emotion_to_pad.get(emotion, (0.0, 0.3, 0.5))

        return EmotionResult(
            valence=v,
            arousal=a,
            dominance=d,
            primary_emotion=emotion,
            emotion_scores={emotion: confidence, "neutral": 1 - confidence},
            language=language,
            confidence=confidence,
        )


# 全局分析器实例
_emotion_analyzer: Optional[MultilingualEmotionAnalyzer] = None


def get_emotion_analyzer() -> MultilingualEmotionAnalyzer:
    """获取情感分析器实例（单例）"""
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = MultilingualEmotionAnalyzer()
    return _emotion_analyzer
