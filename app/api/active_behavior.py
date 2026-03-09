"""主动行为系统API"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.services.active_behavior import frequency_controller, message_generator, scheduler
from app.services.active_behavior.models import ActiveMessageRecord

router = APIRouter(prefix="/active-behavior", tags=["主动行为系统"])


class ActiveMessageResponse(BaseModel):
    """主动消息响应"""

    id: str
    user_id: str
    message_type: str
    content: str
    scheduled_send_time: datetime
    actual_send_time: Optional[datetime]
    status: str
    trigger_reason: str
    priority: int
    user_feedback: Optional[str]
    user_response_time: Optional[datetime]

    class Config:
        from_attributes = True


class UserPreferenceResponse(BaseModel):
    """用户偏好响应"""

    user_id: str
    max_messages_per_day: int
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    enabled_message_types: List[str]
    preferred_send_time_start: int
    preferred_send_time_end: int
    total_sent: int
    positive_feedback_count: int
    negative_feedback_count: int
    last_message_sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdatePreferenceRequest(BaseModel):
    """更新用户偏好请求"""

    max_messages_per_day: Optional[int] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    enabled_message_types: Optional[List[str]] = None
    preferred_send_time_start: Optional[int] = None
    preferred_send_time_end: Optional[int] = None


class FeedbackRequest(BaseModel):
    """用户反馈请求"""

    message_id: str
    feedback: str  # positive/negative/neutral


class GenerateMessageRequest(BaseModel):
    """生成消息请求"""

    user_id: str
    message_type: str  # care/topic/greeting/anniversary
    context: Optional[str] = None


@router.get("/status")
async def get_system_status():
    """获取系统运行状态"""
    return {"running": scheduler.running, "task_count": len(scheduler.tasks)}


@router.post("/start")
async def start_scheduler():
    """启动调度器"""
    if scheduler.running:
        return {"message": "调度器已经在运行中"}

    await scheduler.start()
    return {"message": "调度器已启动"}


@router.post("/stop")
async def stop_scheduler():
    """停止调度器"""
    if not scheduler.running:
        return {"message": "调度器已经停止"}

    await scheduler.stop()
    return {"message": "调度器已停止"}


@router.get("/messages/{user_id}", response_model=List[ActiveMessageResponse])
async def get_user_messages(
    user_id: str, limit: int = 20, status: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """获取用户的主动消息记录"""
    query = select(ActiveMessageRecord).where(ActiveMessageRecord.user_id == user_id)

    if status:
        query = query.where(ActiveMessageRecord.status == status)

    query = query.order_by(desc(ActiveMessageRecord.created_at)).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return messages


@router.get("/preferences/{user_id}", response_model=UserPreferenceResponse)
async def get_user_preferences(user_id: str):
    """获取用户主动消息偏好设置"""
    preference = await frequency_controller.get_user_preferences(user_id)
    return preference


@router.put("/preferences/{user_id}", response_model=UserPreferenceResponse)
async def update_user_preferences(user_id: str, request: UpdatePreferenceRequest):
    """更新用户主动消息偏好设置"""
    update_data = request.dict(exclude_unset=True)

    # 处理enabled_message_types，转换为JSON字符串
    if "enabled_message_types" in update_data:
        import json

        update_data["enabled_message_types"] = json.dumps(update_data["enabled_message_types"])

    preference = await frequency_controller.update_user_preferences(user_id, **update_data)
    return preference


@router.post("/feedback")
async def submit_feedback(user_id: str, request: FeedbackRequest):
    """提交用户对主动消息的反馈"""
    await frequency_controller.record_user_feedback(user_id, request.message_id, request.feedback)
    return {"message": "反馈已记录"}


@router.post("/generate-message")
async def generate_test_message(
    request: GenerateMessageRequest, db: AsyncSession = Depends(get_db)
):
    """生成测试主动消息"""
    from app.models import User, UserProfile

    # 获取用户信息
    user = await db.scalar(select(User).where(User.id == request.user_id).limit(1))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == request.user_id).limit(1)
    )
    if not profile:
        raise HTTPException(status_code=404, detail="用户画像不存在")

    content = ""
    trigger_reason = ""

    if request.message_type == "care":
        content, trigger_reason = await message_generator.generate_care_message(user, profile)
    elif request.message_type == "topic":
        content, trigger_reason = await message_generator.generate_topic_message(user, profile)
    elif request.message_type == "greeting":
        content, trigger_reason = await message_generator.generate_greeting_message(
            user, request.context or ""
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的消息类型")

    return {
        "content": content,
        "trigger_reason": trigger_reason,
        "message_type": request.message_type,
    }


@router.get("/statistics/{user_id}")
async def get_user_statistics(user_id: str):
    """获取用户主动消息统计信息"""
    stats = await frequency_controller.get_user_statistics(user_id)
    return stats


@router.post("/trigger-daily-check")
async def trigger_daily_check():
    """手动触发每日检查任务"""
    if not scheduler.running:
        raise HTTPException(status_code=400, detail="调度器未运行")

    await scheduler._run_daily_check()
    return {"message": "每日检查任务已执行"}


@router.post("/trigger-hourly-check")
async def trigger_hourly_check():
    """手动触发每小时检查任务"""
    if not scheduler.running:
        raise HTTPException(status_code=400, detail="调度器未运行")

    await scheduler._run_hourly_check()
    return {"message": "每小时检查任务已执行"}
