from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import sleep

from generator.editor_jobs import EditorJobManager, generate_editor_document_staged
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_ui import EDITOR_HTML
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorJobsContract:
    staged_progress: bool
    background_import: bool
    atomic_document_replacement: bool
    cooperative_cancellation: bool
    failure_isolation: bool
    job_api_routes: bool
    visual_progress_controls: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.staged_progress,
                self.background_import,
                self.atomic_document_replacement,
                self.cooperative_cancellation,
                self.failure_isolation,
                self.job_api_routes,
                self.visual_progress_controls,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "staged_progress": self.staged_progress,
            "background_import": self.background_import,
            "atomic_document_replacement": self.atomic_document_replacement,
            "cooperative_cancellation": self.cooperative_cancellation,
            "failure_isolation": self.failure_isolation,
            "job_api_routes": self.job_api_routes,
            "visual_progress_controls": self.visual_progress_controls,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Editor background jobs contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Staged progress: {'PASS' if self.staged_progress else 'FAIL'}.",
                f"Background import: {'PASS' if self.background_import else 'FAIL'}.",
                "Atomic document replacement: "
                f"{'PASS' if self.atomic_document_replacement else 'FAIL'}.",
                "Cooperative cancellation: "
                f"{'PASS' if self.cooperative_cancellation else 'FAIL'}.",
                f"Failure isolation: {'PASS' if self.failure_isolation else 'FAIL'}.",
                f"Job API routes: {'PASS' if self.job_api_routes else 'FAIL'}.",
                "Visual progress controls: "
                f"{'PASS' if self.visual_progress_controls else 'FAIL'}.",
            )
        )


def run_editor_jobs_contract() -> EditorJobsContract:
    with TemporaryDirectory(prefix="editor-jobs-contract-") as temporary:
        root = Path(temporary)
        pack = root / "jobs.mrpack"
        _synthetic_pack(pack)
        progress_updates: list[int] = []
        generated = generate_editor_document_staged(
            pack,
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
            progress=lambda _stage, percent, _message: progress_updates.append(percent),
        )
        staged_progress = bool(
            generated.is_clean
            and len(progress_updates) >= 6
            and progress_updates == sorted(progress_updates)
        )

        session = EditorSession.empty(workspace=root / "workspace")
        data = pack.read_bytes()
        queued = session.queue_import_modpack(
            "jobs.mrpack",
            BytesIO(data),
            len(data),
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        completed = session.jobs.wait(str(queued["id"]), timeout=20)
        background_import = completed["state"] == "completed" and len(session.document.quests) == 4
        atomic_document_replacement = bool(
            background_import
            and session.document.is_clean
            and not session.document.errors
        )

        manager = EditorJobManager()
        started = Event()

        def cancellable(progress, cancel_event):
            progress("waiting", 20, "Waiting")
            started.set()
            while not cancel_event.is_set():
                sleep(0.005)
            progress("cancelled", 80, "Cancelled")
            return {}

        cancel_job = manager.submit("contract-cancel", cancellable)
        started.wait(2)
        manager.cancel(str(cancel_job["id"]))
        cancelled = manager.wait(str(cancel_job["id"]), timeout=2)
        cooperative_cancellation = cancelled["state"] == "cancelled"

        original = session.document.format_json()
        broken = session.workspace / "broken.zip"
        broken.write_bytes(b"broken")
        failed_job = session.queue_generate({"path": "broken.zip", "target_quests": 4})
        failed = session.jobs.wait(str(failed_job["id"]), timeout=20)
        failure_isolation = bool(
            failed["state"] == "failed" and session.document.format_json() == original
        )

        list_response = handle_editor_api(session, "GET", "/api/v1/jobs")
        status_response = handle_editor_api(
            session,
            "GET",
            f"/api/v1/jobs/{completed['id']}",
        )
        job_api_routes = bool(
            list_response.status_code == 200
            and status_response.status_code == 200
            and status_response.payload.get("state") == "completed"
        )
        visual_progress_controls = all(
            token in EDITOR_HTML
            for token in (
                'id="job-panel"',
                'id="job-progress"',
                'id="job-cancel"',
                "/api/v1/import-job",
                "monitorJob",
            )
        )

        return EditorJobsContract(
            staged_progress=staged_progress,
            background_import=background_import,
            atomic_document_replacement=atomic_document_replacement,
            cooperative_cancellation=cooperative_cancellation,
            failure_isolation=failure_isolation,
            job_api_routes=job_api_routes,
            visual_progress_controls=visual_progress_controls,
        )
