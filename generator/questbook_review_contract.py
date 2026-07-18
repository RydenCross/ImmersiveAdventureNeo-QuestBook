from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.questbook_review import review_quest_blueprint


@dataclass(frozen=True, slots=True)
class QuestbookReviewContract:
    review_generated: bool
    export_validation_passed: bool
    weak_descriptions_detected: bool
    reward_decisions_detected: bool
    oversized_chapter_detected: bool
    bottleneck_detected: bool
    dangling_dependency_rejected: bool
    deterministic_output: bool
    invalid_threshold_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.review_generated,
            self.export_validation_passed,
            self.weak_descriptions_detected,
            self.reward_decisions_detected,
            self.oversized_chapter_detected,
            self.bottleneck_detected,
            self.dangling_dependency_rejected,
            self.deterministic_output,
            self.invalid_threshold_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "review_generated": self.review_generated,
            "export_validation_passed": self.export_validation_passed,
            "weak_descriptions_detected": self.weak_descriptions_detected,
            "reward_decisions_detected": self.reward_decisions_detected,
            "oversized_chapter_detected": self.oversized_chapter_detected,
            "bottleneck_detected": self.bottleneck_detected,
            "dangling_dependency_rejected": self.dangling_dependency_rejected,
            "deterministic_output": self.deterministic_output,
            "invalid_threshold_rejected": self.invalid_threshold_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Questbook review contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Review generated: {'yes' if self.review_generated else 'no'}.",
            f"Export validation passed: {'yes' if self.export_validation_passed else 'no'}.",
            f"Weak descriptions detected: {'yes' if self.weak_descriptions_detected else 'no'}.",
            f"Reward decisions detected: {'yes' if self.reward_decisions_detected else 'no'}.",
            f"Oversized chapter detected: {'yes' if self.oversized_chapter_detected else 'no'}.",
            f"Bottleneck detected: {'yes' if self.bottleneck_detected else 'no'}.",
            "Dangling dependency rejected: "
            f"{'yes' if self.dangling_dependency_rejected else 'no'}.",
            f"Deterministic output: {'yes' if self.deterministic_output else 'no'}.",
            f"Invalid threshold rejected: {'yes' if self.invalid_threshold_rejected else 'no'}.",
        ))


def _with_bottleneck(blueprint):
    chapter = blueprint.chapters[0]
    quests = list(chapter.quests)
    root = quests[0].quest_id
    quests = [quests[0], *(replace(quest, prerequisite_quests=(root,)) for quest in quests[1:])]
    return replace(blueprint, chapters=(replace(chapter, quests=tuple(quests)),))


def _with_dangling_dependency(blueprint):
    chapter = blueprint.chapters[0]
    quests = list(chapter.quests)
    quests[0] = replace(quests[0], prerequisite_quests=("missing__quest",))
    return replace(blueprint, chapters=(replace(chapter, quests=tuple(quests)),))


def run_questbook_review_contract() -> QuestbookReviewContract:
    with TemporaryDirectory(prefix="questbook-review-contract-") as temporary:
        pack = Path(temporary) / "review.mrpack"
        _synthetic_pack(pack)
        blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
        first = review_quest_blueprint(blueprint)
        second = review_quest_blueprint(blueprint)
        oversized = review_quest_blueprint(blueprint, max_chapter_quests=3)
        bottleneck = review_quest_blueprint(
            _with_bottleneck(blueprint), bottleneck_dependents=2
        )
        dangling = review_quest_blueprint(_with_dangling_dependency(blueprint))
        invalid = review_quest_blueprint(blueprint, min_description_words=0)
        codes = {finding.code for finding in first.findings}
        return QuestbookReviewContract(
            review_generated=first.is_clean and first.quests == 4 and first.chapters == 1,
            export_validation_passed=not any(
                finding.code == "EXPORT_CONVERSION_FAILED" for finding in first.findings
            ),
            weak_descriptions_detected=first.weak_descriptions == 2
            and "WEAK_DESCRIPTION" in codes,
            reward_decisions_detected=first.missing_reward_decisions == 4
            and "MISSING_REWARD_DECISIONS" in codes,
            oversized_chapter_detected=oversized.oversized_chapters == 1,
            bottleneck_detected=bottleneck.bottleneck_quests >= 1,
            dangling_dependency_rejected=not dangling.is_clean
            and any(finding.code == "DANGLING_DEPENDENCY" for finding in dangling.findings),
            deterministic_output=first.format_json() == second.format_json(),
            invalid_threshold_rejected=not invalid.is_clean
            and any(
                finding.code == "INVALID_DESCRIPTION_LIMIT" for finding in invalid.findings
            ),
        )
