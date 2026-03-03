"""数据加密工具类"""
import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptionManager:
    """数据加密管理器"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化加密管理器
        
        Args:
            encryption_key: 加密密钥（base64编码），如果为None则从环境变量读取或生成新密钥
        """
        if encryption_key:
            self._key = encryption_key.encode()
        else:
            # 从环境变量读取或生成新密钥
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self._key = env_key.encode()
            else:
                # 生成新密钥
                self._key = Fernet.generate_key()
                logger.warning(
                    "encryption_key_generated",
                    message="未找到加密密钥，已生成新密钥。请将其保存到环境变量ENCRYPTION_KEY中"
                )
        
        self._fernet = Fernet(self._key)
    
    def encrypt(self, data: str) -> bytes:
        """
        加密字符串数据
        
        Args:
            data: 要加密的字符串
            
        Returns:
            加密后的字节数据
        """
        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return encrypted
        except Exception as e:
            logger.error("encryption_error", error=str(e))
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的字节数据
            
        Returns:
            解密后的字符串
        """
        try:
            decrypted = self._fernet.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error("decryption_error", error=str(e))
            raise
    
    def get_key(self) -> str:
        """
        获取加密密钥（base64编码）
        
        Returns:
            加密密钥字符串
        """
        return self._key.decode('utf-8')
    
    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> str:
        """
        从密码生成加密密钥
        
        Args:
            password: 密码字符串
            salt: 盐值，如果为None则生成新盐值
            
        Returns:
            base64编码的密钥
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode('utf-8')
    
    @staticmethod
    def generate_new_key() -> str:
        """
        生成新的加密密钥
        
        Returns:
            base64编码的密钥
        """
        return Fernet.generate_key().decode('utf-8')
