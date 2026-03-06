"""LLM客户端 - 支持多模型"""

from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()


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

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=settings.API_TIMEOUT,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """发送对话请求"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

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
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class DeepSeekClient(BaseLLMClient):
    """DeepSeek客户端"""

    def __init__(self):
        super().__init__(
            api_key=settings.DEEPSEEK_API_KEY or "",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        )


class KimiClient(BaseLLMClient):
    """Kimi客户端"""

    def __init__(self):
        super().__init__(
            api_key=settings.KIMI_API_KEY or "",
            base_url="https://api.moonshot.cn/v1",
            model="moonshot-v1-8k",
        )


class GLMClient(BaseLLMClient):
    """GLM客户端"""

    def __init__(self):
        super().__init__(
            api_key=settings.GLM_API_KEY or "",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model="glm-4",
        )


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""

    def __init__(self):
        super().__init__(
            api_key=settings.OPENAI_API_KEY or "",
            base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
            model="ark-code-latest",
        )


class LLMRouter:
    """
    LLM路由器
    智能选择模型并处理故障切换
    """

    def __init__(self):
        self.clients: Dict[ModelType, BaseLLMClient] = {}
        self._init_clients()

    def _init_clients(self):
        """初始化客户端"""
        if settings.DEEPSEEK_API_KEY:
            self.clients[ModelType.DEEPSEEK] = DeepSeekClient()
        if settings.KIMI_API_KEY:
            self.clients[ModelType.KIMI] = KimiClient()
        if settings.GLM_API_KEY:
            self.clients[ModelType.GLM] = GLMClient()
        if settings.OPENAI_API_KEY:
            self.clients[ModelType.OPENAI] = OpenAIClient()

    def select_model(self, context_length: int = 0, require_reasoning: bool = False) -> ModelType:
        """
        智能选择模型

        Args:
            context_length: 上下文长度
            require_reasoning: 是否需要深度推理

        Returns:
            模型类型
        """
        # 长上下文 -> Kimi (256K)
        if context_length > 8000 and ModelType.KIMI in self.clients:
            return ModelType.KIMI

        # 需要深度推理 -> DeepSeek
        if require_reasoning and ModelType.DEEPSEEK in self.clients:
            return ModelType.DEEPSEEK

        # 默认使用配置的默认模型
        default = ModelType(settings.DEFAULT_MODEL)
        if default in self.clients:
            return default

        # 返回第一个可用的模型
        if self.clients:
            return list(self.clients.keys())[0]

        raise ValueError("没有可用的LLM客户端")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[ModelType] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback: bool = True,
    ) -> LLMResponse:
        """
        发送对话请求（带故障切换）

        Args:
            messages: 消息列表
            model: 指定模型（None则自动选择）
            temperature: 温度
            max_tokens: 最大token数
            fallback: 是否启用故障切换

        Returns:
            LLM响应
        """
        if model is None:
            model = self.select_model()

        client = self.clients.get(model)
        if not client:
            raise ValueError(f"模型 {model} 不可用")

        try:
            return await client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            if fallback and settings.FALLBACK_ENABLED:
                # 故障切换
                print(f"模型 {model} 失败，尝试切换: {e}")
                for fallback_model in self.clients:
                    if fallback_model != model:
                        try:
                            fallback_client = self.clients[fallback_model]
                            return await fallback_client.chat(
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                            )
                        except Exception:
                            continue
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[ModelType] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        if model is None:
            model = self.select_model()

        client = self.clients.get(model)
        if not client:
            raise ValueError(f"模型 {model} 不可用")

        async for chunk in client.chat_stream(
            messages=messages,
            temperature=temperature,
        ):
            yield chunk


# 全局路由器实例
llm_router = LLMRouter()
