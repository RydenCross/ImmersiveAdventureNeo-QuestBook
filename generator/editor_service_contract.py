from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import urlopen

from generator.editor_service import (
    EditorSession,
    create_editor_http_server,
    handle_editor_api,
)
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorServiceContract:
    session_generated: bool
    operation_history: bool
    save_open_round_trip: bool
    validation_route: bool
    export_route: bool
    workspace_escape_rejected: bool
    loopback_only: bool
    http_round_trip: bool
    deterministic_document: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.session_generated,
                self.operation_history,
                self.save_open_round_trip,
                self.validation_route,
                self.export_route,
                self.workspace_escape_rejected,
                self.loopback_only,
                self.http_round_trip,
                self.deterministic_document,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "session_generated": self.session_generated,
            "operation_history": self.operation_history,
            "save_open_round_trip": self.save_open_round_trip,
            "validation_route": self.validation_route,
            "export_route": self.export_route,
            "workspace_escape_rejected": self.workspace_escape_rejected,
            "loopback_only": self.loopback_only,
            "http_round_trip": self.http_round_trip,
            "deterministic_document": self.deterministic_document,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Local visual editor service contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Session generated: {'yes' if self.session_generated else 'no'}.",
                f"Operation history: {'yes' if self.operation_history else 'no'}.",
                f"Save/open round trip: {'yes' if self.save_open_round_trip else 'no'}.",
                f"Validation route: {'yes' if self.validation_route else 'no'}.",
                f"Export route: {'yes' if self.export_route else 'no'}.",
                "Workspace escape rejected: "
                f"{'yes' if self.workspace_escape_rejected else 'no'}.",
                f"Loopback-only binding: {'yes' if self.loopback_only else 'no'}.",
                f"HTTP round trip: {'yes' if self.http_round_trip else 'no'}.",
                f"Deterministic document: {'yes' if self.deterministic_document else 'no'}.",
            )
        )


def run_editor_service_contract() -> EditorServiceContract:
    with TemporaryDirectory(prefix="editor-service-contract-") as temporary:
        root = Path(temporary)
        pack = root / "service.mrpack"
        workspace = root / "workspace"
        _synthetic_pack(pack)
        session = EditorSession.from_source(
            pack,
            workspace=workspace,
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        repeat = EditorSession.from_source(
            pack,
            workspace=root / "repeat-workspace",
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        first = session.document.quests[0]
        applied = session.apply(
            {
                "action": "update_quest",
                "target_id": first.quest_id,
                "values": {"title": "Service edited title"},
            }
        )
        session.undo()
        undo_title = session.document.quests[0].title
        session.redo()
        redo_title = session.document.quests[0].title

        saved = session.save("models/editor.json")
        session.apply(
            {
                "action": "update_quest",
                "target_id": first.quest_id,
                "values": {"title": "Discarded title"},
            }
        )
        opened = session.open("models/editor.json")

        validation = handle_editor_api(session, "GET", "/api/v1/validation")
        exported = handle_editor_api(
            session,
            "POST",
            "/api/v1/export",
            {"destination": "generated/ftbquests"},
        )
        escaped = handle_editor_api(
            session,
            "POST",
            "/api/v1/save",
            {"path": "../escape.json"},
        )

        loopback_only = False
        try:
            create_editor_http_server(session, host="0.0.0.0", port=0)
        except ValueError:
            loopback_only = True

        http_round_trip = False
        server = create_editor_http_server(session, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address[:2]
        try:
            with urlopen(f"http://{host}:{port}/api/v1/status", timeout=5) as response:
                status_payload = json.loads(response.read().decode("utf-8"))
            http_round_trip = response.status == 200 and status_payload.get("quests") == 4
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        return EditorServiceContract(
            session_generated=(
                session.document.is_clean
                and len(session.document.chapters) == 1
                and len(session.document.quests) == 4
            ),
            operation_history=(
                applied["status"] == "pass"
                and undo_title == first.title
                and redo_title == "Service edited title"
            ),
            save_open_round_trip=(
                saved["status"] == "pass"
                and opened["status"] == "pass"
                and session.document.quests[0].title == "Service edited title"
                and session.status()["has_unsaved_changes"] is False
            ),
            validation_route=(
                validation.status_code == 200 and validation.payload.get("status") == "pass"
            ),
            export_route=(
                exported.status_code == 200
                and exported.payload.get("status") == "pass"
                and (workspace / "generated/ftbquests/quests/data.snbt").is_file()
            ),
            workspace_escape_rejected=(
                escaped.status_code == 400 and escaped.payload.get("status") == "fail"
            ),
            loopback_only=loopback_only,
            http_round_trip=http_round_trip,
            deterministic_document=(
                EditorSession.from_source(
                    pack,
                    workspace=root / "deterministic-workspace",
                    target_quests=4,
                    chapter_size=10,
                    reward_policy="conservative",
                ).document.format_json()
                == repeat.document.format_json()
            ),
        )
