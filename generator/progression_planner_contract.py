from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint


@dataclass(frozen=True, slots=True)
class ProgressionPlannerContract:
    blueprint_generated: bool
    target_respected: bool
    dependencies_preserved: bool
    dangling_dependencies: tuple[str, ...]
    deterministic_output: bool
    chapter_layout_valid: bool
    review_flags_present: bool
    invalid_target_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.blueprint_generated,
            self.target_respected,
            self.dependencies_preserved,
            not self.dangling_dependencies,
            self.deterministic_output,
            self.chapter_layout_valid,
            self.review_flags_present,
            self.invalid_target_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "blueprint_generated": self.blueprint_generated,
            "target_respected": self.target_respected,
            "dependencies_preserved": self.dependencies_preserved,
            "dangling_dependencies": list(self.dangling_dependencies),
            "deterministic_output": self.deterministic_output,
            "chapter_layout_valid": self.chapter_layout_valid,
            "review_flags_present": self.review_flags_present,
            "invalid_target_rejected": self.invalid_target_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Progression planner contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Blueprint generated: {'yes' if self.blueprint_generated else 'no'}.",
            f"Target respected: {'yes' if self.target_respected else 'no'}.",
            f"Dependencies preserved: {'yes' if self.dependencies_preserved else 'no'}.",
            f"Dangling dependencies: {len(self.dangling_dependencies)}.",
            f"Deterministic output: {'yes' if self.deterministic_output else 'no'}.",
            f"Chapter layout valid: {'yes' if self.chapter_layout_valid else 'no'}.",
            f"Review flags present: {'yes' if self.review_flags_present else 'no'}.",
            f"Invalid target rejected: {'yes' if self.invalid_target_rejected else 'no'}.",
        ))


def run_progression_planner_contract() -> ProgressionPlannerContract:
    with TemporaryDirectory(prefix="progression-planner-contract-") as temporary:
        pack = Path(temporary) / "planner.mrpack"
        _synthetic_pack(pack)
        first = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
        second = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
        quests = {
            quest.quest_id: quest
            for chapter in first.chapters
            for quest in chapter.quests
        }
        all_ids = set(quests)
        dangling = tuple(sorted(
            dependency
            for quest in quests.values()
            for dependency in quest.prerequisite_quests
            if dependency not in all_ids
        ))
        machine = next(
            (quest for quest in quests.values() if quest.objective.identifier == "scanner_demo:assembly_machine"),
            None,
        )
        gear = next(
            (quest for quest in quests.values() if quest.objective.identifier == "scanner_demo:copper_gear"),
            None,
        )
        invalid = generate_quest_blueprint(pack, target_quests=0, chapter_size=10)
        positions = [
            (quest.x, quest.y)
            for chapter in first.chapters
            for quest in chapter.quests
        ]
        return ProgressionPlannerContract(
            blueprint_generated=first.is_clean and first.quest_count == 4 and len(first.chapters) == 1,
            target_respected=first.quest_count <= first.requested_quests == 4,
            dependencies_preserved=bool(machine and gear and gear.quest_id in machine.prerequisite_quests),
            dangling_dependencies=dangling,
            deterministic_output=first.format_json() == second.format_json(),
            chapter_layout_valid=len(positions) == len(set(positions)),
            review_flags_present=all(isinstance(quest.review_required, bool) for quest in quests.values()),
            invalid_target_rejected=not invalid.is_clean and any("target quests" in error for error in invalid.errors),
        )
