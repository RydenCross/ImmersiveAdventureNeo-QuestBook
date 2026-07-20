from model import Project

from content.apotheosis.advanced_gear_enchanting import (
    build_apotheosis_advanced_gear_enchanting,
)
from content.apotheosis.foundations import build_apotheosis_foundations
from content.apotheosis.mythic_mastery import build_apotheosis_mythic_mastery


def build_apotheosis(project: Project, ars_complete: str) -> str:
    chapter, foundations_complete = build_apotheosis_foundations(project, ars_complete)
    mastery_complete = build_apotheosis_advanced_gear_enchanting(chapter, foundations_complete)
    build_apotheosis_mythic_mastery(chapter, mastery_complete)
    return mastery_complete


__all__ = ["build_apotheosis"]
