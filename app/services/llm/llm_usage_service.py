"""LLM Token 使用记录服务"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_usage import LLMUsageRecord, LLMUsageStatistics

# Token 价格配置（每 1K tokens 的价格，单位：美元）
TOKEN_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # DeepSeek
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
    # Kimi (Moonshot)
    "moonshot-v1-8k": {"input": 0.0005, "output": 0.0005},
    "moonshot-v1-32k": {"input": 0.001, "output": 0.001},
    "moonshot-v1-128k": {"input": 0.002, "output": 0.002},
    # GLM
    "glm-4": {"input": 0.001, "output": 0.001},
    "glm-4-flash": {"input": 0.0001, "output": 0.0001},
}


class LLMUsageService:
    """LLM 使用记录服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        request_type: str = "chat",
        operation: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        prompt_summary: Optional[str] = None,
        response_summary: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> LLMUsageRecord:
        """
        记录 LLM 使用情况

        Args:
            provider: 厂商名称
            model: 模型名称
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            user_id: 用户ID（可选）
            conversation_id: 对话ID（可选）
            request_type: 请求类型（chat/stream/embedding）
            operation: 具体操作描述
            status: 状态（success/error/timeout）
            error_message: 错误信息
            latency_ms: 延迟（毫秒）
            prompt_summary: 输入内容摘要
            response_summary: 输出内容摘要
            meta_data: 额外元数据

        Returns:
            创建的记录
        """
        total_tokens = prompt_tokens + completion_tokens

        # 计算成本
        estimated_cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        # 截断摘要
        prompt_summary = prompt_summary[:500] if prompt_summary else None
        response_summary = response_summary[:500] if response_summary else None

        record = LLMUsageRecord(
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            request_type=request_type,
            operation=operation,
            status=status,
            error_message=error_message,
            latency_ms=latency_ms,
            prompt_summary=prompt_summary,
            response_summary=response_summary,
            meta_data=json.dumps(meta_data, ensure_ascii=False) if meta_data else None,
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        # 更新统计
        await self._update_statistics(record)

        return record

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """计算预估成本"""
        pricing = TOKEN_PRICING.get(model, TOKEN_PRICING.get("gpt-3.5-turbo"))

        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    async def _update_statistics(self, record: LLMUsageRecord) -> None:
        """更新每日统计"""
        stat_date = record.created_at.strftime("%Y-%m-%d")

        # 查找或创建统计记录
        result = await self.session.execute(
            select(LLMUsageStatistics).where(
                LLMUsageStatistics.user_id == record.user_id,
                LLMUsageStatistics.stat_date == stat_date,
                LLMUsageStatistics.provider == record.provider,
                LLMUsageStatistics.model == record.model,
            )
        )
        stat = result.scalar_one_or_none()

        if not stat:
            stat = LLMUsageStatistics(
                user_id=record.user_id,
                stat_date=stat_date,
                provider=record.provider,
                model=record.model,
            )
            self.session.add(stat)

        # 更新统计
        stat.total_requests += 1
        stat.total_prompt_tokens += record.prompt_tokens
        stat.total_completion_tokens += record.completion_tokens
        stat.total_tokens += record.total_tokens
        stat.total_cost += record.estimated_cost or 0

        if record.status == "success":
            stat.success_count += 1
        else:
            stat.error_count += 1

        # 更新平均延迟
        if record.latency_ms:
            if stat.avg_latency_ms:
                stat.avg_latency_ms = (stat.avg_latency_ms + record.latency_ms) // 2
            else:
                stat.avg_latency_ms = record.latency_ms

        await self.session.commit()

    # ========== 查询方法 ==========

    async def get_user_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取用户的使用统计"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await self.session.execute(
            select(
                func.count(LLMUsageRecord.id).label("total_requests"),
                func.sum(LLMUsageRecord.prompt_tokens).label("total_prompt_tokens"),
                func.sum(LLMUsageRecord.completion_tokens).label("total_completion_tokens"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.estimated_cost).label("total_cost"),
            )
            .where(LLMUsageRecord.user_id == user_id)
            .where(LLMUsageRecord.created_at >= start_date)
            .where(LLMUsageRecord.created_at <= end_date)
        )

        row = result.one()
        return {
            "user_id": user_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_requests": row.total_requests or 0,
            "total_prompt_tokens": row.total_prompt_tokens or 0,
            "total_completion_tokens": row.total_completion_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost": round(row.total_cost or 0, 4),
        }

    async def get_conversation_usage(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话的 Token 消耗"""
        result = await self.session.execute(
            select(
                func.count(LLMUsageRecord.id).label("total_requests"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.estimated_cost).label("total_cost"),
            ).where(LLMUsageRecord.conversation_id == conversation_id)
        )

        row = result.one()
        return {
            "conversation_id": conversation_id,
            "total_requests": row.total_requests or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost": round(row.total_cost or 0, 4),
        }

    async def get_daily_statistics(
        self,
        days: int = 30,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取每日统计"""
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        query = select(LLMUsageStatistics).where(LLMUsageStatistics.stat_date >= start_date)

        if provider:
            query = query.where(LLMUsageStatistics.provider == provider)

        # 按用户筛选
        if user_id:
            query = query.where(LLMUsageStatistics.user_id == user_id)

        query = query.order_by(LLMUsageStatistics.stat_date.desc())

        result = await self.session.execute(query)
        stats = result.scalars().all()

        return [stat.to_dict() for stat in stats]

    async def get_provider_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """按厂商统计使用情况"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await self.session.execute(
            select(
                LLMUsageRecord.provider,
                func.count(LLMUsageRecord.id).label("total_requests"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.estimated_cost).label("total_cost"),
            )
            .where(LLMUsageRecord.created_at >= start_date)
            .where(LLMUsageRecord.created_at <= end_date)
            .group_by(LLMUsageRecord.provider)
            .order_by(func.sum(LLMUsageRecord.total_tokens).desc())
        )

        return [
            {
                "provider": row.provider,
                "total_requests": row.total_requests or 0,
                "total_tokens": row.total_tokens or 0,
                "total_cost": round(row.total_cost or 0, 4),
            }
            for row in result.all()
        ]

    async def get_operation_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """按操作类型统计使用情况"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await self.session.execute(
            select(
                LLMUsageRecord.operation,
                func.count(LLMUsageRecord.id).label("total_requests"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.avg(LLMUsageRecord.latency_ms).label("avg_latency"),
            )
            .where(LLMUsageRecord.created_at >= start_date)
            .where(LLMUsageRecord.created_at <= end_date)
            .where(LLMUsageRecord.operation.isnot(None))
            .group_by(LLMUsageRecord.operation)
            .order_by(func.sum(LLMUsageRecord.total_tokens).desc())
        )

        return [
            {
                "operation": row.operation,
                "total_requests": row.total_requests or 0,
                "total_tokens": row.total_tokens or 0,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
            }
            for row in result.all()
        ]

    async def get_recent_records(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取最近的记录"""
        query = select(LLMUsageRecord)

        if user_id:
            query = query.where(LLMUsageRecord.user_id == user_id)
        if provider:
            query = query.where(LLMUsageRecord.provider == provider)

        query = query.order_by(LLMUsageRecord.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        records = result.scalars().all()

        return [record.to_dict() for record in records]


# 便捷函数
async def record_llm_usage(
    session: AsyncSession,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    **kwargs,
) -> LLMUsageRecord:
    """便捷函数：记录 LLM 使用"""
    service = LLMUsageService(session)
    return await service.record_usage(
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        **kwargs,
    )
