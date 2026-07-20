from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import quote
from urllib.request import Request, urlopen

from generator.editor_service import EditorSession, create_editor_http_server
from generator.editor_ui import EDITOR_HTML
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorUIContract:
    empty_start: bool
    drop_import_interface: bool
    graph_canvas: bool
    drag_editing: bool
    dependency_linking: bool
    direct_import: bool
    http_import: bool
    workspace_confined: bool
    deterministic_quest_graph: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.empty_start,
                self.drop_import_interface,
                self.graph_canvas,
                self.drag_editing,
                self.dependency_linking,
                self.direct_import,
                self.http_import,
                self.workspace_confined,
                self.deterministic_quest_graph,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "empty_start": self.empty_start,
            "drop_import_interface": self.drop_import_interface,
            "graph_canvas": self.graph_canvas,
            "drag_editing": self.drag_editing,
            "dependency_linking": self.dependency_linking,
            "direct_import": self.direct_import,
            "http_import": self.http_import,
            "workspace_confined": self.workspace_confined,
            "deterministic_quest_graph": self.deterministic_quest_graph,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Editor UI contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Empty start: {'PASS' if self.empty_start else 'FAIL'}.",
                f"Drop import interface: {'PASS' if self.drop_import_interface else 'FAIL'}.",
                f"Graph canvas: {'PASS' if self.graph_canvas else 'FAIL'}.",
                f"Drag editing: {'PASS' if self.drag_editing else 'FAIL'}.",
                f"Dependency linking: {'PASS' if self.dependency_linking else 'FAIL'}.",
                f"Direct import: {'PASS' if self.direct_import else 'FAIL'}.",
                f"HTTP import: {'PASS' if self.http_import else 'FAIL'}.",
                f"Workspace confinement: {'PASS' if self.workspace_confined else 'FAIL'}.",
                f"Deterministic quest graph: {'PASS' if self.deterministic_quest_graph else 'FAIL'}.",
            )
        )


def _graph_signature(session: EditorSession) -> tuple[object, ...]:
    return (
        tuple((quest.quest_id, quest.chapter_id, quest.x, quest.y) for quest in session.document.quests),
        tuple(
            (edge.prerequisite_quest, edge.dependent_quest)
            for edge in session.document.edges
        ),
    )


def run_editor_ui_contract() -> EditorUIContract:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        initial = root / "initial.mrpack"
        uploaded = root / "uploaded.mrpack"
        _synthetic_pack(initial)
        _synthetic_pack(uploaded)
        data = uploaded.read_bytes()
        empty_session = EditorSession.empty(workspace=root / "empty-workspace")
        session = EditorSession.from_source(
            initial,
            workspace=root / "workspace",
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        imported = session.import_modpack(
            "Dropped Pack.mrpack",
            BytesIO(data),
            len(data),
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        repeated = EditorSession.from_source(
            uploaded,
            workspace=root / "repeat",
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        workspace_confined = str(imported.get("path", "")).startswith("imports/")

        server = create_editor_http_server(session, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address[:2]
        http_import = False
        try:
            request = Request(
                f"http://{host}:{port}/api/v1/import?target_quests=4&chapter_size=10&reward_policy=conservative",
                method="POST",
                headers={
                    "Content-Type": "application/octet-stream",
                    "X-File-Name": quote("Browser Drop.mrpack"),
                },
                data=data,
            )
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            http_import = (
                response.status == 200
                and payload.get("status") == "pass"
                and payload.get("session", {}).get("quests") == 4
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        return EditorUIContract(
            empty_start=(empty_session.document.is_clean and not empty_session.document.quests),
            drop_import_interface=all(
                token in EDITOR_HTML
                for token in ('id="drop-zone"', 'id="file-input"', "/api/v1/import")
            ),
            graph_canvas=all(
                token in EDITOR_HTML
                for token in ('id="graph"', 'id="edges"', 'id="nodes"', "renderGraph")
            ),
            drag_editing=all(
                token in EDITOR_HTML
                for token in ("startNodeDrag", "pointermove", "move_quest")
            ),
            dependency_linking=all(
                token in EDITOR_HTML
                for token in ("Link prerequisite", "createDependency", "set_dependency")
            ),
            direct_import=(
                imported.get("status") == "pass"
                and imported.get("session", {}).get("quests") == 4
            ),
            http_import=http_import,
            workspace_confined=workspace_confined,
            deterministic_quest_graph=_graph_signature(session) == _graph_signature(repeated),
        )
