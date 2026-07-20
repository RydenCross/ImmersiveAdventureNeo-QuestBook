from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import BinaryIO, Mapping
from urllib.parse import parse_qs, unquote, urlparse
import webbrowser

from generator.editor_model import (
    EDITOR_SCHEMA_VERSION,
    EditorDocument,
    EditorOperation,
    apply_editor_operation,
    editor_document_to_blueprint,
    generate_editor_model,
    validate_editor_document,
)
from generator.editor_ui import EDITOR_HTML
from generator.editor_jobs import (
    EditorJobCancelled,
    EditorJobManager,
    generate_editor_document_staged,
)
from generator.editor_recovery import EditorRecoveryStore
from generator.editor_workspace import apply_editor_batch, auto_layout_editor_document
from generator.ftb_blueprint_exporter import DEFAULT_FTB_QUESTS_VERSION, export_quest_blueprint
from generator.instance_discovery import discover_modpack_instances
from generator.modpack_scanner import scan_modpack
from generator.output_writer import atomic_write_text
from generator.project_bundle import (
    BUNDLE_EXTENSION,
    MAX_BUNDLE_BYTES,
    create_project_bundle,
    install_project_bundle,
    load_project_bundle,
)
from generator.quest_description_generator import DESCRIPTION_STYLES
from generator.reward_planner import REWARD_POLICIES

EDITOR_API_VERSION = "v1"
DEFAULT_EDITOR_HOST = "127.0.0.1"
DEFAULT_EDITOR_PORT = 8765
DEFAULT_EDITOR_WORKSPACE = Path(".quest-editor")
DEFAULT_EDITOR_DOCUMENT = Path("quest-editor-model.json")
DEFAULT_EDITOR_EXPORT = Path("generated/ftbquests")
MAX_REQUEST_BYTES = 1_048_576
MAX_UPLOAD_BYTES = 1_073_741_824
IMPORT_EXTENSIONS = (".mrpack", ".zip")
UPLOAD_CHUNK_BYTES = 1_048_576


def _is_loopback_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _validated_import_name(filename: str) -> str:
    name = unquote(filename).strip()
    if not name or name in {".", ".."}:
        raise ValueError("uploaded modpack filename is required")
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("uploaded modpack filename must not contain path components")
    if any(ord(character) < 32 for character in name):
        raise ValueError("uploaded modpack filename contains control characters")
    if Path(name).suffix.casefold() not in IMPORT_EXTENSIONS:
        raise ValueError("uploaded modpack must be a .zip or .mrpack file")
    return name


def _validated_bundle_name(filename: str) -> str:
    name = unquote(filename).strip()
    if not name or name in {".", ".."}:
        raise ValueError("project bundle filename is required")
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("project bundle filename must not contain path components")
    if any(ord(character) < 32 for character in name):
        raise ValueError("project bundle filename contains control characters")
    if Path(name).suffix.casefold() != BUNDLE_EXTENSION:
        raise ValueError(f"project bundle must use the {BUNDLE_EXTENSION} extension")
    return name


def _integer_option(values: Mapping[str, list[str]], name: str, default: int | None) -> int | None:
    raw = values.get(name, ())
    if not raw or raw[0] == "":
        return default
    value = int(raw[0])
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _load_editor_document(path: Path) -> EditorDocument:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("editor document JSON must contain an object")
    document = EditorDocument.from_dict(payload)
    validation = validate_editor_document(document)
    if document.errors or validation.errors:
        errors = tuple(document.errors) + validation.errors
        raise ValueError("invalid editor document: " + "; ".join(errors))
    return document


@dataclass(frozen=True, slots=True)
class EditorServiceResponse:
    status_code: int
    payload: dict[str, object]

    def format_json(self) -> str:
        return json.dumps(self.payload, indent=2, sort_keys=True)


class EditorSession:
    """Thread-safe mutable session around the immutable editor document model."""

    def __init__(
        self,
        document: EditorDocument,
        *,
        workspace: Path,
        document_path: Path | None = None,
        saved_revision: int = -1,
    ) -> None:
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors = tuple(document.errors) + validation.errors
            raise ValueError("cannot start editor session: " + "; ".join(errors))
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.document = document
        self.document_path = document_path.resolve() if document_path else None
        self.saved_revision = saved_revision
        self.recovery = EditorRecoveryStore(self.workspace)
        self.jobs = EditorJobManager()
        self._undo: list[EditorDocument] = []
        self._redo: list[EditorDocument] = []
        self._lock = RLock()

    @classmethod
    def empty(
        cls,
        *,
        workspace: Path = DEFAULT_EDITOR_WORKSPACE,
    ) -> EditorSession:
        return cls(
            EditorDocument(
                schema_version=EDITOR_SCHEMA_VERSION,
                revision=0,
                source_path="",
                source_format="empty",
                pack_name="Untitled modpack",
                minecraft_version="",
                loader="",
                requested_quests=0,
                available_candidates=0,
                chapters=(),
                quests=(),
                edges=(),
            ),
            workspace=workspace,
        )

    @classmethod
    def from_source(
        cls,
        source: Path,
        *,
        workspace: Path = DEFAULT_EDITOR_WORKSPACE,
        target_quests: int | None = None,
        chapter_size: int = 40,
        description_style: str = "guided",
        reward_policy: str = "unassigned",
    ) -> EditorSession:
        source = Path(source)
        if source.suffix.casefold() == ".json" and source.is_file():
            document = _load_editor_document(source)
            return cls(
                document,
                workspace=workspace,
                document_path=source,
                saved_revision=document.revision,
            )
        document = generate_editor_model(
            source,
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        return cls(document, workspace=workspace)

    def _workspace_path(self, value: str | Path) -> Path:
        raw = Path(value)
        candidate = raw.resolve() if raw.is_absolute() else (self.workspace / raw).resolve()
        if not candidate.is_relative_to(self.workspace):
            raise ValueError("path must remain inside the editor workspace")
        return candidate

    def _replace_document(self, document: EditorDocument, *, reset_history: bool = False) -> None:
        self.document = document
        if reset_history:
            self._undo.clear()
            self._redo.clear()

    def _autosave(self, reason: str) -> None:
        self.recovery.autosave(self.document, reason=reason)

    def status(self) -> dict[str, object]:
        with self._lock:
            validation = validate_editor_document(self.document)
            return {
                "status": "pass" if validation.is_clean and not self.document.errors else "fail",
                "api_version": EDITOR_API_VERSION,
                "workspace": self.workspace.as_posix(),
                "document_path": self.document_path.as_posix() if self.document_path else None,
                "revision": self.document.revision,
                "saved_revision": self.saved_revision,
                "has_unsaved_changes": (
                    self.document.revision != self.saved_revision
                    or bool(self.document.dirty_entities)
                ),
                "undo_depth": len(self._undo),
                "redo_depth": len(self._redo),
                "chapters": len(self.document.chapters),
                "quests": len(self.document.quests),
                "dependency_edges": len(self.document.edges),
                "validation_errors": len(validation.errors),
                "validation_warnings": len(validation.warnings),
                "recovery": self.recovery.status(),
                "active_jobs": self.jobs.list()["active_jobs"],
            }

    def instances_payload(self) -> dict[str, object]:
        return discover_modpack_instances().to_dict()

    def document_payload(self) -> dict[str, object]:
        with self._lock:
            return self.document.to_dict()

    def validation_payload(self) -> dict[str, object]:
        with self._lock:
            return validate_editor_document(self.document).to_dict()

    def apply(self, payload: Mapping[str, object]) -> dict[str, object]:
        action = str(payload.get("action", ""))
        target_id = str(payload.get("target_id", ""))
        values = payload.get("values", {})
        if not isinstance(values, Mapping):
            raise ValueError("operation values must be an object")
        operation = EditorOperation.create(action, target_id, **dict(values))
        with self._lock:
            transaction = apply_editor_operation(self.document, operation)
            if not transaction.is_clean:
                raise ValueError("editor operation rejected: " + "; ".join(transaction.errors))
            self._undo.append(transaction.before)
            self._replace_document(transaction.after)
            self._redo.clear()
            self._autosave(f"operation:{operation.action}")
            return {
                "status": "pass",
                "operation": operation.to_dict(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def apply_batch(self, payload: Mapping[str, object]) -> dict[str, object]:
        raw_operations = payload.get("operations", ())
        if not isinstance(raw_operations, list):
            raise ValueError("operations must be an array")
        operations: list[EditorOperation] = []
        for index, raw in enumerate(raw_operations):
            if not isinstance(raw, Mapping):
                raise ValueError(f"operation {index + 1} must be an object")
            values = raw.get("values", {})
            if not isinstance(values, Mapping):
                raise ValueError(f"operation {index + 1} values must be an object")
            operations.append(
                EditorOperation.create(
                    str(raw.get("action", "")),
                    str(raw.get("target_id", "")),
                    **dict(values),
                )
            )
        with self._lock:
            transaction = apply_editor_batch(self.document, operations)
            if not transaction.is_clean:
                raise ValueError("editor batch rejected: " + "; ".join(transaction.errors))
            self._undo.append(transaction.before)
            self._replace_document(transaction.after)
            self._redo.clear()
            self._autosave("batch-operations")
            return {
                "status": "pass",
                "operations": [operation.to_dict() for operation in operations],
                "operation_count": len(operations),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def auto_layout(self, payload: Mapping[str, object]) -> dict[str, object]:
        chapter_value = payload.get("chapter_id")
        chapter_id = str(chapter_value) if chapter_value not in {None, ""} else None
        horizontal_spacing = int(payload.get("horizontal_spacing", 1))
        vertical_spacing = int(payload.get("vertical_spacing", 1))
        with self._lock:
            result = auto_layout_editor_document(
                self.document,
                chapter_id=chapter_id,
                horizontal_spacing=horizontal_spacing,
                vertical_spacing=vertical_spacing,
            )
            if not result.is_clean:
                raise ValueError("editor auto-layout failed: " + "; ".join(result.errors))
            if result.changed:
                self._undo.append(self.document)
                self._replace_document(result.document)
                self._redo.clear()
                self._autosave("auto-layout")
            return {
                "status": "pass",
                "changed": result.changed,
                "changed_quests": list(result.changed_quests),
                "laid_out_chapters": list(result.laid_out_chapters),
                "depth_levels": result.depth_levels,
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def undo(self) -> dict[str, object]:
        with self._lock:
            if not self._undo:
                raise ValueError("nothing to undo")
            previous = self._undo.pop()
            self._redo.append(self.document)
            self._replace_document(previous)
            self._autosave("undo")
            return {
                "status": "pass",
                "action": "undo",
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def redo(self) -> dict[str, object]:
        with self._lock:
            if not self._redo:
                raise ValueError("nothing to redo")
            following = self._redo.pop()
            self._undo.append(self.document)
            self._replace_document(following)
            self._autosave("redo")
            return {
                "status": "pass",
                "action": "redo",
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def save(self, value: str | Path | None = None) -> dict[str, object]:
        with self._lock:
            path = (
                self._workspace_path(value)
                if value is not None
                else self.document_path or self._workspace_path(DEFAULT_EDITOR_DOCUMENT)
            )
            if path.suffix.casefold() != ".json":
                raise ValueError("editor documents must be saved as .json files")
            cleaned = replace(self.document, dirty_entities=())
            atomic_write_text(path, cleaned.format_json() + "\n")
            self._replace_document(cleaned)
            self.document_path = path
            self.saved_revision = cleaned.revision
            self.recovery.clear_autosave()
            return {
                "status": "pass",
                "path": path.as_posix(),
                "revision": cleaned.revision,
                "bytes": path.stat().st_size,
                "session": self.status(),
            }

    def open(self, value: str | Path) -> dict[str, object]:
        path = self._workspace_path(value)
        if not path.is_file():
            raise ValueError(f"editor document does not exist: {path.as_posix()}")
        document = _load_editor_document(path)
        with self._lock:
            self._replace_document(document, reset_history=True)
            self.document_path = path
            self.saved_revision = document.revision
            self.recovery.clear_autosave()
            return {
                "status": "pass",
                "path": path.as_posix(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def generate(self, payload: Mapping[str, object]) -> dict[str, object]:
        source_value = str(payload.get("path", ""))
        if not source_value:
            raise ValueError("path is required")
        source = self._workspace_path(source_value)
        target_value = payload.get("target_quests")
        target_quests = int(target_value) if target_value is not None else None
        chapter_size = int(payload.get("chapter_size", 40))
        description_style = str(payload.get("description_style", "guided"))
        reward_policy = str(payload.get("reward_policy", "unassigned"))
        if description_style not in DESCRIPTION_STYLES:
            raise ValueError("unsupported description style")
        if reward_policy != "unassigned" and reward_policy not in REWARD_POLICIES:
            raise ValueError("unsupported reward policy")
        document = generate_editor_model(
            source,
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors = tuple(document.errors) + validation.errors
            raise ValueError("generated editor document is invalid: " + "; ".join(errors))
        with self._lock:
            self._replace_document(document, reset_history=True)
            self.document_path = None
            self.saved_revision = -1
            self._autosave("generate")
            return {
                "status": "pass",
                "source": source.as_posix(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def _store_import(
        self,
        filename: str,
        stream: BinaryIO,
        content_length: int,
    ) -> tuple[str, Path, int, str]:
        safe_name = _validated_import_name(filename)
        if content_length <= 0:
            raise ValueError("uploaded modpack is empty")
        if content_length > MAX_UPLOAD_BYTES:
            raise ValueError("uploaded modpack exceeds the editor upload limit")

        import_directory = self._workspace_path("imports")
        import_directory.mkdir(parents=True, exist_ok=True)
        digest = sha256()
        bytes_written = 0
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=import_directory,
                prefix=".upload-",
                suffix=".part",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                while bytes_written < content_length:
                    chunk = stream.read(min(UPLOAD_CHUNK_BYTES, content_length - bytes_written))
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > content_length or bytes_written > MAX_UPLOAD_BYTES:
                        raise ValueError("uploaded modpack exceeds the declared or allowed size")
                    digest.update(chunk)
                    temporary.write(chunk)
            if bytes_written != content_length:
                raise ValueError("uploaded modpack size does not match Content-Length")
            checksum = digest.hexdigest()
            destination = import_directory / f"{checksum[:16]}-{safe_name}"
            if destination.exists():
                temporary_path.unlink(missing_ok=True)
            else:
                os.replace(temporary_path, destination)
            temporary_path = None
            return safe_name, destination, bytes_written, checksum
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def import_project_bundle(
        self,
        filename: str,
        stream: BinaryIO,
        content_length: int,
    ) -> dict[str, object]:
        safe_name = _validated_bundle_name(filename)
        if content_length <= 0:
            raise ValueError("uploaded project bundle is empty")
        if content_length > MAX_BUNDLE_BYTES:
            raise ValueError("uploaded project bundle exceeds the editor limit")
        project_directory = self._workspace_path("projects")
        project_directory.mkdir(parents=True, exist_ok=True)
        digest = sha256()
        bytes_written = 0
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=project_directory,
                prefix=".bundle-",
                suffix=".part",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                while bytes_written < content_length:
                    chunk = stream.read(min(UPLOAD_CHUNK_BYTES, content_length - bytes_written))
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > content_length or bytes_written > MAX_BUNDLE_BYTES:
                        raise ValueError("uploaded project bundle exceeds the declared or allowed size")
                    digest.update(chunk)
                    temporary.write(chunk)
            if bytes_written != content_length:
                raise ValueError("uploaded project bundle size does not match Content-Length")
            checksum = digest.hexdigest()
            destination = project_directory / f"{checksum[:16]}-{safe_name}"
            if destination.exists():
                temporary_path.unlink(missing_ok=True)
            else:
                os.replace(temporary_path, destination)
            temporary_path = None
            document, inspection = load_project_bundle(destination)
            with self._lock:
                self._replace_document(document, reset_history=True)
                self.document_path = None
                self.saved_revision = -1
                self._autosave("bundle-import")
            return {
                "status": "pass",
                "filename": safe_name,
                "path": destination.relative_to(self.workspace).as_posix(),
                "bytes": bytes_written,
                "sha256": checksum,
                "bundle": inspection.to_dict(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _validate_generation_options(
        *,
        target_quests: int | None,
        chapter_size: int,
        description_style: str,
        reward_policy: str,
    ) -> None:
        if chapter_size <= 0:
            raise ValueError("chapter_size must be positive")
        if target_quests is not None and target_quests <= 0:
            raise ValueError("target_quests must be positive")
        if description_style not in DESCRIPTION_STYLES:
            raise ValueError("unsupported description style")
        if reward_policy != "unassigned" and reward_policy not in REWARD_POLICIES:
            raise ValueError("unsupported reward policy")

    def _commit_generated_document(self, document: EditorDocument, *, reason: str) -> None:
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors = tuple(document.errors) + validation.errors
            raise ValueError("generated editor document is invalid: " + "; ".join(errors))
        with self._lock:
            self._replace_document(document, reset_history=True)
            self.document_path = None
            self.saved_revision = -1
            self._autosave(reason)


    def analyze_modpack(self, filename: str, stream: BinaryIO, content_length: int) -> dict[str, object]:
        """Store an uploaded modpack and return a user-facing offline analysis profile."""
        safe_name, destination, bytes_written, checksum = self._store_import(
            filename, stream, content_length
        )
        try:
            profile = scan_modpack(destination)
        except (OSError, TypeError, ValueError):
            destination.unlink(missing_ok=True)
            raise
        if profile.errors:
            destination.unlink(missing_ok=True)
            raise ValueError("modpack scan failed: " + "; ".join(profile.errors))
        return {
            "status": "pass",
            "filename": safe_name,
            "path": destination.relative_to(self.workspace).as_posix(),
            "bytes": bytes_written,
            "sha256": checksum,
            "profile": profile.to_dict(),
        }

    def import_modpack(
        self,
        filename: str,
        stream: BinaryIO,
        content_length: int,
        *,
        target_quests: int | None = None,
        chapter_size: int = 40,
        description_style: str = "guided",
        reward_policy: str = "unassigned",
    ) -> dict[str, object]:
        self._validate_generation_options(
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        safe_name, destination, bytes_written, checksum = self._store_import(
            filename,
            stream,
            content_length,
        )
        try:
            document = generate_editor_model(
                destination,
                target_quests=target_quests,
                chapter_size=chapter_size,
                description_style=description_style,
                reward_policy=reward_policy,
            )
            self._commit_generated_document(document, reason="import")
        except (OSError, TypeError, ValueError):
            destination.unlink(missing_ok=True)
            raise
        return {
            "status": "pass",
            "filename": safe_name,
            "path": destination.relative_to(self.workspace).as_posix(),
            "bytes": bytes_written,
            "sha256": checksum,
            "session": self.status(),
            "document": self.document.to_dict(),
        }

    def _queue_source_generation(
        self,
        source: Path,
        *,
        kind: str,
        target_quests: int | None,
        chapter_size: int,
        description_style: str,
        reward_policy: str,
        reason: str,
        metadata: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        self._validate_generation_options(
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        if not source.exists():
            raise ValueError(f"modpack source does not exist: {source.as_posix()}")

        def runner(progress, cancel_event):
            document = generate_editor_document_staged(
                source,
                target_quests=target_quests,
                chapter_size=chapter_size,
                description_style=description_style,
                reward_policy=reward_policy,
                progress=progress,
                cancel_event=cancel_event,
            )
            if cancel_event.is_set():
                raise EditorJobCancelled("editor job was cancelled")
            self._commit_generated_document(document, reason=reason)
            result = {
                "source": source.relative_to(self.workspace).as_posix()
                if source.is_relative_to(self.workspace)
                else source.as_posix(),
                "session": self.status(),
            }
            if metadata:
                result.update(dict(metadata))
            return result

        return self.jobs.submit(kind, runner)

    def queue_generate(self, payload: Mapping[str, object]) -> dict[str, object]:
        source_value = str(payload.get("path", ""))
        if not source_value:
            raise ValueError("path is required")
        source = self._workspace_path(source_value)
        target_value = payload.get("target_quests")
        target_quests = int(target_value) if target_value is not None else None
        return self._queue_source_generation(
            source,
            kind="generate",
            target_quests=target_quests,
            chapter_size=int(payload.get("chapter_size", 40)),
            description_style=str(payload.get("description_style", "guided")),
            reward_policy=str(payload.get("reward_policy", "unassigned")),
            reason="background-generate",
        )

    def queue_import_modpack(
        self,
        filename: str,
        stream: BinaryIO,
        content_length: int,
        *,
        target_quests: int | None = None,
        chapter_size: int = 40,
        description_style: str = "guided",
        reward_policy: str = "unassigned",
    ) -> dict[str, object]:
        self._validate_generation_options(
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        safe_name, destination, bytes_written, checksum = self._store_import(
            filename,
            stream,
            content_length,
        )
        return self._queue_source_generation(
            destination,
            kind="import",
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
            reason="background-import",
            metadata={
                "filename": safe_name,
                "path": destination.relative_to(self.workspace).as_posix(),
                "bytes": bytes_written,
                "sha256": checksum,
            },
        )

    def jobs_payload(self) -> dict[str, object]:
        return self.jobs.list()

    def job_payload(self, job_id: str) -> dict[str, object]:
        return self.jobs.status(job_id)

    def cancel_job(self, job_id: str) -> dict[str, object]:
        return self.jobs.cancel(job_id)

    def recovery_payload(self) -> dict[str, object]:
        with self._lock:
            return self.recovery.status()

    def create_snapshot(self, payload: Mapping[str, object] | None = None) -> dict[str, object]:
        body = payload or {}
        reason = str(body.get("reason", "manual"))
        with self._lock:
            record = self.recovery.create_snapshot(self.document, reason=reason)
            return {
                "status": "pass",
                "snapshot": record.metadata(relative_to=self.workspace),
                "recovery": self.recovery.status(),
            }

    def recover(self, payload: Mapping[str, object] | None = None) -> dict[str, object]:
        body = payload or {}
        snapshot = str(body.get("snapshot", "")).strip()
        with self._lock:
            if self.document.dirty_entities:
                self.recovery.create_snapshot(self.document, reason="before-restore")
            record = (
                self.recovery.load_snapshot(snapshot)
                if snapshot
                else self.recovery.load_autosave()
            )
            self._replace_document(record.document, reset_history=True)
            self.document_path = None
            self.saved_revision = -1
            self._autosave("restored")
            return {
                "status": "pass",
                "restored": record.metadata(relative_to=self.workspace),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def discard_recovery(self, payload: Mapping[str, object] | None = None) -> dict[str, object]:
        body = payload or {}
        keep_snapshots = bool(body.get("keep_snapshots", True))
        with self._lock:
            self.recovery.discard(keep_snapshots=keep_snapshots)
            return {
                "status": "pass",
                "keep_snapshots": keep_snapshots,
                "recovery": self.recovery.status(),
            }

    def create_bundle(self, payload: Mapping[str, object] | None = None) -> dict[str, object]:
        body = payload or {}
        destination = str(body.get("destination", f"project{BUNDLE_EXTENSION}"))
        path = self._workspace_path(destination)
        settings = body.get("settings", {})
        if not isinstance(settings, Mapping):
            raise ValueError("bundle settings must be an object")
        with self._lock:
            result = create_project_bundle(
                self.document,
                path,
                settings=dict(settings),
                version=str(body.get("version", DEFAULT_FTB_QUESTS_VERSION)),
            )
            if not result.is_clean:
                raise ValueError("project bundle creation failed: " + "; ".join(result.errors))
            return result.to_dict()

    def open_bundle(self, payload: Mapping[str, object]) -> dict[str, object]:
        path = self._workspace_path(str(payload.get("path", "")))
        document, inspection = load_project_bundle(path)
        with self._lock:
            self._replace_document(document, reset_history=True)
            self.document_path = None
            self.saved_revision = -1
            self._autosave("open-bundle")
            return {
                "status": "pass",
                "bundle": inspection.to_dict(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

    def install_bundle(self, payload: Mapping[str, object]) -> dict[str, object]:
        instance_value = str(payload.get("instance", "")).strip()
        if not instance_value:
            raise ValueError("instance path is required")
        bundle_value = str(payload.get("bundle", "")).strip()
        if bundle_value:
            bundle = self._workspace_path(bundle_value)
        else:
            bundle = self._workspace_path(f"bundles/current{BUNDLE_EXTENSION}")
            with self._lock:
                result = create_project_bundle(
                    self.document,
                    bundle,
                    settings={"source": "editor-session"},
                    version=str(payload.get("version", DEFAULT_FTB_QUESTS_VERSION)),
                )
                if not result.is_clean:
                    raise ValueError("project bundle creation failed: " + "; ".join(result.errors))
        result = install_project_bundle(
            bundle,
            Path(instance_value),
            backup=bool(payload.get("backup", True)),
            dry_run=bool(payload.get("dry_run", False)),
            force=bool(payload.get("force", False)),
        )
        if not result.is_clean:
            raise ValueError("project installation failed: " + "; ".join(result.errors))
        return result.to_dict()

    def export(
        self,
        destination: str | Path = DEFAULT_EDITOR_EXPORT,
        *,
        version: str = DEFAULT_FTB_QUESTS_VERSION,
    ) -> dict[str, object]:
        path = self._workspace_path(destination)
        with self._lock:
            validation = validate_editor_document(self.document)
            if validation.errors:
                raise ValueError("cannot export invalid editor document: " + "; ".join(validation.errors))
            result = export_quest_blueprint(
                editor_document_to_blueprint(self.document),
                path,
                version=version,
            )
            if not result.is_clean:
                raise ValueError("FTB Quests export failed: " + "; ".join(result.errors))
            return result.to_dict()


def handle_editor_api(
    session: EditorSession,
    method: str,
    path: str,
    payload: Mapping[str, object] | None = None,
) -> EditorServiceResponse:
    method = method.upper()
    clean_path = urlparse(path).path.rstrip("/") or "/"
    body = payload or {}
    try:
        job_prefix = f"/api/{EDITOR_API_VERSION}/jobs/"
        if method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/jobs":
            result = session.jobs_payload()
        elif method == "GET" and clean_path.startswith(job_prefix):
            job_id = clean_path[len(job_prefix):]
            if not job_id or "/" in job_id:
                raise ValueError("invalid editor job identifier")
            result = session.job_payload(job_id)
        elif method == "POST" and clean_path.startswith(job_prefix) and clean_path.endswith("/cancel"):
            job_id = clean_path[len(job_prefix):-len("/cancel")].rstrip("/")
            if not job_id or "/" in job_id:
                raise ValueError("invalid editor job identifier")
            result = session.cancel_job(job_id)
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/status":
            result = session.status()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/instances":
            result = session.instances_payload()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/document":
            result = session.document_payload()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/validation":
            result = session.validation_payload()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/recovery":
            result = session.recovery_payload()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/operations":
            result = session.apply(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/batch-operations":
            result = session.apply_batch(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/auto-layout":
            result = session.auto_layout(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/undo":
            result = session.undo()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/redo":
            result = session.redo()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/snapshot":
            result = session.create_snapshot(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/recover":
            result = session.recover(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/discard-recovery":
            result = session.discard_recovery(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/save":
            result = session.save(body.get("path") if "path" in body else None)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/open":
            result = session.open(str(body.get("path", "")))
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/generate":
            result = session.generate(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/generate-job":
            return EditorServiceResponse(202, session.queue_generate(body))
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/bundle":
            result = session.create_bundle(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/open-bundle":
            result = session.open_bundle(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/install":
            result = session.install_bundle(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/export":
            result = session.export(
                str(body.get("destination", DEFAULT_EDITOR_EXPORT)),
                version=str(body.get("version", DEFAULT_FTB_QUESTS_VERSION)),
            )
        else:
            return EditorServiceResponse(
                404,
                {"status": "fail", "error": f"unknown editor API route: {method} {clean_path}"},
            )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return EditorServiceResponse(400, {"status": "fail", "error": str(exc)})
    return EditorServiceResponse(200, result)


_EDITOR_HTML = EDITOR_HTML


class EditorHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        session: EditorSession,
    ) -> None:
        self.session = session
        super().__init__(server_address, EditorRequestHandler)


class EditorRequestHandler(BaseHTTPRequestHandler):
    server: EditorHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, response: EditorServiceResponse) -> None:
        self._send_bytes(
            response.status_code,
            (response.format_json() + "\n").encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _read_bundle_import(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        filename = self.headers.get("X-File-Name", "")
        return self.server.session.import_project_bundle(filename, self.rfile, length)

    def _read_import(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        filename = self.headers.get("X-File-Name", "")
        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        target_quests = _integer_option(query, "target_quests", None)
        chapter_size = _integer_option(query, "chapter_size", 40)
        assert chapter_size is not None
        description_style = query.get("description_style", ["guided"])[0]
        reward_policy = query.get("reward_policy", ["unassigned"])[0]
        return self.server.session.import_modpack(
            filename,
            self.rfile,
            length,
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )

    def _read_analyze(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        filename = self.headers.get("X-File-Name", "")
        return self.server.session.analyze_modpack(filename, self.rfile, length)

    def _read_import_job(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        filename = self.headers.get("X-File-Name", "")
        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        target_quests = _integer_option(query, "target_quests", None)
        chapter_size = _integer_option(query, "chapter_size", 40)
        assert chapter_size is not None
        description_style = query.get("description_style", ["guided"])[0]
        reward_policy = query.get("reward_policy", ["unassigned"])[0]
        return self.server.session.queue_import_modpack(
            filename,
            self.rfile,
            length,
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )

    def _read_payload(self) -> Mapping[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("request body exceeds the editor API limit")
        if length == 0:
            return {}
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("request JSON must contain an object")
        return payload

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._send_bytes(200, _EDITOR_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        self._send_json(handle_editor_api(self.server.session, "GET", self.path))

    def do_POST(self) -> None:
        clean_path = urlparse(self.path).path.rstrip("/") or "/"
        if clean_path == f"/api/{EDITOR_API_VERSION}/project-bundle-import":
            try:
                result = self._read_bundle_import()
            except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
                self._send_json(EditorServiceResponse(400, {"status": "fail", "error": str(exc)}))
                return
            self._send_json(EditorServiceResponse(200, result))
            return
        if clean_path == f"/api/{EDITOR_API_VERSION}/analyze":
            try:
                result = self._read_analyze()
            except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
                self._send_json(EditorServiceResponse(400, {"status": "fail", "error": str(exc)}))
                return
            self._send_json(EditorServiceResponse(200, result))
            return
        if clean_path == f"/api/{EDITOR_API_VERSION}/import-job":
            try:
                result = self._read_import_job()
            except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
                self._send_json(EditorServiceResponse(400, {"status": "fail", "error": str(exc)}))
                return
            self._send_json(EditorServiceResponse(202, result))
            return
        if clean_path == f"/api/{EDITOR_API_VERSION}/import":
            try:
                result = self._read_import()
            except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
                self._send_json(EditorServiceResponse(400, {"status": "fail", "error": str(exc)}))
                return
            self._send_json(EditorServiceResponse(200, result))
            return
        try:
            payload = self._read_payload()
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(EditorServiceResponse(400, {"status": "fail", "error": str(exc)}))
            return
        self._send_json(handle_editor_api(self.server.session, "POST", self.path, payload))


def create_editor_http_server(
    session: EditorSession,
    *,
    host: str = DEFAULT_EDITOR_HOST,
    port: int = DEFAULT_EDITOR_PORT,
) -> EditorHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("the editor service may bind only to a loopback host")
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    return EditorHTTPServer((host, port), session)


def serve_editor(
    source: Path | None = None,
    *,
    workspace: Path = DEFAULT_EDITOR_WORKSPACE,
    host: str = DEFAULT_EDITOR_HOST,
    port: int = DEFAULT_EDITOR_PORT,
    target_quests: int | None = None,
    chapter_size: int = 40,
    description_style: str = "guided",
    reward_policy: str = "unassigned",
    open_browser: bool = True,
) -> int:
    session = (
        EditorSession.from_source(
            source,
            workspace=workspace,
            target_quests=target_quests,
            chapter_size=chapter_size,
            description_style=description_style,
            reward_policy=reward_policy,
        )
        if source is not None
        else EditorSession.empty(workspace=workspace)
    )
    server = create_editor_http_server(session, host=host, port=port)
    actual_host, actual_port = server.server_address[:2]
    url = f"http://{actual_host}:{actual_port}/"
    print(f"FTB Quest Maker editor service: {url}")
    print(f"Workspace: {session.workspace.as_posix()}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
