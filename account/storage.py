"""Account storage - 账户数据持久化。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from account.models import User


class AccountStorage:
    """账户存储实现。
    
    使用 JSON 文件存储用户数据。
    """

    DEFAULT_PATH = "data/users.json"

    def __init__(self, file_path: str = DEFAULT_PATH) -> None:
        """初始化存储。
        
        Args:
            file_path: 用户数据文件路径
        """
        self._file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """确保数据文件和目录存在。"""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._save_data({"users": {}})

    def _load_data(self) -> Dict:
        """加载数据文件。"""
        try:
            return json.loads(self._file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"users": {}}

    def _save_data(self, data: Dict) -> None:
        """保存数据文件。"""
        self._file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def save_user(self, user: User) -> None:
        """保存用户。"""
        data = self._load_data()
        data["users"][user.username.lower()] = user.to_dict()
        self._save_data(data)

    def load_user(self, username: str) -> Optional[User]:
        """按用户名加载用户。"""
        data = self._load_data()
        user_data = data["users"].get(username.lower())
        if user_data:
            return User.from_dict(user_data)
        return None

    def load_user_by_id(self, user_id: str) -> Optional[User]:
        """按用户 ID 加载用户。"""
        data = self._load_data()
        for user_data in data["users"].values():
            if user_data.get("user_id") == user_id:
                return User.from_dict(user_data)
        return None

    def user_exists(self, username: str) -> bool:
        """检查用户名是否存在。"""
        data = self._load_data()
        return username.lower() in data["users"]

    def load_all_users(self) -> Dict[str, User]:
        """加载所有用户。"""
        data = self._load_data()
        return {
            k: User.from_dict(v) 
            for k, v in data["users"].items()
        }

    def delete_user(self, username: str) -> bool:
        """删除用户。"""
        data = self._load_data()
        if username.lower() in data["users"]:
            del data["users"][username.lower()]
            self._save_data(data)
            return True
        return False
