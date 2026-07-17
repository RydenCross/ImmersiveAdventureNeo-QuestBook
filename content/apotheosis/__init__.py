from model import Project

from content.apotheosis.advanced_gear_enchanting import (
    build_apotheosis_advanced_gear_enchanting,
)
from content.apotheosis.foundations import build_apotheosis_foundations


def build_apotheosis(project: Project, ars_complete: str) -> str:
    chapter, foundations_complete = build_apotheosis_foundations(project, ars_complete)
    return build_apotheosis_advanced_gear_enchanting(chapter, foundations_complete)


__all__ = ["build_apotheosis"]
