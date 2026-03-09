"""账号管理器 - 管理账号的生命周期"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account

logger = logging.getLogger(__name__)


class AccountManager:
    """账号管理器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_account(
        self,
        name: str,
        platform: str,
        platform_config: dict[str, Any],
        personality_config: dict[str, Any] | None = None,
        max_daily_messages: int = 1000,
        max_daily_cost: float = 50.0,
        enable_text: bool = True,
        enable_emoji: bool = True,
        enable_voice: bool = False,
        enable_image: bool = True,
        enable_proactive: bool = True,
        enable_learning: bool = True,
    ) -> Account:
        """创建新账号

        Args:
            name: 账号名称
            platform: 平台类型 (wechat/qq)
            platform_config: 平台配置
            personality_config: 人格配置
            max_daily_messages: 每日最大消息数
            max_daily_cost: 每日最大成本
            enable_text: 启用文本
            enable_emoji: 启用表情
            enable_voice: 启用语音
            enable_image: 启用图片
            enable_proactive: 启用主动行为
            enable_learning: 启用学习

        Returns:
            创建的账号
        """
        account = Account(
            name=name,
            platform=platform,
            status="stopped",
            platform_config=json.dumps(platform_config),
            personality_config=json.dumps(personality_config) if personality_config else None,
            max_daily_messages=max_daily_messages,
            max_daily_cost=max_daily_cost,
            enable_text=enable_text,
            enable_emoji=enable_emoji,
            enable_voice=enable_voice,
            enable_image=enable_image,
            enable_proactive=enable_proactive,
            enable_learning=enable_learning,
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"账号创建成功: {account.id} ({name})")
        return account

    async def get_account(self, account_id: str) -> Account | None:
        """获取账号

        Args:
            account_id: 账号ID

        Returns:
            账号对象或None
        """
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def list_accounts(
        self,
        platform: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Account]:
        """获取账号列表

        Args:
            platform: 平台过滤
            status: 状态过滤
            limit: 数量限制
            offset: 偏移量

        Returns:
            账号列表
        """
        query = select(Account)

        if platform:
            query = query.where(Account.platform == platform)
        if status:
            query = query.where(Account.status == status)

        query = query.order_by(Account.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_account(self, account_id: str) -> Account:
        """启动账号

        Args:
            account_id: 账号ID

        Returns:
            启动后的账号

        Raises:
            ValueError: 账号不存在
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        if account.is_running():
            logger.warning(f"账号已在运行: {account_id}")
            return account

        try:
            # 验证平台配置
            platform_config = json.loads(account.platform_config)
            if not platform_config:
                raise ValueError("平台配置为空")

            # 启动账号
            account.start()
            await self.db.commit()
            await self.db.refresh(account)

            logger.info(f"账号启动成功: {account_id}")
            return account

        except Exception as e:
            account.set_error(str(e))
            await self.db.commit()
            logger.error(f"账号启动失败: {account_id}, 错误: {e}")
            raise

    async def stop_account(self, account_id: str) -> Account:
        """停止账号

        Args:
            account_id: 账号ID

        Returns:
            停止后的账号

        Raises:
            ValueError: 账号不存在
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        if account.is_stopped():
            logger.warning(f"账号已停止: {account_id}")
            return account

        account.stop()
        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"账号停止成功: {account_id}")
        return account

    async def delete_account(self, account_id: str) -> bool:
        """删除账号

        Args:
            account_id: 账号ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 账号不存在或正在运行
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        if account.is_running():
            raise ValueError(f"账号正在运行，请先停止: {account_id}")

        await self.db.delete(account)
        await self.db.commit()

        logger.info(f"账号删除成功: {account_id}")
        return True

    async def update_account(
        self,
        account_id: str,
        name: str | None = None,
        platform_config: dict[str, Any] | None = None,
        personality_config: dict[str, Any] | None = None,
        max_daily_messages: int | None = None,
        max_daily_cost: float | None = None,
        enable_text: bool | None = None,
        enable_emoji: bool | None = None,
        enable_voice: bool | None = None,
        enable_image: bool | None = None,
        enable_proactive: bool | None = None,
        enable_learning: bool | None = None,
    ) -> Account:
        """更新账号配置

        Args:
            account_id: 账号ID
            name: 账号名称
            platform_config: 平台配置
            personality_config: 人格配置
            max_daily_messages: 每日最大消息数
            max_daily_cost: 每日最大成本
            enable_text: 启用文本
            enable_emoji: 启用表情
            enable_voice: 启用语音
            enable_image: 启用图片
            enable_proactive: 启用主动行为
            enable_learning: 启用学习

        Returns:
            更新后的账号

        Raises:
            ValueError: 账号不存在
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        if name is not None:
            account.name = name
        if platform_config is not None:
            account.platform_config = json.dumps(platform_config)
        if personality_config is not None:
            account.personality_config = json.dumps(personality_config)
        if max_daily_messages is not None:
            account.max_daily_messages = max_daily_messages
        if max_daily_cost is not None:
            account.max_daily_cost = max_daily_cost
        if enable_text is not None:
            account.enable_text = enable_text
        if enable_emoji is not None:
            account.enable_emoji = enable_emoji
        if enable_voice is not None:
            account.enable_voice = enable_voice
        if enable_image is not None:
            account.enable_image = enable_image
        if enable_proactive is not None:
            account.enable_proactive = enable_proactive
        if enable_learning is not None:
            account.enable_learning = enable_learning

        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"账号更新成功: {account_id}")
        return account

    async def get_account_stats(self, account_id: str) -> dict[str, Any]:
        """获取账号统计

        Args:
            account_id: 账号ID

        Returns:
            统计数据

        Raises:
            ValueError: 账号不存在
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        return {
            "account_id": account.id,
            "name": account.name,
            "platform": account.platform,
            "status": account.status,
            "today": {
                "message_count": account.today_message_count,
                "cost": account.today_cost,
            },
            "total": {
                "message_count": account.total_message_count,
                "cost": account.total_cost,
            },
            "limits": {
                "max_daily_messages": account.max_daily_messages,
                "max_daily_cost": account.max_daily_cost,
                "message_remaining": account.max_daily_messages - account.today_message_count,
                "cost_remaining": account.max_daily_cost - account.today_cost,
            },
            "timestamps": {
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "last_active_at": (
                    account.last_active_at.isoformat() if account.last_active_at else None
                ),
                "started_at": account.started_at.isoformat() if account.started_at else None,
                "stopped_at": account.stopped_at.isoformat() if account.stopped_at else None,
                "stats_reset_at": (
                    account.stats_reset_at.isoformat() if account.stats_reset_at else None
                ),
            },
            "error": (
                {
                    "error_count": account.error_count,
                    "error_message": account.error_message,
                }
                if account.error_message
                else None
            ),
        }

    async def reset_daily_stats(self, account_id: str) -> Account:
        """重置账号每日统计

        Args:
            account_id: 账号ID

        Returns:
            重置后的账号

        Raises:
            ValueError: 账号不存在
        """
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"账号不存在: {account_id}")

        account.reset_daily_stats()
        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"账号每日统计重置: {account_id}")
        return account

    async def reset_all_daily_stats(self) -> int:
        """重置所有账号的每日统计

        Returns:
            重置的账号数量
        """
        accounts = await self.list_accounts()
        count = 0

        for account in accounts:
            account.reset_daily_stats()
            count += 1

        await self.db.commit()
        logger.info(f"重置了 {count} 个账号的每日统计")
        return count
