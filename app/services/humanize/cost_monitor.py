# -*- coding: utf-8 -*-
"""成本监控器 - 监控LLM真人化的成本"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class CostStats:
    """成本统计"""

    # 请求统计
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Token统计
    input_tokens_cached: int = 0
    input_tokens_uncached: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # 成本统计（元）
    cost_cached: float = 0.0
    cost_uncached: float = 0.0
    cost_output: float = 0.0
    total_cost: float = 0.0

    # 时间统计
    start_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
            "input_tokens_cached": self.input_tokens_cached,
            "input_tokens_uncached": self.input_tokens_uncached,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_cached": round(self.cost_cached, 6),
            "cost_uncached": round(self.cost_uncached, 6),
            "cost_output": round(self.cost_output, 6),
            "total_cost": round(self.total_cost, 6),
            "start_time": self.start_time.isoformat(),
        }

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class CostMonitor:
    """
    成本监控器

    基于价格模型：
    - 输入（缓存命中）：¥0.2/百万tokens
    - 输入（缓存未命中）：¥2/百万tokens
    - 输出：¥3/百万tokens
    """

    # 价格配置（元/百万tokens）
    PRICE_INPUT_CACHED = 0.2
    PRICE_INPUT_UNCACHED = 2.0
    PRICE_OUTPUT = 3.0

    # 单次请求估算token数
    ESTIMATED_INPUT_TOKENS = 800
    ESTIMATED_OUTPUT_TOKENS = 100

    def __init__(self):
        self.stats = CostStats()

    def record_request(
        self,
        cache_hit: bool,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> Dict:
        """
        记录一次请求

        Args:
            cache_hit: 是否命中缓存
            input_tokens: 输入token数（可选，使用估算值）
            output_tokens: 输出token数（可选，使用估算值）

        Returns:
            本次请求的成本信息
        """
        self.stats.total_requests += 1

        # 使用估算值或实际值
        input_tokens = input_tokens or self.ESTIMATED_INPUT_TOKENS
        output_tokens = output_tokens or self.ESTIMATED_OUTPUT_TOKENS

        if cache_hit:
            self.stats.cache_hits += 1
            self.stats.input_tokens_cached += input_tokens
            cost = (input_tokens / 1_000_000) * self.PRICE_INPUT_CACHED
            self.stats.cost_cached += cost
        else:
            self.stats.cache_misses += 1
            self.stats.input_tokens_uncached += input_tokens
            self.stats.output_tokens += output_tokens

            input_cost = (input_tokens / 1_000_000) * self.PRICE_INPUT_UNCACHED
            output_cost = (output_tokens / 1_000_000) * self.PRICE_OUTPUT

            self.stats.cost_uncached += input_cost
            self.stats.cost_output += output_cost
            cost = input_cost + output_cost

        self.stats.total_tokens += input_tokens + output_tokens
        self.stats.total_cost += cost

        return {
            "cache_hit": cache_hit,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens if not cache_hit else 0,
            "cost": round(cost, 6),
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.to_dict()

    def get_monthly_estimate(self, days: int = 30) -> Dict:
        """
        估算月成本

        Args:
            days: 统计天数（默认30天）

        Returns:
            月成本估算
        """
        elapsed = datetime.now() - self.stats.start_time
        elapsed_days = elapsed.total_seconds() / (24 * 3600)

        if elapsed_days < 0.01:  # 避免除零
            return {
                "estimated_monthly_cost": 0.0,
                "estimated_monthly_requests": 0,
                "note": "数据不足，无法估算",
            }

        # 计算日均值
        daily_cost = self.stats.total_cost / elapsed_days
        daily_requests = self.stats.total_requests / elapsed_days

        # 估算月值
        monthly_cost = daily_cost * days
        monthly_requests = daily_requests * days

        return {
            "estimated_monthly_cost": round(monthly_cost, 2),
            "estimated_monthly_requests": int(monthly_requests),
            "daily_average_cost": round(daily_cost, 4),
            "daily_average_requests": int(daily_requests),
            "current_hit_rate": round(self.stats.hit_rate, 3),
            "based_on_days": round(elapsed_days, 2),
        }

    def reset(self):
        """重置统计"""
        self.stats = CostStats()

    def print_report(self):
        """打印成本报告"""
        stats = self.get_stats()
        monthly = self.get_monthly_estimate()

        print("\n" + "=" * 60)
        print("💰 LLM真人化成本报告")
        print("=" * 60)

        print("\n📊 请求统计:")
        print(f"  总请求数: {stats['total_requests']}")
        print(f"  缓存命中: {stats['cache_hits']} ({stats['hit_rate']:.1%})")
        print(f"  缓存未命中: {stats['cache_misses']}")

        print("\n📝 Token统计:")
        print(f"  输入Tokens(缓存命中): {stats['input_tokens_cached']:,}")
        print(f"  输入Tokens(缓存未命中): {stats['input_tokens_uncached']:,}")
        print(f"  输出Tokens: {stats['output_tokens']:,}")
        print(f"  总Tokens: {stats['total_tokens']:,}")

        print("\n💸 成本统计:")
        print(f"  缓存命中成本: ¥{stats['cost_cached']:.6f}")
        print(f"  缓存未命中成本: ¥{stats['cost_uncached']:.6f}")
        print(f"  输出成本: ¥{stats['cost_output']:.6f}")
        print(f"  总成本: ¥{stats['total_cost']:.6f}")

        print("\n📈 月成本估算:")
        print(f"  估算月成本: ¥{monthly['estimated_monthly_cost']:.2f}")
        print(f"  估算月请求数: {monthly['estimated_monthly_requests']:,}")
        print(f"  日均成本: ¥{monthly['daily_average_cost']:.4f}")

        print("=" * 60 + "\n")


# 全局单例
_cost_monitor: Optional[CostMonitor] = None


def get_cost_monitor() -> CostMonitor:
    """获取成本监控器实例（单例）"""
    global _cost_monitor
    if _cost_monitor is None:
        _cost_monitor = CostMonitor()
    return _cost_monitor
