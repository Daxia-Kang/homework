"""Account service - 账户服务。

提供用户注册、登录、战绩管理等功能。
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime
from typing import List, Optional

from account.models import User, GameTypeRecord, Result
from account.hasher import PasswordHasher
from account.storage import AccountStorage


class AccountService:
    """账户服务实现。
    
    职责：
    1. 用户注册/登录
    2. 会话管理
    3. 战绩更新
    4. 录像关联
    """

    _instance: Optional["AccountService"] = None

    def __new__(cls, storage: Optional[AccountStorage] = None) -> "AccountService":
        """单例模式（可选）。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage: Optional[AccountStorage] = None) -> None:
        if self._initialized:
            return
        self._storage = storage or AccountStorage()
        self._current_user: Optional[User] = None
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "AccountService":
        """获取单例实例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）。"""
        cls._instance = None

    def register(self, username: str, password: str) -> Result:
        """注册新用户。
        
        Args:
            username: 用户名（3-20 字符，字母数字下划线）
            password: 密码（至少 6 字符）
            
        Returns:
            Result 包含 User 或错误信息
        """
        # 验证用户名
        if not self._validate_username(username):
            return Result.fail("用户名必须为 3-20 个字符，仅含字母数字下划线")

        # 检查用户名是否已存在
        if self._storage.user_exists(username):
            return Result.fail("用户名已存在")

        # 验证密码强度
        if len(password) < 6:
            return Result.fail("密码至少 6 个字符")

        # 创建用户
        user_id = f"user_{username.lower()}_{secrets.token_hex(4)}"
        password_hash = PasswordHasher.hash_password(password)

        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=datetime.now().isoformat()
        )

        self._storage.save_user(user)
        return Result.ok(user)

    def login(self, username: str, password: str) -> Result:
        """用户登录。
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Result 包含 User 或错误信息
        """
        user = self._storage.load_user(username)
        if not user:
            return Result.fail("用户不存在")

        if not PasswordHasher.verify_password(password, user.password_hash):
            return Result.fail("密码错误")

        user.last_login = datetime.now().isoformat()
        self._storage.save_user(user)
        self._current_user = user
        return Result.ok(user)

    def logout(self) -> None:
        """登出当前用户。"""
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        """获取当前登录用户。"""
        return self._current_user

    def is_logged_in(self) -> bool:
        """检查是否已登录。"""
        return self._current_user is not None

    def update_record(
        self,
        user_id: str,
        game_type: str,
        is_win: bool,
        is_draw: bool = False
    ) -> None:
        """更新用户战绩。
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
            is_win: 是否获胜
            is_draw: 是否平局
        """
        user = self._storage.load_user_by_id(user_id)
        if not user:
            return

        record = user.get_record(game_type.lower())
        record.total_games += 1
        
        if is_draw:
            record.draws += 1
        elif is_win:
            record.wins += 1
        else:
            record.losses += 1

        self._storage.save_user(user)
        
        # 更新当前用户缓存
        if self._current_user and self._current_user.user_id == user_id:
            self._current_user = user

    def add_replay(self, user_id: str, replay_id: str) -> None:
        """关联录像到用户。
        
        Args:
            user_id: 用户 ID
            replay_id: 录像 ID
        """
        user = self._storage.load_user_by_id(user_id)
        if user:
            if replay_id not in user.replay_ids:
                user.replay_ids.append(replay_id)
                self._storage.save_user(user)

    def get_user_replays(self, user_id: str) -> List[str]:
        """获取用户的录像列表。"""
        user = self._storage.load_user_by_id(user_id)
        return user.replay_ids if user else []

    def get_user_stats_display(self, user: Optional[User] = None) -> str:
        """获取用户战绩显示字符串。"""
        if user is None:
            user = self._current_user
        if user is None:
            return "游客"

        stats = user.get_total_stats()
        if stats["total_games"] == 0:
            return f"{user.username} (暂无战绩)"
        
        return (
            f"{user.username} "
            f"(总: {stats['total_games']}场, "
            f"胜: {stats['wins']}, "
            f"负: {stats['losses']}, "
            f"平: {stats['draws']})"
        )

    def _validate_username(self, username: str) -> bool:
        """验证用户名格式。"""
        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))
