"""初始化管理员账号"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_password_hash
from app.models.admin_user import AdminUser


async def init_default_admin(db: AsyncSession):
    """初始化默认管理员账号

    如果数据库中没有管理员，创建一个默认的超级管理员
    """
    # 检查是否已有管理员
    result = await db.execute(select(AdminUser).limit(1))
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        print("  管理员账号已存在，跳过初始化")
        return

    # 创建默认超级管理员
    default_admin = AdminUser(
        username="admin",
        password_hash=get_password_hash("admin123"),
        nickname="超级管理员",
        email="admin@example.com",
        role="super_admin",
        is_active=True,
    )

    db.add(default_admin)
    await db.commit()

    print("  默认管理员账号已创建")
    print(f"    用户名: {default_admin.username}")
    print("    密码: admin123")
    print(f"    角色: {default_admin.role}")
