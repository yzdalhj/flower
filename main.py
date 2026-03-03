"""
AI Companion Bot - 主入口
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config import ConfigurationManager
from src.utils.logger import get_logger, setup_logging


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 设置日志
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # 确保日志目录存在
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    setup_logging(log_level=log_level, log_file=log_file)
    logger = get_logger(__name__)
    
    logger.info("starting_ai_companion_bot", version="0.1.0")
    
    try:
        # 加载配置
        config_path = os.getenv('CONFIG_PATH', 'config.yaml')
        config_manager = ConfigurationManager()
        config = config_manager.load_config(config_path)
        
        logger.info(
            "config_loaded_successfully",
            ai_providers=len(config.ai_providers),
            platforms=len(config.platforms),
            profiles=len(config.personality_profiles)
        )
        
        # TODO: 初始化各个组件
        # - 数据库连接
        # - Redis连接
        # - 平台适配器
        # - AI服务管理器
        # - 消息处理器
        # 等等...
        
        logger.info("ai_companion_bot_started")
        
        # TODO: 启动主事件循环
        # asyncio.run(run_bot())
        
        logger.warning("bot_not_fully_implemented", message="核心功能尚未实现，请继续开发")
        
    except FileNotFoundError as e:
        logger.error("config_file_not_found", error=str(e))
        logger.info("hint", message="请复制 config.example.yaml 为 config.yaml 并配置")
        sys.exit(1)
    except ValueError as e:
        logger.error("config_validation_failed", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("startup_error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
