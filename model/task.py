from dataclasses import dataclass, field
from typing import Any
from model.enums import TaskType

@dataclass(slots=True)
class Task:
    id: str
    type: TaskType
    data: dict[str, Any] = field(default_factory=dict)
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Task id cannot be empty.")
        if not isinstance(self.type, TaskType):
            self.type = TaskType(self.type)
