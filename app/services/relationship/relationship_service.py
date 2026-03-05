import math
import re
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from app.services.profile.models import RelationshipStage, UserProfile

from .models import InteractionRecord


class RelationshipService:
    """
    关系管理服务
    管理亲密度、信任度和关系阶段演进
    """

    def __init__(self):
        self.interaction_history: Dict[str, List[InteractionRecord]] = defaultdict(list)
        self.time_decay_lambda = 0.01  # 时间衰减系数，半衰期约69天

    async def record_interaction(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        emotional_context: Dict[str, float] = None,
    ) -> InteractionRecord:
        """
        记录单次互动并计算质量分数
        """
        emotional_context = emotional_context or {}

        # 分析自我披露深度
        disclosure_depth = self._analyze_disclosure_depth(user_message)
        disclosure_topics = self._extract_disclosure_topics(user_message)

        # 计算情感共鸣度
        emotional_resonance = self._calculate_emotional_resonance(
            emotional_context.get("user_emotion", {}), emotional_context.get("ai_emotion", {})
        )

        # 计算重要性分数
        importance = self._calculate_importance(
            disclosure_depth, emotional_context.get("intensity", 0.5), len(disclosure_topics)
        )

        # 计算综合质量分
        quality_score = emotional_resonance * 0.3 + disclosure_depth * 0.4 + importance * 0.3

        record = InteractionRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.now(),
            user_message=user_message,
            ai_response=ai_response,
            user_emotion=emotional_context.get("user_emotion", {}),
            ai_emotion=emotional_context.get("ai_emotion", {}),
            emotional_resonance=emotional_resonance,
            user_disclosure_depth=disclosure_depth,
            disclosure_topics=disclosure_topics,
            quality_score=quality_score,
            importance_score=importance,
            topics=emotional_context.get("topics", []),
            entities=[],
        )

        self.interaction_history[user_id].append(record)

        return record

    async def calculate_intimacy(self, user_id: str) -> float:
        """
        计算当前亲密度
        公式: 亲密度 = Σ(互动质量 × 时间衰减因子)
        """
        interactions = self.interaction_history[user_id]
        if not interactions:
            return 0.0

        now = datetime.now()
        total_weight = 0.0
        weighted_sum = 0.0

        for interaction in interactions:
            # 时间衰减因子
            days_passed = (now - interaction.timestamp).days
            time_decay = math.exp(-self.time_decay_lambda * days_passed)

            # 加权质量分
            weighted_quality = interaction.quality_score * time_decay

            weighted_sum += weighted_quality
            total_weight += time_decay

        # 归一化到0-1
        if total_weight > 0:
            intimacy = weighted_sum / total_weight
            return min(1.0, intimacy * 2)  # 放大系数，让增长更明显

        return 0.0

    async def calculate_trust(self, user_id: str) -> float:
        """
        计算信任度
        基于诚实度、可靠性和亲密度
        """
        interactions = self.interaction_history[user_id]
        if len(interactions) < 5:
            return 0.1  # 初始信任度

        # 诚实度：用户自我披露的一致性
        honesty = self._calculate_honesty(interactions)

        # 可靠性：互动频率的稳定性
        reliability = self._calculate_reliability(interactions)

        # 亲密度影响
        intimacy = await self.calculate_intimacy(user_id)

        # 信任度公式
        trust = honesty * 0.4 + reliability * 0.3 + intimacy * 0.3

        return min(1.0, trust)

    async def update_relationship_stage(
        self, user_id: str, profile: UserProfile
    ) -> RelationshipStage:
        """
        检查并更新关系阶段
        基于社会渗透理论的阶段跃迁逻辑
        """
        current_stage = profile.relationship.stage
        intimacy = await self.calculate_intimacy(user_id)
        trust = await self.calculate_trust(user_id)

        # 阶段跃迁条件（严格按照Social Penetration Theory）
        new_stage = current_stage

        if trust > 0.9 and intimacy > 0.8:
            new_stage = RelationshipStage.CONFIDANT
        elif trust > 0.7 and intimacy > 0.6:
            new_stage = RelationshipStage.CLOSE_FRIEND
        elif trust > 0.5 and intimacy > 0.4:
            new_stage = RelationshipStage.FRIEND
        elif trust > 0.3 and intimacy > 0.2:
            new_stage = RelationshipStage.ACQUAINTANCE
        else:
            new_stage = RelationshipStage.STRANGER

        # 阶段变化处理
        if new_stage != current_stage:
            # 记录历史
            profile.relationship.stage_history.append(
                {
                    "stage": current_stage.value,
                    "entered_at": profile.relationship.stage_entered_at.isoformat(),
                    "left_at": datetime.now().isoformat(),
                    "intimacy": float(intimacy),
                    "trust": float(trust),
                }
            )

            # 更新当前阶段
            profile.relationship.stage = new_stage
            profile.relationship.stage_entered_at = datetime.now()

            # 触发阶段变化事件
            await self._on_stage_change(user_id, current_stage, new_stage)

        # 更新指标
        profile.relationship.intimacy = float(intimacy)
        profile.relationship.trust = float(trust)
        profile.relationship.interaction_count += 1
        profile.relationship.last_interaction_at = datetime.now()

        # 获取用户互动历史
        user_interactions = self.interaction_history.get(user_id, [])
        profile.relationship.self_disclosure_depth = max(
            profile.relationship.self_disclosure_depth,
            (
                self._analyze_disclosure_depth(user_interactions[-1].user_message)
                if user_interactions
                else 0
            ),
        )

        return new_stage

    def _analyze_disclosure_depth(self, text: str) -> float:
        """
        分析自我披露深度
        基于话题敏感度和隐私程度
        """
        depth_indicators = {
            0.1: ["天气", "新闻", "电影", "电视剧", "综艺", "吃饭"],  # 表层
            0.3: ["工作", "学习", "爱好", "游戏", "音乐", "旅行"],  # 一般
            0.5: ["家庭", "朋友", "计划", "目标", "理想", "生活"],  # 个人
            0.7: ["感情", "压力", "梦想", "烦恼", "焦虑", "难过"],  # 深层
            0.9: ["创伤", "恐惧", "秘密", "隐私", "往事", "经历"],  # 核心
        }

        max_depth = 0.1
        for depth, keywords in depth_indicators.items():
            if any(kw in text for kw in keywords):
                max_depth = max(max_depth, depth)

        # 结合情感强度调整
        emotional_words = len(
            re.findall(r"[很|非常|特别|超级|真的].*?[开心|难过|生气|害怕|想哭|感动]", text)
        )
        depth_boost = min(0.1, emotional_words * 0.02)

        return min(1.0, max_depth + depth_boost)

    def _extract_disclosure_topics(self, text: str) -> List[str]:
        """提取披露的话题"""
        topics = []

        # 简单话题匹配
        topic_keywords = [
            "工作",
            "学习",
            "生活",
            "感情",
            "家庭",
            "朋友",
            "游戏",
            "音乐",
            "电影",
            "旅行",
            "美食",
            "运动",
            "梦想",
            "计划",
            "烦恼",
            "压力",
            "快乐",
            "难过",
        ]

        for keyword in topic_keywords:
            if keyword in text:
                topics.append(keyword)

        return topics

    def _calculate_emotional_resonance(
        self, user_emotion: Dict[str, float], ai_emotion: Dict[str, float]
    ) -> float:
        """
        计算情感共鸣度
        基于情感状态的相似性
        """
        if not user_emotion or not ai_emotion:
            return 0.5

        # 计算愉悦度和激活度的相似性
        valence_sim = 1 - abs(user_emotion.get("valence", 0) - ai_emotion.get("valence", 0))
        arousal_sim = 1 - abs(user_emotion.get("arousal", 0) - ai_emotion.get("arousal", 0))

        # 共鸣度 = 相似度 × 情感强度
        user_intensity = user_emotion.get("intensity", 0.5)

        resonance = (valence_sim * 0.5 + arousal_sim * 0.5) * user_intensity

        return resonance

    def _calculate_importance(
        self, disclosure_depth: float, intensity: float, topic_count: int
    ) -> float:
        """计算互动重要性"""
        return min(1.0, disclosure_depth * 0.6 + intensity * 0.3 + topic_count * 0.1)

    def _calculate_honesty(self, interactions: List[InteractionRecord]) -> float:
        """计算诚实度：基于用户自我披露的一致性"""
        # 简单实现：披露深度越高，诚实度越高
        total_disclosure = sum(ir.user_disclosure_depth for ir in interactions)
        avg_disclosure = total_disclosure / len(interactions)
        return min(1.0, avg_disclosure * 1.5)

    def _calculate_reliability(self, interactions: List[InteractionRecord]) -> float:
        """计算可靠性：基于互动频率的稳定性"""
        if len(interactions) < 2:
            return 0.5

        # 计算互动间隔的标准差，越小越可靠
        timestamps = [ir.timestamp.timestamp() for ir in interactions]
        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

        if not intervals:
            return 0.5

        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std = math.sqrt(variance)

        # 归一化，标准差越小可靠性越高
        reliability = 1 - min(1.0, std / (7 * 24 * 3600))  # 以一周为基准

        return reliability

    async def _on_stage_change(
        self, user_id: str, old_stage: RelationshipStage, new_stage: RelationshipStage
    ):
        """阶段变化回调，可用于触发特殊事件"""
        # 例如：关系升级时发送特别消息
        stage_messages = {
            RelationshipStage.ACQUAINTANCE: "我们已经是熟人啦😉",
            RelationshipStage.FRIEND: "感觉我们已经是很好的朋友了呢🥰",
            RelationshipStage.CLOSE_FRIEND: "现在我们是无话不谈的好朋友啦✨",
            RelationshipStage.CONFIDANT: "能成为你的挚友真的很开心🫂",
        }

        if new_stage in stage_messages:
            # 这里可以触发主动消息发送逻辑
            pass
