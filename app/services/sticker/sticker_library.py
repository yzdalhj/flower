"""动态表情包库服务

支持从远程仓库动态同步网络梗图
"""

from typing import Any, Dict, List, Optional

import httpx

from app.models.sticker import StickerEmotion, StickerPersonalityMatch, StickerType

# 标签系统配置
STICKER_TAG_CATEGORIES = {
    "情绪": [
        "开心",
        "难过",
        "生气",
        "惊讶",
        "困惑",
        "害羞",
        "兴奋",
        "平静",
        "激动",
        "失望",
        "期待",
        "焦虑",
        "骄傲",
        "嫉妒",
        "感激",
        "思念",
    ],
    "场景": [
        "问候",
        "告别",
        "感谢",
        "道歉",
        "祝贺",
        "鼓励",
        "安慰",
        "调侃",
        "吐槽",
        "正经",
        "搞笑",
        "卖萌",
        "耍帅",
        "无奈",
        "尴尬",
        "求助",
    ],
    "风格": [
        "可爱",
        "沙雕",
        "炫酷",
        "文艺",
        "复古",
        "清新",
        "暗黑",
        "萌系",
        "写实",
        "卡通",
        "手绘",
        "3D",
        "像素",
        "蒸汽波",
        "赛博朋克",
    ],
    "适用人群": ["通用", "男生", "女生", "情侣", "朋友", "同事", "长辈", "晚辈"],
    "节日": [
        "春节",
        "元宵",
        "清明",
        "端午",
        "中秋",
        "国庆",
        "圣诞",
        "元旦",
        "情人节",
        "儿童节",
        "劳动节",
        "教师节",
        "母亲节",
        "父亲节",
    ],
}


class DynamicStickerLibrary:
    """动态表情包库

    从远程JSON索引动态获取表情包信息，支持自动更新
    默认使用开源项目 ChineseBQB (https://github.com/zhaoolee/ChineseBQB) 提供的5791张表情包
    """

    DEFAULT_REPO_URL = (
        "https://raw.githubusercontent.com/zhaoolee/ChineseBQB/master/chinesebqb_github.json"
    )

    def __init__(
        self,
        repo_url: str = DEFAULT_REPO_URL,
        cache_ttl: int = 86400,
        timeout: int = 10,
    ):
        self.repo_url = repo_url
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._cached_stickers: Optional[List[Dict]] = None
        self._last_update: int = 0

    async def fetch_sticker_list(self, force_update: bool = False) -> List[Dict]:
        """从远程仓库获取表情包列表

        如果远程仓库未配置或获取失败，返回默认内置梗图列表
        支持解析 ChineseBQB 格式的JSON数据
        """
        if not force_update and self._cached_stickers and self._is_cache_valid():
            return self._cached_stickers

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"[StickerLibrary] 正在从远程获取表情包: {self.repo_url}")
                response = await client.get(self.repo_url)
                print(f"[StickerLibrary] 远程响应状态: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(
                        f"[StickerLibrary] 获取到 {len(data) if isinstance(data, list) else 'N/A'} 条数据"
                    )
                    stickers = self._convert_chinesebqb_format(data)
                    self._cached_stickers = stickers
                    self._last_update = self._get_current_timestamp()
                    print(f"[StickerLibrary] 成功转换 {len(stickers)} 个表情包")
                    return stickers
                else:
                    print("[StickerLibrary] 远程请求失败，使用默认梗图")
                    return self._get_default_memes()
        except Exception as e:
            print(f"[StickerLibrary] 获取远程表情包失败: {e}")
            import traceback

            traceback.print_exc()
            return self._get_default_memes()

    def _convert_chinesebqb_format(self, data: Any) -> List[Dict]:
        """转换 ChineseBQB JSON 格式到内部格式

        ChineseBQB 格式:
        {
            "status": 1000,
            "info": "...",
            "data": [
                {
                    "name": "xxx.gif",
                    "category": "分类",
                    "url": "https://..."
                }
            ]
        }
        """
        converted = []

        # 解析 ChineseBQB 格式，数据在 data 字段中
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif isinstance(data, list):
            items = data
        else:
            print(f"[StickerLibrary] 无法解析的数据格式: {type(data)}")
            return self._get_default_memes()

        print(f"[StickerLibrary] 开始转换 {len(items)} 个表情包...")

        for item in items:
            try:
                # ChineseBQB 使用 name 和 url 字段
                name = item.get("name", "").strip()
                image_url = item.get("url", "")
                category = item.get("category", "")

                # 转换 GitHub raw 到 jsdelivr CDN 加速（国内访问更快）
                # raw.githubusercontent.com -> cdn.jsdelivr.net/gh
                image_url = image_url.replace(
                    "https://raw.githubusercontent.com/", "https://cdn.jsdelivr.net/gh/"
                )

                if not name or not image_url:
                    continue

                # 从文件名提取标题（去掉扩展名）
                title = name.rsplit(".", 1)[0] if "." in name else name
                # 清理文件名中的乱码字符
                title = title.replace("%", "").replace("_", " ")[:50]

                # 从分类提取标签
                tags = []
                if category:
                    # 提取中文标签
                    import re

                    chinese_tags = re.findall(r"[\u4e00-\u9fff]+", category)
                    if chinese_tags:
                        tags = chinese_tags[:3]

                file_format = image_url.split(".")[-1].lower()
                if file_format not in ["png", "jpg", "jpeg", "gif", "webp"]:
                    file_format = "gif"

                converted_sticker = {
                    "name": title or name,
                    "type": StickerType.MEME,
                    "url": image_url,
                    "emotion": None,
                    "personality_match": StickerPersonalityMatch.ALL,
                    "tags": tags,
                    "keywords": tags.copy(),
                    "description": (
                        f"来自ChineseBQB的{category}表情包" if category else "ChineseBQB表情包"
                    ),
                    "source": "ChineseBQB",
                    "file_format": file_format,
                    "base_weight": 1.0,
                }
                converted.append(converted_sticker)
            except Exception as e:
                print(f"[StickerLibrary] 转换单个表情包失败: {e}")
                continue

        print(f"[StickerLibrary] 成功转换 {len(converted)} 个表情包")

        if not converted:
            return self._get_default_memes()

        return converted

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        current = self._get_current_timestamp()
        return (current - self._last_update) < self.cache_ttl

    def _get_current_timestamp(self) -> int:
        import time

        return int(time.time())

    def _get_default_memes(self) -> List[Dict]:
        """获取默认内置梗图列表（最小化内置，只保留经典热门梗图）"""
        return [
            {
                "name": "听我说谢谢你",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/thankyou.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["谢谢", "感恩", "梗图", "经典"],
                "keywords": ["谢谢", "感谢", "听我说谢谢你"],
                "description": "听我说谢谢你梗图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 0.9,
            },
            {
                "name": "你懂我的意思吧",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/understand.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.SARCASTIC,
                "tags": ["懂我意思", "暗示", "梗图", "吐槽"],
                "keywords": ["你懂的", "暗示", "对吧", "明白我意思吧"],
                "description": "你懂我的意思吧梗图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 0.8,
            },
            {
                "name": "我想开了",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/enlightened.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["想开了", "佛系", "无所谓", "随缘"],
                "keywords": ["算了", "无所谓", "想开了", "随便吧"],
                "description": "我想开了佛系带字图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.0,
            },
            {
                "name": "熊猫头微笑",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/panda_smile.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["熊猫头", "微笑", "礼貌", "阴阳"],
                "keywords": ["熊猫头", "微笑", "你说的对", "呵呵"],
                "description": "经典熊猫头微笑表情包",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.2,
            },
            {
                "name": "就这",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/this_it.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.SARCASTIC,
                "tags": ["就这", "嘲讽", "不屑", "梗图"],
                "keywords": ["就这", "就这啊", "这也不行", "就这?", "就这吗"],
                "description": "就这梗图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.1,
            },
            {
                "name": "救救我",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/help.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["救命", "救救我", "难受", "痛苦"],
                "keywords": ["救命", "救救我", "不行了", "顶不住", "熬不住"],
                "description": "救救我梗图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.0,
            },
            {
                "name": "我真的会谢",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/thank_you_very_much.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["无语", "感谢", "离谱", "吐槽"],
                "keywords": ["我真的会谢", "谢谢你", "真的会谢", "无语"],
                "description": "我真的会谢网络梗",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.3,
            },
            {
                "name": "离谱",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/absurd.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["离谱", "离大谱", "惊讶", "不懂"],
                "keywords": ["离谱", "离大谱", "太离谱", "这就离谱"],
                "description": "离大谱梗图",
                "source": "网络",
                "file_format": "png",
                "base_weight": 1.2,
            },
            {
                "name": "微笑面对",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/smile_face.png",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["微笑", "面对", "坚强", "佛系"],
                "keywords": ["微笑", "面对", "加油", "坚持"],
                "description": "微笑面对生活梗图",
                "source": "network",
                "file_format": "png",
                "base_weight": 0.9,
            },
            {
                "name": "根本停不下来",
                "type": StickerType.MEME,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/memes/cant_stop.gif",
                "emotion": None,
                "personality_match": StickerPersonalityMatch.CHEERFUL,
                "tags": ["停不下来", "兴奋", "根本停不下来"],
                "keywords": ["根本停不下来", "停不下来", "太爽了"],
                "description": "根本停不下来动图",
                "source": "network",
                "file_format": "gif",
                "base_weight": 1.0,
            },
        ]

    def get_default_emotion_stickers(self) -> List[Dict]:
        """获取默认情绪表情包列表（保留少量基础情绪表情）"""
        return [
            {
                "name": "狗头",
                "type": StickerType.EMOTION,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/emotion/silly/dog.png",
                "emotion": StickerEmotion.SILLY,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["狗头", "滑稽", "搞怪"],
                "keywords": ["狗头", "滑稽", "doge", "保命"],
                "description": "经典狗头表情",
                "source": "官方",
                "file_format": "png",
                "base_weight": 1.5,
            },
            {
                "name": "问号脸",
                "type": StickerType.EMOTION,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/emotion/confused/question.gif",
                "emotion": StickerEmotion.CONFUSED,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["困惑", "疑问", "不懂"],
                "keywords": ["？", "什么", "不懂", "啥意思", "是吗"],
                "description": "满头问号",
                "source": "官方",
                "file_format": "gif",
                "base_weight": 1.2,
            },
            {
                "name": "摸摸头",
                "type": StickerType.EMOTION,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/emotion/supportive/pat.gif",
                "emotion": StickerEmotion.SUPPORTIVE,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["安慰", "摸摸头", "鼓励"],
                "keywords": ["摸摸头", "不哭", "加油", "我在"],
                "description": "温柔地摸摸头",
                "source": "官方",
                "file_format": "gif",
                "base_weight": 1.3,
            },
            {
                "name": "比心",
                "type": StickerType.EMOTION,
                "url": "https://cdn.jsdelivr.net/gh/chiwhye/flower-stickers@main/emotion/loving/love.png",
                "emotion": StickerEmotion.LOVING,
                "personality_match": StickerPersonalityMatch.ALL,
                "tags": ["比心", "爱你", "感谢"],
                "keywords": ["比心", "爱你", "谢谢", "么么哒"],
                "description": "比个小心心",
                "source": "官方",
                "file_format": "png",
                "base_weight": 1.2,
            },
        ]


# 全局默认实例
default_sticker_library = DynamicStickerLibrary()


def get_dynamic_sticker_library() -> DynamicStickerLibrary:
    """获取动态表情包库实例"""
    return default_sticker_library
