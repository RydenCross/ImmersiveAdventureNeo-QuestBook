from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
from typing import Iterable

from generator.ftb_blueprint_exporter import blueprint_to_project
from generator.progression_planner import (
    BlueprintChapter,
    BlueprintQuest,
    QuestBlueprint,
    generate_quest_blueprint,
)
from generator.reward_planner import plan_quest_rewards
from generator.quest_description_generator import plan_quest_descriptions
from generator.validator import ProjectValidator

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_MIN_DESCRIPTION_WORDS = 6
DEFAULT_MAX_CHAPTER_QUESTS = 50
DEFAULT_BOTTLENECK_DEPENDENTS = 8
_SUPPORTED_OBJECTIVES = {"item", "advancement"}
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_-]*")
_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


@dataclass(frozen=True, slots=True)
class QuestbookReviewFinding:
    severity: str
    code: str
    message: str
    chapter_id: str | None = None
    quest_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.chapter_id is not None:
            result["chapter_id"] = self.chapter_id
        if self.quest_id is not None:
            result["quest_id"] = self.quest_id
        return result


@dataclass(frozen=True, slots=True)
class QuestbookReview:
    pack_name: str
    requested_quests: int
    quests: int
    chapters: int
    dependency_edges: int
    root_quests: int
    leaf_quests: int
    maximum_depth: int
    low_confidence_quests: int
    manual_review_quests: int
    weak_descriptions: int
    missing_reward_decisions: int
    oversized_chapters: int
    bottleneck_quests: int
    duplicate_objectives: int
    export_validation_warnings: int
    findings: tuple[QuestbookReviewFinding, ...]

    @property
    def errors(self) -> tuple[QuestbookReviewFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[QuestbookReviewFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "warning")

    @property
    def review_items(self) -> tuple[QuestbookReviewFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "review")

    @property
    def is_clean(self) -> bool:
        return not self.errors

    @property
    def publish_ready(self) -> bool:
        return self.is_clean and not self.warnings and not self.review_items

    @property
    def requires_review(self) -> bool:
        return bool(self.warnings or self.review_items)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "publish_ready": self.publish_ready,
            "requires_review": self.requires_review,
            "pack_name": self.pack_name,
            "summary": {
                "requested_quests": self.requested_quests,
                "quests": self.quests,
                "chapters": self.chapters,
                "dependency_edges": self.dependency_edges,
                "root_quests": self.root_quests,
                "leaf_quests": self.leaf_quests,
                "maximum_depth": self.maximum_depth,
                "low_confidence_quests": self.low_confidence_quests,
                "manual_review_quests": self.manual_review_quests,
                "weak_descriptions": self.weak_descriptions,
                "missing_reward_decisions": self.missing_reward_decisions,
                "oversized_chapters": self.oversized_chapters,
                "bottleneck_quests": self.bottleneck_quests,
                "duplicate_objectives": self.duplicate_objectives,
                "export_validation_warnings": self.export_validation_warnings,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "review_items": len(self.review_items),
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Generated questbook review: {'PASS' if self.is_clean else 'FAIL'}",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Publish ready: {'yes' if self.publish_ready else 'no'}.",
            f"Quests: {self.quests}/{self.requested_quests} requested.",
            f"Chapters: {self.chapters}.",
            f"Dependency edges: {self.dependency_edges}.",
            f"Maximum progression depth: {self.maximum_depth}.",
            f"Low-confidence quests: {self.low_confidence_quests}.",
            f"Manual-review quests: {self.manual_review_quests}.",
            f"Weak descriptions: {self.weak_descriptions}.",
            f"Missing reward decisions: {self.missing_reward_decisions}.",
            f"Oversized chapters: {self.oversized_chapters}.",
            f"Progression bottlenecks: {self.bottleneck_quests}.",
            f"Duplicate objectives: {self.duplicate_objectives}.",
            f"Errors: {len(self.errors)}.",
            f"Warnings: {len(self.warnings)}.",
            f"Review items: {len(self.review_items)}.",
        ]
        lines.extend(
            f"{finding.severity.upper()} {finding.code}"
            f"{f' [{finding.quest_id}]' if finding.quest_id else ''}: {finding.message}"
            for finding in self.findings
        )
        return "\n".join(lines)


def _flatten(blueprint: QuestBlueprint) -> tuple[tuple[BlueprintChapter, BlueprintQuest], ...]:
    return tuple(
        (chapter, quest)
        for chapter in blueprint.chapters
        for quest in chapter.quests
    )


def _dependency_cycles(graph: dict[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, ()):
            if dependency not in graph:
                continue
            if state.get(dependency, 0) == 0:
                visit(dependency)
            elif state.get(dependency) == 1:
                start = stack.index(dependency)
                raw = stack[start:] + [dependency]
                body = raw[:-1]
                rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
                cycles.add(min(rotations))
        stack.pop()
        state[node] = 2

    for identifier in sorted(graph):
        if state.get(identifier, 0) == 0:
            visit(identifier)
    return tuple(sorted(cycles))


def _depths(graph: dict[str, tuple[str, ...]]) -> dict[str, int]:
    remaining = {
        node: {dependency for dependency in dependencies if dependency in graph}
        for node, dependencies in graph.items()
    }
    depths: dict[str, int] = {}
    while remaining:
        ready = sorted(node for node, dependencies in remaining.items() if not dependencies)
        if not ready:
            break
        for node in ready:
            original = graph.get(node, ())
            depths[node] = 0 if not original else 1 + max(
                (depths.get(dependency, 0) for dependency in original if dependency in graph),
                default=-1,
            )
            remaining.pop(node)
            for dependencies in remaining.values():
                dependencies.discard(node)
    return depths


def _finding_sort_key(finding: QuestbookReviewFinding) -> tuple[int, str, str, str]:
    severity_order = {"error": 0, "warning": 1, "review": 2}
    return (
        severity_order.get(finding.severity, 9),
        finding.code,
        finding.chapter_id or "",
        finding.quest_id or "",
    )


def review_quest_blueprint(
    blueprint: QuestBlueprint,
    *,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    min_description_words: int = DEFAULT_MIN_DESCRIPTION_WORDS,
    max_chapter_quests: int = DEFAULT_MAX_CHAPTER_QUESTS,
    bottleneck_dependents: int = DEFAULT_BOTTLENECK_DEPENDENTS,
) -> QuestbookReview:
    findings: list[QuestbookReviewFinding] = []
    if not 0.0 <= low_confidence_threshold <= 1.0:
        findings.append(QuestbookReviewFinding(
            "error", "INVALID_LOW_CONFIDENCE_THRESHOLD",
            "Low-confidence threshold must be between 0 and 1.",
        ))
    if min_description_words < 1:
        findings.append(QuestbookReviewFinding(
            "error", "INVALID_DESCRIPTION_LIMIT",
            "Minimum description words must be at least 1.",
        ))
    if max_chapter_quests < 1:
        findings.append(QuestbookReviewFinding(
            "error", "INVALID_CHAPTER_LIMIT",
            "Maximum chapter quests must be at least 1.",
        ))
    if bottleneck_dependents < 1:
        findings.append(QuestbookReviewFinding(
            "error", "INVALID_BOTTLENECK_LIMIT",
            "Bottleneck dependent threshold must be at least 1.",
        ))

    safe_confidence = min(1.0, max(0.0, low_confidence_threshold))
    safe_description_words = max(1, min_description_words)
    safe_chapter_quests = max(1, max_chapter_quests)
    safe_bottleneck = max(1, bottleneck_dependents)

    findings.extend(
        QuestbookReviewFinding("error", "BLUEPRINT_ERROR", message)
        for message in blueprint.errors
    )
    findings.extend(
        QuestbookReviewFinding("warning", "BLUEPRINT_WARNING", message)
        for message in blueprint.warnings
    )

    rows = _flatten(blueprint)
    if not rows:
        findings.append(QuestbookReviewFinding(
            "error", "EMPTY_BLUEPRINT", "The generated blueprint contains no quests."
        ))

    quest_ids = [quest.quest_id for _, quest in rows]
    known_ids = set(quest_ids)
    duplicate_quest_ids = {
        identifier for identifier in quest_ids if quest_ids.count(identifier) > 1
    }
    for quest_id in sorted(duplicate_quest_ids):
        findings.append(QuestbookReviewFinding(
            "error", "DUPLICATE_QUEST_ID", f"Quest ID '{quest_id}' appears more than once.",
            quest_id=quest_id,
        ))

    graph = {
        quest.quest_id: tuple(quest.prerequisite_quests)
        for _, quest in rows
    }
    dangling = sorted({
        dependency
        for _, quest in rows
        for dependency in quest.prerequisite_quests
        if dependency not in known_ids
    })
    for dependency in dangling:
        findings.append(QuestbookReviewFinding(
            "error", "DANGLING_DEPENDENCY",
            f"Prerequisite quest '{dependency}' does not exist.",
            quest_id=dependency,
        ))
    for cycle in _dependency_cycles(graph):
        findings.append(QuestbookReviewFinding(
            "error", "DEPENDENCY_CYCLE",
            "Dependency cycle detected: " + " -> ".join((*cycle, cycle[0])),
            quest_id=cycle[0],
        ))

    dependents: dict[str, int] = {identifier: 0 for identifier in known_ids}
    for dependencies in graph.values():
        for dependency in dependencies:
            if dependency in dependents:
                dependents[dependency] += 1
    depths = _depths(graph)

    objective_owners: dict[tuple[str, str], list[str]] = {}
    low_confidence = 0
    manual_review = 0
    weak_descriptions = 0
    for chapter, quest in rows:
        objective_key = (quest.objective.objective_type, quest.objective.identifier)
        objective_owners.setdefault(objective_key, []).append(quest.quest_id)
        if quest.objective.objective_type not in _SUPPORTED_OBJECTIVES:
            findings.append(QuestbookReviewFinding(
                "error", "UNSUPPORTED_OBJECTIVE",
                f"Objective type '{quest.objective.objective_type}' cannot be exported.",
                chapter.chapter_id, quest.quest_id,
            ))
        if not _RESOURCE_LOCATION.fullmatch(quest.objective.identifier):
            findings.append(QuestbookReviewFinding(
                "error", "INVALID_OBJECTIVE_ID",
                f"Objective '{quest.objective.identifier}' is not a namespace:path identifier.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.objective.count < 1:
            findings.append(QuestbookReviewFinding(
                "error", "INVALID_OBJECTIVE_COUNT", "Objective count must be at least one.",
                chapter.chapter_id, quest.quest_id,
            ))
        if not quest.source_kind or not quest.source_id:
            findings.append(QuestbookReviewFinding(
                "error", "MISSING_SOURCE_PROVENANCE",
                "Generated quest is missing source provenance.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.confidence < safe_confidence:
            low_confidence += 1
            findings.append(QuestbookReviewFinding(
                "review", "LOW_CONFIDENCE_QUEST",
                f"Confidence {quest.confidence:.2f} is below {safe_confidence:.2f}.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.review_required:
            manual_review += 1
            findings.append(QuestbookReviewFinding(
                "review", "MANUAL_REVIEW_REQUIRED",
                "The progression planner marked this quest for manual review.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.reward_decision not in {"unassigned", "none", "rewarded"}:
            findings.append(QuestbookReviewFinding(
                "error", "INVALID_REWARD_DECISION",
                f"Reward decision '{quest.reward_decision}' is not supported.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.reward_decision == "rewarded" and not quest.rewards:
            findings.append(QuestbookReviewFinding(
                "error", "MISSING_REWARD_DEFINITION",
                "Quest is marked rewarded but contains no reward definition.",
                chapter.chapter_id, quest.quest_id,
            ))
        if quest.reward_decision == "none" and quest.rewards:
            findings.append(QuestbookReviewFinding(
                "error", "CONTRADICTORY_REWARD_DECISION",
                "Quest is marked no-reward but contains reward definitions.",
                chapter.chapter_id, quest.quest_id,
            ))
        for reward in quest.rewards:
            if reward.reward_type != "item":
                findings.append(QuestbookReviewFinding(
                    "error", "UNSUPPORTED_REWARD_TYPE",
                    f"Reward type '{reward.reward_type}' cannot be exported.",
                    chapter.chapter_id, quest.quest_id,
                ))
            if not _RESOURCE_LOCATION.fullmatch(reward.identifier):
                findings.append(QuestbookReviewFinding(
                    "error", "INVALID_REWARD_ID",
                    f"Reward '{reward.identifier}' is not a namespace:path identifier.",
                    chapter.chapter_id, quest.quest_id,
                ))
            if reward.count < 1:
                findings.append(QuestbookReviewFinding(
                    "error", "INVALID_REWARD_COUNT",
                    "Reward count must be at least one.",
                    chapter.chapter_id, quest.quest_id,
                ))
        word_count = len(_WORD.findall(quest.description))
        if word_count < safe_description_words:
            weak_descriptions += 1
            findings.append(QuestbookReviewFinding(
                "review", "WEAK_DESCRIPTION",
                f"Description has {word_count} words; "
                f"at least {safe_description_words} are recommended.",
                chapter.chapter_id, quest.quest_id,
            ))

    duplicate_objectives = 0
    for (objective_type, identifier), owners in sorted(objective_owners.items()):
        if len(owners) < 2:
            continue
        duplicate_objectives += 1
        findings.append(QuestbookReviewFinding(
            "warning", "DUPLICATE_OBJECTIVE",
            f"{objective_type} objective '{identifier}' is used by {len(owners)} quests: "
            + ", ".join(sorted(owners)),
        ))

    oversized_chapters = 0
    for chapter in blueprint.chapters:
        if len(chapter.quests) > safe_chapter_quests:
            oversized_chapters += 1
            findings.append(QuestbookReviewFinding(
                "warning", "OVERSIZED_CHAPTER",
                f"Chapter contains {len(chapter.quests)} quests; limit is {safe_chapter_quests}.",
                chapter_id=chapter.chapter_id,
            ))

    bottlenecks = 0
    for quest_id, count in sorted(dependents.items()):
        if count >= safe_bottleneck:
            bottlenecks += 1
            chapter_id = next(
                (chapter.chapter_id for chapter, quest in rows if quest.quest_id == quest_id),
                None,
            )
            findings.append(QuestbookReviewFinding(
                "warning", "PROGRESSION_BOTTLENECK",
                f"Quest directly gates {count} later quests; threshold is {safe_bottleneck}.",
                chapter_id, quest_id,
            ))

    if blueprint.shortfall:
        findings.append(QuestbookReviewFinding(
            "warning", "QUEST_TARGET_SHORTFALL",
            f"Blueprint is {blueprint.shortfall} quests below the requested target.",
        ))

    export_warnings = 0
    missing_rewards = sum(
        quest.reward_decision == "unassigned" for _, quest in rows
    )
    try:
        project = blueprint_to_project(blueprint)
        validation = ProjectValidator().validate(project)
        export_warnings = len(validation.warnings)
        for issue in validation.errors:
            findings.append(QuestbookReviewFinding(
                "error", "EXPORT_VALIDATION_ERROR", issue.format()
            ))
        for issue in validation.warnings:
            findings.append(QuestbookReviewFinding(
                "warning", "EXPORT_VALIDATION_WARNING", issue.format()
            ))
    except (OSError, TypeError, ValueError) as exc:
        findings.append(QuestbookReviewFinding(
            "error", "EXPORT_CONVERSION_FAILED", str(exc)
        ))

    if missing_rewards:
        findings.append(QuestbookReviewFinding(
            "review", "MISSING_REWARD_DECISIONS",
            f"{missing_rewards} quests have no reward decision. "
            "Confirm intentional no-reward quests or add rewards.",
        ))

    roots = sum(not graph.get(identifier) for identifier in graph)
    leaves = sum(dependents.get(identifier, 0) == 0 for identifier in graph)
    return QuestbookReview(
        pack_name=blueprint.pack_name,
        requested_quests=blueprint.requested_quests,
        quests=len(rows),
        chapters=len(blueprint.chapters),
        dependency_edges=sum(len(dependencies) for dependencies in graph.values()),
        root_quests=roots,
        leaf_quests=leaves,
        maximum_depth=max(depths.values(), default=0),
        low_confidence_quests=low_confidence,
        manual_review_quests=manual_review,
        weak_descriptions=weak_descriptions,
        missing_reward_decisions=missing_rewards,
        oversized_chapters=oversized_chapters,
        bottleneck_quests=bottlenecks,
        duplicate_objectives=duplicate_objectives,
        export_validation_warnings=export_warnings,
        findings=tuple(sorted(findings, key=_finding_sort_key)),
    )


def review_modpack_questbook(
    path: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    min_description_words: int = DEFAULT_MIN_DESCRIPTION_WORDS,
    max_chapter_quests: int = DEFAULT_MAX_CHAPTER_QUESTS,
    bottleneck_dependents: int = DEFAULT_BOTTLENECK_DEPENDENTS,
    description_style: str = "guided",
    reward_policy: str = "unassigned",
) -> QuestbookReview:
    blueprint = generate_quest_blueprint(
        path,
        target_quests=target_quests,
        chapter_size=chapter_size,
    )
    description_plan = plan_quest_descriptions(blueprint, style=description_style)
    if description_plan.is_clean:
        blueprint = description_plan.blueprint
    else:
        blueprint = replace(
            blueprint,
            errors=tuple((*blueprint.errors, *description_plan.errors)),
        )
    if reward_policy != "unassigned":
        reward_plan = plan_quest_rewards(blueprint, policy=reward_policy)
        if reward_plan.is_clean:
            blueprint = reward_plan.blueprint
        else:
            blueprint = replace(
                blueprint,
                errors=tuple((*blueprint.errors, *reward_plan.errors)),
            )
    return review_quest_blueprint(
        blueprint,
        low_confidence_threshold=low_confidence_threshold,
        min_description_words=min_description_words,
        max_chapter_quests=max_chapter_quests,
        bottleneck_dependents=bottleneck_dependents,
    )
