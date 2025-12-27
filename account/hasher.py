"""Password hashing utilities.

使用 SHA-256 + Salt 进行密码哈希。
"""
from __future__ import annotations

import hashlib
import secrets


class PasswordHasher:
    """密码哈希处理器。
    
    使用 PBKDF2-SHA256 进行密码哈希，包含随机盐值。
    存储格式：algorithm:salt:hash
    """

    ALGORITHM = "sha256"
    SALT_LENGTH = 16
    ITERATIONS = 100000

    @classmethod
    def hash_password(cls, password: str) -> str:
        """生成密码哈希。
        
        Args:
            password: 明文密码
            
        Returns:
            格式为 "algorithm:salt:hash" 的哈希字符串
        """
        salt = secrets.token_hex(cls.SALT_LENGTH)
        hash_value = cls._compute_hash(password, salt)
        return f"{cls.ALGORITHM}:{salt}:{hash_value}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """验证密码。
        
        Args:
            password: 待验证的明文密码
            stored_hash: 存储的哈希字符串
            
        Returns:
            密码是否正确
        """
        try:
            algorithm, salt, hash_value = stored_hash.split(":")
            if algorithm != cls.ALGORITHM:
                return False
            computed = cls._compute_hash(password, salt)
            return secrets.compare_digest(computed, hash_value)
        except ValueError:
            return False

    @classmethod
    def _compute_hash(cls, password: str, salt: str) -> str:
        """计算哈希值。"""
        key = hashlib.pbkdf2_hmac(
            cls.ALGORITHM,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            cls.ITERATIONS
        )
        return key.hex()
