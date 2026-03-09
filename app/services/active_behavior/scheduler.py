"""主动行为调度器"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models import User, UserProfile
from app.services.active_behavior.models import (
    ActiveMessageRecord,
    ActiveMessageStatus,
    ActiveMessageType,
    ScheduledTaskLog,
    ScheduledTaskType,
    UserActivePreference,
)

settings = get_settings()


class ActiveBehaviorScheduler:
    """主动行为调度器"""

    def __init__(self):
        self.running = False
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        print("✅ 主动行为调度器已启动")

        # 启动定时任务
        self.tasks.append(asyncio.create_task(self._daily_check_task()))
        self.tasks.append(asyncio.create_task(self._hourly_check_task()))
        self.tasks.append(asyncio.create_task(self._pending_message_sender()))

    async def stop(self):
        """停止调度器"""
        self.running = False

        # 取消所有任务
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.tasks.clear()
        print("✅ 主动行为调度器已停止")

    async def _daily_check_task(self):
        """每日检查任务：每天凌晨1点执行"""
        while self.running:
            now = datetime.utcnow()
            next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            if not self.running:
                break

            try:
                await self._run_daily_check()
            except Exception as e:
                print(f"❌ 每日检查任务执行失败: {e}")

    async def _hourly_check_task(self):
        """每小时检查任务"""
        while self.running:
            await asyncio.sleep(3600)  # 等待1小时

            if not self.running:
                break

            try:
                await self._run_hourly_check()
            except Exception as e:
                print(f"❌ 每小时检查任务执行失败: {e}")

    async def _pending_message_sender(self):
        """待发送消息发送器：每分钟检查一次待发送的消息"""
        while self.running:
            await asyncio.sleep(60)  # 等待1分钟

            if not self.running:
                break

            try:
                await self._send_pending_messages()
            except Exception as e:
                print(f"❌ 待发送消息发送失败: {e}")

    async def _run_daily_check(self):
        """执行每日检查"""
        async with AsyncSessionLocal() as db:
            # 记录任务开始
            task_log = ScheduledTaskLog(task_type=ScheduledTaskType.DAILY_CHECK, status="running")
            db.add(task_log)
            await db.commit()

            try:
                # 1. 重要日期检测
                important_date_count = await self._check_important_dates(db)

                # 2. 长时间未联系检测
                no_contact_count = await self._check_long_time_no_contact(db)

                # 更新任务日志
                task_log.status = "success"
                task_log.completed_at = datetime.utcnow()
                task_log.message_count = important_date_count + no_contact_count
                await db.commit()

                print(
                    f"✅ 每日检查完成：重要日期生成 {important_date_count} 条消息，长时间未联系生成 {no_contact_count} 条消息"
                )

            except Exception as e:
                task_log.status = "failed"
                task_log.completed_at = datetime.utcnow()
                task_log.error_message = str(e)
                await db.commit()
                raise

    async def _run_hourly_check(self):
        """执行每小时检查"""
        async with AsyncSessionLocal() as db:
            # 记录任务开始
            task_log = ScheduledTaskLog(
                task_type=ScheduledTaskType.LONG_TIME_NO_CONTACT, status="running"
            )
            db.add(task_log)
            await db.commit()

            try:
                # 检查超过3天未联系的用户
                count = await self._check_long_time_no_contact(db, days=3)

                # 更新任务日志
                task_log.status = "success"
                task_log.completed_at = datetime.utcnow()
                task_log.message_count = count
                await db.commit()

                print(f"✅ 每小时检查完成：长时间未联系生成 {count} 条消息")

            except Exception as e:
                task_log.status = "failed"
                task_log.completed_at = datetime.utcnow()
                task_log.error_message = str(e)
                await db.commit()
                raise

    async def _check_important_dates(self, db: AsyncSession) -> int:
        """检查重要日期，生成提醒消息"""
        today = datetime.utcnow().date()
        count = 0

        # 查询所有用户的生日和重要日期
        result = await db.execute(
            select(User, UserProfile).join(UserProfile, User.id == UserProfile.user_id)
        )
        users_with_profiles = result.all()

        for user, profile in users_with_profiles:
            # 检查生日
            if profile.birthday:
                birthday = profile.birthday.date()
                if birthday.month == today.month and birthday.day == today.day:
                    # 今天是用户生日
                    await self._create_birthday_message(db, user, birthday.year)
                    count += 1

            # 检查其他重要日期
            if profile.important_dates:
                try:
                    important_dates = json.loads(profile.important_dates)
                    for date_item in important_dates:
                        date_str = date_item.get("date")
                        if not date_str:
                            continue

                        date_obj = datetime.fromisoformat(date_str).date()
                        if date_obj.month == today.month and date_obj.day == today.day:
                            # 今天是重要日期
                            await self._create_important_date_message(
                                db, user, date_item.get("title", "重要纪念日"), date_obj.year
                            )
                            count += 1
                except json.JSONDecodeError:
                    continue

        return count

    async def _check_long_time_no_contact(self, db: AsyncSession, days: int = 7) -> int:
        """检查长时间未联系的用户"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # 查询超过指定天数未互动的用户
        result = await db.execute(
            select(User)
            .where(User.last_interaction_at <= cutoff_time)
            .where(User.last_interaction_at.isnot(None))
        )
        users = result.scalars().all()

        count = 0
        for user in users:
            # 检查是否已经生成过未联系提醒
            existing = await db.execute(
                select(ActiveMessageRecord)
                .where(ActiveMessageRecord.user_id == user.id)
                .where(ActiveMessageRecord.trigger_reason == f"long_time_no_contact_{days}d")
                .where(ActiveMessageRecord.scheduled_send_time >= cutoff_time)
                .limit(1)
            )
            if existing.scalar_one_or_none():
                continue  # 已经生成过，跳过

            # 生成未联系问候消息
            await self._create_no_contact_message(db, user, days)
            count += 1

        return count

    async def _create_birthday_message(self, db: AsyncSession, user: User, birth_year: int):
        """创建生日祝福消息"""
        age = datetime.utcnow().year - birth_year

        # 计算合适的发送时间（用户偏好时间的中间点）
        preference = await self._get_or_create_user_preference(db, user.id)
        send_hour = (preference.preferred_send_time_start + preference.preferred_send_time_end) // 2
        send_time = datetime.utcnow().replace(hour=send_hour, minute=0, second=0, microsecond=0)

        # 如果当前时间已经过了发送时间，就明天发
        if send_time < datetime.utcnow():
            send_time += timedelta(days=1)

        message = ActiveMessageRecord(
            user_id=user.id,
            message_type=ActiveMessageType.ANNIVERSARY,
            content=f"🎉 生日快乐呀！今天是你{age}岁的生日，希望你今天过得开心，所有的愿望都能实现~",
            scheduled_send_time=send_time,
            trigger_reason=f"birthday_{birth_year}",
            priority=10,  # 生日祝福最高优先级
        )
        db.add(message)
        await db.commit()

    async def _create_important_date_message(
        self, db: AsyncSession, user: User, title: str, year: int
    ):
        """创建重要日期提醒消息"""
        anniversary = datetime.utcnow().year - year

        # 计算合适的发送时间
        preference = await self._get_or_create_user_preference(db, user.id)
        send_hour = (preference.preferred_send_time_start + preference.preferred_send_time_end) // 2
        send_time = datetime.utcnow().replace(hour=send_hour, minute=0, second=0, microsecond=0)

        if send_time < datetime.utcnow():
            send_time += timedelta(days=1)

        message = ActiveMessageRecord(
            user_id=user.id,
            message_type=ActiveMessageType.ANNIVERSARY,
            content=f"📅 今天是{title}哦！已经{anniversary}年啦，还记得当时的情景吗？",
            scheduled_send_time=send_time,
            trigger_reason=f"important_date_{title}",
            priority=8,
        )
        db.add(message)
        await db.commit()

    async def _create_no_contact_message(self, db: AsyncSession, user: User, days: int):
        """创建长时间未联系问候消息"""
        # 计算合适的发送时间
        preference = await self._get_or_create_user_preference(db, user.id)
        now = datetime.utcnow()
        send_hour = max(
            preference.preferred_send_time_start,
            min(now.hour + 1, preference.preferred_send_time_end),
        )
        send_time = now.replace(hour=send_hour, minute=0, second=0, microsecond=0)

        # 如果当前时间已经超过偏好结束时间，就明天发
        if now.hour >= preference.preferred_send_time_end:
            send_time = (now + timedelta(days=1)).replace(
                hour=preference.preferred_send_time_start, minute=0, second=0, microsecond=0
            )

        # 根据未联系天数生成不同的消息
        if days >= 7:
            content = "👋 好久没见到你啦，最近过得怎么样？有没有什么有趣的事情想要分享呀？"
        elif days >= 3:
            content = "😊 有几天没聊天了，最近忙不忙呀？"
        else:
            content = "😃 今天过得怎么样呀？"

        message = ActiveMessageRecord(
            user_id=user.id,
            message_type=ActiveMessageType.GREETING,
            content=content,
            scheduled_send_time=send_time,
            trigger_reason=f"long_time_no_contact_{days}d",
            priority=5,
        )
        db.add(message)
        await db.commit()

    async def _send_pending_messages(self):
        """发送待发送的消息"""
        now = datetime.utcnow()

        async with AsyncSessionLocal() as db:
            # 查询到了发送时间且状态为待发送的消息，按优先级排序
            result = await db.execute(
                select(ActiveMessageRecord)
                .where(ActiveMessageRecord.status == ActiveMessageStatus.PENDING)
                .where(ActiveMessageRecord.scheduled_send_time <= now)
                .order_by(ActiveMessageRecord.priority.desc())
                .limit(10)  # 每次最多发送10条，避免批量发送过多
            )
            messages = result.scalars().all()

            for message in messages:
                try:
                    # 检查是否在免打扰时间
                    preference = await self._get_or_create_user_preference(db, message.user_id)
                    if await self._is_in_quiet_hours(preference, now):
                        # 推迟到明天的偏好时间发送
                        message.scheduled_send_time = (now + timedelta(days=1)).replace(
                            hour=preference.preferred_send_time_start,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        await db.commit()
                        continue

                    # 检查今日发送次数是否超过限制
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = today_start + timedelta(days=1)

                    today_count = await db.scalar(
                        select(func.count(ActiveMessageRecord.id))
                        .where(ActiveMessageRecord.user_id == message.user_id)
                        .where(ActiveMessageRecord.status == ActiveMessageStatus.SENT)
                        .where(ActiveMessageRecord.actual_send_time >= today_start)
                        .where(ActiveMessageRecord.actual_send_time < today_end)
                    )

                    if today_count >= preference.max_messages_per_day:
                        # 超过今日限制，推迟到明天
                        message.scheduled_send_time = (now + timedelta(days=1)).replace(
                            hour=preference.preferred_send_time_start,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        await db.commit()
                        continue

                    # 发送消息（这里调用实际的发送接口）
                    await self._send_message_to_user(message)

                    # 更新消息状态
                    message.status = ActiveMessageStatus.SENT
                    message.actual_send_time = now

                    # 更新用户偏好统计
                    preference.total_sent += 1
                    preference.last_message_sent_at = now

                    await db.commit()
                    print(f"✅ 已发送主动消息给用户 {message.user_id}: {message.content[:50]}...")

                except Exception as e:
                    message.status = ActiveMessageStatus.FAILED
                    await db.commit()
                    print(f"❌ 发送主动消息失败 {message.id}: {e}")

    async def _send_message_to_user(self, message: ActiveMessageRecord):
        """实际发送消息给用户（这里需要对接具体的消息发送通道）"""
        # TODO: 实现实际的消息发送逻辑，对接微信/QQ等平台
        # 暂时打印日志模拟发送
        print(f"📤 发送主动消息给用户 {message.user_id}: {message.content}")

    async def _get_or_create_user_preference(
        self, db: AsyncSession, user_id: str
    ) -> UserActivePreference:
        """获取或创建用户主动消息偏好设置"""
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

    async def _is_in_quiet_hours(self, preference: UserActivePreference, now: datetime) -> bool:
        """检查当前时间是否在用户免打扰时间段"""
        if preference.quiet_hours_start is None or preference.quiet_hours_end is None:
            return False

        current_hour = now.hour

        if preference.quiet_hours_start < preference.quiet_hours_end:
            # 免打扰时间在同一天，比如 23:00 - 7:00 不适用这种情况
            return preference.quiet_hours_start <= current_hour < preference.quiet_hours_end
        else:
            # 免打扰时间跨天，比如 23:00 - 7:00
            return (
                current_hour >= preference.quiet_hours_start
                or current_hour < preference.quiet_hours_end
            )


# 全局调度器实例
scheduler = ActiveBehaviorScheduler()
