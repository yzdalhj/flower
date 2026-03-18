"""
成本优化器
提供响应缓存、规则回复、批处理优化等功能
"""

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CachedResponse:
    """缓存的响应"""

    content: str
    personality_id: str
    cached_at: datetime
    hits: int = 0


@dataclass
class RuleReply:
    """规则回复"""

    patterns: List[str]
    responses: List[str]
    personality_id: str = "default"


class ResponseCache:
    """响应缓存"""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache: OrderedDict[str, CachedResponse] = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)

    def _generate_key(self, user_message: str, personality_id: str) -> str:
        """生成缓存键"""
        normalized_message = user_message.strip().lower()
        key_data = f"{normalized_message}:{personality_id}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, user_message: str, personality_id: str) -> Optional[str]:
        """获取缓存的响应"""
        key = self._generate_key(user_message, personality_id)

        if key not in self.cache:
            return None

        cached = self.cache[key]

        if datetime.now() - cached.cached_at > self.ttl:
            del self.cache[key]
            return None

        cached.hits += 1
        self.cache.move_to_end(key)
        return cached.content

    def put(self, user_message: str, personality_id: str, content: str) -> None:
        """缓存响应"""
        key = self._generate_key(user_message, personality_id)

        if key in self.cache:
            self.cache.move_to_end(key)
            return

        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = CachedResponse(
            content=content, personality_id=personality_id, cached_at=datetime.now()
        )

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_hits = sum(c.hits for c in self.cache.values())
        return {"size": len(self.cache), "max_size": self.max_size, "total_hits": total_hits}


class RuleBasedResponder:
    """规则回复器"""

    def __init__(self):
        self.rules: List[RuleReply] = []
        self._init_default_rules()
        # 记录最近使用的回复，避免短时间内重复
        self._recent_responses: OrderedDict[str, datetime] = OrderedDict()
        self._max_recent = 20  # 最多记录最近20条回复
        self._recent_ttl = timedelta(minutes=5)  # 5分钟内避免重复

    def _init_default_rules(self):
        """初始化默认规则 - 增加多样性"""
        self.rules.extend(
            [
                RuleReply(
                    patterns=[r"^(你好|嗨|hello|hi|早上好|下午好|晚上好)\s*[!！?？]*$"],
                    responses=[
                        "你好呀！",
                        "嗨～",
                        "哈喽哈喽",
                        "害，来啦",
                        "哟，来啦",
                        "嘿！",
                        "来啦老弟",
                        "👋 哈喽",
                        "嗨害嗨",
                        "哟哟哟",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(在吗|在不在)\s*[!！?？]*$"],
                    responses=[
                        "在呢在呢",
                        "害，我在",
                        "怎么啦？",
                        "在的在的，啥事？",
                        "在呢，你说",
                        "在！",
                        "在的呀",
                        "在呢在呢，咋了",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(谢谢|感谢|多谢|thanks|thank you)\s*[!！?？]*$"],
                    responses=[
                        "客气啥～",
                        "害，小事儿",
                        "不用谢啦",
                        "谢啥谢",
                        "这有啥",
                        "客气了不是",
                        "害，应该的",
                        "不客气不客气",
                        "小意思啦",
                        "咱俩谁跟谁",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(再见|拜拜|bye|晚安)\s*[!！?？]*$"],
                    responses=[
                        "拜拜～",
                        "晚安晚安",
                        "回见啦",
                        "拜拜👋",
                        "回头聊",
                        "好嘞拜拜",
                        "嗯嗯拜拜",
                        "去吧去吧",
                        "晚安好梦",
                        "拜拜，早点休息",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(哈哈|哈哈哈|哈哈哈哈|哈哈哈哈哈+)\s*[!！?？]*$"],
                    responses=[
                        "哈哈哈哈",
                        "绝了绝了",
                        "笑死我了😂",
                        "哈哈哈哈哈哈",
                        "笑不活了",
                        "哈哈哈哈嗝",
                        "笑死",
                        "😂😂😂",
                        "哈哈哈哈有毒",
                        "别笑了别笑了",
                        "你笑啥呢",
                        "啥事这么好笑",
                        "哈哈哈哈哈哈停",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(笑死|绝了|卧槽|woc|wc|牛逼|牛|6|六)\s*[!！?？]*$"],
                    responses=[
                        "确实",
                        "哈哈哈",
                        "雀食",
                        "我也觉得",
                        "没毛病",
                        "哈哈哈雀食",
                        "绝了",
                        "牛的",
                        "可以可以",
                        "👍",
                        "哈哈哈哈",
                        "有点东西",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(嗯|哦|好的|行|ok|好|嗯嗯|哦哦)\s*[!！?？.。]*$"],
                    responses=[
                        "嗯嗯",
                        "好哒",
                        "害，行",
                        "okk",
                        "👌",
                        "好嘞",
                        "行吧",
                        "嗯呢",
                        "好的好的",
                        "ojbk",
                        "可以",
                        "没问题",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(？|\?|什么|啥|咋了|怎么了)\s*[!！?？]*$"],
                    responses=[
                        "咋了？",
                        "嗯？",
                        "咋回事",
                        "咋啦",
                        "？",
                        "啥情况",
                        "咋了这是",
                        "咋",
                        "咋回事儿",
                        "咋了嘛",
                    ],
                ),
                RuleReply(
                    patterns=[r"^(哦豁|完了|惨了|糟糕|不好)\s*[!！?？]*$"],
                    responses=[
                        "咋了咋了",
                        "咋回事",
                        "咋了？",
                        "咋搞的",
                        "咋了这是",
                        "咋了嘛",
                        "咋回事儿",
                        "咋了",
                        "咋搞的这是",
                        "咋了你说",
                    ],
                ),
            ]
        )

    def _is_recently_used(self, response: str) -> bool:
        """检查回复是否最近使用过"""
        now = datetime.now()
        # 清理过期的记录
        expired_keys = [
            key
            for key, timestamp in self._recent_responses.items()
            if now - timestamp > self._recent_ttl
        ]
        for key in expired_keys:
            del self._recent_responses[key]

        return response in self._recent_responses

    def _record_response(self, response: str):
        """记录已使用的回复"""
        now = datetime.now()
        self._recent_responses[response] = now
        # 保持记录数量在限制内
        while len(self._recent_responses) > self._max_recent:
            self._recent_responses.popitem(last=False)

    def match(self, user_message: str, personality_id: str = "default") -> Optional[str]:
        """匹配规则回复 - 避免短时间内重复"""
        import random

        normalized_message = user_message.strip().lower()

        for rule in self.rules:
            for pattern in rule.patterns:
                if re.match(pattern, normalized_message, re.IGNORECASE):
                    # 过滤掉最近使用过的回复
                    available_responses = [
                        r for r in rule.responses if not self._is_recently_used(r)
                    ]

                    # 如果所有回复都最近用过，就用全部选项
                    if not available_responses:
                        available_responses = rule.responses

                    response = random.choice(available_responses)
                    self._record_response(response)
                    return response

        return None

    def add_rule(self, patterns: List[str], responses: List[str], personality_id: str = "default"):
        """添加规则"""
        self.rules.append(
            RuleReply(patterns=patterns, responses=responses, personality_id=personality_id)
        )


class CostOptimizer:
    """成本优化器"""

    def __init__(self):
        self.cache = ResponseCache()
        self.rule_responder = RuleBasedResponder()
        self.stats = {"cache_hits": 0, "rule_hits": 0, "llm_calls": 0, "total_requests": 0}

    async def process(
        self, user_message: str, personality_id: str, llm_callback: Callable[[], Any]
    ) -> Tuple[str, str]:
        """
        处理消息，直接使用LLM生成回复（已移除规则回复）

        Args:
            user_message: 用户消息
            personality_id: 人格ID
            llm_callback: LLM回调函数

        Returns:
            (回复内容, 来源: cache/llm)
        """
        self.stats["total_requests"] += 1

        # 规则回复已移除，直接使用LLM生成更自然的回复
        # 保留缓存机制用于完全相同的输入
        cached_response = self.cache.get(user_message, personality_id)
        if cached_response:
            self.stats["cache_hits"] += 1
            return cached_response, "cache"

        self.stats["llm_calls"] += 1
        llm_result = await llm_callback()

        response_content = llm_result.content if hasattr(llm_result, "content") else str(llm_result)
        self.cache.put(user_message, personality_id, response_content)

        return response_content, "llm"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_stats": self.cache.stats(),
            "cache_hit_rate": (
                (self.stats["cache_hits"] / self.stats["total_requests"] * 100)
                if self.stats["total_requests"] > 0
                else 0
            ),
            "rule_hit_rate": (
                (self.stats["rule_hits"] / self.stats["total_requests"] * 100)
                if self.stats["total_requests"] > 0
                else 0
            ),
            "llm_rate": (
                (self.stats["llm_calls"] / self.stats["total_requests"] * 100)
                if self.stats["total_requests"] > 0
                else 0
            ),
        }

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

    async def process_batch(
        self,
        messages: List[Dict[str, str]],
        personality_id: str,
        llm_batch_callback: Callable[[List[Dict[str, str]]], Any],
    ) -> List[Tuple[str, str]]:
        """
        批量处理消息，直接使用LLM生成回复（已移除规则回复）

        Args:
            messages: 消息列表，每个元素为 {"id": str, "content": str}
            personality_id: 人格ID
            llm_batch_callback: LLM批量回调函数，接收需要LLM处理的消息列表

        Returns:
            回复列表，每个元素为 (回复内容, 来源: cache/llm)
        """
        results = []
        llm_messages = []
        llm_indices = []

        for idx, msg in enumerate(messages):
            self.stats["total_requests"] += 1
            msg_id = msg.get("id", str(idx))
            msg_content = msg.get("content", "")

            # 规则回复已移除
            cached_response = self.cache.get(msg_content, personality_id)
            if cached_response:
                self.stats["cache_hits"] += 1
                results.append((cached_response, "cache"))
                continue

            llm_messages.append({"id": msg_id, "content": msg_content})
            llm_indices.append(idx)
            results.append(None)

        if llm_messages:
            self.stats["llm_calls"] += len(llm_messages)
            llm_responses = await llm_batch_callback(llm_messages)

            for idx, (llm_msg, llm_resp) in enumerate(zip(llm_messages, llm_responses)):
                response_content = (
                    llm_resp.content if hasattr(llm_resp, "content") else str(llm_resp)
                )
                original_idx = llm_indices[idx]
                results[original_idx] = (response_content, "llm")
                self.cache.put(llm_msg["content"], personality_id, response_content)

        return results


_cost_optimizer: Optional[CostOptimizer] = None


def get_cost_optimizer() -> CostOptimizer:
    """获取成本优化器单例"""
    global _cost_optimizer
    if _cost_optimizer is None:
        _cost_optimizer = CostOptimizer()
    return _cost_optimizer
