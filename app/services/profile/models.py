from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RelationshipStage(Enum):
    """关系阶段枚举"""

    STRANGER = "stranger"  # 陌生人 (0.0-0.2)
    ACQUAINTANCE = "acquaintance"  # 熟人 (0.2-0.4)
    FRIEND = "friend"  # 朋友 (0.4-0.6)
    CLOSE_FRIEND = "close_friend"  # 密友 (0.6-0.8)
    CONFIDANT = "confidant"  # 挚友 (0.8-1.0)


@dataclass
class RelationshipState:
    """
    关系状态模型
    管理用户与AI之间的关系演进
    """

    # 关系阶段
    stage: RelationshipStage = RelationshipStage.STRANGER

    # 核心指标 (0-1)
    intimacy: float = 0.0  # 亲密度
    trust: float = 0.0  # 信任度
    familiarity: float = 0.0  # 熟悉度

    # 互动指标
    interaction_count: int = 0  # 互动次数
    self_disclosure_depth: float = 0.0  # 用户自我披露深度
    ai_disclosure_depth: float = 0.0  # AI自我披露深度

    # 时间戳
    stage_entered_at: datetime = field(default_factory=datetime.now)
    last_interaction_at: Optional[datetime] = None

    # 历史记录
    stage_history: List[Dict] = field(default_factory=list)
    # [{"stage": "STRANGER", "entered_at": ..., "left_at": ..., "intimacy": 0.1}]

    # 关系标签
    tags: List[str] = field(default_factory=list)
    # ["游戏伙伴", "深夜树洞", "职场导师"]


@dataclass
class UserProfile:
    """
    用户画像数据模型
    使用spaCy NER自动提取和更新
    """

    user_id: str  # 用户唯一标识
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # ===== 基础信息 (Basic Info) =====
    basic_info: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "name": "小明",                  # 姓名（NER提取）
    #     "nickname": "",                   # 昵称偏好
    #     "gender": "male",                 # 性别推断
    #     "age_estimate": 25,               # 年龄估计
    #     "location": "北京",               # 地理位置（NER）
    #     "occupation": "程序员",           # 职业（NER）
    #     "education": "本科",              # 教育背景
    # }

    # ===== 偏好画像 (Preferences) =====
    preferences: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "likes": ["游戏", "音乐", "旅行"],     # 喜好（NER提取）
    #     "dislikes": ["加班", "早起"],          # 厌恶
    #     "hobbies": ["打篮球", "看电影"],       # 爱好
    #     "food_preferences": ["辣", "火锅"],    # 饮食偏好
    #     "music_taste": ["周杰伦", "摇滚"],     # 音乐品味
    #     "communication_style": "casual",       # 沟通风格
    # }

    # ===== 情感模式 (Emotional Patterns) =====
    emotional_patterns: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "baseline_mood": 0.6,              # 基线情绪值
    #     "mood_volatility": 0.3,            # 情绪波动性
    #     "stress_triggers": ["deadline", "批评"],  # 压力触发点
    #     "comfort_topics": ["游戏", "美食"],       # 安慰话题
    #     "emotional_needs": ["认可", "陪伴"],      # 情感需求
    # }

    # ===== 关系状态 (Relationship State) =====
    relationship: RelationshipState = field(default_factory=RelationshipState)

    # ===== 互动统计 (Interaction Stats) =====
    interaction_stats: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "total_messages": 1000,            # 总消息数
    #     "total_sessions": 50,              # 总会话数
    #     "avg_session_length": 20,          # 平均会话长度
    #     "last_interaction": datetime,      # 最后互动时间
    #     "interaction_frequency": 0.5,      # 互动频率(次/天)
    # }

    # ===== 记忆摘要 (Memory Summary) =====
    memory_summary: str = ""  # 用户记忆文本摘要
    key_memories: List[str] = field(default_factory=list)  # 关键记忆列表

    # ===== 实体提取缓存 (NER Cache) =====
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    # {
    #     "PERSON": ["张三", "李四"],        # 人物
    #     "ORG": ["腾讯", "阿里巴巴"],       # 组织
    #     "GPE": ["北京", "上海"],           # 地理政治实体
    #     "EVENT": ["生日", "年会"],         # 事件
    #     "DATE": ["2024-01-01"],            # 日期
    # }
