from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import re

from content import create_project
from model import Project
from model.enums import TaskType

_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


@dataclass(frozen=True, slots=True)
class TaskAudit:
    task_count: int
    tasked_quests: int
    task_types: Counter[str]
    duplicate_task_ids: tuple[str, ...]
    invalid_tasks: tuple[str, ...]
    taskless_quests: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.duplicate_task_ids and not self.invalid_tasks and not self.taskless_quests

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "task_count": self.task_count,
            "tasked_quests": self.tasked_quests,
            "task_types": dict(sorted(self.task_types.items())),
            "duplicate_task_ids": list(self.duplicate_task_ids),
            "invalid_tasks": list(self.invalid_tasks),
            "taskless_quests": list(self.taskless_quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        task_summary = (
            ", ".join(f"{name}={count}" for name, count in sorted(self.task_types.items()))
            or "none"
        )
        lines = [
            f"Task integrity audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Tasks: {self.task_count} across {self.tasked_quests} quest(s).",
            f"Task types: {task_summary}.",
            f"Duplicate task IDs: {len(self.duplicate_task_ids)}.",
            f"Invalid task definitions: {len(self.invalid_tasks)}.",
            f"Taskless quests: {len(self.taskless_quests)}.",
        ]
        lines.extend(f"Duplicate task ID: {value}" for value in self.duplicate_task_ids)
        lines.extend(f"Invalid task: {value}" for value in self.invalid_tasks)
        lines.extend(f"Taskless quest: {value}" for value in self.taskless_quests)
        return "\n".join(lines)


def _positive_count(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def _item_task_error(quest_id: str, task: object) -> str | None:
    item = task.data.get("item")
    if not isinstance(item, dict):
        return f"{quest_id}/{task.id}: item task is missing an item object"
    item_id = item.get("id")
    if not isinstance(item_id, str) or not _RESOURCE_LOCATION.fullmatch(item_id):
        return f"{quest_id}/{task.id}: invalid item id {item_id!r}"
    count = task.data.get("count", item.get("count", 1))
    if not _positive_count(count):
        return f"{quest_id}/{task.id}: item count must be a positive integer"
    return None


def _advancement_task_error(quest_id: str, task: object) -> str | None:
    advancement = task.data.get("advancement")
    if not isinstance(advancement, str) or not _RESOURCE_LOCATION.fullmatch(advancement):
        return f"{quest_id}/{task.id}: invalid advancement id {advancement!r}"
    criterion = task.data.get("criterion", "")
    if not isinstance(criterion, str):
        return f"{quest_id}/{task.id}: advancement criterion must be a string"
    return None


def audit_tasks(project: Project) -> TaskAudit:
    task_ids: defaultdict[str, list[str]] = defaultdict(list)
    invalid: list[str] = []
    task_types: Counter[str] = Counter()
    tasked_quests = 0
    taskless: list[str] = []

    for quest in project.quests:
        if quest.tasks:
            tasked_quests += 1
        else:
            taskless.append(quest.id)
        for task in quest.tasks:
            task_ids[task.id].append(quest.id)
            task_types[task.type.value] += 1
            if not task.id:
                invalid.append(f"{quest.id}: task is missing an ID")
            if task.type is TaskType.ITEM:
                error = _item_task_error(quest.id, task)
                if error:
                    invalid.append(error)
            elif task.type is TaskType.ADVANCEMENT:
                error = _advancement_task_error(quest.id, task)
                if error:
                    invalid.append(error)
            elif task.type is TaskType.CHECKMARK and task.data:
                invalid.append(f"{quest.id}/{task.id}: checkmark task must not contain data")
            elif task.type is TaskType.CUSTOM and not task.data:
                invalid.append(f"{quest.id}/{task.id}: custom task has no data")

    duplicates = tuple(
        sorted(
            f"{task_id} ({', '.join(sorted(quest_ids))})"
            for task_id, quest_ids in task_ids.items()
            if task_id and len(quest_ids) > 1
        )
    )

    return TaskAudit(
        task_count=sum(task_types.values()),
        tasked_quests=tasked_quests,
        task_types=task_types,
        duplicate_task_ids=duplicates,
        invalid_tasks=tuple(sorted(invalid)),
        taskless_quests=tuple(sorted(taskless)),
    )


def run_task_audit() -> TaskAudit:
    return audit_tasks(create_project())
