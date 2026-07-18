from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.ftb_blueprint_exporter import blueprint_to_project
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.quest_description_generator import plan_quest_descriptions
from generator.questbook_review import review_quest_blueprint


@dataclass(frozen=True, slots=True)
class QuestDescriptionContract:
    descriptions_generated: bool
    recipe_guidance_generated: bool
    advancement_guidance_generated: bool
    prerequisites_named: bool
    low_confidence_review_guidance: bool
    weak_descriptions_resolved: bool
    exporter_round_trip: bool
    deterministic_output: bool
    style_scaling: bool
    invalid_style_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.descriptions_generated,
            self.recipe_guidance_generated,
            self.advancement_guidance_generated,
            self.prerequisites_named,
            self.low_confidence_review_guidance,
            self.weak_descriptions_resolved,
            self.exporter_round_trip,
            self.deterministic_output,
            self.style_scaling,
            self.invalid_style_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "descriptions_generated": self.descriptions_generated,
            "recipe_guidance_generated": self.recipe_guidance_generated,
            "advancement_guidance_generated": self.advancement_guidance_generated,
            "prerequisites_named": self.prerequisites_named,
            "low_confidence_review_guidance": self.low_confidence_review_guidance,
            "weak_descriptions_resolved": self.weak_descriptions_resolved,
            "exporter_round_trip": self.exporter_round_trip,
            "deterministic_output": self.deterministic_output,
            "style_scaling": self.style_scaling,
            "invalid_style_rejected": self.invalid_style_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Quest description contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Descriptions generated: {'yes' if self.descriptions_generated else 'no'}.",
            f"Recipe guidance generated: {'yes' if self.recipe_guidance_generated else 'no'}.",
            "Advancement guidance generated: "
            f"{'yes' if self.advancement_guidance_generated else 'no'}.",
            f"Prerequisites named: {'yes' if self.prerequisites_named else 'no'}.",
            "Low-confidence review guidance: "
            f"{'yes' if self.low_confidence_review_guidance else 'no'}.",
            f"Weak descriptions resolved: {'yes' if self.weak_descriptions_resolved else 'no'}.",
            f"Exporter round trip: {'yes' if self.exporter_round_trip else 'no'}.",
            f"Deterministic output: {'yes' if self.deterministic_output else 'no'}.",
            f"Style scaling: {'yes' if self.style_scaling else 'no'}.",
            f"Invalid style rejected: {'yes' if self.invalid_style_rejected else 'no'}.",
        ))


def run_quest_description_contract() -> QuestDescriptionContract:
    with TemporaryDirectory(prefix="quest-description-contract-") as temporary:
        pack = Path(temporary) / "description.mrpack"
        _synthetic_pack(pack)
        blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
        chapter = blueprint.chapters[0]
        registry_quest = replace(
            chapter.quests[0],
            source_kind="registry",
            confidence=0.55,
            review_required=True,
        )
        review_blueprint = replace(
            blueprint,
            chapters=(replace(chapter, quests=(registry_quest, *chapter.quests[1:])),),
        )

        concise = plan_quest_descriptions(blueprint, style="concise")
        guided = plan_quest_descriptions(blueprint, style="guided")
        detailed = plan_quest_descriptions(review_blueprint, style="detailed")
        repeat = plan_quest_descriptions(blueprint, style="guided")
        invalid = plan_quest_descriptions(blueprint, style="invalid")

        guided_quests = [quest for item in guided.blueprint.chapters for quest in item.quests]
        detailed_quests = [quest for item in detailed.blueprint.chapters for quest in item.quests]
        recipe_descriptions = [
            quest.description
            for quest in guided_quests
            if quest.source_kind == "recipe"
        ]
        advancement_descriptions = [
            quest.description for quest in guided_quests if quest.source_kind == "advancement"
        ]
        review = review_quest_blueprint(guided.blueprint)
        project = blueprint_to_project(guided.blueprint)

        return QuestDescriptionContract(
            descriptions_generated=(
                guided.generated_descriptions == guided.blueprint.quest_count == 4
            ),
            recipe_guidance_generated=bool(recipe_descriptions)
            and all("recipe" in description.casefold() for description in recipe_descriptions),
            advancement_guidance_generated=bool(advancement_descriptions)
            and all(
                "advancement" in description.casefold()
                for description in advancement_descriptions
            ),
            prerequisites_named=any("Copper Gear" in quest.description for quest in guided_quests),
            low_confidence_review_guidance=any(
                "human reviewer" in quest.description.casefold() for quest in detailed_quests
            ),
            weak_descriptions_resolved=review.weak_descriptions == 0,
            exporter_round_trip=len(project.quests) == guided.blueprint.quest_count,
            deterministic_output=guided.format_json() == repeat.format_json(),
            style_scaling=concise.minimum_words < guided.minimum_words < detailed.minimum_words,
            invalid_style_rejected=not invalid.is_clean and bool(invalid.errors),
        )
