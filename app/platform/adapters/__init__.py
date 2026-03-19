"""平台适配器"""

from .wechat_client import WechatClientAdapter
from .wechat_official import WechatOfficialAdapter

__all__ = [
    WechatOfficialAdapter,
    WechatClientAdapter,
]
