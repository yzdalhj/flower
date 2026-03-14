"""
记忆调度器
定期执行记忆整合和优化任务
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.core.session import AsyncSessionLocal
from app.services.memory.conversation_memory_extractor import MemoryConsolidator


class MemoryScheduler:
    """
    记忆调度器
    定期执行记忆相关的后台任务
    """

    def __init__(self):
        self.running = False
        self.tasks = []

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        print("[MemoryScheduler] 记忆调度器已启动")

        # 启动定时任务
        self.tasks = [
            asyncio.create_task(self._consolidation_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]

    async def stop(self):
        """停止调度器"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        print("[MemoryScheduler] 记忆调度器已停止")

    async def _consolidation_loop(self):
        """记忆整合循环 - 每小时执行一次"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次
                await self._consolidate_all_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MemoryScheduler] 记忆整合任务失败: {e}")

    async def _cleanup_loop(self):
        """记忆清理循环 - 每天执行一次"""
        while self.running:
            try:
                await asyncio.sleep(86400)  # 每天执行一次
                await self._cleanup_old_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MemoryScheduler] 记忆清理任务失败: {e}")

    async def _consolidate_all_memories(self):
        """整合所有用户的记忆"""
        print(f"[MemoryScheduler] 开始记忆整合任务: {datetime.now()}")

        async with AsyncSessionLocal() as session:
            from sqlalchemy import distinct, select

            from app.models.memory import Memory

            # 获取所有有记忆的用户
            result = await session.execute(select(distinct(Memory.user_id)))
            user_ids = [row[0] for row in result.all()]

            print(f"[MemoryScheduler] 发现 {len(user_ids)} 个用户需要整合")

            consolidator = MemoryConsolidator(session)

            for user_id in user_ids:
                try:
                    profile = await consolidator.consolidate_memories(user_id)
                    print(
                        f"[MemoryScheduler] 用户 {user_id}: {profile.get('memory_count', 0)} 条记忆"
                    )
                except Exception as e:
                    print(f"[MemoryScheduler] 整合用户 {user_id} 记忆失败: {e}")

    async def _cleanup_old_memories(self):
        """清理过期记忆"""
        print(f"[MemoryScheduler] 开始记忆清理任务: {datetime.now()}")

        async with AsyncSessionLocal() as session:
            from datetime import datetime

            from sqlalchemy import delete

            from app.models.memory import Memory

            # 删除过期记忆（超过1年且重要性低于5的记忆）
            cutoff_date = datetime.utcnow() - timedelta(days=365)

            result = await session.execute(
                delete(Memory).where(Memory.created_at < cutoff_date, Memory.importance < 5)
            )
            await session.commit()

            print(f"[MemoryScheduler] 清理了 {result.rowcount} 条过期记忆")


# 全局调度器实例
_memory_scheduler: Optional[MemoryScheduler] = None


def get_memory_scheduler() -> MemoryScheduler:
    """获取记忆调度器实例"""
    global _memory_scheduler
    if _memory_scheduler is None:
        _memory_scheduler = MemoryScheduler()
    return _memory_scheduler
