"""Match module - 对局管理层。

提供对局控制、录像记录功能。
设计模式：观察者模式 - 对局事件通知多个观察者。
"""
from match.controller import MatchController, TurnResult, MatchResult
from match.recorder import GameRecorder, MoveRecord, RecordMetadata

__all__ = [
    "MatchController",
    "TurnResult",
    "MatchResult",
    "GameRecorder",
    "MoveRecord",
    "RecordMetadata",
]
