"""初始化表情包数据"""

import asyncio

from app.core.session import AsyncSessionLocal
from app.services.sticker.init_stickers import init_default_stickers


async def main():
    async with AsyncSessionLocal() as db:
        print("开始初始化表情包...")
        count = await init_default_stickers(db, overwrite=False, sync_remote=True)
        print(f"初始化完成，共导入 {count} 个表情包")


if __name__ == "__main__":
    asyncio.run(main())
