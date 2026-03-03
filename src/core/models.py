"""核心数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import (
    ConnectionType,
    EmotionalTone,
    EmotionType,
    Gender,
    MessageType,
    Personality,
    Platform,
    Role,
    SceneType,
    SessionStatus,
)


@dataclass
class MessageContent:
    """消息内容"""
    type: MessageType
    text: Optional[str] = None
    image_url: Optional[str] = None
    file_path: Optional[str] = None
    raw_data: Optional[Any] = None


@dataclass
class Message:
    """消息数据模型"""
    id: str
    user_id: str
    platform: Platform
    content: MessageContent
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalityProfile:
    """性格配置"""
    id: str
    personality: Personality
    role: Role
    gender: Gender
    traits: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class EmotionState:
    """情绪状态"""
    emotion_type: EmotionType
    intensity: float  # 0-10
    timestamp: datetime = field(default_factory=datetime.now)
    trigger: Optional[str] = None
    previous_state: Optional[EmotionType] = None


@dataclass
class SceneAnalysis:
    """场景分析结果"""
    scene_type: SceneType
    emotional_tone: EmotionalTone
    urgency: int  # 1-10
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: str
    messages: List[Message] = field(default_factory=list)
    personality_profile: Optional[PersonalityProfile] = None
    emotion_state: Optional[EmotionState] = None
    scene_history: List[SceneAnalysis] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SlangItem:
    """网络用语条目"""
    id: str
    content: str
    meaning: str
    tags: List[str]
    popularity: float  # 1-10
    usage_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    is_outdated: bool = False


@dataclass
class EmojiItem:
    """表情包条目"""
    id: str
    file_path: str
    tags: List[str]
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Response:
    """回复数据模型"""
    text: str
    emoji: Optional[EmojiItem] = None
    delay: float = 0.0  # 延迟时间（秒）
    split_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientStatus:
    """客户端状态"""
    is_running: bool
    is_logged_in: bool
    client_version: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class LoginStatus:
    """登录状态"""
    is_logged_in: bool
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    login_time: Optional[datetime] = None


@dataclass
class FileInfo:
    """文件信息"""
    file_name: str
    file_size: int  # 字节
    file_type: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    cached: bool = False
    cache_path: Optional[str] = None


@dataclass
class VoiceInfo:
    """语音信息"""
    duration: int  # 秒
    format: str
    file_size: int
    file_path: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class VideoInfo:
    """视频信息"""
    duration: int  # 秒
    format: str
    resolution: str
    file_size: int
    file_path: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class ClientSession:
    """客户端会话"""
    session_id: str
    platform: Platform
    connection_type: ConnectionType
    status: SessionStatus
    last_heartbeat: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    reconnect_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
