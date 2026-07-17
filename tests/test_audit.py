from content import create_project
from generator.audit import audit_project
from generator.cli import main


def test_authored_content_audit_is_clean() -> None:
    audit = audit_project(create_project())

    assert audit.chapters == 13
    assert audit.quests == 656
    assert audit.optional_quests == 223
    assert audit.empty_descriptions == ()
    assert audit.taskless_quests == ()
    assert audit.duplicate_titles == ()
    assert sum(audit.task_types.values()) >= audit.quests


def test_audit_cli_reports_project_summary(capsys) -> None:
    assert main(["audit", "--strict"]) == 0
    output = capsys.readouterr().out

    assert "13 chapter(s), 656 quest(s), 223 optional" in output
    assert "Empty descriptions: 0" in output
    assert "Taskless quests: 0" in output
