"""频率控制器"""

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.active_behavior.models import (
    ActiveMessageRecord,
    ActiveMessageStatus,
    UserActivePreference,
)


class FrequencyController:
    """频率控制器"""

    def __init__(self):
        self.default_max_per_day = 2
        self.default_cooldown_hours = 4
        self.min_cooldown_hours = 1
        self.max_cooldown_hours = 24

    async def can_send_message(
        self, user_id: str, message_type: Optional[str] = None
    ) -> tuple[bool, str]:
        """检查是否可以发送消息给用户"""
        async with AsyncSessionLocal() as db:
            preference = await self._get_or_create_preference(db, user_id)

            # 1. 检查用户是否启用了该类型消息
            if message_type:
                enabled_types = json.loads(preference.enabled_message_types)
                if message_type not in enabled_types:
                    return False, f"消息类型 {message_type} 已被用户禁用"

            # 2. 检查当前时间是否在免打扰时间段
            now = datetime.utcnow()
            if await self._is_in_quiet_hours(preference, now):
                return False, "当前处于免打扰时间段"

            # 3. 检查今日发送次数是否超过限制
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            today_count = await db.scalar(
                select(func.count(ActiveMessageRecord.id))
                .where(ActiveMessageRecord.user_id == user_id)
                .where(ActiveMessageRecord.status == ActiveMessageStatus.SENT)
                .where(ActiveMessageRecord.actual_send_time >= today_start)
                .where(ActiveMessageRecord.actual_send_time < today_end)
            )

            if today_count >= preference.max_messages_per_day:
                return False, f"今日发送次数已达上限 {preference.max_messages_per_day} 条"

            # 4. 检查冷却时间
            if preference.last_message_sent_at:
                time_since_last = now - preference.last_message_sent_at
                cooldown_hours = await self._calculate_cooldown_hours(preference)

                if time_since_last < timedelta(hours=cooldown_hours):
                    remaining = cooldown_hours - time_since_last.total_seconds() / 3600
                    return False, f"冷却时间未到，还需等待 {remaining:.1f} 小时"

            return True, "可以发送"

    async def record_user_feedback(self, user_id: str, message_id: str, feedback: str):
        """记录用户反馈并调整发送策略"""
        async with AsyncSessionLocal() as db:
            # 更新消息记录的反馈
            message = await db.scalar(
                select(ActiveMessageRecord)
                .where(ActiveMessageRecord.id == message_id)
                .where(ActiveMessageRecord.user_id == user_id)
                .limit(1)
            )

            if not message:
                return

            message.user_feedback = feedback
            message.user_response_time = datetime.utcnow()

            # 更新用户偏好统计
            preference = await self._get_or_create_preference(db, user_id)

            if feedback == "positive":
                preference.positive_feedback_count += 1
                # 正面反馈：适当增加每日发送上限，减少冷却时间
                if preference.max_messages_per_day < 5:
                    preference.max_messages_per_day += 1
            elif feedback == "negative":
                preference.negative_feedback_count += 1
                # 负面反馈：减少每日发送上限，增加冷却时间
                if preference.max_messages_per_day > 1:
                    preference.max_messages_per_day -= 1

            await db.commit()

    async def update_user_preferences(self, user_id: str, **kwargs):
        """更新用户偏好设置"""
        async with AsyncSessionLocal() as db:
            preference = await self._get_or_create_preference(db, user_id)

            for key, value in kwargs.items():
                if hasattr(preference, key):
                    setattr(preference, key, value)

            await db.commit()
            await db.refresh(preference)

            return preference

    async def get_user_preferences(self, user_id: str) -> UserActivePreference:
        """获取用户偏好设置"""
        async with AsyncSessionLocal() as db:
            return await self._get_or_create_preference(db, user_id)

    async def get_user_statistics(self, user_id: str) -> dict:
        """获取用户主动消息统计信息"""
        async with AsyncSessionLocal() as db:
            preference = await self._get_or_create_preference(db, user_id)

            # 计算最近7天的发送情况
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            week_count = await db.scalar(
                select(func.count(ActiveMessageRecord.id))
                .where(ActiveMessageRecord.user_id == user_id)
                .where(ActiveMessageRecord.status == ActiveMessageStatus.SENT)
                .where(ActiveMessageRecord.actual_send_time >= seven_days_ago)
            )

            # 计算反馈率
            total_feedback = preference.positive_feedback_count + preference.negative_feedback_count
            feedback_rate = 0.0
            if preference.total_sent > 0:
                feedback_rate = total_feedback / preference.total_sent

            positive_rate = 0.0
            if total_feedback > 0:
                positive_rate = preference.positive_feedback_count / total_feedback

            return {
                "total_sent": preference.total_sent,
                "week_count": week_count,
                "max_per_day": preference.max_messages_per_day,
                "positive_count": preference.positive_feedback_count,
                "negative_count": preference.negative_feedback_count,
                "feedback_rate": feedback_rate,
                "positive_rate": positive_rate,
                "last_sent_at": (
                    preference.last_message_sent_at.isoformat()
                    if preference.last_message_sent_at
                    else None
                ),
            }

    async def _calculate_cooldown_hours(self, preference: UserActivePreference) -> float:
        """计算冷却时间（小时）"""
        # 根据用户反馈调整冷却时间
        if preference.total_sent == 0:
            return self.default_cooldown_hours

        positive_rate = preference.positive_feedback_count / preference.total_sent
        negative_rate = preference.negative_feedback_count / preference.total_sent

        # 正面反馈越多，冷却时间越短
        if positive_rate > 0.7:
            base_cooldown = 2.0
        elif positive_rate > 0.5:
            base_cooldown = 4.0
        elif negative_rate > 0.3:
            base_cooldown = 12.0
        elif negative_rate > 0.1:
            base_cooldown = 8.0
        else:
            base_cooldown = self.default_cooldown_hours

        # 确保在合理范围内
        return max(self.min_cooldown_hours, min(base_cooldown, self.max_cooldown_hours))

    async def _is_in_quiet_hours(self, preference: UserActivePreference, now: datetime) -> bool:
        """检查当前时间是否在免打扰时间段"""
        if preference.quiet_hours_start is None or preference.quiet_hours_end is None:
            return False

        current_hour = now.hour

        if preference.quiet_hours_start < preference.quiet_hours_end:
            # 免打扰时间在同一天
            return preference.quiet_hours_start <= current_hour < preference.quiet_hours_end
        else:
            # 免打扰时间跨天，比如 23:00 - 7:00
            return (
                current_hour >= preference.quiet_hours_start
                or current_hour < preference.quiet_hours_end
            )

    async def _get_or_create_preference(
        self, db: AsyncSession, user_id: str
    ) -> UserActivePreference:
        """获取或创建用户偏好设置"""
        result = await db.execute(
            select(UserActivePreference).where(UserActivePreference.user_id == user_id).limit(1)
        )
        preference = result.scalar_one_or_none()

        if not preference:
            preference = UserActivePreference(user_id=user_id)
            db.add(preference)
            await db.commit()
            await db.refresh(preference)

        return preference


# 全局控制器实例
frequency_controller = FrequencyController()
