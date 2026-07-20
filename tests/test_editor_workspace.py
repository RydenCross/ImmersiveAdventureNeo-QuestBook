from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from generator.editor_model import EditorOperation, validate_editor_document
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_workspace import apply_editor_batch, auto_layout_editor_document
from generator.modpack_content_scanner_contract import _synthetic_pack


def _session(tmp_path: Path) -> EditorSession:
    pack = tmp_path / "workspace.mrpack"
    _synthetic_pack(pack)
    return EditorSession.from_source(
        pack,
        workspace=tmp_path / "editor",
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
    )


def test_auto_layout_is_deterministic_and_dependency_safe(tmp_path: Path) -> None:
    session = _session(tmp_path)
    scrambled = replace(
        session.document,
        quests=tuple(replace(quest, x=9, y=index * 3) for index, quest in enumerate(session.document.quests)),
    )
    first = auto_layout_editor_document(scrambled)
    second = auto_layout_editor_document(scrambled)

    assert first.is_clean
    assert first.changed
    assert first.document.to_dict() == second.document.to_dict()
    assert not validate_editor_document(first.document).warnings
    positions = {quest.quest_id: quest.x for quest in first.document.quests}
    for edge in first.document.edges:
        assert positions[edge.prerequisite_quest] < positions[edge.dependent_quest]


def test_auto_layout_can_target_one_chapter(tmp_path: Path) -> None:
    session = _session(tmp_path)
    chapter = session.document.chapters[0].chapter_id
    unchanged = session.document.quests[-1]
    document = replace(
        session.document,
        quests=tuple(
            replace(quest, x=7, y=index + 7) if quest.quest_id != unchanged.quest_id else quest
            for index, quest in enumerate(session.document.quests)
        ),
    )
    result = auto_layout_editor_document(document, chapter_id=chapter)
    assert result.is_clean
    assert result.laid_out_chapters == (chapter,)
    assert result.document.revision == document.revision + 1


def test_editor_batch_is_atomic_and_reversible(tmp_path: Path) -> None:
    session = _session(tmp_path)
    quest_ids = [quest.quest_id for quest in session.document.quests[:2]]
    result = session.apply_batch(
        {
            "operations": [
                {
                    "action": "update_quest",
                    "target_id": quest_id,
                    "values": {"review_required": True},
                }
                for quest_id in quest_ids
            ]
        }
    )
    assert result["operation_count"] == 2
    assert session.status()["undo_depth"] == 1
    assert all(
        quest.review_required for quest in session.document.quests if quest.quest_id in quest_ids
    )
    session.undo()
    assert not any(
        quest.review_required for quest in session.document.quests if quest.quest_id in quest_ids
    )


def test_editor_batch_rolls_back_when_any_operation_fails(tmp_path: Path) -> None:
    session = _session(tmp_path)
    before = session.document
    operations = (
        EditorOperation.create(
            "update_quest", before.quests[0].quest_id, review_required=True
        ),
        EditorOperation.create("update_quest", "missing", review_required=True),
    )
    result = apply_editor_batch(before, operations)
    assert not result.is_clean
    assert result.after == before


def test_editor_workspace_api_routes(tmp_path: Path) -> None:
    session = _session(tmp_path)
    quest_id = session.document.quests[0].quest_id
    batch = handle_editor_api(
        session,
        "POST",
        "/api/v1/batch-operations",
        {
            "operations": [
                {
                    "action": "update_quest",
                    "target_id": quest_id,
                    "values": {"review_required": True},
                }
            ]
        },
    )
    layout = handle_editor_api(session, "POST", "/api/v1/auto-layout", {})
    assert batch.status_code == 200
    assert layout.status_code == 200
    assert layout.payload["status"] == "pass"
