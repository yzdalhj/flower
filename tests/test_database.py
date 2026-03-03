"""数据库层测试"""
import asyncio
import os
import uuid
from datetime import datetime

import pytest

from src.config.manager import DatabaseConfig
from src.storage.database import DatabaseManager
from src.storage.encryption import EncryptionManager
from src.storage.init_db import DatabaseInitializer


@pytest.fixture
async def db_manager():
    """数据库管理器fixture"""
    config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "ai_companion_bot_test"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        pool_size=5
    )
    
    manager = DatabaseManager(config)
    await manager.initialize()
    
    yield manager
    
    await manager.close()


@pytest.fixture
async def initialized_db(db_manager):
    """初始化的数据库fixture"""
    initializer = DatabaseInitializer(db_manager)
    
    # 重置数据库
    await initializer.drop_all_tables()
    await initializer.initialize_schema()
    
    yield db_manager
    
    # 清理
    await initializer.drop_all_tables()


class TestEncryptionManager:
    """加密管理器测试"""
    
    def test_encrypt_decrypt(self):
        """测试加密和解密"""
        manager = EncryptionManager()
        
        original_text = "这是一条需要加密的对话记录"
        encrypted = manager.encrypt(original_text)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original_text
        assert encrypted != original_text.encode()
    
    def test_generate_key(self):
        """测试密钥生成"""
        key = EncryptionManager.generate_new_key()
        assert key is not None
        assert len(key) > 0
        
        # 使用生成的密钥创建管理器
        manager = EncryptionManager(key)
        text = "测试文本"
        encrypted = manager.encrypt(text)
        decrypted = manager.decrypt(encrypted)
        assert decrypted == text
    
    def test_key_from_password(self):
        """测试从密码生成密钥"""
        password = "my-secure-password"
        key = EncryptionManager.generate_key_from_password(password)
        
        assert key is not None
        assert len(key) > 0


class TestDatabaseManager:
    """数据库管理器测试"""
    
    @pytest.mark.asyncio
    async def test_connection(self, db_manager):
        """测试数据库连接"""
        assert db_manager.is_connected
        
        # 测试简单查询
        result = await db_manager.fetchval("SELECT 1")
        assert result == 1
    
    @pytest.mark.asyncio
    async def test_execute_query(self, initialized_db):
        """测试执行查询"""
        # 插入测试数据
        conversation_id = str(uuid.uuid4())
        await initialized_db.execute(
            """
            INSERT INTO conversations (id, user_id, platform, message_type, content, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            conversation_id,
            "test_user",
            "wechat",
            "text",
            "测试消息",
            datetime.now()
        )
        
        # 查询数据
        row = await initialized_db.fetchrow(
            "SELECT * FROM conversations WHERE id = $1",
            conversation_id
        )
        
        assert row is not None
        assert row['user_id'] == "test_user"
        assert row['content'] == "测试消息"
    
    @pytest.mark.asyncio
    async def test_fetch_multiple(self, initialized_db):
        """测试查询多行数据"""
        # 插入多条测试数据
        user_id = "test_user_multi"
        for i in range(3):
            await initialized_db.execute(
                """
                INSERT INTO conversations (id, user_id, platform, message_type, content, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(uuid.uuid4()),
                user_id,
                "wechat",
                "text",
                f"消息{i}",
                datetime.now()
            )
        
        # 查询所有数据
        rows = await initialized_db.fetch(
            "SELECT * FROM conversations WHERE user_id = $1 ORDER BY timestamp",
            user_id
        )
        
        assert len(rows) == 3
        assert rows[0]['content'] == "消息0"
        assert rows[2]['content'] == "消息2"


class TestDatabaseInitializer:
    """数据库初始化器测试"""
    
    @pytest.mark.asyncio
    async def test_initialize_schema(self, db_manager):
        """测试初始化数据库模式"""
        initializer = DatabaseInitializer(db_manager)
        
        # 删除所有表
        await initializer.drop_all_tables()
        
        # 初始化模式
        success = await initializer.initialize_schema()
        assert success
        
        # 检查表是否存在
        tables_exist = await initializer.check_tables_exist()
        assert tables_exist
    
    @pytest.mark.asyncio
    async def test_check_tables(self, initialized_db):
        """测试检查表是否存在"""
        initializer = DatabaseInitializer(initialized_db)
        
        # 所有表应该存在
        assert await initializer.check_tables_exist()
    
    @pytest.mark.asyncio
    async def test_drop_tables(self, initialized_db):
        """测试删除所有表"""
        initializer = DatabaseInitializer(initialized_db)
        
        # 删除所有表
        success = await initializer.drop_all_tables()
        assert success
        
        # 表应该不存在了
        tables_exist = await initializer.check_tables_exist()
        assert not tables_exist


class TestEncryptedStorage:
    """加密存储测试"""
    
    @pytest.mark.asyncio
    async def test_store_encrypted_conversation(self, initialized_db):
        """测试存储加密的对话记录"""
        encryption_manager = EncryptionManager()
        
        # 准备数据
        conversation_id = str(uuid.uuid4())
        user_id = "test_user_encrypted"
        original_content = "这是一条敏感的对话内容"
        
        # 加密内容
        encrypted_content = encryption_manager.encrypt(original_content)
        
        # 存储到数据库
        await initialized_db.execute(
            """
            INSERT INTO conversations 
            (id, user_id, platform, message_type, content, encrypted_content, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            conversation_id,
            user_id,
            "wechat",
            "text",
            "[加密]",  # 明文字段存储占位符
            encrypted_content,
            datetime.now()
        )
        
        # 从数据库读取
        row = await initialized_db.fetchrow(
            "SELECT * FROM conversations WHERE id = $1",
            conversation_id
        )
        
        assert row is not None
        assert row['encrypted_content'] is not None
        
        # 解密内容
        decrypted_content = encryption_manager.decrypt(bytes(row['encrypted_content']))
        assert decrypted_content == original_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
