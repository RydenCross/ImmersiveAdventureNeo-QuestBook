from __future__ import annotations

from pathlib import Path

import pytest

from generator.editor_recovery import EditorRecoveryStore
from generator.editor_service import EditorSession, handle_editor_api
from generator.modpack_content_scanner_contract import _synthetic_pack


def _session(tmp_path: Path) -> EditorSession:
    tmp_path.mkdir(parents=True, exist_ok=True)
    pack = tmp_path / "recovery.mrpack"
    _synthetic_pack(pack)
    return EditorSession.from_source(
        pack,
        workspace=tmp_path / "workspace",
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
    )


def _edit_title(session: EditorSession, title: str) -> None:
    session.apply(
        {
            "action": "update_quest",
            "target_id": session.document.quests[0].quest_id,
            "values": {"title": title},
        }
    )


def test_editor_session_autosaves_and_recovers_latest_edit(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _edit_title(session, "Recovered title")
    status = session.recovery_payload()
    assert status["autosave_available"] is True
    assert status["autosave"]["revision"] == 1

    replacement = _session(tmp_path / "replacement")
    replacement.recovery = EditorRecoveryStore(session.workspace)
    result = replacement.recover({})
    assert result["status"] == "pass"
    assert replacement.document.quests[0].title == "Recovered title"


def test_editor_session_restores_named_snapshot_and_resets_history(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _edit_title(session, "Checkpoint")
    snapshot = session.create_snapshot({"reason": "before bulk edit"})
    _edit_title(session, "Changed later")
    name = Path(str(snapshot["snapshot"]["path"])).name
    session.recover({"snapshot": name})
    assert session.document.quests[0].title == "Checkpoint"
    assert session.status()["undo_depth"] == 0
    assert session.status()["has_unsaved_changes"] is True


def test_editor_recovery_rejects_corrupt_or_unsafe_snapshots(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _edit_title(session, "Autosaved")
    session.recovery.autosave_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid recovery record"):
        session.recover({})
    with pytest.raises(ValueError, match="path components"):
        session.recover({"snapshot": "../outside.json"})


def test_editor_save_clears_autosave_but_preserves_snapshots(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _edit_title(session, "Saved")
    session.create_snapshot({"reason": "manual checkpoint"})
    assert session.recovery.autosave_path.is_file()
    session.save("project.json")
    assert not session.recovery.autosave_path.exists()
    assert session.recovery.status()["snapshot_count"] == 1


def test_editor_recovery_api_routes(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _edit_title(session, "API recovery")
    status = handle_editor_api(session, "GET", "/api/v1/recovery")
    snapshot = handle_editor_api(
        session, "POST", "/api/v1/snapshot", {"reason": "API snapshot"}
    )
    restored = handle_editor_api(session, "POST", "/api/v1/recover", {})
    discarded = handle_editor_api(
        session,
        "POST",
        "/api/v1/discard-recovery",
        {"keep_snapshots": True},
    )
    assert status.status_code == 200
    assert snapshot.status_code == 200
    assert restored.status_code == 200
    assert discarded.status_code == 200
    assert discarded.payload["recovery"]["autosave_available"] is False
