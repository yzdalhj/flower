"""表情包初始化脚本"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sticker import Sticker
from app.services.sticker.sticker_library import DEFAULT_STICKERS
from app.services.sticker.sticker_service import StickerService


async def init_default_stickers(db: AsyncSession, overwrite: bool = False) -> int:
    """
    初始化默认表情包库

    Args:
        db: 数据库会话
        overwrite: 是否覆盖已有的同名表情包

    Returns:
        成功导入的表情包数量
    """
    sticker_service = StickerService(db)

    # 检查是否已经初始化过
    existing_count = await db.scalar("SELECT COUNT(*) FROM stickers WHERE source = '官方'")

    if existing_count and not overwrite:
        print(f"已存在 {existing_count} 个官方表情包，跳过初始化")
        return 0

    count = 0
    for sticker_data in DEFAULT_STICKERS:
        try:
            # 检查是否已存在同名表情包
            existing = await db.execute(
                Sticker.__table__.select().where(Sticker.name == sticker_data["name"])
            )
            existing_sticker = existing.first()

            if existing_sticker and not overwrite:
                continue

            if existing_sticker:
                # 更新现有表情包
                await sticker_service.update_sticker(existing_sticker.id, **sticker_data)
            else:
                # 创建新表情包
                await sticker_service.create_sticker(**sticker_data)

            count += 1
        except Exception as e:
            print(f"导入表情包 {sticker_data['name']} 失败: {e}")
            continue

    print(f"成功导入 {count} 个默认表情包")
    return count


async def main():
    """主函数"""
    from app.core.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await init_default_stickers(db, overwrite=False)


if __name__ == "__main__":
    asyncio.run(main())
