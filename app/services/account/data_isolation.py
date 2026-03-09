"""数据隔离服务 - 实现多账号数据隔离"""

import hashlib
import logging
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DataIsolation:
    """数据隔离服务

    提供多账号环境下的数据隔离能力，包括：
    - 缓存命名空间隔离
    - 文件存储隔离
    - 向量数据库隔离
    """

    def __init__(self):
        self.base_data_dir = (
            Path(settings.DATA_DIR) if hasattr(settings, "DATA_DIR") else Path("./data")
        )
        self.base_cache_prefix = "flower"

    def get_cache_namespace(self, account_id: str) -> str:
        """获取缓存命名空间

        Args:
            account_id: 账号ID

        Returns:
            缓存命名空间
        """
        return f"{self.base_cache_prefix}:account:{account_id}"

    def get_cache_key(self, account_id: str, key: str) -> str:
        """获取带命名空间的缓存键

        Args:
            account_id: 账号ID
            key: 原始缓存键

        Returns:
            带命名空间的缓存键
        """
        namespace = self.get_cache_namespace(account_id)
        return f"{namespace}:{key}"

    def get_file_storage_path(self, account_id: str, sub_path: str = "") -> Path:
        """获取文件存储路径

        Args:
            account_id: 账号ID
            sub_path: 子路径

        Returns:
            文件存储路径
        """
        # 使用账号ID的MD5哈希前16位作为目录名，确保唯一性且避免目录名过长
        account_hash = hashlib.md5(account_id.encode()).hexdigest()[:16]
        path = self.base_data_dir / "accounts" / account_hash

        if sub_path:
            path = path / sub_path

        # 确保目录存在
        path.mkdir(parents=True, exist_ok=True)

        return path

    def get_vector_collection_name(self, account_id: str, collection_type: str = "memories") -> str:
        """获取向量数据库集合名称

        Args:
            account_id: 账号ID
            collection_type: 集合类型 (memories/conversations/knowledge)

        Returns:
            集合名称
        """
        # 使用账号ID的哈希值作为集合名的一部分
        account_hash = hashlib.md5(account_id.encode()).hexdigest()[:8]
        return f"account_{account_hash}_{collection_type}"

    def get_sticker_storage_path(self, account_id: str) -> Path:
        """获取表情包存储路径

        Args:
            account_id: 账号ID

        Returns:
            表情包存储路径
        """
        return self.get_file_storage_path(account_id, "stickers")

    def get_avatar_storage_path(self, account_id: str) -> Path:
        """获取头像存储路径

        Args:
            account_id: 账号ID

        Returns:
            头像存储路径
        """
        return self.get_file_storage_path(account_id, "avatars")

    def get_backup_storage_path(self, account_id: str) -> Path:
        """获取备份存储路径

        Args:
            account_id: 账号ID

        Returns:
            备份存储路径
        """
        return self.get_file_storage_path(account_id, "backups")

    def get_log_file_path(self, account_id: str) -> Path:
        """获取日志文件路径

        Args:
            account_id: 账号ID

        Returns:
            日志文件路径
        """
        return self.get_file_storage_path(account_id, "logs") / "account.log"

    async def cleanup_account_data(self, account_id: str) -> dict[str, Any]:
        """清理账号相关数据

        Args:
            account_id: 账号ID

        Returns:
            清理结果
        """
        result = {
            "account_id": account_id,
            "files_removed": 0,
            "cache_keys_removed": 0,
            "errors": [],
        }

        # 清理文件存储
        try:
            account_hash = account_id[:8]
            account_dir = self.base_data_dir / "accounts" / account_hash

            if account_dir.exists():
                import shutil

                file_count = sum(1 for _ in account_dir.rglob("*") if _.is_file())
                shutil.rmtree(account_dir)
                result["files_removed"] = file_count
                logger.info(f"已清理账号 {account_id} 的文件存储，共 {file_count} 个文件")
        except Exception as e:
            result["errors"].append(f"清理文件存储失败: {e}")
            logger.error(f"清理账号 {account_id} 文件存储失败: {e}")

        # 注意：缓存和向量数据库的清理需要在外部调用时处理
        # 因为这里不直接操作Redis和ChromaDB

        return result

    def get_isolation_info(self, account_id: str) -> dict[str, Any]:
        """获取数据隔离信息

        Args:
            account_id: 账号ID

        Returns:
            隔离信息
        """
        return {
            "account_id": account_id,
            "cache_namespace": self.get_cache_namespace(account_id),
            "file_storage_path": str(self.get_file_storage_path(account_id)),
            "sticker_path": str(self.get_sticker_storage_path(account_id)),
            "avatar_path": str(self.get_avatar_storage_path(account_id)),
            "backup_path": str(self.get_backup_storage_path(account_id)),
            "log_path": str(self.get_log_file_path(account_id)),
            "vector_collections": {
                "memories": self.get_vector_collection_name(account_id, "memories"),
                "conversations": self.get_vector_collection_name(account_id, "conversations"),
                "knowledge": self.get_vector_collection_name(account_id, "knowledge"),
            },
        }

    @staticmethod
    def validate_account_id(account_id: str) -> bool:
        """验证账号ID格式

        Args:
            account_id: 账号ID

        Returns:
            是否有效
        """
        if not account_id:
            return False

        # UUID格式验证
        import re

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
        )

        return bool(uuid_pattern.match(account_id))


class IsolatedCache:
    """隔离的缓存包装器

    为每个账号提供独立的缓存命名空间
    """

    def __init__(self, cache_client: Any, account_id: str):
        """
        Args:
            cache_client: 缓存客户端 (Redis等)
            account_id: 账号ID
        """
        self.cache = cache_client
        self.isolation = DataIsolation()
        self.account_id = account_id
        self.namespace = self.isolation.get_cache_namespace(account_id)

    def _make_key(self, key: str) -> str:
        """生成带命名空间的键"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any:
        """获取缓存值"""
        namespaced_key = self._make_key(key)
        return await self.cache.get(namespaced_key)

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """设置缓存值"""
        namespaced_key = self._make_key(key)
        return await self.cache.set(namespaced_key, value, expire=expire)

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        namespaced_key = self._make_key(key)
        return await self.cache.delete(namespaced_key)

    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        namespaced_key = self._make_key(key)
        return await self.cache.exists(namespaced_key)

    async def clear(self) -> int:
        """清除该账号的所有缓存

        Returns:
            清除的键数量
        """
        pattern = f"{self.namespace}:*"
        keys = await self.cache.keys(pattern)

        if keys:
            return await self.cache.delete(*keys)
        return 0

    async def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        pattern = f"{self.namespace}:*"
        keys = await self.cache.keys(pattern)

        return {
            "account_id": self.account_id,
            "namespace": self.namespace,
            "key_count": len(keys),
            "keys": keys[:100],  # 最多返回100个键
        }
