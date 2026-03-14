"""LLM客户端 - 支持多模型"""

from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import AsyncSessionLocal
from app.models.settings import LLMProvider


class ModelType(str, Enum):
    """支持的模型类型"""

    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    GLM = "glm"
    OPENAI = "openai"


@dataclass
class LLMConfig:
    """LLM连接配置"""

    api_key: str
    base_url: str
    model: str
    timeout: int = 30


@dataclass
class LLMResponse:
    """LLM响应"""

    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class BaseLLMClient:
    """基础LLM客户端"""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        deep_thinking: bool = False,
    ) -> LLMResponse:
        """发送对话请求"""
        # 构建请求参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        # 深度思考模式 - 降低温度，增加最大token
        if deep_thinking:
            params["temperature"] = min(temperature, 0.3)  # 更低的温度，更确定的输出
            params["max_tokens"] = max(max_tokens or 4096, 4096)  # 更多token用于推理

            # DeepSeek 支持 reasoning 参数
            if "deepseek" in self.model.lower():
                params["extra_body"] = {"reasoning": True}

        response = await self.client.chat.completions.create(**params)

        if stream:
            # 流式响应处理
            content = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
            return LLMResponse(
                content=content,
                model=self.model,
            )
        else:
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason,
            )

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        deep_thinking: bool = False,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        # 构建请求参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # 深度思考模式
        if deep_thinking:
            params["temperature"] = min(temperature, 0.3)
            params["max_tokens"] = max(max_tokens or 4096, 4096)
            if "deepseek" in self.model.lower():
                params["extra_body"] = {"reasoning": True}

        response = await self.client.chat.completions.create(**params)

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMRouter:
    """
    LLM路由器
    智能选择模型并处理故障切换
    """

    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.providers: Dict[str, LLMProvider] = {}

    async def load_providers(self, db: Optional[AsyncSession] = None):
        """从数据库加载厂商配置"""
        # 如果没有传入db，创建新的会话
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            result = await db.execute(
                select(LLMProvider)
                .where(LLMProvider.is_enabled.is_(True))
                .order_by(LLMProvider.priority.desc())
            )
            providers = result.scalars().all()

            self.clients.clear()
            self.providers.clear()

            for provider in providers:
                if provider.api_key:  # 只加载有API密钥的
                    self.providers[provider.name] = provider
                    self.clients[provider.name] = BaseLLMClient(
                        api_key=provider.api_key,
                        base_url=provider.base_url,
                        model=provider.default_model,
                        timeout=provider.timeout,
                    )
        finally:
            if should_close:
                await db.close()

    async def get_default_provider(self, db: AsyncSession) -> Optional[LLMProvider]:
        """获取默认厂商"""
        # 先查找标记为默认的
        result = await db.execute(
            select(LLMProvider)
            .where(LLMProvider.is_default.is_(True))
            .where(LLMProvider.is_enabled.is_(True))
        )
        provider = result.scalar_one_or_none()
        if provider:
            return provider

        # 否则返回优先级最高的
        result = await db.execute(
            select(LLMProvider)
            .where(LLMProvider.is_enabled.is_(True))
            .order_by(LLMProvider.priority.desc())
        )
        return result.scalars().first()

    def select_model(
        self,
        context_length: int = 0,
        require_reasoning: bool = False,
        preferred_provider: Optional[str] = None,
    ) -> Optional[str]:
        """
        智能选择模型

        Args:
            context_length: 上下文长度
            require_reasoning: 是否需要深度推理
            preferred_provider: 优先使用的厂商

        Returns:
            厂商名称
        """
        if not self.clients:
            return None

        # 优先使用指定厂商
        if preferred_provider and preferred_provider in self.clients:
            return preferred_provider

        # 长上下文 -> kimi (256K)
        if context_length > 8000 and "kimi" in self.clients:
            return "kimi"

        # 需要深度推理 -> deepseek
        if require_reasoning and "deepseek" in self.clients:
            return "deepseek"

        # 返回第一个可用的（按优先级排序）
        if self.clients:
            return list(self.clients.keys())[0]

        return None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback: bool = True,
        deep_thinking: bool = False,
        db: Optional[AsyncSession] = None,
    ) -> LLMResponse:
        """
        发送对话请求（带故障切换）

        Args:
            messages: 消息列表
            provider: 指定厂商（None则自动选择）
            temperature: 温度
            max_tokens: 最大token数
            fallback: 是否启用故障切换
            deep_thinking: 是否启用深度思考模式
            db: 数据库会话

        Returns:
            LLM响应
        """
        # 每次都重新加载配置，确保使用最新的数据库配置
        await self.load_providers(db)

        if not self.clients:
            raise ValueError("没有可用的LLM客户端，请先在设置页面配置LLM厂商的API密钥")

        if provider is None:
            # 深度思考模式优先选择 deepseek
            if deep_thinking and "deepseek" in self.clients:
                provider = "deepseek"
            else:
                provider = self.select_model()

        if not provider or provider not in self.clients:
            raise ValueError(f"厂商 {provider} 不可用")

        client = self.clients[provider]

        try:
            return await client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                deep_thinking=deep_thinking,
            )
        except Exception as e:
            if fallback:
                # 故障切换
                print(f"厂商 {provider} 失败，尝试切换: {e}")
                for fallback_provider in self.clients:
                    if fallback_provider != provider:
                        try:
                            fallback_client = self.clients[fallback_provider]
                            return await fallback_client.chat(
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                deep_thinking=deep_thinking,
                            )
                        except Exception:
                            continue
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        deep_thinking: bool = False,
        db: Optional[AsyncSession] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        # 每次都重新加载配置，确保使用最新的数据库配置
        await self.load_providers(db)

        if not self.clients:
            raise ValueError("没有可用的LLM客户端，请先配置LLM厂商")

        if provider is None:
            # 深度思考模式优先选择 deepseek
            if deep_thinking and "deepseek" in self.clients:
                provider = "deepseek"
            else:
                provider = self.select_model()

        if not provider or provider not in self.clients:
            raise ValueError(f"厂商 {provider} 不可用")

        client = self.clients[provider]

        async for chunk in client.chat_stream(
            messages=messages,
            temperature=temperature,
            deep_thinking=deep_thinking,
        ):
            yield chunk


# 全局路由器实例
llm_router = LLMRouter()
