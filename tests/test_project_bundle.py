from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from threading import Thread
from urllib.parse import quote
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from generator.editor_model import generate_editor_model
from generator.editor_service import EditorSession, create_editor_http_server
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.project_bundle import (
    create_project_bundle,
    inspect_project_bundle,
    install_project_bundle,
    load_project_bundle,
)


def _document(tmp_path: Path):
    pack = tmp_path / "bundle.mrpack"
    _synthetic_pack(pack)
    return generate_editor_model(
        pack,
        target_quests=4,
        chapter_size=10,
        description_style="guided",
        reward_policy="conservative",
    )


def test_project_bundle_is_deterministic_and_round_trips(tmp_path: Path) -> None:
    document = _document(tmp_path)
    first = tmp_path / "first.ftbqproj"
    second = tmp_path / "second.ftbqproj"
    result = create_project_bundle(document, first, settings={"chapter_size": 10})
    other = create_project_bundle(document, second, settings={"chapter_size": 10})
    assert result.is_clean and other.is_clean
    assert first.read_bytes() == second.read_bytes()
    inspection = inspect_project_bundle(first)
    assert inspection.is_clean
    restored, restored_inspection = load_project_bundle(first)
    assert restored_inspection.is_clean
    assert restored.pack_name == document.pack_name
    assert restored.quest_count == document.quest_count
    assert restored.source_path == Path(document.source_path).name


def test_project_bundle_detects_tampered_payload(tmp_path: Path) -> None:
    document = _document(tmp_path)
    bundle = tmp_path / "tampered.ftbqproj"
    create_project_bundle(document, bundle)
    with ZipFile(bundle) as source:
        entries = {info.filename: source.read(info) for info in source.infolist()}
    entries["project/settings.json"] = b'{"tampered": true}\n'
    with ZipFile(bundle, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
    inspection = inspect_project_bundle(bundle)
    assert not inspection.is_clean
    assert inspection.changed_entries == ("project/settings.json",)


def test_project_bundle_installs_and_preserves_backup(tmp_path: Path) -> None:
    document = _document(tmp_path)
    bundle = tmp_path / "install.ftbqproj"
    create_project_bundle(document, bundle)
    instance = tmp_path / "instance"
    old = instance / "config" / "ftbquests"
    old.mkdir(parents=True)
    (old / "legacy.txt").write_text("legacy", encoding="utf-8")
    result = install_project_bundle(bundle, instance, force=True)
    assert result.is_clean
    assert result.installed_files >= 6
    assert (instance / "config" / "ftbquests" / "quests" / "data.snbt").is_file()
    assert result.backup
    assert (Path(result.backup) / "legacy.txt").read_text(encoding="utf-8") == "legacy"


def test_project_bundle_dry_run_does_not_modify_instance(tmp_path: Path) -> None:
    document = _document(tmp_path)
    bundle = tmp_path / "dry-run.ftbqproj"
    create_project_bundle(document, bundle)
    instance = tmp_path / "instance"
    instance.mkdir()
    result = install_project_bundle(bundle, instance, dry_run=True, force=True)
    assert result.is_clean
    assert result.dry_run
    assert not (instance / "config" / "ftbquests").exists()


def test_project_bundle_rejects_invalid_extension(tmp_path: Path) -> None:
    document = _document(tmp_path)
    result = create_project_bundle(document, tmp_path / "project.zip")
    assert not result.is_clean
    assert "extension" in result.errors[0]


def test_editor_session_imports_portable_bundle(tmp_path: Path) -> None:
    document = _document(tmp_path)
    bundle = tmp_path / "shared.ftbqproj"
    create_project_bundle(document, bundle)
    data = bundle.read_bytes()
    session = EditorSession.empty(workspace=tmp_path / "workspace")
    result = session.import_project_bundle("shared.ftbqproj", BytesIO(data), len(data))
    assert result["status"] == "pass"
    assert session.document.quest_count == document.quest_count
    assert result["bundle"]["status"] == "pass"


def test_http_project_bundle_upload_round_trip(tmp_path: Path) -> None:
    document = _document(tmp_path)
    bundle = tmp_path / "upload.ftbqproj"
    create_project_bundle(document, bundle)
    data = bundle.read_bytes()
    session = EditorSession.empty(workspace=tmp_path / "workspace")
    server = create_editor_http_server(session, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        request = Request(
            f"http://{host}:{port}/api/v1/project-bundle-import",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "X-File-Name": quote("upload.ftbqproj"),
            },
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["status"] == "pass"
        assert payload["bundle"]["status"] == "pass"
        assert session.document.quest_count == document.quest_count
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
