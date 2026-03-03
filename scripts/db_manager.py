#!/usr/bin/env python3
"""数据库管理命令行工具"""
import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.manager import ConfigurationManager
from src.storage.database import DatabaseManager
from src.storage.encryption import EncryptionManager
from src.storage.init_db import DatabaseInitializer, init_database
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def cmd_init(args):
    """初始化数据库"""
    print("正在初始化数据库...")
    
    config_manager = ConfigurationManager()
    config = config_manager.load_config(args.config)
    
    success = await init_database(config.database, reset=args.reset)
    
    if success:
        print("✓ 数据库初始化成功")
        return 0
    else:
        print("✗ 数据库初始化失败")
        return 1


async def cmd_check(args):
    """检查数据库状态"""
    print("正在检查数据库状态...")
    
    config_manager = ConfigurationManager()
    config = config_manager.load_config(args.config)
    
    db_manager = DatabaseManager(config.database)
    
    try:
        # 初始化连接
        if not await db_manager.initialize():
            print("✗ 无法连接到数据库")
            return 1
        
        print("✓ 数据库连接成功")
        
        # 检查表
        initializer = DatabaseInitializer(db_manager)
        if await initializer.check_tables_exist():
            print("✓ 所有必需的表都存在")
            
            # 统计数据
            stats = {}
            tables = [
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
            
            for table in tables:
                count = await db_manager.fetchval(f"SELECT COUNT(*) FROM {table}")
                stats[table] = count
            
            print("\n数据统计:")
            for table, count in stats.items():
                print(f"  {table}: {count} 条记录")
            
            return 0
        else:
            print("✗ 部分表不存在，请运行初始化命令")
            return 1
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return 1
    finally:
        await db_manager.close()


async def cmd_reset(args):
    """重置数据库"""
    if not args.yes:
        response = input("警告: 此操作将删除所有数据！是否继续? (yes/no): ")
        if response.lower() != 'yes':
            print("操作已取消")
            return 0
    
    print("正在重置数据库...")
    
    config_manager = ConfigurationManager()
    config = config_manager.load_config(args.config)
    
    success = await init_database(config.database, reset=True)
    
    if success:
        print("✓ 数据库重置成功")
        return 0
    else:
        print("✗ 数据库重置失败")
        return 1


def cmd_genkey(args):
    """生成加密密钥"""
    if args.password:
        key = EncryptionManager.generate_key_from_password(args.password)
        print(f"从密码生成的密钥: {key}")
    else:
        key = EncryptionManager.generate_new_key()
        print(f"新生成的密钥: {key}")
    
    print("\n请将此密钥保存到环境变量或 .env 文件中:")
    print(f"export ENCRYPTION_KEY='{key}'")
    print(f"或在 .env 文件中添加:")
    print(f"ENCRYPTION_KEY={key}")
    
    return 0


async def cmd_backup(args):
    """备份数据库（导出为SQL）"""
    import subprocess
    
    config_manager = ConfigurationManager()
    config = config_manager.load_config(args.config)
    
    output_file = args.output or f"backup_{config.database.database}.sql"
    
    print(f"正在备份数据库到 {output_file}...")
    
    try:
        cmd = [
            'pg_dump',
            '-h', config.database.host,
            '-p', str(config.database.port),
            '-U', config.database.username,
            '-d', config.database.database,
            '-f', output_file
        ]
        
        env = {'PGPASSWORD': config.database.password}
        subprocess.run(cmd, env=env, check=True)
        
        print(f"✓ 数据库已备份到 {output_file}")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 备份失败: {e}")
        return 1
    except FileNotFoundError:
        print("✗ 未找到 pg_dump 命令，请确保已安装 PostgreSQL 客户端工具")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI伴侣机器人数据库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    parser_init = subparsers.add_parser('init', help='初始化数据库')
    parser_init.add_argument(
        '--reset',
        action='store_true',
        help='重置数据库（删除所有表后重新创建）'
    )
    
    # check 命令
    subparsers.add_parser('check', help='检查数据库状态')
    
    # reset 命令
    parser_reset = subparsers.add_parser('reset', help='重置数据库（危险操作）')
    parser_reset.add_argument(
        '-y', '--yes',
        action='store_true',
        help='跳过确认提示'
    )
    
    # genkey 命令
    parser_genkey = subparsers.add_parser('genkey', help='生成加密密钥')
    parser_genkey.add_argument(
        '-p', '--password',
        help='从密码生成密钥'
    )
    
    # backup 命令
    parser_backup = subparsers.add_parser('backup', help='备份数据库')
    parser_backup.add_argument(
        '-o', '--output',
        help='输出文件路径'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level)
    
    # 执行命令
    if args.command == 'init':
        return asyncio.run(cmd_init(args))
    elif args.command == 'check':
        return asyncio.run(cmd_check(args))
    elif args.command == 'reset':
        return asyncio.run(cmd_reset(args))
    elif args.command == 'genkey':
        return cmd_genkey(args)
    elif args.command == 'backup':
        return asyncio.run(cmd_backup(args))
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
