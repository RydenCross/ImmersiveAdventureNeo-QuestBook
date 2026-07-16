from enum import Enum


class Level(Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


def log(level: Level, message: str) -> None:
    print(f"[{level.value}] {message}")