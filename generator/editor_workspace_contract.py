from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.editor_model import EditorOperation
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_ui import EDITOR_HTML
from generator.editor_workspace import apply_editor_batch, auto_layout_editor_document
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorWorkspaceContract:
    deterministic_layout: bool
    dependency_safe_layout: bool
    collision_free_layout: bool
    atomic_bulk_edit: bool
    single_step_undo: bool
    failed_batch_rollback: bool
    workspace_api_routes: bool
    visual_bulk_controls: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.deterministic_layout,
                self.dependency_safe_layout,
                self.collision_free_layout,
                self.atomic_bulk_edit,
                self.single_step_undo,
                self.failed_batch_rollback,
                self.workspace_api_routes,
                self.visual_bulk_controls,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "deterministic_layout": self.deterministic_layout,
            "dependency_safe_layout": self.dependency_safe_layout,
            "collision_free_layout": self.collision_free_layout,
            "atomic_bulk_edit": self.atomic_bulk_edit,
            "single_step_undo": self.single_step_undo,
            "failed_batch_rollback": self.failed_batch_rollback,
            "workspace_api_routes": self.workspace_api_routes,
            "visual_bulk_controls": self.visual_bulk_controls,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Editor workspace contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Deterministic layout: {'PASS' if self.deterministic_layout else 'FAIL'}.",
                f"Dependency-safe layout: {'PASS' if self.dependency_safe_layout else 'FAIL'}.",
                f"Collision-free layout: {'PASS' if self.collision_free_layout else 'FAIL'}.",
                f"Atomic bulk edit: {'PASS' if self.atomic_bulk_edit else 'FAIL'}.",
                f"Single-step undo: {'PASS' if self.single_step_undo else 'FAIL'}.",
                f"Failed batch rollback: {'PASS' if self.failed_batch_rollback else 'FAIL'}.",
                f"Workspace API routes: {'PASS' if self.workspace_api_routes else 'FAIL'}.",
                f"Visual bulk controls: {'PASS' if self.visual_bulk_controls else 'FAIL'}.",
            )
        )


def run_editor_workspace_contract() -> EditorWorkspaceContract:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        pack = root / "workspace.mrpack"
        _synthetic_pack(pack)
        session = EditorSession.from_source(
            pack,
            workspace=root / "editor",
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        scrambled = replace(
            session.document,
            quests=tuple(
                replace(quest, x=8, y=index * 2)
                for index, quest in enumerate(session.document.quests)
            ),
        )
        first = auto_layout_editor_document(scrambled)
        second = auto_layout_editor_document(scrambled)
        x_positions = {quest.quest_id: quest.x for quest in first.document.quests}
        dependency_safe = all(
            x_positions[edge.prerequisite_quest] < x_positions[edge.dependent_quest]
            for edge in first.document.edges
        )

        quest_ids = [quest.quest_id for quest in session.document.quests[:2]]
        batch_result = session.apply_batch(
            {
                "operations": [
                    {
                        "action": "update_quest",
                        "target_id": quest_id,
                        "values": {"review_required": True},
                    }
                    for quest_id in quest_ids
                ]
            }
        )
        undo_depth = session.status()["undo_depth"]
        session.undo()
        reverted = not any(
            quest.review_required
            for quest in session.document.quests
            if quest.quest_id in quest_ids
        )

        before = session.document
        rollback = apply_editor_batch(
            before,
            (
                EditorOperation.create(
                    "update_quest", before.quests[0].quest_id, review_required=True
                ),
                EditorOperation.create("update_quest", "missing", review_required=True),
            ),
        )
        api_batch = handle_editor_api(
            session,
            "POST",
            "/api/v1/batch-operations",
            {
                "operations": [
                    {
                        "action": "update_quest",
                        "target_id": before.quests[0].quest_id,
                        "values": {"review_required": True},
                    }
                ]
            },
        )
        api_layout = handle_editor_api(session, "POST", "/api/v1/auto-layout", {})

        return EditorWorkspaceContract(
            deterministic_layout=(
                first.is_clean and first.document.to_dict() == second.document.to_dict()
            ),
            dependency_safe_layout=dependency_safe,
            collision_free_layout=not first.collisions,
            atomic_bulk_edit=(
                batch_result.get("operation_count") == 2
                and all(
                    bool(quest["review_required"])
                    for quest in batch_result["document"]["quests"]
                    if quest["id"] in quest_ids
                )
            ),
            single_step_undo=(undo_depth == 1 and reverted),
            failed_batch_rollback=(not rollback.is_clean and rollback.after == before),
            workspace_api_routes=(
                api_batch.status_code == 200 and api_layout.status_code == 200
            ),
            visual_bulk_controls=all(
                token in EDITOR_HTML
                for token in (
                    'id="auto-layout-button"',
                    'id="bulk-chapter"',
                    'id="bulk-review-button"',
                    "/batch-operations",
                    "/auto-layout",
                    "selectedQuests",
                )
            ),
        )
