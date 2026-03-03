"""枚举类型定义"""
from enum import Enum


class Platform(Enum):
    """平台类型"""
    WECHAT = "wechat"
    QQ = "qq"


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"


class Personality(Enum):
    """性格类型"""
    LIVELY = "lively"          # 活泼
    GENTLE = "gentle"          # 温柔
    HUMOROUS = "humorous"      # 幽默
    SERIOUS = "serious"        # 严肃
    INTELLECTUAL = "intellectual"  # 知性


class Role(Enum):
    """角色类型"""
    FRIEND = "friend"          # 朋友
    ASSISTANT = "assistant"    # 助手
    MENTOR = "mentor"          # 导师
    LISTENER = "listener"      # 倾听者


class Gender(Enum):
    """性别表现"""
    MALE = "male"              # 男性
    FEMALE = "female"          # 女性
    NEUTRAL = "neutral"        # 中性


class EmotionType(Enum):
    """情绪类型"""
    HAPPY = "happy"            # 开心
    CALM = "calm"              # 平静
    EXCITED = "excited"        # 兴奋
    SAD = "sad"                # 难过
    WORRIED = "worried"        # 担心
    SURPRISED = "surprised"    # 惊讶
    ANGRY = "angry"            # 生气
    SHY = "shy"                # 害羞


class SceneType(Enum):
    """场景类型"""
    CHAT = "chat"              # 闲聊
    HELP = "help"              # 求助
    CONFIDE = "confide"        # 倾诉
    SHARE_JOY = "share_joy"    # 分享喜悦
    DISCUSS = "discuss"        # 讨论问题
    OTHER = "other"            # 其他


class EmotionalTone(Enum):
    """情感基调"""
    POSITIVE = "positive"      # 积极
    NEGATIVE = "negative"      # 消极
    NEUTRAL = "neutral"        # 中性


class ConnectionType(Enum):
    """连接类型"""
    WEB_API = "web_api"        # Web API
    CLIENT_CONTROL = "client_control"  # 客户端控制
    PROTOCOL_SIMULATION = "protocol_simulation"  # 协议模拟


class SessionStatus(Enum):
    """会话状态"""
    CONNECTED = "connected"    # 已连接
    DISCONNECTED = "disconnected"  # 已断开
    RECONNECTING = "reconnecting"  # 重连中
    ERROR = "error"            # 错误状态
