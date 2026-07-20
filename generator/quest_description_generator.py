from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re

from generator.progression_planner import (
    BlueprintChapter,
    BlueprintQuest,
    QuestBlueprint,
    generate_quest_blueprint,
)

DESCRIPTION_STYLES = ("concise", "guided", "detailed")

_STYLE_MIN_WORDS = {
    "concise": 14,
    "guided": 24,
    "detailed": 36,
}


def _humanize_identifier(identifier: str) -> str:
    value = identifier.removeprefix("#")
    _, _, path = value.partition(":")
    raw = path or value
    raw = raw.rsplit("/", 1)[-1]
    words = re.sub(r"[_\-.]+", " ", raw).strip()
    return words.title() or identifier


def _objective_name(quest: BlueprintQuest) -> str:
    title = quest.title.strip()
    for prefix in ("Craft ", "Obtain ", "Acquire ", "Complete "):
        if title.casefold().startswith(prefix.casefold()):
            title = title[len(prefix) :].strip()
            break
    return title or _humanize_identifier(quest.objective.identifier)


def _natural_join(values: tuple[str, ...]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _quest_index(blueprint: QuestBlueprint) -> dict[str, BlueprintQuest]:
    return {
        quest.quest_id: quest
        for chapter in blueprint.chapters
        for quest in chapter.quests
    }


def _dependent_index(blueprint: QuestBlueprint) -> dict[str, tuple[str, ...]]:
    dependents: dict[str, list[str]] = {
        quest.quest_id: []
        for chapter in blueprint.chapters
        for quest in chapter.quests
    }
    for chapter in blueprint.chapters:
        for quest in chapter.quests:
            for dependency in quest.prerequisite_quests:
                if dependency in dependents:
                    dependents[dependency].append(quest.quest_id)
    return {key: tuple(sorted(values)) for key, values in dependents.items()}


def _base_instruction(quest: BlueprintQuest) -> str:
    objective = _objective_name(quest)
    if quest.objective.objective_type == "advancement":
        return (
            f"Complete the in-game advancement “{objective}”. Follow the criteria shown by "
            "Minecraft or the modpack; this quest finishes when that advancement is awarded."
        )
    if quest.source_kind == "recipe":
        return (
            f"Craft or obtain {objective}, then keep at least {quest.objective.count} in your "
            "inventory so FTB Quests can detect the objective. Use the recipe currently supplied "
            "by this modpack, because pack scripts may change the original mod recipe."
        )
    if quest.source_kind == "registry":
        return (
            f"Obtain {objective} and keep it in your inventory so FTB Quests can detect it. This "
            "objective was inferred from registry data, so confirm its acquisition method in the "
            "pack's recipe viewer or mod guide before publishing the questbook."
        )
    return (
        f"Obtain {objective} and keep at least {quest.objective.count} in your inventory until the "
        "quest completes. Follow the acquisition method available in this modpack."
    )


def _prerequisite_guidance(
    quest: BlueprintQuest,
    *,
    quests: dict[str, BlueprintQuest],
    style: str,
) -> tuple[str, ...]:
    guidance: list[str] = []
    prerequisite_titles = tuple(
        quests[identifier].title
        for identifier in quest.prerequisite_quests
        if identifier in quests
    )
    if prerequisite_titles:
        guidance.append(f"Complete {_natural_join(prerequisite_titles)} first.")

    if style in {"guided", "detailed"} and quest.prerequisite_items:
        items = tuple(_humanize_identifier(item) for item in quest.prerequisite_items[:5])
        suffix = "" if len(quest.prerequisite_items) <= 5 else ", plus other listed inputs"
        guidance.append(f"Known item inputs include {_natural_join(items)}{suffix}.")

    if style in {"guided", "detailed"} and quest.prerequisite_tags:
        tags = tuple(f"#{tag.removeprefix('#')}" for tag in quest.prerequisite_tags[:4])
        suffix = "" if len(quest.prerequisite_tags) <= 4 else ", plus other accepted tags"
        guidance.append(
            "Any ingredient accepted by "
            f"{_natural_join(tags)} may satisfy the tagged inputs{suffix}."
        )
    return tuple(guidance)


def _progression_guidance(
    chapter: BlueprintChapter,
    quest: BlueprintQuest,
    *,
    quests: dict[str, BlueprintQuest],
    dependents: dict[str, tuple[str, ...]],
    style: str,
) -> tuple[str, ...]:
    if style == "concise":
        return ()
    next_titles = tuple(
        quests[identifier].title
        for identifier in dependents.get(quest.quest_id, ())[:4]
        if identifier in quests
    )
    lines: list[str] = []
    if not quest.prerequisite_quests:
        lines.append(f"This is an entry step in the {chapter.title} chapter.")
    if next_titles:
        suffix = "" if len(dependents.get(quest.quest_id, ())) <= 4 else " and later milestones"
        lines.append(f"Completing it unlocks {_natural_join(next_titles)}{suffix}.")
    elif style == "detailed":
        lines.append("This is a terminal milestone for its current generated progression branch.")
    return tuple(lines)


def _source_context(quest: BlueprintQuest, *, style: str) -> tuple[str, ...]:
    if style != "detailed":
        return ()
    if quest.source_kind == "advancement" and quest.description.strip():
        original = quest.description.strip().rstrip(".")
        return (f"The source advancement describes this milestone as: {original}.",)
    if quest.source_kind == "recipe":
        return (
            "The objective was discovered from a recipe bundled with the pack, but the generated "
            "instructions intentionally avoid claiming a specific machine or process that was not "
            "confirmed by the scanner.",
        )
    if quest.source_kind == "registry":
        return (
            "Because no recipe or advancement was discovered for this item, a human "
            "reviewer should confirm that the objective is obtainable and belongs at "
            "this point in progression.",
        )
    return ()


def _description(
    chapter: BlueprintChapter,
    quest: BlueprintQuest,
    *,
    quests: dict[str, BlueprintQuest],
    dependents: dict[str, tuple[str, ...]],
    style: str,
) -> str:
    parts = [_base_instruction(quest)]
    parts.extend(_prerequisite_guidance(quest, quests=quests, style=style))
    parts.extend(
        _progression_guidance(
            chapter,
            quest,
            quests=quests,
            dependents=dependents,
            style=style,
        )
    )
    parts.extend(_source_context(quest, style=style))
    description = " ".join(part.strip() for part in parts if part.strip())
    minimum = _STYLE_MIN_WORDS[style]
    if len(description.split()) < minimum:
        description += " Check the quest objective and current pack recipes before continuing."
    return description


@dataclass(frozen=True, slots=True)
class QuestDescriptionPlan:
    style: str
    blueprint: QuestBlueprint
    generated_descriptions: int
    recipe_instructions: int
    advancement_instructions: int
    registry_instructions: int
    prerequisite_guidance: int
    review_guidance: int
    minimum_words: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.blueprint.is_clean
            and not self.errors
            and self.generated_descriptions == self.blueprint.quest_count
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "style": self.style,
            "summary": {
                "quests": self.blueprint.quest_count,
                "generated_descriptions": self.generated_descriptions,
                "recipe_instructions": self.recipe_instructions,
                "advancement_instructions": self.advancement_instructions,
                "registry_instructions": self.registry_instructions,
                "prerequisite_guidance": self.prerequisite_guidance,
                "review_guidance": self.review_guidance,
                "minimum_words": self.minimum_words,
            },
            "blueprint": self.blueprint.to_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest description plan: {'PASS' if self.is_clean else 'FAIL'}",
            f"Style: {self.style}.",
            f"Quests: {self.blueprint.quest_count}.",
            f"Generated descriptions: {self.generated_descriptions}.",
            f"Recipe instructions: {self.recipe_instructions}.",
            f"Advancement instructions: {self.advancement_instructions}.",
            f"Registry instructions: {self.registry_instructions}.",
            f"Descriptions with prerequisite guidance: {self.prerequisite_guidance}.",
            f"Descriptions with review guidance: {self.review_guidance}.",
            f"Minimum words: {self.minimum_words}.",
        ]
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def plan_quest_descriptions(
    blueprint: QuestBlueprint,
    *,
    style: str = "guided",
) -> QuestDescriptionPlan:
    if style not in DESCRIPTION_STYLES:
        return QuestDescriptionPlan(
            style=style,
            blueprint=blueprint,
            generated_descriptions=0,
            recipe_instructions=0,
            advancement_instructions=0,
            registry_instructions=0,
            prerequisite_guidance=0,
            review_guidance=0,
            minimum_words=0,
            warnings=(),
            errors=(f"description style must be one of: {', '.join(DESCRIPTION_STYLES)}",),
        )

    quests = _quest_index(blueprint)
    dependents = _dependent_index(blueprint)
    updated_chapters: list[BlueprintChapter] = []
    generated = recipe_count = advancement_count = registry_count = 0
    prerequisite_count = review_count = 0
    minimum_words = 10_000

    for chapter in blueprint.chapters:
        updated_quests: list[BlueprintQuest] = []
        for quest in chapter.quests:
            description = _description(
                chapter,
                quest,
                quests=quests,
                dependents=dependents,
                style=style,
            )
            word_count = len(description.split())
            minimum_words = min(minimum_words, word_count)
            generated += 1
            recipe_count += quest.source_kind == "recipe"
            advancement_count += quest.source_kind == "advancement"
            registry_count += quest.source_kind == "registry"
            prerequisite_count += bool(
                quest.prerequisite_quests or quest.prerequisite_items or quest.prerequisite_tags
            )
            review_count += quest.source_kind == "registry"
            updated_quests.append(replace(quest, description=description))
        updated_chapters.append(replace(chapter, quests=tuple(updated_quests)))

    enriched = replace(blueprint, chapters=tuple(updated_chapters))
    if not generated:
        minimum_words = 0
    return QuestDescriptionPlan(
        style=style,
        blueprint=enriched,
        generated_descriptions=generated,
        recipe_instructions=recipe_count,
        advancement_instructions=advancement_count,
        registry_instructions=registry_count,
        prerequisite_guidance=prerequisite_count,
        review_guidance=review_count,
        minimum_words=minimum_words,
        warnings=blueprint.warnings,
        errors=(),
    )


def generate_quest_description_plan(
    source: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    style: str = "guided",
) -> QuestDescriptionPlan:
    blueprint = generate_quest_blueprint(
        source,
        target_quests=target_quests,
        chapter_size=chapter_size,
    )
    return plan_quest_descriptions(blueprint, style=style)
