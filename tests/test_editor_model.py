from dataclasses import replace
import json
from pathlib import Path

from generator.editor_model import (
    EDITOR_SCHEMA_VERSION,
    EditorDocument,
    EditorEdge,
    EditorOperation,
    apply_editor_operation,
    build_editor_document,
    editor_document_to_blueprint,
    generate_editor_model,
    validate_editor_document,
)
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.quest_description_generator import plan_quest_descriptions


def _document(tmp_path: Path) -> EditorDocument:
    pack = tmp_path / "editor.mrpack"
    _synthetic_pack(pack)
    return generate_editor_model(pack, target_quests=4, chapter_size=10)


def test_editor_document_serializes_and_restores(tmp_path: Path) -> None:
    document = _document(tmp_path)
    restored = EditorDocument.from_dict(json.loads(document.format_json()))
    assert document.schema_version == EDITOR_SCHEMA_VERSION
    assert restored.to_dict() == document.to_dict()
    assert validate_editor_document(restored).is_clean


def test_editor_document_round_trips_blueprint(tmp_path: Path) -> None:
    pack = tmp_path / "roundtrip.mrpack"
    _synthetic_pack(pack)
    blueprint = plan_quest_descriptions(
        generate_quest_blueprint(pack, target_quests=4, chapter_size=10),
        style="guided",
    ).blueprint
    document = build_editor_document(blueprint)
    restored = editor_document_to_blueprint(document)
    assert restored.format_json() == blueprint.format_json()


def test_editor_operation_is_reversible_and_tracks_revision(tmp_path: Path) -> None:
    document = _document(tmp_path)
    quest = document.quests[0]
    transaction = apply_editor_operation(
        document,
        EditorOperation.create("update_quest", quest.quest_id, title="New title"),
    )
    assert transaction.is_clean
    assert transaction.after.revision == 1
    assert transaction.after.change_log[-1].changed_fields == ("title",)
    assert transaction.after.quests[0].title == "New title"
    assert transaction.undo() == document
    assert transaction.redo() == transaction.after


def test_editor_rejects_cycle_and_dangling_edge(tmp_path: Path) -> None:
    document = _document(tmp_path)
    edge = document.edges[0]
    cycle = apply_editor_operation(
        document,
        EditorOperation.create(
            "set_dependency",
            edge.prerequisite_quest,
            prerequisite_id=edge.dependent_quest,
            enabled=True,
        ),
    )
    assert not cycle.is_clean
    assert any("cycle" in error for error in cycle.errors)

    dangling = replace(
        document,
        edges=document.edges + (EditorEdge.create("missing:quest", document.quests[0].quest_id),),
    )
    validation = validate_editor_document(dangling)
    assert not validation.is_clean
    assert any("unknown prerequisite quest" in error for error in validation.errors)


def test_editor_rejects_invalid_operation(tmp_path: Path) -> None:
    document = _document(tmp_path)
    result = apply_editor_operation(
        document,
        EditorOperation.create("delete_everything", document.quests[0].quest_id),
    )
    assert not result.is_clean
    assert result.after == document
