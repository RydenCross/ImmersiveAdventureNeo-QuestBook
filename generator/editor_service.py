from __future__ import annotations

from dataclasses import dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
from threading import RLock
from typing import Mapping
from urllib.parse import urlparse
import webbrowser

from generator.editor_model import (
    EditorDocument,
    EditorOperation,
    apply_editor_operation,
    editor_document_to_blueprint,
    generate_editor_model,
    validate_editor_document,
)
from generator.ftb_blueprint_exporter import DEFAULT_FTB_QUESTS_VERSION, export_quest_blueprint
from generator.output_writer import atomic_write_text
from generator.quest_description_generator import DESCRIPTION_STYLES
from generator.reward_planner import REWARD_POLICIES

EDITOR_API_VERSION = "v1"
DEFAULT_EDITOR_HOST = "127.0.0.1"
DEFAULT_EDITOR_PORT = 8765
DEFAULT_EDITOR_WORKSPACE = Path(".quest-editor")
DEFAULT_EDITOR_DOCUMENT = Path("quest-editor-model.json")
DEFAULT_EDITOR_EXPORT = Path("generated/ftbquests")
MAX_REQUEST_BYTES = 1_048_576


def _is_loopback_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


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
        self._undo: list[EditorDocument] = []
        self._redo: list[EditorDocument] = []
        self._lock = RLock()

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
            }

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
            return {
                "status": "pass",
                "operation": operation.to_dict(),
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
            return {
                "status": "pass",
                "source": source.as_posix(),
                "session": self.status(),
                "document": self.document.to_dict(),
            }

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
        if method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/status":
            result = session.status()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/document":
            result = session.document_payload()
        elif method == "GET" and clean_path == f"/api/{EDITOR_API_VERSION}/validation":
            result = session.validation_payload()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/operations":
            result = session.apply(body)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/undo":
            result = session.undo()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/redo":
            result = session.redo()
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/save":
            result = session.save(body.get("path") if "path" in body else None)
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/open":
            result = session.open(str(body.get("path", "")))
        elif method == "POST" and clean_path == f"/api/{EDITOR_API_VERSION}/generate":
            result = session.generate(body)
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


_EDITOR_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FTB Quest Maker</title>
<style>
:root { color-scheme: dark; font-family: system-ui, sans-serif; }
body { margin: 0; background: #111827; color: #e5e7eb; }
header { padding: 16px 24px; background: #1f2937; display: flex; gap: 12px; align-items: center; }
button { padding: 8px 12px; border: 0; border-radius: 6px; cursor: pointer; }
main { display: grid; grid-template-columns: 280px 1fr; min-height: calc(100vh - 68px); }
aside { padding: 16px; border-right: 1px solid #374151; overflow: auto; }
section { padding: 20px; }
.quest { display: block; width: 100%; margin: 6px 0; text-align: left; background: #374151; color: inherit; }
label { display: block; margin: 12px 0 4px; }
input, textarea { width: 100%; box-sizing: border-box; padding: 8px; background: #111827; color: inherit; border: 1px solid #4b5563; }
textarea { min-height: 180px; }
#status { margin-left: auto; font-size: 0.9rem; }
pre { white-space: pre-wrap; color: #fca5a5; }
</style>
</head>
<body>
<header>
<strong>FTB Quest Maker</strong>
<button onclick="undo()">Undo</button><button onclick="redo()">Redo</button>
<button onclick="saveModel()">Save model</button><button onclick="exportQuestbook()">Export FTB Quests</button>
<span id="status">Loading…</span>
</header>
<main><aside><div id="chapters"></div></aside><section>
<h2 id="quest-title">Select a quest</h2>
<div id="editor" hidden>
<label>Title</label><input id="title">
<label>Description</label><textarea id="description"></textarea>
<button onclick="saveQuest()">Apply quest changes</button>
</div><pre id="error"></pre>
</section></main>
<script>
const api = '/api/v1'; let doc = null; let selected = null;
async function request(path, options={}) {
  const response = await fetch(api + path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed'); return data;
}
function showError(error) { document.getElementById('error').textContent = error ? String(error) : ''; }
async function refresh() {
  try { doc = await request('/document'); const status = await request('/status'); render();
    document.getElementById('status').textContent = `${status.quests} quests · revision ${status.revision}${status.has_unsaved_changes ? ' · unsaved' : ''}`;
  } catch (error) { showError(error); }
}
function render() {
  const root = document.getElementById('chapters'); root.innerHTML = '';
  for (const chapter of doc.chapters) {
    const heading = document.createElement('h3'); heading.textContent = chapter.title; root.appendChild(heading);
    for (const quest of doc.quests.filter(item => item.chapter_id === chapter.id)) {
      const button = document.createElement('button'); button.className = 'quest'; button.textContent = quest.title;
      button.onclick = () => selectQuest(quest.id); root.appendChild(button);
    }
  }
  if (selected) selectQuest(selected);
}
function selectQuest(id) {
  const quest = doc.quests.find(item => item.id === id); if (!quest) return; selected = id;
  document.getElementById('quest-title').textContent = quest.title; document.getElementById('title').value = quest.title;
  document.getElementById('description').value = quest.description; document.getElementById('editor').hidden = false;
}
async function saveQuest() { try { await request('/operations', {method:'POST', body:JSON.stringify({action:'update_quest', target_id:selected, values:{title:document.getElementById('title').value, description:document.getElementById('description').value}})}); showError(); await refresh(); } catch (error) { showError(error); } }
async function undo() { try { await request('/undo', {method:'POST', body:'{}'}); showError(); await refresh(); } catch (error) { showError(error); } }
async function redo() { try { await request('/redo', {method:'POST', body:'{}'}); showError(); await refresh(); } catch (error) { showError(error); } }
async function saveModel() { try { await request('/save', {method:'POST', body:JSON.stringify({path:'quest-editor-model.json'})}); showError(); await refresh(); } catch (error) { showError(error); } }
async function exportQuestbook() { try { const result = await request('/export', {method:'POST', body:JSON.stringify({destination:'generated/ftbquests'})}); showError(`Exported ${result.summary.quests} quests to ${result.destination}`); } catch (error) { showError(error); } }
refresh();
</script>
</body></html>
"""


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
    source: Path,
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
    session = EditorSession.from_source(
        source,
        workspace=workspace,
        target_quests=target_quests,
        chapter_size=chapter_size,
        description_style=description_style,
        reward_policy=reward_policy,
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
