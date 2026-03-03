"""数据库初始化模块"""
import asyncio
from pathlib import Path
from typing import Optional

from src.config.manager import DatabaseConfig
from src.storage.database import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据库初始化器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    async def initialize_schema(self, schema_file: Optional[str] = None) -> bool:
        """
        初始化数据库模式
        
        Args:
            schema_file: SQL模式文件路径，如果为None则使用默认路径
            
        Returns:
            是否初始化成功
        """
        try:
            # 确定schema文件路径
            if schema_file is None:
                schema_file = Path(__file__).parent / "schema.sql"
            else:
                schema_file = Path(schema_file)
            
            if not schema_file.exists():
                logger.error("schema_file_not_found", path=str(schema_file))
                return False
            
            logger.info("initializing_database_schema", schema_file=str(schema_file))
            
            # 读取SQL文件
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（按分号分割，但忽略注释中的分号）
            statements = self._split_sql_statements(sql_content)
            
            # 执行每条SQL语句
            async with self.db_manager.acquire() as conn:
                for i, statement in enumerate(statements):
                    statement = statement.strip()
                    if not statement or statement.startswith('--'):
                        continue
                    
                    try:
                        await conn.execute(statement)
                        logger.debug("sql_statement_executed", statement_num=i+1)
                    except Exception as e:
                        logger.error(
                            "sql_statement_error",
                            statement_num=i+1,
                            error=str(e),
                            statement=statement[:100]
                        )
                        raise
            
            logger.info("database_schema_initialized")
            return True
            
        except Exception as e:
            logger.error("schema_initialization_error", error=str(e))
            return False
    
    def _split_sql_statements(self, sql_content: str) -> list:
        """
        分割SQL语句
        
        Args:
            sql_content: SQL文件内容
            
        Returns:
            SQL语句列表
        """
        statements = []
        current_statement = []
        in_comment = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                continue
            
            # 处理注释
            if stripped.startswith('--'):
                continue
            
            # 处理多行注释
            if '/*' in stripped:
                in_comment = True
            if '*/' in stripped:
                in_comment = False
                continue
            if in_comment:
                continue
            
            current_statement.append(line)
            
            # 如果行以分号结尾，表示语句结束
            if stripped.endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        # 添加最后一条语句（如果有）
        if current_statement:
            statements.append('\n'.join(current_statement))
        
        return statements
    
    async def check_tables_exist(self) -> bool:
        """
        检查所有必需的表是否存在
        
        Returns:
            所有表是否都存在
        """
        required_tables = [
            'conversations',
            'emotion_history',
            'personality_profiles',
            'slang_database',
            'emoji_library',
            'role_transitions',
            'client_sessions',
            'media_cache',
            'connection_logs'
        ]
        
        try:
            async with self.db_manager.acquire() as conn:
                for table in required_tables:
                    exists = await conn.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                        """,
                        table
                    )
                    
                    if not exists:
                        logger.warning("table_not_found", table=table)
                        return False
            
            logger.info("all_tables_exist", count=len(required_tables))
            return True
            
        except Exception as e:
            logger.error("table_check_error", error=str(e))
            return False
    
    async def drop_all_tables(self) -> bool:
        """
        删除所有表（危险操作，仅用于开发/测试）
        
        Returns:
            是否删除成功
        """
        tables = [
            'connection_logs',
            'media_cache',
            'client_sessions',
            'role_transitions',
            'emoji_library',
            'slang_database',
            'personality_profiles',
            'emotion_history',
            'conversations'
        ]
        
        try:
            logger.warning("dropping_all_tables")
            
            async with self.db_manager.acquire() as conn:
                for table in tables:
                    await conn.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                    logger.debug("table_dropped", table=table)
            
            logger.info("all_tables_dropped")
            return True
            
        except Exception as e:
            logger.error("drop_tables_error", error=str(e))
            return False


async def init_database(config: DatabaseConfig, reset: bool = False) -> bool:
    """
    初始化数据库（便捷函数）
    
    Args:
        config: 数据库配置
        reset: 是否重置数据库（删除所有表后重新创建）
        
    Returns:
        是否初始化成功
    """
    db_manager = DatabaseManager(config)
    
    try:
        # 初始化连接池
        if not await db_manager.initialize():
            return False
        
        initializer = DatabaseInitializer(db_manager)
        
        # 如果需要重置，先删除所有表
        if reset:
            logger.warning("resetting_database")
            if not await initializer.drop_all_tables():
                return False
        
        # 初始化模式
        if not await initializer.initialize_schema():
            return False
        
        # 检查表是否都存在
        if not await initializer.check_tables_exist():
            return False
        
        logger.info("database_initialization_complete")
        return True
        
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        return False
    finally:
        await db_manager.close()


if __name__ == "__main__":
    # 用于命令行直接初始化数据库
    import sys
    from src.config.manager import ConfigurationManager
    
    # 设置日志
    from src.utils.logger import setup_logging
    setup_logging("INFO")
    
    # 加载配置
    config_path = "config.yaml" if len(sys.argv) < 2 else sys.argv[1]
    reset = "--reset" in sys.argv
    
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config(config_path)
        
        # 初始化数据库
        success = asyncio.run(init_database(config.database, reset=reset))
        
        if success:
            print("✓ 数据库初始化成功")
            sys.exit(0)
        else:
            print("✗ 数据库初始化失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)
