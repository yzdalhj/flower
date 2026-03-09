"""账号限制器 - 管理账号的每日限制和频率限制"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """频率限制超出异常"""

    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class DailyLimitExceeded(Exception):
    """每日限制超出异常"""

    def __init__(self, limit_type: str, current: float, maximum: float):
        self.limit_type = limit_type
        self.current = current
        self.maximum = maximum
        message = f"{limit_type}限制超出: {current}/{maximum}"
        super().__init__(message)


class AccountLimiter:
    """账号限制器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 内存中的频率限制记录: {account_id: [(timestamp, count), ...]}
        self._rate_limit_cache: dict[str, list[tuple[datetime, int]]] = {}

    async def check_and_update_limits(
        self,
        account_id: str,
        message_count: int = 1,
        cost: float = 0.0,
    ) -> dict[str, Any]:
        """检查并更新限制

        Args:
            account_id: 账号ID
            message_count: 消息数量
            cost: 成本

        Returns:
            限制状态

        Raises:
            ValueError: 账号不存在
            DailyLimitExceeded: 每日限制超出
        """
        # 获取账号
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        # 检查账号状态
        if not account.is_running():
            raise ValueError(f"账号未运行: {account_id}")

        # 检查是否需要重置每日统计
        await self._check_daily_reset(account)

        # 检查每日消息数限制
        if account.today_message_count + message_count > account.max_daily_messages:
            raise DailyLimitExceeded(
                limit_type="每日消息数",
                current=account.today_message_count + message_count,
                maximum=account.max_daily_messages,
            )

        # 检查每日成本限制
        if account.today_cost + cost > account.max_daily_cost:
            raise DailyLimitExceeded(
                limit_type="每日成本",
                current=account.today_cost + cost,
                maximum=account.max_daily_cost,
            )

        # 检查频率限制
        await self._check_rate_limit(account_id, message_count)

        # 更新统计
        account.update_stats(message_count, cost)
        await self.db.commit()

        return account.check_daily_limit()

    async def _check_daily_reset(self, account: Account) -> bool:
        """检查是否需要重置每日统计

        Args:
            account: 账号对象

        Returns:
            是否已重置
        """
        now = datetime.utcnow()
        last_reset = account.stats_reset_at

        # 如果上次重置是昨天或更早，则重置
        if last_reset.date() < now.date():
            account.reset_daily_stats()
            logger.info(f"账号 {account.id} 每日统计已自动重置")
            return True

        return False

    async def _check_rate_limit(
        self,
        account_id: str,
        message_count: int,
        window_seconds: int = 60,
    ) -> bool:
        """检查频率限制

        Args:
            account_id: 账号ID
            message_count: 消息数量
            window_seconds: 时间窗口（秒）

        Returns:
            是否通过检查

        Raises:
            RateLimitExceeded: 频率限制超出
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # 获取账号的频率限制配置
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        max_requests = account.response_rate_limit

        # 清理过期的记录
        if account_id in self._rate_limit_cache:
            self._rate_limit_cache[account_id] = [
                (ts, count) for ts, count in self._rate_limit_cache[account_id] if ts > window_start
            ]
        else:
            self._rate_limit_cache[account_id] = []

        # 计算当前窗口内的请求数
        current_count = sum(count for ts, count in self._rate_limit_cache[account_id])

        # 检查是否超出限制
        if current_count + message_count > max_requests:
            # 计算需要等待的时间
            if self._rate_limit_cache[account_id]:
                oldest = min(ts for ts, _ in self._rate_limit_cache[account_id])
                retry_after = int(
                    (oldest + timedelta(seconds=window_seconds) - now).total_seconds()
                )
                retry_after = max(1, retry_after)
            else:
                retry_after = window_seconds

            raise RateLimitExceeded(
                message=f"频率限制超出: {current_count + message_count}/{max_requests} 请求/分钟",
                retry_after=retry_after,
            )

        # 记录本次请求
        self._rate_limit_cache[account_id].append((now, message_count))
        return True

    async def get_limit_status(self, account_id: str) -> dict[str, Any]:
        """获取限制状态

        Args:
            account_id: 账号ID

        Returns:
            限制状态

        Raises:
            ValueError: 账号不存在
        """
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        # 检查是否需要重置
        await self._check_daily_reset(account)

        limits = account.check_daily_limit()

        return {
            "account_id": account_id,
            "status": account.status,
            "daily_limits": {
                "messages": {
                    "used": account.today_message_count,
                    "limit": account.max_daily_messages,
                    "remaining": limits["message_remaining"],
                    "reached": limits["message_limit_reached"],
                },
                "cost": {
                    "used": round(account.today_cost, 4),
                    "limit": account.max_daily_cost,
                    "remaining": round(limits["cost_remaining"], 4),
                    "reached": limits["cost_limit_reached"],
                },
            },
            "rate_limit": {
                "limit": account.response_rate_limit,
                "window": "1分钟",
            },
            "can_send": account.can_send_message(),
        }

    async def reset_rate_limit(self, account_id: str) -> bool:
        """重置频率限制

        Args:
            account_id: 账号ID

        Returns:
            是否成功重置
        """
        if account_id in self._rate_limit_cache:
            del self._rate_limit_cache[account_id]
            logger.info(f"账号 {account_id} 频率限制已重置")
            return True
        return False

    async def get_all_limit_status(self) -> list[dict[str, Any]]:
        """获取所有账号的限制状态

        Returns:
            限制状态列表
        """
        result = await self.db.execute(select(Account))
        accounts = result.scalars().all()

        statuses = []
        for account in accounts:
            # 检查是否需要重置
            await self._check_daily_reset(account)

            limits = account.check_daily_limit()
            statuses.append(
                {
                    "account_id": account.id,
                    "name": account.name,
                    "platform": account.platform,
                    "status": account.status,
                    "daily_limits": {
                        "messages": {
                            "used": account.today_message_count,
                            "limit": account.max_daily_messages,
                            "remaining": limits["message_remaining"],
                            "reached": limits["message_limit_reached"],
                        },
                        "cost": {
                            "used": round(account.today_cost, 4),
                            "limit": account.max_daily_cost,
                            "remaining": round(limits["cost_remaining"], 4),
                            "reached": limits["cost_limit_reached"],
                        },
                    },
                    "can_send": account.can_send_message(),
                }
            )

        return statuses

    async def check_alert_thresholds(self, account_id: str) -> list[dict[str, Any]]:
        """检查告警阈值

        Args:
            account_id: 账号ID

        Returns:
            告警列表

        Raises:
            ValueError: 账号不存在
        """
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        alerts = []

        # 检查消息数告警 (80%, 90%, 100%)
        message_usage = account.today_message_count / account.max_daily_messages
        if message_usage >= 1.0:
            alerts.append(
                {
                    "type": "daily_message_limit",
                    "severity": "critical",
                    "message": f"每日消息数已用完: {account.today_message_count}/{account.max_daily_messages}",
                    "usage_percent": round(message_usage * 100, 1),
                }
            )
        elif message_usage >= 0.9:
            alerts.append(
                {
                    "type": "daily_message_limit",
                    "severity": "warning",
                    "message": f"每日消息数即将用完: {account.today_message_count}/{account.max_daily_messages}",
                    "usage_percent": round(message_usage * 100, 1),
                }
            )
        elif message_usage >= 0.8:
            alerts.append(
                {
                    "type": "daily_message_limit",
                    "severity": "info",
                    "message": f"每日消息数已使用80%: {account.today_message_count}/{account.max_daily_messages}",
                    "usage_percent": round(message_usage * 100, 1),
                }
            )

        # 检查成本告警
        cost_usage = (
            account.today_cost / account.max_daily_cost if account.max_daily_cost > 0 else 0
        )
        if cost_usage >= 1.0:
            alerts.append(
                {
                    "type": "daily_cost_limit",
                    "severity": "critical",
                    "message": f"每日成本已用完: ¥{account.today_cost:.2f}/¥{account.max_daily_cost:.2f}",
                    "usage_percent": round(cost_usage * 100, 1),
                }
            )
        elif cost_usage >= 0.9:
            alerts.append(
                {
                    "type": "daily_cost_limit",
                    "severity": "warning",
                    "message": f"每日成本即将用完: ¥{account.today_cost:.2f}/¥{account.max_daily_cost:.2f}",
                    "usage_percent": round(cost_usage * 100, 1),
                }
            )

        # 检查错误告警
        if account.error_count > 0:
            alerts.append(
                {
                    "type": "error_count",
                    "severity": "warning" if account.error_count < 5 else "critical",
                    "message": f"账号错误次数: {account.error_count}",
                    "error_message": account.error_message,
                }
            )

        return alerts
