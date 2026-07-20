from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable, Mapping

from generator.editor_model import EditorDocument, build_editor_document, validate_editor_document
from generator.modpack_content_scanner import scan_modpack_content
from generator.modpack_scanner import scan_modpack
from generator.progression_planner import MAX_TARGET_QUESTS, plan_quest_blueprint
from generator.quest_description_generator import DESCRIPTION_STYLES, plan_quest_descriptions
from generator.reward_planner import REWARD_POLICIES, plan_quest_rewards

JOB_STATES = ("queued", "running", "completed", "failed", "cancelled")
MAX_RETAINED_JOBS = 25


class EditorJobCancelled(RuntimeError):
    """Raised when a cooperative editor generation job is cancelled."""


ProgressCallback = Callable[[str, int, str], None]
JobRunner = Callable[[ProgressCallback, Event], Mapping[str, object]]


@dataclass(slots=True)
class _EditorJobRecord:
    job_id: str
    kind: str
    state: str = "queued"
    stage: str = "queued"
    progress: int = 0
    message: str = "Waiting to start"
    result: dict[str, object] | None = None
    error: str | None = None
    cancel_event: Event = field(default_factory=Event)
    finished_event: Event = field(default_factory=Event)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.job_id,
            "kind": self.kind,
            "state": self.state,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "cancellable": self.state in {"queued", "running"},
            "result": self.result,
            "error": self.error,
        }


class EditorJobManager:
    """Small in-process job queue for long-running local editor generation work."""

    def __init__(self, *, max_retained_jobs: int = MAX_RETAINED_JOBS) -> None:
        if max_retained_jobs < 1:
            raise ValueError("max_retained_jobs must be positive")
        self.max_retained_jobs = max_retained_jobs
        self._jobs: dict[str, _EditorJobRecord] = {}
        self._sequence = 0
        self._lock = Lock()

    def _record(self, job_id: str) -> _EditorJobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise ValueError(f"unknown editor job: {job_id}") from exc

    def _prune(self) -> None:
        completed = [
            record
            for record in self._jobs.values()
            if record.state in {"completed", "failed", "cancelled"}
        ]
        excess = len(self._jobs) - self.max_retained_jobs
        for record in completed[: max(0, excess)]:
            self._jobs.pop(record.job_id, None)

    def submit(self, kind: str, runner: JobRunner) -> dict[str, object]:
        clean_kind = kind.strip()
        if not clean_kind:
            raise ValueError("job kind is required")
        with self._lock:
            self._sequence += 1
            job_id = f"job-{self._sequence:06d}"
            record = _EditorJobRecord(job_id=job_id, kind=clean_kind)
            self._jobs[job_id] = record
            self._prune()

        thread = Thread(
            target=self._run,
            args=(record, runner),
            daemon=True,
            name=f"editor-{job_id}",
        )
        thread.start()
        return record.to_dict()

    def _run(self, record: _EditorJobRecord, runner: JobRunner) -> None:
        def progress(stage: str, percent: int, message: str) -> None:
            if record.cancel_event.is_set():
                raise EditorJobCancelled("editor job was cancelled")
            bounded = min(100, max(0, int(percent)))
            with self._lock:
                record.state = "running"
                record.stage = stage
                record.progress = max(record.progress, bounded)
                record.message = message

        try:
            progress("starting", 1, "Starting generation")
            result = dict(runner(progress, record.cancel_event))
            with self._lock:
                record.state = "completed"
                record.stage = "completed"
                record.progress = 100
                record.message = "Generation completed"
                record.result = result
        except EditorJobCancelled as exc:
            with self._lock:
                record.state = "cancelled"
                record.stage = "cancelled"
                record.message = str(exc)
                record.error = None
        except Exception as exc:
            with self._lock:
                record.state = "failed"
                record.stage = "failed"
                record.message = "Generation failed"
                record.error = str(exc)
        finally:
            record.finished_event.set()

    def status(self, job_id: str) -> dict[str, object]:
        with self._lock:
            return self._record(job_id).to_dict()

    def list(self) -> dict[str, object]:
        with self._lock:
            jobs = [record.to_dict() for record in self._jobs.values()]
        return {
            "status": "pass",
            "jobs": jobs,
            "active_jobs": sum(job["state"] in {"queued", "running"} for job in jobs),
            "retained_jobs": len(jobs),
            "max_retained_jobs": self.max_retained_jobs,
        }

    def cancel(self, job_id: str) -> dict[str, object]:
        with self._lock:
            record = self._record(job_id)
            if record.state not in {"queued", "running"}:
                raise ValueError(f"editor job is not cancellable: {job_id}")
            record.cancel_event.set()
            record.message = "Cancellation requested"
            return record.to_dict()

    def wait(self, job_id: str, timeout: float | None = None) -> dict[str, object]:
        with self._lock:
            record = self._record(job_id)
            finished = record.finished_event
        if not finished.wait(timeout):
            raise TimeoutError(f"editor job did not finish: {job_id}")
        return self.status(job_id)


def _check_cancelled(cancel_event: Event) -> None:
    if cancel_event.is_set():
        raise EditorJobCancelled("editor job was cancelled")


def generate_editor_document_staged(
    source: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    description_style: str = "guided",
    reward_policy: str = "unassigned",
    progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> EditorDocument:
    """Generate an editor document in observable, cooperatively cancellable stages."""

    if description_style not in DESCRIPTION_STYLES:
        raise ValueError("unsupported description style")
    if reward_policy != "unassigned" and reward_policy not in REWARD_POLICIES:
        raise ValueError("unsupported reward policy")
    if chapter_size <= 0:
        raise ValueError("chapter_size must be positive")
    if target_quests is not None and target_quests <= 0:
        raise ValueError("target_quests must be positive")

    notify = progress or (lambda _stage, _percent, _message: None)
    cancellation = cancel_event or Event()

    notify("pack-profile", 10, "Reading modpack metadata")
    profile = scan_modpack(Path(source))
    _check_cancelled(cancellation)
    if profile.errors:
        raise ValueError("modpack scan failed: " + "; ".join(profile.errors))

    requested = target_quests
    if requested is None:
        requested = int(profile.quest_target.get("target", 0) or 25)
    requested = min(MAX_TARGET_QUESTS, max(1, requested))

    notify("content-scan", 35, "Scanning recipes, advancements, tags, and registries")
    content = scan_modpack_content(Path(source), candidate_limit=requested)
    _check_cancelled(cancellation)
    if content.errors:
        raise ValueError("content scan failed: " + "; ".join(content.errors))

    notify("progression", 58, "Planning chapters and prerequisite-safe quests")
    blueprint = plan_quest_blueprint(
        profile,
        content,
        target_quests=requested,
        chapter_size=chapter_size,
    )
    _check_cancelled(cancellation)
    if not blueprint.is_clean:
        raise ValueError("progression planning failed: " + "; ".join(blueprint.errors))

    notify("descriptions", 76, "Generating grounded quest instructions")
    description_plan = plan_quest_descriptions(blueprint, style=description_style)
    _check_cancelled(cancellation)
    if not description_plan.is_clean:
        raise ValueError("description generation failed: " + "; ".join(description_plan.errors))
    blueprint = description_plan.blueprint

    if reward_policy != "unassigned":
        notify("rewards", 88, "Planning quest reward decisions")
        reward_plan = plan_quest_rewards(blueprint, policy=reward_policy)
        _check_cancelled(cancellation)
        if not reward_plan.is_clean:
            raise ValueError("reward planning failed: " + "; ".join(reward_plan.errors))
        blueprint = reward_plan.blueprint

    notify("editor-model", 96, "Building and validating the editor graph")
    document = build_editor_document(blueprint)
    validation = validate_editor_document(document)
    if document.errors or validation.errors:
        errors = tuple(document.errors) + validation.errors
        raise ValueError("generated editor document is invalid: " + "; ".join(errors))
    _check_cancelled(cancellation)
    return document
