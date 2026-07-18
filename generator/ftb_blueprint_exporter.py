from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
from typing import Iterable

from generator.ids import UUIDService
from generator.parser import FTBQuestParser
from generator.progression_planner import BlueprintQuest, QuestBlueprint, generate_quest_blueprint
from generator.reward_planner import plan_quest_rewards
from generator.validator import ProjectValidator
from generator.writer import FTBQuestWriter
from model import (
    Chapter,
    Dependency,
    Position,
    Project,
    Quest,
    Reward,
    RewardType,
    Task,
    TaskType,
)

DEFAULT_FTB_QUESTS_VERSION = "13"
_SAFE_SLUG = re.compile(r"[^a-z0-9_]+")
_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


def _slug(value: str) -> str:
    normalized = _SAFE_SLUG.sub("_", value.casefold()).strip("_")
    return normalized or "generated"


def _ftb_id(value: int) -> str:
    return f"{value & ((1 << 64) - 1):016X}"


def _scope(blueprint: QuestBlueprint) -> str:
    return "/".join(
        (
            "generated",
            _slug(blueprint.pack_name),
            _slug(blueprint.minecraft_version or "unknown"),
            _slug(blueprint.loader or "unknown"),
        )
    )


def _quest_icon(quest: BlueprintQuest) -> str:
    if quest.objective.objective_type == "item":
        return quest.objective.identifier
    if quest.prerequisite_items:
        return quest.prerequisite_items[0]
    return "minecraft:knowledge_book"


def _task_for(quest: BlueprintQuest, *, task_id: str) -> Task:
    if quest.objective.objective_type == "item":
        return Task(
            id=task_id,
            type=TaskType.ITEM,
            data={
                "item": {"id": quest.objective.identifier, "count": 1},
                "count": quest.objective.count,
            },
        )
    if quest.objective.objective_type == "advancement":
        return Task(
            id=task_id,
            type=TaskType.ADVANCEMENT,
            data={"advancement": quest.objective.identifier, "criterion": ""},
        )
    raise ValueError(
        f"unsupported blueprint objective type '{quest.objective.objective_type}' "
        f"for quest {quest.quest_id}"
    )


def _rewards_for(quest: BlueprintQuest, *, ids: UUIDService, quest_key: str) -> list[Reward]:
    if quest.reward_decision not in {"unassigned", "none", "rewarded"}:
        raise ValueError(
            f"invalid reward decision '{quest.reward_decision}' for quest {quest.quest_id}"
        )
    if quest.reward_decision == "none" and quest.rewards:
        raise ValueError(f"no-reward quest {quest.quest_id} contains reward definitions")
    if quest.reward_decision == "rewarded" and not quest.rewards:
        raise ValueError(f"rewarded quest {quest.quest_id} has no reward definitions")

    rewards: list[Reward] = []
    for index, reward in enumerate(quest.rewards):
        if reward.reward_type != "item":
            raise ValueError(
                f"unsupported blueprint reward type '{reward.reward_type}' "
                f"for quest {quest.quest_id}"
            )
        if not _RESOURCE_LOCATION.fullmatch(reward.identifier):
            raise ValueError(
                f"invalid blueprint reward item '{reward.identifier}' "
                f"for quest {quest.quest_id}"
            )
        if isinstance(reward.count, bool) or not isinstance(reward.count, int) or reward.count < 1:
            raise ValueError(
                f"blueprint reward count must be positive for quest {quest.quest_id}"
            )
        reward_key = f"{quest_key}/reward/{index}/{reward.identifier}"
        rewards.append(Reward(
            id=_ftb_id(ids.reward(quest_key, reward_key).int),
            type=RewardType.ITEM,
            data={
                "item": {"id": reward.identifier, "count": 1},
                "count": reward.count,
            },
            raw_data={
                "generated_reason": reward.reason,
                "generated_reward_decision": quest.reward_decision,
            },
        ))
    return rewards


def blueprint_to_project(
    blueprint: QuestBlueprint,
    *,
    version: str = DEFAULT_FTB_QUESTS_VERSION,
) -> Project:
    """Convert a reviewable blueprint into the repository's FTB Quests model.

    Stable UUIDv5-derived FTB IDs are generated from the pack identity, chapter ID,
    and quest ID. The conversion never executes mod code or invents objectives.
    """
    if blueprint.errors:
        raise ValueError("cannot export a blueprint with errors: " + "; ".join(blueprint.errors))
    if not blueprint.chapters:
        raise ValueError("cannot export an empty quest blueprint")

    ids = UUIDService()
    scope = _scope(blueprint)
    project = Project(name=blueprint.pack_name or "Generated Modpack Questbook", version=version)

    quest_ids: dict[str, str] = {}
    chapter_ids: dict[str, str] = {}
    for chapter in blueprint.chapters:
        chapter_key = f"{scope}/chapter/{chapter.chapter_id}"
        chapter_ids[chapter.chapter_id] = _ftb_id(ids.chapter(chapter_key).int)
        for quest in chapter.quests:
            if quest.quest_id in quest_ids:
                raise ValueError(f"duplicate blueprint quest id: {quest.quest_id}")
            quest_key = f"{scope}/quest/{quest.quest_id}"
            quest_ids[quest.quest_id] = _ftb_id(ids.quest(quest_key).int)

    for chapter in blueprint.chapters:
        chapter_key = f"{scope}/chapter/{chapter.chapter_id}"
        chapter_uuid = ids.chapter(chapter_key)
        first_quest = chapter.quests[0] if chapter.quests else None
        icon = _quest_icon(first_quest) if first_quest else "minecraft:book"
        model_chapter = Chapter(
            id=_slug(chapter.chapter_id),
            uuid=chapter_uuid,
            ftb_id=chapter_ids[chapter.chapter_id],
            title=chapter.title,
            description=(
                f"Generated {chapter.category} progression for {chapter.title}. "
                "Review objectives and rewards before publishing."
            ),
            icon=icon,
            raw_data={"order_index": chapter.order, "quest_links": []},
        )

        for blueprint_quest in chapter.quests:
            ftb_quest_id = quest_ids[blueprint_quest.quest_id]
            missing = tuple(
                dependency
                for dependency in blueprint_quest.prerequisite_quests
                if dependency not in quest_ids
            )
            if missing:
                raise ValueError(
                    f"quest {blueprint_quest.quest_id} has missing dependencies: "
                    + ", ".join(missing)
                )
            quest_key = f"{scope}/quest/{blueprint_quest.quest_id}"
            task_key = f"{quest_key}/task/objective"
            task_id = _ftb_id(ids.task(quest_key, task_key).int)
            raw_data = {
                "generated_source": blueprint_quest.source_kind,
                "generated_source_id": blueprint_quest.source_id,
                "generated_confidence": blueprint_quest.confidence,
                "generated_review_required": blueprint_quest.review_required,
                "generated_reward_decision": blueprint_quest.reward_decision,
            }
            model_chapter.add_quest(
                Quest(
                    id=ftb_quest_id,
                    uuid=ids.quest(quest_key),
                    ftb_id=ftb_quest_id,
                    title=blueprint_quest.title,
                    description=blueprint_quest.description,
                    icon=_quest_icon(blueprint_quest),
                    tasks=[_task_for(blueprint_quest, task_id=task_id)],
                    rewards=_rewards_for(blueprint_quest, ids=ids, quest_key=quest_key),
                    dependencies=[
                        Dependency(quest_ids[dependency])
                        for dependency in blueprint_quest.prerequisite_quests
                    ],
                    position=Position(float(blueprint_quest.x), float(blueprint_quest.y)),
                    raw_data=raw_data,
                )
            )
        project.add_chapter(model_chapter)

    report = ProjectValidator().validate(project)
    if not report.is_valid:
        raise ValueError(
            "generated FTB Quests project failed validation: "
            + "; ".join(issue.format() for issue in report.errors)
        )
    return project


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class FTBQuestExportResult:
    destination: str
    quests_root: str
    pack_name: str
    chapters: int
    quests: int
    tasks: int
    dependency_edges: int
    files: tuple[str, ...]
    tree_sha256: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "destination": self.destination,
            "quests_root": self.quests_root,
            "pack_name": self.pack_name,
            "summary": {
                "chapters": self.chapters,
                "quests": self.quests,
                "tasks": self.tasks,
                "dependency_edges": self.dependency_edges,
                "files": len(self.files),
            },
            "files": list(self.files),
            "tree_sha256": self.tree_sha256,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"FTB Quests blueprint export: {'PASS' if self.is_clean else 'FAIL'}",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Destination: {self.destination}.",
            f"Chapters: {self.chapters}.",
            f"Quests: {self.quests}.",
            f"Tasks: {self.tasks}.",
            f"Dependency edges: {self.dependency_edges}.",
            f"Files: {len(self.files)}.",
            f"Tree SHA-256: {self.tree_sha256 or '<none>'}.",
        ]
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def export_quest_blueprint(
    blueprint: QuestBlueprint,
    destination: Path,
    *,
    version: str = DEFAULT_FTB_QUESTS_VERSION,
) -> FTBQuestExportResult:
    """Write a blueprint as a clean FTB Quests directory tree.

    A staging directory prevents stale chapter files from surviving a later export.
    The completed tree is parsed again before it replaces the requested destination.
    """
    destination = Path(destination)
    errors: list[str] = []
    warnings = list(blueprint.warnings)
    try:
        project = blueprint_to_project(blueprint, version=version)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="ftb-quest-export-", dir=destination.parent) as temporary:
            staged_destination = Path(temporary) / destination.name
            staged_quests_root = FTBQuestWriter().write(project, staged_destination)
            restored = FTBQuestParser().load(staged_quests_root)
            validation = ProjectValidator().validate(restored)
            if not validation.is_valid:
                raise ValueError(
                    "exported SNBT failed round-trip validation: "
                    + "; ".join(issue.format() for issue in validation.errors)
                )
            if len(restored.chapters) != len(project.chapters) or len(restored.quests) != len(project.quests):
                raise ValueError("exported SNBT round trip changed chapter or quest counts")
            if destination.exists():
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            shutil.move(str(staged_destination), str(destination))
    except (OSError, TypeError, ValueError) as exc:
        errors.append(str(exc))
        return FTBQuestExportResult(
            destination=destination.as_posix(),
            quests_root="",
            pack_name=blueprint.pack_name,
            chapters=0,
            quests=0,
            tasks=0,
            dependency_edges=0,
            files=(),
            tree_sha256="",
            warnings=tuple(sorted(set(warnings))),
            errors=tuple(errors),
        )

    quests_root = destination if destination.name == "quests" else destination / "quests"
    restored = FTBQuestParser().load(quests_root)
    files = tuple(
        path.relative_to(destination).as_posix()
        for path in sorted(
            (item for item in destination.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix(),
        )
    )
    return FTBQuestExportResult(
        destination=destination.as_posix(),
        quests_root=quests_root.as_posix(),
        pack_name=blueprint.pack_name,
        chapters=len(restored.chapters),
        quests=len(restored.quests),
        tasks=sum(len(quest.tasks) for quest in restored.quests),
        dependency_edges=sum(len(quest.dependencies) for quest in restored.quests),
        files=files,
        tree_sha256=_tree_digest(destination),
        warnings=tuple(sorted(set(warnings))),
        errors=(),
    )


def export_modpack_questbook(
    source: Path,
    destination: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    reward_policy: str = "unassigned",
    version: str = DEFAULT_FTB_QUESTS_VERSION,
) -> FTBQuestExportResult:
    blueprint = generate_quest_blueprint(
        source,
        target_quests=target_quests,
        chapter_size=chapter_size,
    )
    if reward_policy != "unassigned":
        reward_plan = plan_quest_rewards(blueprint, policy=reward_policy)
        if not reward_plan.is_clean:
            return FTBQuestExportResult(
                destination=Path(destination).as_posix(),
                quests_root="",
                pack_name=blueprint.pack_name,
                chapters=0,
                quests=0,
                tasks=0,
                dependency_edges=0,
                files=(),
                tree_sha256="",
                warnings=reward_plan.warnings,
                errors=reward_plan.errors,
            )
        blueprint = reward_plan.blueprint
    return export_quest_blueprint(blueprint, destination, version=version)
