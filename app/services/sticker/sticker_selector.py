"""表情包智能选择器"""

import random
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sticker import (
    Sticker,
    StickerEmotion,
    StickerPersonalityMatch,
    StickerSelection,
    StickerSendStrategy,
)
from app.services.sticker.sticker_service import StickerService


class StickerSelector:
    """表情包智能选择器"""

    def __init__(self, db: AsyncSession, strategy: Optional[StickerSendStrategy] = None):
        self.db = db
        self.sticker_service = StickerService(db)
        self.strategy = strategy or StickerSendStrategy()

    async def select_optimal_sticker(
        self,
        current_emotion: Dict[str, float],
        personality_type: str = "default",
        context_keywords: Optional[List[str]] = None,
        conversation_context: Optional[str] = None,
        is_serious_context: bool = False,
        sticker_type_filter: Optional[str] = None,
    ) -> Optional[StickerSelection]:
        """
        选择最适合当前场景的表情包

        Args:
            current_emotion: 当前情绪字典，key为情绪类型，value为强度(0-1)
            personality_type: 人格类型
            context_keywords: 上下文关键词
            conversation_context: 对话上下文
            is_serious_context: 是否为严肃场景
            sticker_type_filter: 表情包类型过滤，只返回指定类型（"emotion", "reaction", "meme", "custom"）

        Returns:
            选中的表情包，如果不需要发表情包则返回None
        """
        # 1. 先判断是否需要发表情包
        should_send, send_mode = self._should_send_sticker(
            personality_type, current_emotion, is_serious_context
        )

        if not should_send:
            return None

        # 2. 获取主导情绪（允许为None）
        dominant_emotion, emotion_intensity = self._get_dominant_emotion(current_emotion)

        # 如果没有主导情绪但情绪强度足够，也可以继续
        if not dominant_emotion and emotion_intensity < self.strategy.min_emotion_intensity:
            print(f"[StickerSelector] 情绪强度不足: {emotion_intensity}")
            return None

        # 3. 获取候选表情包
        candidates = await self._get_candidate_stickers(
            dominant_emotion, personality_type, context_keywords, sticker_type_filter
        )

        if not candidates:
            print("[StickerSelector] 没有找到候选表情包")
            return None

        print(f"[StickerSelector] 找到 {len(candidates)} 个候选表情包")

        # 4. 计算每个候选的匹配分数
        scored_candidates = []
        for sticker in candidates:
            score, emotion_match, personality_match, context_match = self._calculate_match_score(
                sticker, dominant_emotion, emotion_intensity, personality_type, context_keywords
            )
            scored_candidates.append(
                (sticker, score, emotion_match, personality_match, context_match)
            )

        # 5. 按分数排序，选择最优的几个
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:3]  # 取前3个

        # 6. 带权重随机选择（分数越高概率越大）
        selected = self._weighted_random_choice(top_candidates)
        if not selected:
            return None

        sticker, total_score, emotion_match, personality_match, context_match = selected

        # 7. 构造选择结果
        emotion_str = dominant_emotion.value if dominant_emotion else "无"
        return StickerSelection(
            sticker=sticker,
            match_score=total_score,
            emotion_match=emotion_match,
            personality_match=personality_match,
            context_match=context_match,
            reason=f"匹配情绪：{emotion_str}，强度：{emotion_intensity:.2f}，人格适配：{personality_type}",
        )

    def _should_send_sticker(
        self,
        personality_type: str,
        current_emotion: Dict[str, float],
        is_serious_context: bool,
    ) -> Tuple[bool, str]:
        """判断是否应该发送表情包"""
        # 严肃场景默认不发送
        if is_serious_context and not self.strategy.use_sticker_in_serious_context:
            return False, "no_sticker"

        # 获取人格调整系数
        personality_coeff = self.strategy.personality_adjustment.get(
            personality_type, self.strategy.personality_adjustment["default"]
        )

        # 计算调整后的概率
        only_sticker_prob = self.strategy.only_sticker_probability * personality_coeff
        text_with_sticker_prob = self.strategy.text_with_sticker_probability * personality_coeff
        no_sticker_prob = self.strategy.no_sticker_probability / personality_coeff

        # 归一化概率
        total = only_sticker_prob + text_with_sticker_prob + no_sticker_prob
        only_sticker_prob /= total
        text_with_sticker_prob /= total
        no_sticker_prob /= total

        # 随机选择发送模式
        rand = random.random()
        if rand < only_sticker_prob:
            return True, "only_sticker"
        elif rand < only_sticker_prob + text_with_sticker_prob:
            return True, "text_with_sticker"
        else:
            return False, "no_sticker"

    def _get_dominant_emotion(
        self, emotion_dict: Dict[str, float]
    ) -> Tuple[Optional[StickerEmotion], float]:
        """获取主导情绪"""
        if not emotion_dict:
            return None, 0.0

        # 找到强度最高的情绪
        max_emotion = max(emotion_dict.items(), key=lambda x: x[1])
        emotion_str, intensity = max_emotion

        # 转换为StickerEmotion枚举
        try:
            emotion = StickerEmotion(emotion_str.lower())
            return emotion, intensity
        except ValueError:
            # 如果情绪类型不匹配，尝试寻找最接近的
            return self._map_emotion_to_enum(emotion_str), intensity

    def _map_emotion_to_enum(self, emotion_str: str) -> Optional[StickerEmotion]:
        """将自定义情绪字符串映射到标准情绪枚举"""
        emotion_map = {
            "happy": StickerEmotion.HAPPY,
            "joy": StickerEmotion.HAPPY,
            "glad": StickerEmotion.HAPPY,
            "pleased": StickerEmotion.HAPPY,
            "excited": StickerEmotion.EXCITED,
            "thrilled": StickerEmotion.EXCITED,
            "sad": StickerEmotion.SAD,
            "unhappy": StickerEmotion.SAD,
            "sorrow": StickerEmotion.SAD,
            "angry": StickerEmotion.ANGRY,
            "mad": StickerEmotion.ANGRY,
            "furious": StickerEmotion.ANGRY,
            "surprised": StickerEmotion.SURPRISED,
            "shocked": StickerEmotion.SURPRISED,
            "amazed": StickerEmotion.SURPRISED,
            "confused": StickerEmotion.CONFUSED,
            "puzzled": StickerEmotion.CONFUSED,
            "loving": StickerEmotion.LOVING,
            "affectionate": StickerEmotion.LOVING,
            "embarrassed": StickerEmotion.EMBARRASSED,
            "shy": StickerEmotion.EMBARRASSED,
            "proud": StickerEmotion.PROUD,
            "confident": StickerEmotion.PROUD,
            "relaxed": StickerEmotion.RELAXED,
            "calm": StickerEmotion.RELAXED,
            "silly": StickerEmotion.SILLY,
            "funny": StickerEmotion.SILLY,
            "goofy": StickerEmotion.SILLY,
            "supportive": StickerEmotion.SUPPORTIVE,
            "encouraging": StickerEmotion.SUPPORTIVE,
            "comforting": StickerEmotion.SUPPORTIVE,
        }

        return emotion_map.get(emotion_str.lower())

    async def _get_candidate_stickers(
        self,
        emotion: Optional[StickerEmotion],
        personality_type: str,
        context_keywords: Optional[List[str]] = None,
        sticker_type_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Sticker]:
        """获取候选表情包"""
        from app.models.sticker import StickerType

        # 转换类型
        sticker_type = None
        if sticker_type_filter:
            try:
                sticker_type = StickerType(sticker_type_filter)
            except ValueError:
                pass

        stickers = []

        # 如果有情绪，优先根据情绪获取
        if emotion:
            stickers = await self.sticker_service.get_stickers_by_emotion(
                emotion=emotion,
                personality=personality_type,
                sticker_type=sticker_type,
                limit=limit,
            )

        # 如果数量不足或没有情绪，尝试搜索关键词（不限制情绪）
        if len(stickers) < 10 and context_keywords:
            for keyword in context_keywords[:3]:  # 只搜索前3个关键词
                keyword_stickers = await self.sticker_service.search_stickers(
                    keyword=keyword, type=sticker_type, emotion=None, limit=20
                )
                # 去重
                existing_ids = {s.id for s in stickers}
                for s in keyword_stickers:
                    if s.id not in existing_ids:
                        stickers.append(s)
                        existing_ids.add(s.id)

        # 如果还是不够，随机获取一些梗图
        if sticker_type_filter == "meme" and len(stickers) < 5:
            random_stickers = await self.sticker_service.get_random_stickers(
                type=sticker_type, limit=10
            )
            existing_ids = {s.id for s in stickers}
            for s in random_stickers:
                if s.id not in existing_ids:
                    stickers.append(s)
                    existing_ids.add(s.id)

        return stickers

    def _calculate_match_score(
        self,
        sticker: Sticker,
        dominant_emotion: Optional[StickerEmotion],
        emotion_intensity: float,
        personality_type: str,
        context_keywords: Optional[List[str]] = None,
    ) -> Tuple[float, float, float, float]:
        """计算表情包的匹配分数"""
        # 1. 情绪匹配分 (0-1)
        emotion_match = 0.0
        if dominant_emotion and sticker.emotion == dominant_emotion:
            emotion_match = 1.0 * emotion_intensity
        # 如果表情包没有情绪标签，给一个基础分
        elif not sticker.emotion:
            emotion_match = 0.5
        emotion_match *= sticker.emotion_weight

        # 2. 人格匹配分 (0-1)
        personality_match = 0.0
        if sticker.personality_match == StickerPersonalityMatch.ALL:
            personality_match = 1.0
        elif sticker.personality_match.value == personality_type:
            personality_match = 1.0
        personality_match *= sticker.personality_weight

        # 3. 上下文匹配分 (0-1)
        context_match = 0.0
        if context_keywords:
            # 计算关键词匹配度
            sticker_keywords = set(sticker.keywords + sticker.tags)
            matched_keywords = [k for k in context_keywords if k.lower() in sticker_keywords]
            if matched_keywords:
                context_match = min(1.0, len(matched_keywords) / len(context_keywords))
        context_match *= sticker.context_weight

        # 4. 基础权重和成功率
        base_score = sticker.base_weight * sticker.success_rate

        # 5. 综合评分（总分0-4左右）
        total_score = (
            base_score * (1 + emotion_match) * (1 + personality_match) * (1 + context_match)
        )

        # 6. 使用次数衰减（避免总是选同一个）
        usage_penalty = min(0.9, 1.0 - (sticker.usage_count / 1000))  # 最多衰减10%
        total_score *= usage_penalty

        return total_score, emotion_match, personality_match, context_match

    def _weighted_random_choice(self, candidates: List[Tuple]) -> Optional[Tuple]:
        """带权重的随机选择"""
        if not candidates:
            return None

        # 提取权重
        total_weight = sum(score for _, score, _, _, _ in candidates)
        if total_weight <= 0:
            # 如果所有权重都是0，随机选一个
            return random.choice(candidates)

        # 随机选择
        rand = random.uniform(0, total_weight)
        cumulative = 0.0
        for candidate in candidates:
            _, score, _, _, _ = candidate
            cumulative += score
            if cumulative >= rand:
                return candidate

        # 默认返回第一个
        return candidates[0]

    async def select_stickers_for_reply(
        self,
        current_emotion: Dict[str, float],
        personality_type: str = "default",
        context_keywords: Optional[List[str]] = None,
        is_serious_context: bool = False,
        sticker_type_filter: Optional[str] = None,
    ) -> Tuple[Optional[Sticker], str]:
        """
        为回复选择合适的表情包

        Returns:
            (sticker, send_mode) - send_mode: "only_sticker", "text_with_sticker", "no_sticker"
        """
        selection = await self.select_optimal_sticker(
            current_emotion=current_emotion,
            personality_type=personality_type,
            context_keywords=context_keywords,
            is_serious_context=is_serious_context,
            sticker_type_filter=sticker_type_filter,
        )

        if not selection:
            return None, "no_sticker"

        # 记录使用次数
        await self.sticker_service.increment_usage(selection.sticker.id)

        # 确定发送模式
        # 根据之前的概率判断，这里简化处理
        personality_coeff = self.strategy.personality_adjustment.get(
            personality_type, self.strategy.personality_adjustment["default"]
        )
        if random.random() < 0.375 * personality_coeff:  # 0.3 / (0.3 + 0.5)
            send_mode = "only_sticker"
        else:
            send_mode = "text_with_sticker"

        return selection.sticker, send_mode
