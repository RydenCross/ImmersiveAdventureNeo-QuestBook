from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable

from generator.modpack_content_scanner import ModpackContentScan, QuestCandidate, scan_modpack_content
from generator.modpack_scanner import ModpackProfile, PackMod, scan_modpack

MIN_TARGET_QUESTS = 1
MAX_TARGET_QUESTS = 5000
MIN_CHAPTER_SIZE = 5
MAX_CHAPTER_SIZE = 100

_CATEGORY_ORDER = {
    "technology": 0,
    "magic": 1,
    "storage": 2,
    "farming": 3,
    "exploration": 4,
    "combat": 5,
    "utility": 6,
    "unknown": 7,
    "library": 8,
}


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", value.casefold()).strip("_")
    return normalized or "unknown"


@dataclass(frozen=True, slots=True)
class BlueprintObjective:
    objective_type: str
    identifier: str
    count: int = 1

    def to_dict(self) -> dict[str, object]:
        return {"type": self.objective_type, "id": self.identifier, "count": self.count}


@dataclass(frozen=True, slots=True)
class BlueprintReward:
    reward_type: str
    identifier: str
    count: int = 1
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.reward_type,
            "id": self.identifier,
            "count": self.count,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class BlueprintQuest:
    quest_id: str
    candidate_id: str
    title: str
    description: str
    objective: BlueprintObjective
    prerequisite_quests: tuple[str, ...]
    prerequisite_items: tuple[str, ...]
    prerequisite_tags: tuple[str, ...]
    source_kind: str
    source_id: str
    confidence: float
    score: int
    x: int
    y: int
    review_required: bool
    reward_decision: str = "unassigned"
    rewards: tuple[BlueprintReward, ...] = ()
    difficulty: str = "normal"
    hidden: bool = False
    optional: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "quest_id": self.quest_id,
            "candidate_id": self.candidate_id,
            "title": self.title,
            "description": self.description,
            "objective": self.objective.to_dict(),
            "prerequisite_quests": list(self.prerequisite_quests),
            "prerequisite_items": list(self.prerequisite_items),
            "prerequisite_tags": list(self.prerequisite_tags),
            "source": {"kind": self.source_kind, "id": self.source_id},
            "confidence": self.confidence,
            "score": self.score,
            "position": {"x": self.x, "y": self.y},
            "review_required": self.review_required,
            "reward_decision": self.reward_decision,
            "rewards": [reward.to_dict() for reward in self.rewards],
            "difficulty": self.difficulty,
            "hidden": self.hidden,
            "optional": self.optional,
        }


@dataclass(frozen=True, slots=True)
class BlueprintChapter:
    chapter_id: str
    title: str
    category: str
    mod_id: str
    order: int
    prerequisite_chapters: tuple[str, ...]
    quests: tuple[BlueprintQuest, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chapter_id": self.chapter_id,
            "title": self.title,
            "category": self.category,
            "mod_id": self.mod_id,
            "order": self.order,
            "prerequisite_chapters": list(self.prerequisite_chapters),
            "quest_count": len(self.quests),
            "quests": [quest.to_dict() for quest in self.quests],
        }


@dataclass(frozen=True, slots=True)
class QuestBlueprint:
    source_path: str
    source_format: str
    pack_name: str
    minecraft_version: str
    loader: str
    requested_quests: int
    available_candidates: int
    chapters: tuple[BlueprintChapter, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def quest_count(self) -> int:
        return sum(len(chapter.quests) for chapter in self.chapters)

    @property
    def shortfall(self) -> int:
        return max(0, self.requested_quests - self.quest_count)

    @property
    def dependency_edges(self) -> int:
        return sum(
            len(quest.prerequisite_quests)
            for chapter in self.chapters
            for quest in chapter.quests
        )

    @property
    def review_required(self) -> int:
        return sum(
            quest.review_required
            for chapter in self.chapters
            for quest in chapter.quests
        )

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "source": {"path": self.source_path, "format": self.source_format},
            "pack": {
                "name": self.pack_name,
                "minecraft": self.minecraft_version,
                "loader": self.loader,
            },
            "summary": {
                "requested_quests": self.requested_quests,
                "available_candidates": self.available_candidates,
                "selected_quests": self.quest_count,
                "shortfall": self.shortfall,
                "chapters": len(self.chapters),
                "dependency_edges": self.dependency_edges,
                "review_required": self.review_required,
            },
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest blueprint: {'PASS' if self.is_clean else 'FAIL'}",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Minecraft: {self.minecraft_version or '<unknown>'}.",
            f"Loader: {self.loader or '<unknown>'}.",
            f"Requested quests: {self.requested_quests}.",
            f"Selected quests: {self.quest_count}.",
            f"Available candidates: {self.available_candidates}.",
            f"Chapters: {len(self.chapters)}.",
            f"Dependency edges: {self.dependency_edges}.",
            f"Review required: {self.review_required}.",
            f"Shortfall: {self.shortfall}.",
        ]
        lines.extend(
            f"Chapter {chapter.order + 1}: {chapter.title} ({len(chapter.quests)} quests)."
            for chapter in self.chapters
        )
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def _candidate_priority(candidate: QuestCandidate) -> tuple[int, float, str]:
    return (-candidate.score, -candidate.confidence, candidate.candidate_id)


def _round_robin_candidates(candidates: Iterable[QuestCandidate]) -> tuple[QuestCandidate, ...]:
    grouped: dict[str, list[QuestCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.mod_id, []).append(candidate)
    for values in grouped.values():
        values.sort(key=_candidate_priority)
    result: list[QuestCandidate] = []
    mod_ids = sorted(grouped)
    while any(grouped.values()):
        for mod_id in mod_ids:
            if grouped[mod_id]:
                result.append(grouped[mod_id].pop(0))
    return tuple(result)


def _dependency_closure(
    candidate_id: str,
    candidates: dict[str, QuestCandidate],
    selected: set[str],
) -> tuple[str, ...]:
    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(identifier: str) -> None:
        if identifier in selected or identifier in visited:
            return
        if identifier in visiting:
            return
        candidate = candidates.get(identifier)
        if candidate is None:
            return
        visiting.add(identifier)
        for dependency in sorted(candidate.prerequisite_candidates):
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)
        ordered.append(identifier)

    visit(candidate_id)
    return tuple(ordered)


def _select_candidates(candidates: tuple[QuestCandidate, ...], target: int) -> tuple[QuestCandidate, ...]:
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    selected: set[str] = set()
    for candidate in _round_robin_candidates(candidates):
        closure = _dependency_closure(candidate.candidate_id, by_id, selected)
        if len(selected) + len(closure) > target:
            continue
        selected.update(closure)
        if len(selected) >= target:
            break
    return _topological_order(tuple(by_id[identifier] for identifier in selected))


def _topological_order(candidates: tuple[QuestCandidate, ...]) -> tuple[QuestCandidate, ...]:
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    remaining = {
        identifier: {dep for dep in candidate.prerequisite_candidates if dep in by_id}
        for identifier, candidate in by_id.items()
    }
    ordered: list[QuestCandidate] = []
    while remaining:
        ready = sorted(
            (identifier for identifier, deps in remaining.items() if not deps),
            key=lambda identifier: _candidate_priority(by_id[identifier]),
        )
        if not ready:
            # The content scanner already removes cycles. Keep deterministic output
            # and let validation surface the unexpected cycle if one is introduced.
            ready = [min(remaining)]
        for identifier in ready:
            ordered.append(by_id[identifier])
            remaining.pop(identifier, None)
            for dependencies in remaining.values():
                dependencies.discard(identifier)
    return tuple(ordered)


def _candidate_depths(candidates: tuple[QuestCandidate, ...]) -> dict[str, int]:
    depths: dict[str, int] = {}
    selected = {candidate.candidate_id for candidate in candidates}
    for candidate in candidates:
        dependencies = [depths.get(dep, 0) for dep in candidate.prerequisite_candidates if dep in selected]
        depths[candidate.candidate_id] = (max(dependencies) + 1) if dependencies else 0
    return depths


def _mod_metadata(profile: ModpackProfile, mod_id: str) -> tuple[str, str]:
    matching: PackMod | None = next((mod for mod in profile.mods if mod.mod_id == mod_id), None)
    if matching is None:
        return mod_id.replace("_", " ").title(), "unknown"
    return matching.display_name, matching.category


def _build_chapters(
    profile: ModpackProfile,
    candidates: tuple[QuestCandidate, ...],
    chapter_size: int,
) -> tuple[BlueprintChapter, ...]:
    by_mod: dict[str, list[QuestCandidate]] = {}
    for candidate in candidates:
        by_mod.setdefault(candidate.mod_id, []).append(candidate)

    mod_order = sorted(
        by_mod,
        key=lambda mod_id: (
            _CATEGORY_ORDER.get(_mod_metadata(profile, mod_id)[1], 99),
            _mod_metadata(profile, mod_id)[0].casefold(),
            mod_id,
        ),
    )
    chapter_candidates: list[tuple[str, str, str, int, tuple[QuestCandidate, ...]]] = []
    candidate_to_chapter: dict[str, str] = {}
    for mod_id in mod_order:
        display_name, category = _mod_metadata(profile, mod_id)
        values = by_mod[mod_id]
        parts = [values[index : index + chapter_size] for index in range(0, len(values), chapter_size)]
        for part_index, part in enumerate(parts, start=1):
            chapter_id = _slug(mod_id) if len(parts) == 1 else f"{_slug(mod_id)}_{part_index}"
            title = display_name if len(parts) == 1 else f"{display_name} {part_index}"
            chapter_candidates.append((chapter_id, title, category, part_index, tuple(part)))
            for candidate in part:
                candidate_to_chapter[candidate.candidate_id] = chapter_id

    depths = _candidate_depths(candidates)
    chapter_order = {entry[0]: index for index, entry in enumerate(chapter_candidates)}
    chapters: list[BlueprintChapter] = []
    for chapter_id, title, category, part_index, values in chapter_candidates:
        prerequisite_chapters: set[str] = set()
        if part_index > 1:
            prerequisite_chapters.add(f"{_slug(values[0].mod_id)}_{part_index - 1}")
        depth_rows: dict[int, int] = {}
        quests: list[BlueprintQuest] = []
        for candidate in values:
            for dependency in candidate.prerequisite_candidates:
                dependency_chapter = candidate_to_chapter.get(dependency)
                if dependency_chapter and dependency_chapter != chapter_id:
                    prerequisite_chapters.add(dependency_chapter)
            depth = depths.get(candidate.candidate_id, 0)
            row = depth_rows.get(depth, 0)
            depth_rows[depth] = row + 1
            quests.append(BlueprintQuest(
                quest_id=candidate.candidate_id,
                candidate_id=candidate.candidate_id,
                title=candidate.title,
                description=candidate.description,
                objective=BlueprintObjective(candidate.objective_type, candidate.objective_id),
                prerequisite_quests=tuple(sorted(candidate.prerequisite_candidates)),
                prerequisite_items=candidate.prerequisite_items,
                prerequisite_tags=candidate.prerequisite_tags,
                source_kind=candidate.source_kind,
                source_id=candidate.source_id,
                confidence=candidate.confidence,
                score=candidate.score,
                x=depth * 3,
                y=row * 2,
                review_required=candidate.confidence < 0.75 or candidate.source_kind == "registry",
            ))
        chapters.append(BlueprintChapter(
            chapter_id=chapter_id,
            title=title,
            category=category,
            mod_id=values[0].mod_id,
            order=chapter_order[chapter_id],
            prerequisite_chapters=tuple(sorted(prerequisite_chapters, key=lambda value: chapter_order.get(value, 9999))),
            quests=tuple(quests),
        ))
    return tuple(chapters)


def plan_quest_blueprint(
    profile: ModpackProfile,
    content: ModpackContentScan,
    *,
    target_quests: int,
    chapter_size: int = 40,
) -> QuestBlueprint:
    errors = list(profile.errors) + list(content.errors)
    warnings = list(profile.warnings) + list(content.warnings)
    if not MIN_TARGET_QUESTS <= target_quests <= MAX_TARGET_QUESTS:
        errors.append(f"target quests must be between {MIN_TARGET_QUESTS} and {MAX_TARGET_QUESTS}")
    if not MIN_CHAPTER_SIZE <= chapter_size <= MAX_CHAPTER_SIZE:
        errors.append(f"chapter size must be between {MIN_CHAPTER_SIZE} and {MAX_CHAPTER_SIZE}")
    safe_target = min(MAX_TARGET_QUESTS, max(MIN_TARGET_QUESTS, target_quests))
    safe_chapter_size = min(MAX_CHAPTER_SIZE, max(MIN_CHAPTER_SIZE, chapter_size))
    selected = _select_candidates(content.candidates, safe_target)
    chapters = _build_chapters(profile, selected, safe_chapter_size) if selected else ()
    if len(selected) < safe_target and not errors:
        warnings.append(
            f"only {len(selected)} progression-safe candidates were available for target {safe_target}"
        )
    if not selected and not errors:
        warnings.append("no quest candidates were available for blueprint generation")
    return QuestBlueprint(
        source_path=content.source_path,
        source_format=content.source_format,
        pack_name=content.pack_name,
        minecraft_version=content.minecraft_version,
        loader=content.loader,
        requested_quests=safe_target,
        available_candidates=len(content.candidates),
        chapters=chapters,
        warnings=tuple(sorted(set(warnings))),
        errors=tuple(sorted(set(errors))),
    )


def generate_quest_blueprint(
    path: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
) -> QuestBlueprint:
    profile = scan_modpack(path)
    if target_quests is None:
        target = profile.quest_target.get("target", 0) or 25
    else:
        target = target_quests
    content = scan_modpack_content(path, candidate_limit=min(MAX_TARGET_QUESTS, max(1, target)))
    return plan_quest_blueprint(
        profile,
        content,
        target_quests=target,
        chapter_size=chapter_size,
    )
