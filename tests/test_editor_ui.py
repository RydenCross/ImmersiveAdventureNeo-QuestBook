from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from threading import Thread
from urllib.parse import quote
from urllib.request import Request, urlopen

import pytest

from generator.editor_service import MAX_UPLOAD_BYTES, EditorSession, create_editor_http_server
from generator.editor_ui import EDITOR_HTML
from generator.modpack_content_scanner_contract import _synthetic_pack


def _pack_bytes(tmp_path: Path) -> bytes:
    path = tmp_path / "visual.mrpack"
    _synthetic_pack(path)
    return path.read_bytes()


def _session(tmp_path: Path) -> EditorSession:
    pack = tmp_path / "initial.mrpack"
    _synthetic_pack(pack)
    return EditorSession.from_source(
        pack,
        workspace=tmp_path / "workspace",
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
    )


def test_empty_editor_session_waits_for_browser_import(tmp_path: Path) -> None:
    session = EditorSession.empty(workspace=tmp_path / "empty-workspace")
    assert session.document.is_clean
    assert session.status()["quests"] == 0
    assert session.document.source_format == "empty"


def test_import_modpack_replaces_document_and_records_digest(tmp_path: Path) -> None:
    session = _session(tmp_path)
    data = _pack_bytes(tmp_path)
    result = session.import_modpack(
        "replacement.mrpack",
        BytesIO(data),
        len(data),
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
    )
    assert result["status"] == "pass"
    assert result["bytes"] == len(data)
    assert len(str(result["sha256"])) == 64
    assert str(result["path"]).startswith("imports/")
    assert (session.workspace / str(result["path"])).is_file()
    assert len(session.document.quests) == 4
    assert session.status()["undo_depth"] == 0


def test_import_modpack_rejects_unsafe_names_and_sizes(tmp_path: Path) -> None:
    session = _session(tmp_path)
    data = _pack_bytes(tmp_path)
    with pytest.raises(ValueError, match="path components"):
        session.import_modpack("../unsafe.mrpack", BytesIO(data), len(data))
    with pytest.raises(ValueError, match=".zip or .mrpack"):
        session.import_modpack("unsafe.jar", BytesIO(data), len(data))
    with pytest.raises(ValueError, match="upload limit"):
        session.import_modpack("large.zip", BytesIO(b"x"), MAX_UPLOAD_BYTES + 1)


def test_editor_http_upload_imports_modpack(tmp_path: Path) -> None:
    session = _session(tmp_path)
    data = _pack_bytes(tmp_path)
    server = create_editor_http_server(session, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        request = Request(
            f"http://{host}:{port}/api/v1/import?target_quests=4&chapter_size=10&reward_policy=conservative",
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "X-File-Name": quote("Dropped Pack.mrpack"),
            },
            data=data,
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["filename"] == "Dropped Pack.mrpack"
        assert payload["session"]["quests"] == 4
        assert payload["session"]["dependency_edges"] == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_editor_html_contains_drop_import_and_interactive_graph() -> None:
    required = (
        'id="drop-zone"',
        'id="file-input"',
        '/api/v1/import',
        'id="graph"',
        'id="edges"',
        'id="nodes"',
        "startNodeDrag",
        "move_quest",
        "set_dependency",
        "Link prerequisite",
        "fitGraph",
        'id="reward-decision"',
        'id="reward-list"',
        'id="add-reward"',
        "readRewards",
        "reward_decision",
        'id="objective-type"',
        'id="objective-id"',
        'id="objective-count"',
        'id="quest-difficulty"',
        'id="quest-optional"',
        'id="quest-hidden"',
        "objective,difficulty",
        'id="regenerate-quest"',
        'id="regenerate-chapter"',
        'id="preserve-manual"',
        "regenerateSelection",
        "'/regenerate'",
    )
    assert all(token in EDITOR_HTML for token in required)


def test_editor_ui_exposes_pre_generation_analysis_dashboard() -> None:
    from generator.editor_ui import EDITOR_HTML

    assert 'id="analysis-panel"' in EDITOR_HTML
    assert 'Modpack analysis' in EDITOR_HTML
    assert 'Quest density' in EDITOR_HTML
    assert 'Lore style' in EDITOR_HTML
    assert 'Generate quest book' in EDITOR_HTML
    assert "`${api}/analyze`" in EDITOR_HTML
    assert "'/generate-job'" in EDITOR_HTML
