"""真人化回复处理服务

⚠️ 废弃警告 (Deprecated):
此模块已被废弃。拟人化功能已通过强化Prompt在LLM层面实现，
不再需要在生成后进行处理。

新的流程：
1. 在PromptBuilder中构建强化的系统提示（包含说话风格、口头禅、表情使用等要求）
2. LLM直接生成拟人化的回复
3. 移除后处理步骤

保留此模块仅用于向后兼容，新代码不应使用。
"""

import warnings

from app.services.humanize.cached_llm_humanizer import CachedLLMHumanizer, get_cached_llm_humanizer
from app.services.humanize.conversation_strategy import (
    ConversationConfig,
    ConversationStrategy,
    get_conversation_strategy,
)
from app.services.humanize.cost_monitor import CostMonitor, get_cost_monitor
from app.services.humanize.humanize_processor import HumanizeProcessor, get_humanize_processor
from app.services.humanize.hybrid_humanizer import HybridHumanizer, get_hybrid_humanizer
from app.services.humanize.llm_humanizer import LLMHumanizer
from app.services.humanize.lru_cache import LRUCache
from app.services.humanize.style_templates import (
    StyleTemplate,
    StyleTemplateManager,
    get_style_manager,
)

warnings.warn(
    "humanize模块已被废弃。拟人化功能已通过强化Prompt实现，"
    "请直接使用PromptBuilder构建提示，无需后处理。",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "CachedLLMHumanizer",
    "get_cached_llm_humanizer",
    "ConversationConfig",
    "ConversationStrategy",
    "get_conversation_strategy",
    "CostMonitor",
    "get_cost_monitor",
    "HumanizeProcessor",
    "get_humanize_processor",
    "HybridHumanizer",
    "get_hybrid_humanizer",
    "LLMHumanizer",
    "LRUCache",
    "StyleTemplate",
    "StyleTemplateManager",
    "get_style_manager",
]
