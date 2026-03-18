"""表情包管理服务"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sticker import Sticker, StickerEmotion, StickerPersonalityMatch, StickerType


class StickerService:
    """表情包管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sticker(
        self,
        name: str,
        type: StickerType,
        url: str,
        emotion: Optional[StickerEmotion] = None,
        personality_match: StickerPersonalityMatch = StickerPersonalityMatch.ALL,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        file_size: Optional[int] = None,
        file_format: Optional[str] = None,
        base_weight: float = 1.0,
    ) -> Sticker:
        """创建新表情包"""
        sticker = Sticker(
            name=name,
            type=type,
            url=url,
            emotion=emotion,
            personality_match=personality_match,
            tags=tags or [],
            keywords=keywords or [],
            description=description,
            source=source,
            file_size=file_size,
            file_format=file_format,
            base_weight=base_weight,
        )

        self.db.add(sticker)
        await self.db.commit()
        await self.db.refresh(sticker)

        return sticker

    async def get_random_stickers(
        self,
        type: Optional[StickerType] = None,
        limit: int = 10,
    ) -> List[Sticker]:
        """随机获取表情包"""
        from sqlalchemy import func

        query = select(Sticker).where(Sticker.is_active is True)

        if type:
            query = query.where(Sticker.type == type)

        # SQLite 使用 RANDOM() 函数
        query = query.order_by(func.random()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_sticker_by_id(self, sticker_id: str) -> Optional[Sticker]:
        """根据ID获取表情包"""
        result = await self.db.execute(select(Sticker).where(Sticker.id == sticker_id))
        return result.scalar_one_or_none()

    async def list_stickers(
        self,
        type: Optional[StickerType] = None,
        emotion: Optional[StickerEmotion] = None,
        personality_match: Optional[StickerPersonalityMatch] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Sticker], int]:
        """分页查询表情包列表"""
        query = select(Sticker).where(Sticker.is_active == is_active)

        if type:
            query = query.where(Sticker.type == type)
        if emotion:
            query = query.where(Sticker.emotion == emotion)
        if personality_match:
            query = query.where(
                (Sticker.personality_match == personality_match)
                | (Sticker.personality_match == StickerPersonalityMatch.ALL)
            )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # 分页查询
        query = query.order_by(Sticker.usage_count.desc(), Sticker.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        stickers = result.scalars().all()

        return list(stickers), total

    async def search_stickers(
        self,
        keyword: str,
        type: Optional[StickerType] = None,
        emotion: Optional[StickerEmotion] = None,
        limit: int = 20,
    ) -> List[Sticker]:
        """搜索表情包"""
        keyword = keyword.lower()

        query = select(Sticker).where(
            Sticker.is_active is True,
            (func.lower(Sticker.name).contains(keyword))
            | (func.lower(Sticker.description).contains(keyword))
            | (func.json_extract(Sticker.tags, "$").contains(keyword))
            | (func.json_extract(Sticker.keywords, "$").contains(keyword)),
        )

        if type:
            query = query.where(Sticker.type == type)
        if emotion:
            query = query.where(Sticker.emotion == emotion)

        query = query.order_by(Sticker.usage_count.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_sticker(
        self,
        sticker_id: str,
        **kwargs,
    ) -> Optional[Sticker]:
        """更新表情包信息"""
        sticker = await self.get_sticker_by_id(sticker_id)
        if not sticker:
            return None

        allowed_fields = [
            "name",
            "type",
            "url",
            "emotion",
            "personality_match",
            "tags",
            "keywords",
            "description",
            "source",
            "file_size",
            "file_format",
            "base_weight",
            "emotion_weight",
            "personality_weight",
            "context_weight",
            "is_active",
        ]

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(sticker, field, value)

        await self.db.commit()
        await self.db.refresh(sticker)

        return sticker

    async def delete_sticker(self, sticker_id: str) -> bool:
        """删除表情包（软删除）"""
        sticker = await self.get_sticker_by_id(sticker_id)
        if not sticker:
            return False

        sticker.is_active = False
        await self.db.commit()

        return True

    async def increment_usage(self, sticker_id: str, success: bool = True) -> None:
        """增加使用次数并更新成功率"""
        sticker = await self.get_sticker_by_id(sticker_id)
        if not sticker:
            return

        sticker.usage_count += 1

        # 更新成功率
        if success:
            # 成功时按指数移动平均更新
            sticker.success_rate = 0.9 * sticker.success_rate + 0.1 * 1.0
        else:
            sticker.success_rate = 0.9 * sticker.success_rate + 0.1 * 0.0

        # 限制在0-1之间
        sticker.success_rate = max(0.0, min(1.0, sticker.success_rate))

        await self.db.commit()

    async def get_stickers_by_emotion(
        self,
        emotion: StickerEmotion,
        personality: Optional[str] = None,
        sticker_type: Optional[StickerType] = None,
        limit: int = 50,
    ) -> List[Sticker]:
        """根据情绪获取表情包"""
        query = select(Sticker).where(Sticker.is_active is True, Sticker.emotion == emotion)

        if personality:
            query = query.where(
                (Sticker.personality_match == personality)
                | (Sticker.personality_match == StickerPersonalityMatch.ALL)
            )

        if sticker_type:
            query = query.where(Sticker.type == sticker_type)

        # 按权重和成功率排序
        query = query.order_by(
            (Sticker.base_weight * Sticker.success_rate).desc(), Sticker.usage_count.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def batch_import_stickers(self, stickers_data: List[dict]) -> int:
        """批量导入表情包"""
        count = 0
        for data in stickers_data:
            try:
                sticker = Sticker(**data)
                self.db.add(sticker)
                count += 1
            except Exception:
                continue

        if count > 0:
            await self.db.commit()

        return count

    async def get_statistics(self) -> dict:
        """获取表情包统计信息"""
        # 总数量
        total = await self.db.scalar(select(func.count()).where(Sticker.is_active is True))

        # 按类型统计
        type_stats = {}
        for sticker_type in StickerType:
            count = await self.db.scalar(
                select(func.count()).where(Sticker.is_active is True, Sticker.type == sticker_type)
            )
            type_stats[sticker_type.value] = count

        # 按情绪统计
        emotion_stats = {}
        for emotion in StickerEmotion:
            count = await self.db.scalar(
                select(func.count()).where(Sticker.is_active is True, Sticker.emotion == emotion)
            )
            emotion_stats[emotion.value] = count

        # 总使用次数
        total_usage = (
            await self.db.scalar(
                select(func.sum(Sticker.usage_count)).where(Sticker.is_active is True)
            )
            or 0
        )

        return {
            "total_stickers": total,
            "by_type": type_stats,
            "by_emotion": emotion_stats,
            "total_usage": total_usage,
        }
