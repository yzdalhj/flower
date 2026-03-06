"""情感系统模块"""

from app.services.emotion.emotion_analyzer import (
    EmotionResult,
    MultilingualEmotionAnalyzer,
    get_emotion_analyzer,
)
from app.services.emotion.emotion_dynamics import (
    AIEmotionalState,
    DecayCurve,
    EmotionDynamics,
    EmotionState,
    Stimulus,
    create_negative_stimulus,
    create_positive_stimulus,
    create_surprise_stimulus,
)
from app.services.emotion.emotion_state import (
    AIEmotionManager,
    get_emotion_manager,
    remove_emotion_manager,
)

__all__ = [
    # emotion_analyzer
    "EmotionResult",
    "MultilingualEmotionAnalyzer",
    "get_emotion_analyzer",
    # emotion_dynamics
    "AIEmotionalState",
    "DecayCurve",
    "EmotionDynamics",
    "EmotionState",
    "Stimulus",
    "create_negative_stimulus",
    "create_positive_stimulus",
    "create_surprise_stimulus",
    # emotion_state
    "AIEmotionManager",
    "get_emotion_manager",
    "remove_emotion_manager",
]
