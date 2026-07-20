from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

import pytest

from generator.editor_service import (
    EditorSession,
    create_editor_http_server,
    handle_editor_api,
)
from generator.modpack_content_scanner_contract import _synthetic_pack


def _session(tmp_path: Path) -> EditorSession:
    pack = tmp_path / "service.mrpack"
    _synthetic_pack(pack)
    return EditorSession.from_source(
        pack,
        workspace=tmp_path / "workspace",
        target_quests=4,
        chapter_size=10,
        description_style="guided",
        reward_policy="conservative",
    )


def test_editor_session_applies_undoes_and_redoes_operations(tmp_path: Path) -> None:
    session = _session(tmp_path)
    quest = session.document.quests[0]
    result = session.apply(
        {
            "action": "update_quest",
            "target_id": quest.quest_id,
            "values": {"title": "Edited through service"},
        }
    )
    assert result["status"] == "pass"
    assert session.document.revision == 1
    assert session.document.quests[0].title == "Edited through service"
    session.undo()
    assert session.document.revision == 0
    assert session.document.quests[0].title == quest.title
    session.redo()
    assert session.document.revision == 1
    assert session.document.quests[0].title == "Edited through service"


def test_editor_session_saves_and_opens_workspace_document(tmp_path: Path) -> None:
    session = _session(tmp_path)
    saved = session.save("models/editor.json")
    assert Path(str(saved["path"])).is_file()
    assert session.status()["has_unsaved_changes"] is False

    quest = session.document.quests[0]
    session.apply(
        {
            "action": "update_quest",
            "target_id": quest.quest_id,
            "values": {"title": "Temporary edit"},
        }
    )
    assert session.status()["has_unsaved_changes"] is True
    opened = session.open("models/editor.json")
    assert opened["status"] == "pass"
    assert session.document.revision == 0
    assert session.document.quests[0].title == quest.title
    assert session.status()["undo_depth"] == 0


def test_editor_session_rejects_workspace_escape(tmp_path: Path) -> None:
    session = _session(tmp_path)
    with pytest.raises(ValueError, match="inside the editor workspace"):
        session.save("../escaped.json")
    response = handle_editor_api(
        session,
        "POST",
        "/api/v1/export",
        {"destination": "../escaped-export"},
    )
    assert response.status_code == 400
    assert response.payload["status"] == "fail"


def test_editor_api_routes_validate_and_export(tmp_path: Path) -> None:
    session = _session(tmp_path)
    status = handle_editor_api(session, "GET", "/api/v1/status")
    assert status.status_code == 200
    assert status.payload["quests"] == 4

    quest = session.document.quests[0]
    operation = handle_editor_api(
        session,
        "POST",
        "/api/v1/operations",
        {
            "action": "move_quest",
            "target_id": quest.quest_id,
            "values": {
                "chapter_id": quest.chapter_id,
                "order": quest.order,
                "x": quest.x + 2,
                "y": quest.y + 3,
            },
        },
    )
    assert operation.status_code == 200
    validation = handle_editor_api(session, "GET", "/api/v1/validation")
    assert validation.payload["status"] == "pass"

    exported = handle_editor_api(
        session,
        "POST",
        "/api/v1/export",
        {"destination": "exports/ftbquests"},
    )
    assert exported.status_code == 200
    assert exported.payload["summary"]["quests"] == 4
    assert (session.workspace / "exports" / "ftbquests" / "quests" / "data.snbt").is_file()


def test_editor_http_server_serves_interface_and_json_api(tmp_path: Path) -> None:
    session = _session(tmp_path)
    server = create_editor_http_server(session, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        with urlopen(f"http://{host}:{port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert response.status == 200
        assert "FTB Quest Maker" in html

        with urlopen(f"http://{host}:{port}/api/v1/status", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["quests"] == 4

        request = Request(
            f"http://{host}:{port}/api/v1/save",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"path": "http-editor.json"}).encode("utf-8"),
        )
        with urlopen(request, timeout=5) as response:
            saved = json.loads(response.read().decode("utf-8"))
        assert saved["status"] == "pass"
        assert (session.workspace / "http-editor.json").is_file()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_editor_http_server_rejects_non_loopback_binding(tmp_path: Path) -> None:
    session = _session(tmp_path)
    with pytest.raises(ValueError, match="loopback"):
        create_editor_http_server(session, host="0.0.0.0", port=0)


def test_modpack_analysis_stores_archive_and_returns_profile(tmp_path: Path) -> None:
    from io import BytesIO

    pack = tmp_path / "analysis.mrpack"
    _synthetic_pack(pack)
    data = pack.read_bytes()
    session = EditorSession.empty(workspace=tmp_path / "workspace")

    result = session.analyze_modpack("Analysis Pack.mrpack", BytesIO(data), len(data))

    assert result["status"] == "pass"
    assert result["filename"] == "Analysis Pack.mrpack"
    assert result["profile"]["status"] == "pass"
    assert result["profile"]["summary"]["mods"] > 0
    assert result["profile"]["summary"]["recommended_quests"]["target"] > 0
    assert (session.workspace / str(result["path"])).is_file()


def test_http_analyze_endpoint_returns_dashboard_profile(tmp_path: Path) -> None:
    from urllib.parse import quote

    pack = tmp_path / "analysis-http.mrpack"
    _synthetic_pack(pack)
    session = EditorSession.empty(workspace=tmp_path / "workspace")
    server = create_editor_http_server(session, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        request = Request(
            f"http://{host}:{port}/api/v1/analyze",
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "X-File-Name": quote("Dashboard Pack.mrpack"),
            },
            data=pack.read_bytes(),
        )
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["profile"]["pack"]["minecraft"]
        assert payload["profile"]["summary"]["category_counts"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_selective_regeneration_preserves_manual_quest_fields(tmp_path: Path) -> None:
    session = _session(tmp_path)
    quest = session.document.quests[0]
    original_title = quest.title
    session.apply({
        "action": "update_quest",
        "target_id": quest.quest_id,
        "values": {"title": "My handcrafted title"},
    })

    preserved = session.regenerate({
        "scope": "quest",
        "target_id": quest.quest_id,
        "preserve_manual": True,
        "target_quests": 4,
        "chapter_size": 10,
        "reward_policy": "conservative",
    })
    assert preserved["status"] == "pass"
    assert next(item for item in session.document.quests if item.quest_id == quest.quest_id).title == "My handcrafted title"
    assert session.status()["undo_depth"] == 2

    replaced = session.regenerate({
        "scope": "quest",
        "target_id": quest.quest_id,
        "preserve_manual": False,
        "target_quests": 4,
        "chapter_size": 10,
        "reward_policy": "conservative",
    })
    assert replaced["updated_quests"] >= 1
    assert next(item for item in session.document.quests if item.quest_id == quest.quest_id).title == original_title


def test_regeneration_api_supports_chapter_scope_and_rejects_unknown_target(tmp_path: Path) -> None:
    session = _session(tmp_path)
    chapter = session.document.chapters[0]
    response = handle_editor_api(session, "POST", "/api/v1/regenerate", {
        "scope": "chapter",
        "target_id": chapter.chapter_id,
        "preserve_manual": True,
        "chapter_size": 10,
        "reward_policy": "conservative",
    })
    assert response.status_code == 200
    assert response.payload["scope"] == "chapter"

    missing = handle_editor_api(session, "POST", "/api/v1/regenerate", {
        "scope": "quest", "target_id": "missing"
    })
    assert missing.status_code == 400
    assert "unknown quest" in str(missing.payload["error"])
