"""表情包初始化脚本

支持从动态表情包库初始化，并可同步远程梗图
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sticker import Sticker
from app.services.sticker.sticker_library import get_dynamic_sticker_library
from app.services.sticker.sticker_service import StickerService


async def init_default_stickers(
    db: AsyncSession, overwrite: bool = False, sync_remote: bool = False
) -> int:
    """
    初始化默认表情包库

    Args:
        db: 数据库会话
        overwrite: 是否覆盖已有的同名表情包
        sync_remote: 是否尝试同步远程表情包

    Returns:
        成功导入的表情包数量
    """
    sticker_service = StickerService(db)
    library = get_dynamic_sticker_library()

    # 获取表情包列表
    if sync_remote:
        stickers_data = await library.fetch_sticker_list(force_update=True)
    else:
        # 使用默认内置梗图 + 少量情绪表情
        stickers_data = library._get_default_memes()
        stickers_data.extend(library.get_default_emotion_stickers())

    count = 0
    for sticker_data in stickers_data:
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
            print(f"导入表情包 {sticker_data.get('name', 'unknown')} 失败: {e}")
            continue

    print(f"成功导入 {count} 个默认表情包")
    return count


async def sync_remote_stickers(
    db: AsyncSession, repo_url: Optional[str] = None, overwrite_existing: bool = True
) -> int:
    """
    从远程仓库同步表情包

    Args:
        db: 数据库会话
        repo_url: 远程仓库JSON索引URL，如果不指定使用默认配置
        overwrite_existing: 是否覆盖已有的同名表情包

    Returns:
        新增/更新的表情包数量
    """
    from app.services.sticker.sticker_library import DynamicStickerLibrary

    if repo_url:
        library = DynamicStickerLibrary(repo_url=repo_url)
    else:
        library = get_dynamic_sticker_library()

    sticker_service = StickerService(db)
    stickers_data = await library.fetch_sticker_list(force_update=True)

    count = 0
    for sticker_data in stickers_data:
        try:
            existing = await db.execute(
                Sticker.__table__.select().where(Sticker.name == sticker_data["name"])
            )
            existing_sticker = existing.first()

            if existing_sticker and not overwrite_existing:
                continue

            if existing_sticker:
                await sticker_service.update_sticker(existing_sticker.id, **sticker_data)
            else:
                await sticker_service.create_sticker(**sticker_data)

            count += 1
        except Exception as e:
            print(f"同步表情包 {sticker_data.get('name', 'unknown')} 失败: {e}")
            continue

    print(f"成功从远程同步 {count} 个表情包")
    return count


async def main():
    """主函数"""
    from app.core.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await init_default_stickers(db, overwrite=False)


if __name__ == "__main__":
    asyncio.run(main())
