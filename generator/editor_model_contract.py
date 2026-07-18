from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.editor_model import (
    EditorDocument,
    EditorOperation,
    apply_editor_operation,
    editor_document_to_blueprint,
    generate_editor_model,
    validate_editor_document,
)
from generator.ftb_blueprint_exporter import blueprint_to_project
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorModelContract:
    document_generated: bool
    stable_nodes_and_edges: bool
    json_round_trip: bool
    blueprint_round_trip: bool
    ftb_export_compatible: bool
    reversible_update: bool
    position_edit_recorded: bool
    cycle_rejected: bool
    dangling_dependency_rejected: bool
    deterministic_output: bool
    invalid_policy_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.document_generated,
            self.stable_nodes_and_edges,
            self.json_round_trip,
            self.blueprint_round_trip,
            self.ftb_export_compatible,
            self.reversible_update,
            self.position_edit_recorded,
            self.cycle_rejected,
            self.dangling_dependency_rejected,
            self.deterministic_output,
            self.invalid_policy_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "document_generated": self.document_generated,
            "stable_nodes_and_edges": self.stable_nodes_and_edges,
            "json_round_trip": self.json_round_trip,
            "blueprint_round_trip": self.blueprint_round_trip,
            "ftb_export_compatible": self.ftb_export_compatible,
            "reversible_update": self.reversible_update,
            "position_edit_recorded": self.position_edit_recorded,
            "cycle_rejected": self.cycle_rejected,
            "dangling_dependency_rejected": self.dangling_dependency_rejected,
            "deterministic_output": self.deterministic_output,
            "invalid_policy_rejected": self.invalid_policy_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Visual editor data model contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Document generated: {'yes' if self.document_generated else 'no'}.",
            f"Stable nodes and edges: {'yes' if self.stable_nodes_and_edges else 'no'}.",
            f"JSON round trip: {'yes' if self.json_round_trip else 'no'}.",
            f"Blueprint round trip: {'yes' if self.blueprint_round_trip else 'no'}.",
            f"FTB export compatible: {'yes' if self.ftb_export_compatible else 'no'}.",
            f"Reversible update: {'yes' if self.reversible_update else 'no'}.",
            f"Position edit recorded: {'yes' if self.position_edit_recorded else 'no'}.",
            f"Cycle rejected: {'yes' if self.cycle_rejected else 'no'}.",
            "Dangling dependency rejected: "
            f"{'yes' if self.dangling_dependency_rejected else 'no'}.",
            f"Deterministic output: {'yes' if self.deterministic_output else 'no'}.",
            f"Invalid policy rejected: {'yes' if self.invalid_policy_rejected else 'no'}.",
        ))


def run_editor_model_contract() -> EditorModelContract:
    with TemporaryDirectory(prefix="editor-model-contract-") as temporary:
        pack = Path(temporary) / "editor.mrpack"
        _synthetic_pack(pack)
        document = generate_editor_model(
            pack,
            target_quests=4,
            chapter_size=10,
            description_style="guided",
            reward_policy="conservative",
        )
        repeat = generate_editor_model(
            pack,
            target_quests=4,
            chapter_size=10,
            description_style="guided",
            reward_policy="conservative",
        )
        validation = validate_editor_document(document)
        restored = EditorDocument.from_dict(json.loads(document.format_json()))
        blueprint = editor_document_to_blueprint(document)
        project = blueprint_to_project(blueprint)

        first = document.quests[0]
        update = apply_editor_operation(
            document,
            EditorOperation.create("update_quest", first.quest_id, title="Edited Quest Title"),
        )
        move = apply_editor_operation(
            update.after,
            EditorOperation.create(
                "move_quest",
                first.quest_id,
                chapter_id=first.chapter_id,
                x=first.x + 7,
                y=first.y + 5,
            ),
        )

        cycle_rejected = False
        if document.edges:
            edge = document.edges[0]
            reverse = apply_editor_operation(
                document,
                EditorOperation.create(
                    "set_dependency",
                    edge.prerequisite_quest,
                    prerequisite_id=edge.dependent_quest,
                    enabled=True,
                ),
            )
            cycle_rejected = not reverse.is_clean and any(
                "cycle" in error for error in reverse.errors
            )

        dangling = apply_editor_operation(
            document,
            EditorOperation.create(
                "set_dependency",
                first.quest_id,
                prerequisite_id="missing:quest",
                enabled=True,
            ),
        )
        invalid = generate_editor_model(pack, reward_policy="invalid")

        round_trip_blueprint = editor_document_to_blueprint(restored)
        return EditorModelContract(
            document_generated=document.is_clean and document.quest_count == 4,
            stable_nodes_and_edges=(
                len({chapter.chapter_id for chapter in document.chapters}) == len(document.chapters)
                and len({quest.quest_id for quest in document.quests}) == len(document.quests)
                and len({edge.edge_id for edge in document.edges}) == len(document.edges)
                and validation.is_clean
            ),
            json_round_trip=restored.to_dict() == document.to_dict(),
            blueprint_round_trip=(
                round_trip_blueprint.quest_count == blueprint.quest_count
                and round_trip_blueprint.dependency_edges == blueprint.dependency_edges
                and round_trip_blueprint.format_json() == blueprint.format_json()
            ),
            ftb_export_compatible=(
                len(project.quests) == document.quest_count
                and sum(len(quest.rewards) for quest in project.quests)
                == sum(len(quest.rewards) for quest in document.quests)
            ),
            reversible_update=(
                update.is_clean
                and update.after.revision == 1
                and update.after.quests[0].title == "Edited Quest Title"
                and update.undo() == document
                and update.redo() == update.after
            ),
            position_edit_recorded=(
                move.is_clean
                and move.after.revision == 2
                and move.after.change_log[-1].action == "move_quest"
                and move.after.quests[0].x == first.x + 7
                and first.quest_id in move.after.dirty_entities
            ),
            cycle_rejected=cycle_rejected,
            dangling_dependency_rejected=(
                not dangling.is_clean
                and any("unknown prerequisite quest" in error for error in dangling.errors)
            ),
            deterministic_output=document.format_json() == repeat.format_json(),
            invalid_policy_rejected=not invalid.is_clean and bool(invalid.errors),
        )
