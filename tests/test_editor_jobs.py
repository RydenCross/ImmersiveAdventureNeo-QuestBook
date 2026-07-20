from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from threading import Event, Thread
from time import sleep
from urllib.parse import quote
from urllib.request import Request, urlopen

from generator.editor_jobs import EditorJobManager, generate_editor_document_staged
from generator.editor_service import EditorSession, create_editor_http_server
from generator.modpack_content_scanner_contract import _synthetic_pack


def _pack(tmp_path: Path, name: str = "jobs.mrpack") -> Path:
    path = tmp_path / name
    _synthetic_pack(path)
    return path


def test_staged_generation_reports_monotonic_progress(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    updates: list[tuple[str, int]] = []
    document = generate_editor_document_staged(
        pack,
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
        progress=lambda stage, percent, _message: updates.append((stage, percent)),
    )
    assert document.is_clean
    assert len(document.quests) == 4
    assert [percent for _stage, percent in updates] == sorted(
        percent for _stage, percent in updates
    )
    assert {stage for stage, _percent in updates} >= {
        "pack-profile",
        "content-scan",
        "progression",
        "descriptions",
        "rewards",
        "editor-model",
    }


def test_background_import_replaces_document_only_after_completion(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    data = pack.read_bytes()
    session = EditorSession.empty(workspace=tmp_path / "workspace")
    queued = session.queue_import_modpack(
        "background.mrpack",
        BytesIO(data),
        len(data),
        target_quests=4,
        chapter_size=10,
        reward_policy="conservative",
    )
    assert queued["state"] in {"queued", "running"}
    result = session.jobs.wait(str(queued["id"]), timeout=20)
    assert result["state"] == "completed"
    assert result["progress"] == 100
    assert len(session.document.quests) == 4
    assert session.status()["active_jobs"] == 0


def test_background_generation_failure_preserves_current_document(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "initial.mrpack")
    session = EditorSession.from_source(
        pack,
        workspace=tmp_path / "workspace",
        target_quests=4,
        chapter_size=10,
    )
    original = session.document.format_json()
    broken = session.workspace / "broken.zip"
    broken.write_bytes(b"not a zip")
    queued = session.queue_generate({"path": "broken.zip", "target_quests": 4})
    result = session.jobs.wait(str(queued["id"]), timeout=20)
    assert result["state"] == "failed"
    assert result["error"]
    assert session.document.format_json() == original


def test_job_cancellation_is_cooperative_and_terminal() -> None:
    manager = EditorJobManager()
    started = Event()

    def runner(progress, cancel_event):
        progress("waiting", 20, "Waiting for cancellation")
        started.set()
        while not cancel_event.is_set():
            sleep(0.01)
        progress("should-not-complete", 90, "Cancelled")
        return {"unexpected": True}

    queued = manager.submit("cancel-test", runner)
    assert started.wait(2)
    manager.cancel(str(queued["id"]))
    result = manager.wait(str(queued["id"]), timeout=2)
    assert result["state"] == "cancelled"
    assert result["result"] is None
    assert result["cancellable"] is False


def test_http_import_job_reports_progress_and_completes(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    data = pack.read_bytes()
    session = EditorSession.empty(workspace=tmp_path / "workspace")
    server = create_editor_http_server(session, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        request = Request(
            f"http://{host}:{port}/api/v1/import-job?target_quests=4&chapter_size=10&reward_policy=conservative",
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "X-File-Name": quote("Background Pack.mrpack"),
            },
            data=data,
        )
        with urlopen(request, timeout=20) as response:
            accepted = json.loads(response.read().decode("utf-8"))
        assert response.status == 202
        job_id = accepted["id"]
        final = None
        for _ in range(100):
            with urlopen(f"http://{host}:{port}/api/v1/jobs/{job_id}", timeout=10) as response:
                final = json.loads(response.read().decode("utf-8"))
            if final["state"] not in {"queued", "running"}:
                break
            sleep(0.05)
        assert final is not None
        assert final["state"] == "completed"
        assert final["result"]["filename"] == "Background Pack.mrpack"
        assert session.status()["quests"] == 4
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
