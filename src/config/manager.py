"""配置管理器"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.enums import ConnectionType, Gender, Personality, Platform, Role
from src.core.models import PersonalityProfile
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIProviderConfig:
    """AI提供商配置"""
    name: str
    api_key: str
    endpoint: Optional[str] = None
    model: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformConfig:
    """平台配置"""
    platform: Platform
    connection_type: ConnectionType
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "ai_companion_bot"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


@dataclass
class SystemConfig:
    """系统配置"""
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"
    data_retention_days: int = 30
    max_concurrent_conversations: int = 10


@dataclass
class Config:
    """完整配置"""
    ai_providers: Dict[str, AIProviderConfig] = field(default_factory=dict)
    platforms: Dict[str, PlatformConfig] = field(default_factory=dict)
    personality_profiles: Dict[str, PersonalityProfile] = field(default_factory=dict)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    system: SystemConfig = field(default_factory=SystemConfig)


class ConfigurationManager:
    """配置管理器"""
    
    def __init__(self):
        self._config: Optional[Config] = None
        self._config_path: Optional[Path] = None
    
    def load_config(self, config_path: str) -> Config:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Config对象
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        logger.info("loading_config", path=str(path))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ValueError("配置文件为空")
            
            config = self._parse_config(data)
            
            if not self.validate_config(config):
                raise ValueError("配置验证失败")
            
            self._config = config
            self._config_path = path
            
            logger.info("config_loaded", providers=len(config.ai_providers))
            return config
            
        except yaml.YAMLError as e:
            logger.error("yaml_parse_error", error=str(e))
            raise ValueError(f"YAML解析错误: {e}")
        except Exception as e:
            logger.error("config_load_error", error=str(e))
            raise
    
    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """解析配置数据"""
        config = Config()
        
        # 解析AI提供商配置
        if 'ai_providers' in data:
            for name, provider_data in data['ai_providers'].items():
                config.ai_providers[name] = AIProviderConfig(
                    name=name,
                    api_key=provider_data.get('api_key', ''),
                    endpoint=provider_data.get('endpoint'),
                    model=provider_data.get('model'),
                    parameters=provider_data.get('parameters', {})
                )
        
        # 解析平台配置
        if 'platforms' in data:
            for platform_name, platform_data in data['platforms'].items():
                config.platforms[platform_name] = PlatformConfig(
                    platform=Platform(platform_name),
                    connection_type=ConnectionType(platform_data.get('connection_type', 'web_api')),
                    enabled=platform_data.get('enabled', True),
                    config=platform_data.get('config', {})
                )
        
        # 解析性格配置
        if 'personality_profiles' in data:
            for profile_id, profile_data in data['personality_profiles'].items():
                from datetime import datetime
                config.personality_profiles[profile_id] = PersonalityProfile(
                    id=profile_id,
                    personality=Personality(profile_data['personality']),
                    role=Role(profile_data['role']),
                    gender=Gender(profile_data['gender']),
                    traits=profile_data.get('traits', {}),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
        
        # 解析数据库配置
        if 'database' in data:
            db_data = data['database']
            config.database = DatabaseConfig(
                host=db_data.get('host', 'localhost'),
                port=db_data.get('port', 5432),
                database=db_data.get('database', 'ai_companion_bot'),
                username=db_data.get('username', 'postgres'),
                password=db_data.get('password', ''),
                pool_size=db_data.get('pool_size', 10)
            )
        
        # 解析Redis配置
        if 'redis' in data:
            redis_data = data['redis']
            config.redis = RedisConfig(
                host=redis_data.get('host', 'localhost'),
                port=redis_data.get('port', 6379),
                db=redis_data.get('db', 0),
                password=redis_data.get('password')
            )
        
        # 解析系统配置
        if 'system' in data:
            sys_data = data['system']
            config.system = SystemConfig(
                log_level=sys_data.get('log_level', 'INFO'),
                log_file=sys_data.get('log_file', 'logs/app.log'),
                data_retention_days=sys_data.get('data_retention_days', 30),
                max_concurrent_conversations=sys_data.get('max_concurrent_conversations', 10)
            )
        
        return config
    
    def save_config(self, config: Config, config_path: str) -> bool:
        """
        保存配置到文件
        
        Args:
            config: Config对象
            config_path: 配置文件路径
            
        Returns:
            是否保存成功
        """
        try:
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为字典
            data = self._config_to_dict(config)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            
            logger.info("config_saved", path=str(path))
            return True
            
        except Exception as e:
            logger.error("config_save_error", error=str(e))
            return False
    
    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """将Config对象转换为字典"""
        data = {}
        
        # AI提供商
        if config.ai_providers:
            data['ai_providers'] = {
                name: {
                    'api_key': provider.api_key,
                    'endpoint': provider.endpoint,
                    'model': provider.model,
                    'parameters': provider.parameters
                }
                for name, provider in config.ai_providers.items()
            }
        
        # 平台配置
        if config.platforms:
            data['platforms'] = {
                platform.platform.value: {
                    'connection_type': platform.connection_type.value,
                    'enabled': platform.enabled,
                    'config': platform.config
                }
                for platform in config.platforms.values()
            }
        
        # 性格配置
        if config.personality_profiles:
            data['personality_profiles'] = {
                profile_id: {
                    'personality': profile.personality.value,
                    'role': profile.role.value,
                    'gender': profile.gender.value,
                    'traits': profile.traits
                }
                for profile_id, profile in config.personality_profiles.items()
            }
        
        # 数据库配置
        data['database'] = {
            'host': config.database.host,
            'port': config.database.port,
            'database': config.database.database,
            'username': config.database.username,
            'password': config.database.password,
            'pool_size': config.database.pool_size
        }
        
        # Redis配置
        data['redis'] = {
            'host': config.redis.host,
            'port': config.redis.port,
            'db': config.redis.db,
            'password': config.redis.password
        }
        
        # 系统配置
        data['system'] = {
            'log_level': config.system.log_level,
            'log_file': config.system.log_file,
            'data_retention_days': config.system.data_retention_days,
            'max_concurrent_conversations': config.system.max_concurrent_conversations
        }
        
        return data
    
    def validate_config(self, config: Config) -> bool:
        """
        验证配置有效性
        
        Args:
            config: Config对象
            
        Returns:
            配置是否有效
        """
        try:
            # 验证至少有一个AI提供商
            if not config.ai_providers:
                logger.error("validation_error", reason="至少需要配置一个AI提供商")
                return False
            
            # 验证AI提供商配置
            for name, provider in config.ai_providers.items():
                if not provider.api_key:
                    logger.error("validation_error", provider=name, reason="API密钥不能为空")
                    return False
            
            # 验证至少有一个平台
            if not config.platforms:
                logger.error("validation_error", reason="至少需要配置一个平台")
                return False
            
            # 验证数据库配置
            if not config.database.host or not config.database.database:
                logger.error("validation_error", reason="数据库配置不完整")
                return False
            
            logger.info("config_validation_passed")
            return True
            
        except Exception as e:
            logger.error("validation_error", error=str(e))
            return False
    
    def get_ai_provider_config(self, provider: str) -> Optional[AIProviderConfig]:
        """获取AI提供商配置"""
        if not self._config:
            return None
        return self._config.ai_providers.get(provider)
    
    def get_personality_profile(self, profile_id: str) -> Optional[PersonalityProfile]:
        """获取性格配置"""
        if not self._config:
            return None
        return self._config.personality_profiles.get(profile_id)
    
    @property
    def config(self) -> Optional[Config]:
        """获取当前配置"""
        return self._config
