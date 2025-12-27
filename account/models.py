"""Account data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GameTypeRecord:
    """某游戏类型的战绩记录。"""
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    def to_dict(self) -> Dict:
        return {
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GameTypeRecord":
        return cls(
            total_games=data.get("total_games", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            draws=data.get("draws", 0)
        )


@dataclass
class User:
    """用户数据模型。"""
    user_id: str
    username: str
    password_hash: str
    created_at: str
    last_login: Optional[str] = None
    records: Dict[str, GameTypeRecord] = field(default_factory=dict)
    replay_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "records": {k: v.to_dict() for k, v in self.records.items()},
            "replay_ids": self.replay_ids
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        records = {}
        for k, v in data.get("records", {}).items():
            records[k] = GameTypeRecord.from_dict(v)
        
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password_hash=data["password_hash"],
            created_at=data["created_at"],
            last_login=data.get("last_login"),
            records=records,
            replay_ids=data.get("replay_ids", [])
        )

    def get_record(self, game_type: str) -> GameTypeRecord:
        """获取指定游戏类型的战绩。"""
        if game_type not in self.records:
            self.records[game_type] = GameTypeRecord()
        return self.records[game_type]

    def get_total_stats(self) -> Dict[str, int]:
        """获取总战绩统计。"""
        total = {"total_games": 0, "wins": 0, "losses": 0, "draws": 0}
        for record in self.records.values():
            total["total_games"] += record.total_games
            total["wins"] += record.wins
            total["losses"] += record.losses
            total["draws"] += record.draws
        return total


@dataclass
class Result:
    """操作结果封装。"""
    success: bool
    value: Optional[any] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, value: any = None) -> "Result":
        return cls(success=True, value=value)

    @classmethod
    def fail(cls, error: str) -> "Result":
        return cls(success=False, error=error)

    @property
    def is_success(self) -> bool:
        return self.success

    @property
    def is_failure(self) -> bool:
        return not self.success
