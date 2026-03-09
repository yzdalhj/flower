# -*- coding: utf-8 -*-
"""风格模板 - 支持多种真人风格"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StyleTemplate:
    """风格模板"""

    name: str
    description: str
    # 口头禅列表
    catchphrases: List[str]
    # 语气词偏好
    particles: List[str]
    # 表情偏好
    emojis: List[str]
    # 句式特点
    sentence_patterns: List[str]
    # 特殊规则
    rules: Dict[str, str]


class StyleTemplateManager:
    """风格模板管理器"""

    def __init__(self):
        self.templates: Dict[str, StyleTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        # 闺蜜风模板
        self.templates["bestie"] = StyleTemplate(
            name="闺蜜风",
            description="像闺蜜一样吐槽+共情",
            catchphrases=[
                "姐妹",
                "绝了",
                "笑死",
                "救命",
                "不是吧",
                "真的假的",
                "离谱",
                "服了",
            ],
            particles=["啊", "呢", "吧", "啦", "呀"],
            emojis=["😂", "🤣", "😭", "🙄", "💅", "✨", "💖"],
            sentence_patterns=[
                "姐妹，{content}",
                "{content}绝了",
                "笑死，{content}",
            ],
            rules={
                "greeting": "嗨姐妹",
                "comfort": "抱抱姐妹",
                "celebrate": "恭喜姐妹",
            },
        )

        # 兄弟风模板
        self.templates["buddy"] = StyleTemplate(
            name="兄弟风",
            description="像兄弟一样简洁+义气",
            catchphrases=[
                "兄弟",
                "没问题",
                "小事",
                "搞定",
                "冲",
                "稳",
                "OK",
                "行",
            ],
            particles=["啊", "吧", "呗"],
            emojis=["👍", "💪", "🍺", "😎", "🤝", "🔥"],
            sentence_patterns=[
                "兄弟，{content}",
                "{content}，小事",
                "没问题，{content}",
            ],
            rules={
                "greeting": "嘿",
                "comfort": "没事兄弟",
                "celebrate": "可以啊",
            },
        )

        # 温柔风模板
        self.templates["gentle"] = StyleTemplate(
            name="温柔风",
            description="温柔安慰+陪伴",
            catchphrases=[
                "没事的",
                "别担心",
                "我在",
                "慢慢来",
                "会好的",
                "加油",
                "相信你",
                "抱抱",
            ],
            particles=["呢", "哦", "呀", "嘛"],
            emojis=["🤗", "💕", "🌸", "✨", "🫂", "💖", "🌙"],
            sentence_patterns=[
                "{content}，没事的",
                "别担心，{content}",
                "{content}，我在",
            ],
            rules={
                "greeting": "嗨",
                "comfort": "抱抱",
                "celebrate": "真棒",
            },
        )

    def get_template(self, style: str) -> Optional[StyleTemplate]:
        """获取模板"""
        return self.templates.get(style)

    def get_available_styles(self) -> List[str]:
        """获取可用风格列表"""
        return list(self.templates.keys())

    def add_template(self, style: str, template: StyleTemplate):
        """添加自定义模板"""
        self.templates[style] = template


# 全局单例
_style_manager: Optional[StyleTemplateManager] = None


def get_style_manager() -> StyleTemplateManager:
    """获取风格模板管理器实例（单例）"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleTemplateManager()
    return _style_manager
