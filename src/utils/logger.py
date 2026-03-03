"""日志系统配置"""
import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    配置结构化日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(file_handler)
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if not log_file else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    获取logger实例
    
    Args:
        name: logger名称，通常使用模块名 __name__
        
    Returns:
        structlog.BoundLogger实例
    """
    return structlog.get_logger(name)


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    脱敏处理敏感数据
    
    Args:
        data: 原始数据字典
        
    Returns:
        脱敏后的数据字典
    """
    sensitive_keys = [
        'password', 'api_key', 'token', 'secret', 'credential',
        'phone', 'mobile', 'id_card', 'ssn', 'credit_card'
    ]
    
    masked_data = data.copy()
    for key, value in masked_data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                masked_data[key] = '***'
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
    
    return masked_data
