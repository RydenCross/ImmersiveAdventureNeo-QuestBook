from __future__ import annotations

import json

from content import create_project
from generator.cli import main
from generator.task_audit import audit_tasks, run_task_audit


def test_checked_in_tasks_pass_integrity_audit() -> None:
    result = run_task_audit()
    assert result.is_clean
    assert result.task_count == 673
    assert result.tasked_quests == 656
    assert result.task_types == {"advancement": 21, "checkmark": 295, "item": 357}


def test_audit_detects_duplicate_task_ids() -> None:
    project = create_project()
    tasks = [task for quest in project.quests for task in quest.tasks]
    tasks[1].id = tasks[0].id
    result = audit_tasks(project)
    assert not result.is_clean
    assert len(result.duplicate_task_ids) == 1


def test_audit_detects_invalid_item_task_data() -> None:
    project = create_project()
    task = next(task for quest in project.quests for task in quest.tasks if task.type.value == "item")
    task.data["count"] = 0
    result = audit_tasks(project)
    assert not result.is_clean
    assert "positive integer" in result.invalid_tasks[0]


def test_audit_detects_taskless_quest() -> None:
    project = create_project()
    project.quests[0].tasks.clear()
    result = audit_tasks(project)
    assert not result.is_clean
    assert project.quests[0].id in result.taskless_quests


def test_cli_writes_task_audit_report(tmp_path) -> None:
    output = tmp_path / "task-audit.json"
    assert main(["task-audit", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["task_count"] == 673
