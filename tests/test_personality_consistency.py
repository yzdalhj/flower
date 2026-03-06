"""人格一致性保障功能测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.personality.personality_consistency import get_personality_consistency_checker
from app.services.personality.personality_service import get_personality_service


@pytest.mark.asyncio
async def test_personality_consistency_checker():
    """测试人格一致性检测功能"""
    # 获取人格一致性检测服务
    consistency_checker = get_personality_consistency_checker()

    # 测试默认人格的一致性检测
    default_response = "害，这有什么大不了的，别想太多啦！"
    result = consistency_checker.check_consistency(default_response, "default")
    assert result["overall_score"] >= 0.7
    assert result["consistent"] is True

    # 测试不符合人格特征的回复
    inconsistent_response = "我理解您的感受，作为AI助手，我建议您保持冷静。"
    result = consistency_checker.check_consistency(inconsistent_response, "default")
    assert result["overall_score"] < 0.7
    assert result["consistent"] is False

    # 测试生成修正提示
    correction_prompt = consistency_checker.generate_correction_prompt(
        inconsistent_response, "default", result
    )
    assert "不符合" in correction_prompt
    assert "人格特征" in correction_prompt


@pytest.mark.asyncio
async def test_personality_evolution(db_session: AsyncSession):
    """测试人格演化功能"""
    # 获取人格服务
    personality_service = get_personality_service()

    # 获取默认人格
    default_personality = personality_service.get_personality("default")
    assert default_personality is not None

    # 保存初始版本号和演化历史长度
    initial_version = default_personality.version
    initial_history_length = len(default_personality.evolution_history)

    # 准备交互数据
    interaction_data = {
        "user_feedback": "positive",
        "emotion_valence": 0.8,
        "response_length": 50,
    }

    # 更新人格演化
    updated_personality = personality_service.update_personality_evolution(
        "default", interaction_data
    )

    # 验证人格已更新
    assert updated_personality.version > initial_version
    assert len(updated_personality.evolution_history) > initial_history_length


@pytest.mark.asyncio
async def test_cross_session_personality_transition(db_session: AsyncSession):
    """测试跨会话人格平滑过渡"""
    # 获取人格服务
    personality_service = get_personality_service()

    # 模拟用户ID
    user_id = "test_user_123"

    # 测试人格平滑过渡功能
    # 第一个会话使用默认人格
    first_personality = personality_service.get_personality_for_new_conversation(user_id)
    first_personality_id = first_personality.id

    # 第二个会话应该基于第一个会话的人格
    second_personality = personality_service.get_personality_for_new_conversation(
        user_id, first_personality_id
    )
    second_personality_id = second_personality.id

    # 验证第二个会话的人格ID基于第一个会话
    assert second_personality_id != first_personality_id
    assert first_personality_id in second_personality_id

    # 验证人格特征基本一致（平滑过渡）
    assert abs(second_personality.big_five.openness - first_personality.big_five.openness) < 0.1
    assert abs(second_personality.traits.warmth - first_personality.traits.warmth) < 0.1


@pytest.mark.asyncio
async def test_in_session_personality_consistency(db_session: AsyncSession):
    """测试同一会话中人格参数固定"""
    # 模拟用户ID
    user_id = "test_user_456"

    # 直接创建会话并设置人格ID
    from datetime import datetime

    from app.models.conversation import Conversation

    # 创建会话
    conversation = Conversation(
        user_id=user_id,
        status="active",
        personality_id="test_personality_123",
        started_at=datetime.now(),
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    # 保存初始人格ID
    initial_personality_id = conversation.personality_id

    # 模拟会话中的多次交互，验证人格ID保持不变
    # 这里我们只需要验证人格ID字段在会话中保持不变
    # 实际的对话处理会在其他测试中验证
    assert conversation.personality_id == initial_personality_id

    # 模拟更新会话（不修改人格ID）
    conversation.message_count = 5
    conversation.last_message_at = datetime.now()
    await db_session.commit()
    await db_session.refresh(conversation)

    # 验证人格ID仍然保持不变
    assert conversation.personality_id == initial_personality_id
