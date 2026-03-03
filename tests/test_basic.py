"""基础测试 - 验证项目结构和核心模块"""
import pytest
from datetime import datetime

from src.core.enums import (
    Platform, MessageType, Personality, Role, Gender,
    EmotionType, SceneType, EmotionalTone
)
from src.core.models import (
    Message, MessageContent, PersonalityProfile,
    EmotionState, SceneAnalysis, ConversationContext
)
from src.utils.logger import setup_logging, get_logger, mask_sensitive_data


def test_enums():
    """测试枚举类型"""
    assert Platform.WECHAT.value == "wechat"
    assert Platform.QQ.value == "qq"
    assert MessageType.TEXT.value == "text"
    assert Personality.LIVELY.value == "lively"
    assert Role.FRIEND.value == "friend"
    assert Gender.FEMALE.value == "female"
    assert EmotionType.HAPPY.value == "happy"
    assert SceneType.CHAT.value == "chat"
    assert EmotionalTone.POSITIVE.value == "positive"


def test_message_model():
    """测试消息数据模型"""
    content = MessageContent(
        type=MessageType.TEXT,
        text="Hello, world!"
    )
    
    message = Message(
        id="msg_001",
        user_id="user_001",
        platform=Platform.WECHAT,
        content=content,
        timestamp=datetime.now()
    )
    
    assert message.id == "msg_001"
    assert message.user_id == "user_001"
    assert message.platform == Platform.WECHAT
    assert message.content.text == "Hello, world!"


def test_personality_profile():
    """测试性格配置模型"""
    profile = PersonalityProfile(
        id="profile_001",
        personality=Personality.LIVELY,
        role=Role.FRIEND,
        gender=Gender.FEMALE,
        traits={"friendliness": 0.8, "humor": 0.7}
    )
    
    assert profile.personality == Personality.LIVELY
    assert profile.role == Role.FRIEND
    assert profile.gender == Gender.FEMALE
    assert profile.traits["friendliness"] == 0.8


def test_emotion_state():
    """测试情绪状态模型"""
    emotion = EmotionState(
        emotion_type=EmotionType.HAPPY,
        intensity=8.5,
        trigger="用户表达了感谢"
    )
    
    assert emotion.emotion_type == EmotionType.HAPPY
    assert emotion.intensity == 8.5
    assert emotion.trigger == "用户表达了感谢"


def test_scene_analysis():
    """测试场景分析模型"""
    scene = SceneAnalysis(
        scene_type=SceneType.CHAT,
        emotional_tone=EmotionalTone.POSITIVE,
        urgency=3,
        confidence=0.85
    )
    
    assert scene.scene_type == SceneType.CHAT
    assert scene.emotional_tone == EmotionalTone.POSITIVE
    assert scene.urgency == 3
    assert scene.confidence == 0.85


def test_conversation_context():
    """测试对话上下文模型"""
    context = ConversationContext(
        user_id="user_001"
    )
    
    assert context.user_id == "user_001"
    assert len(context.messages) == 0
    assert context.personality_profile is None


def test_logger_setup():
    """测试日志系统"""
    setup_logging(log_level="INFO")
    logger = get_logger("test")
    
    # 这不会抛出异常
    logger.info("test_message", key="value")


def test_mask_sensitive_data():
    """测试敏感数据脱敏"""
    data = {
        "username": "john",
        "password": "secret123",
        "api_key": "sk-1234567890abcdef",
        "phone": "13800138000",
        "normal_field": "normal_value"
    }
    
    masked = mask_sensitive_data(data)
    
    assert masked["username"] == "john"
    assert masked["password"] == "***"
    assert "***" in masked["api_key"]
    assert "***" in masked["phone"]
    assert masked["normal_field"] == "normal_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
