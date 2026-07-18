from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.ftb_blueprint_exporter import export_quest_blueprint
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.parser import FTBQuestParser
from generator.progression_planner import generate_quest_blueprint
from model import TaskType


@dataclass(frozen=True, slots=True)
class FTBBlueprintExporterContract:
    export_generated: bool
    round_trip_valid: bool
    quest_count_preserved: bool
    dependencies_preserved: bool
    item_tasks_exported: bool
    advancement_tasks_exported: bool
    deterministic_tree: bool
    stale_files_removed: bool
    invalid_blueprint_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.export_generated,
            self.round_trip_valid,
            self.quest_count_preserved,
            self.dependencies_preserved,
            self.item_tasks_exported,
            self.advancement_tasks_exported,
            self.deterministic_tree,
            self.stale_files_removed,
            self.invalid_blueprint_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "export_generated": self.export_generated,
            "round_trip_valid": self.round_trip_valid,
            "quest_count_preserved": self.quest_count_preserved,
            "dependencies_preserved": self.dependencies_preserved,
            "item_tasks_exported": self.item_tasks_exported,
            "advancement_tasks_exported": self.advancement_tasks_exported,
            "deterministic_tree": self.deterministic_tree,
            "stale_files_removed": self.stale_files_removed,
            "invalid_blueprint_rejected": self.invalid_blueprint_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"FTB blueprint exporter contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Export generated: {'yes' if self.export_generated else 'no'}.",
            f"Round trip valid: {'yes' if self.round_trip_valid else 'no'}.",
            f"Quest count preserved: {'yes' if self.quest_count_preserved else 'no'}.",
            f"Dependencies preserved: {'yes' if self.dependencies_preserved else 'no'}.",
            f"Item tasks exported: {'yes' if self.item_tasks_exported else 'no'}.",
            f"Advancement tasks exported: {'yes' if self.advancement_tasks_exported else 'no'}.",
            f"Deterministic tree: {'yes' if self.deterministic_tree else 'no'}.",
            f"Stale files removed: {'yes' if self.stale_files_removed else 'no'}.",
            f"Invalid blueprint rejected: {'yes' if self.invalid_blueprint_rejected else 'no'}.",
        ))


def run_ftb_blueprint_exporter_contract() -> FTBBlueprintExporterContract:
    with TemporaryDirectory(prefix="ftb-blueprint-exporter-contract-") as temporary:
        root = Path(temporary)
        pack = root / "exporter.mrpack"
        destination = root / "config" / "ftbquests"
        _synthetic_pack(pack)
        blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

        first = export_quest_blueprint(blueprint, destination)
        stale = destination / "quests" / "chapters" / "stale.snbt"
        stale.write_text("{ id: \"0000000000000000\" }\n", encoding="utf-8")
        second = export_quest_blueprint(blueprint, destination)
        restored = FTBQuestParser().load(destination)
        quests = restored.quests
        dependency_edges = sum(len(quest.dependencies) for quest in quests)
        task_types = {task.type for quest in quests for task in quest.tasks}

        invalid = export_quest_blueprint(
            replace(blueprint, errors=("synthetic blueprint defect",)),
            root / "invalid",
        )
        return FTBBlueprintExporterContract(
            export_generated=first.is_clean and (destination / "quests" / "data.snbt").is_file(),
            round_trip_valid=len(restored.chapters) == 1 and len(quests) == 4,
            quest_count_preserved=second.quests == blueprint.quest_count == 4,
            dependencies_preserved=dependency_edges == blueprint.dependency_edges == 2,
            item_tasks_exported=TaskType.ITEM in task_types,
            advancement_tasks_exported=TaskType.ADVANCEMENT in task_types,
            deterministic_tree=first.tree_sha256 == second.tree_sha256,
            stale_files_removed=not stale.exists(),
            invalid_blueprint_rejected=not invalid.is_clean and bool(invalid.errors),
        )
